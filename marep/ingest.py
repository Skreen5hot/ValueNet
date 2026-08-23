"""Build a MAREP sprint input substrate from real repository data.

MAREP v2.2 §7. Until this exists the substrate has to be hand-authored, which
makes the grounding gate circular: evidence is "verified" against a file
somebody typed. This module produces the substrate from sources that exist
independently of the retrospective — git history, pull requests, CI runs — so
that verification means something.

Two properties matter more than coverage breadth:

**Determinism.** The same repository and the same date range produce byte-
identical output, because records are sorted before identifiers are minted.

That is weaker than it sounds, and worth being exact about: sorting keeps
identifiers stable only while the record *set* is unchanged. Add one file to a
scanned directory and every later identifier shifts. Evidence meant to outlive
a single run should therefore cite a record's `ref` — a commit SHA, a
`check:scope` pair — which is content-derived and survives. `Substrate.resolve`
accepts either.

**Honest gaps.** Every record type in the schema gets a coverage entry. A
source that is absent, unauthenticated, or erroring is reported as unavailable
with the real reason (§7.3), never silently omitted. A retrospective that
concludes things about deployment while `deploy` was never collected should
say so on the face of its own input.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from . import ontology_source as onto
from .substrate import RECORD_TYPES
from .validate import validate_substrate

#: Identifier prefix per record type. Stable; changing one invalidates
#: evidence in any retrospective already built against this substrate.
ID_PREFIX: dict[str, str] = {
    "commit": "CMT",
    "pull_request": "PR",
    "ticket": "TIC",
    "ci_run": "CI",
    "deploy": "DEP",
    "incident": "INC",
    "metric": "MET",
    "review": "REV",
    "document": "DOC",
    "note": "NOTE",
}

SUMMARY_LIMIT = 200

#: Field separator for `git log --format`. Not NUL: Windows CreateProcess
#: rejects an embedded null in an argv entry, so the obvious choice is
#: unusable on one of the two platforms this has to run on.
SEP = "\x1f"


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout, proc.stderr


def _iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _clip(text: str, limit: int = SUMMARY_LIMIT) -> str:
    flat = " ".join((text or "").split())
    if not flat:
        return "(no description)"
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


@dataclass
class Collected:
    """What one source produced, and whether it was reachable at all."""

    type: str
    records: list[dict[str, Any]] = field(default_factory=list)
    available: bool = True
    reason: str = ""


# ----------------------------------------------------------------------
# sources
# ----------------------------------------------------------------------

def collect_commits(repo: Path, since: str, until: str) -> Collected:
    """Commits from git log. The one source that needs no network or auth."""
    if not (repo / ".git").exists():
        return Collected("commit", available=False, reason=f"{repo} is not a git repository")
    code, out, err = _run([
        "git", "log", f"--since={since}", f"--until={until}",
        f"--format=COMMIT{SEP}%H{SEP}%aI{SEP}%an{SEP}%s", "--numstat",
    ], cwd=repo)
    if code != 0:
        return Collected("commit", available=False, reason=f"git log failed: {_clip(err, 120)}")

    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in out.splitlines():
        if line.startswith(f"COMMIT{SEP}"):
            _, sha, ts, author, subject = line.split(SEP, 4)
            current = {
                "type": "commit", "ref": sha, "timestamp": ts,
                "summary": _clip(subject),
                "payload": {"author": author, "files_changed": 0,
                            "insertions": 0, "deletions": 0, "short_sha": sha[:8]},
            }
            records.append(current)
        elif line.strip() and current is not None:
            parts = line.split("\t")
            if len(parts) == 3:
                add, dele, _path = parts
                current["payload"]["files_changed"] += 1
                current["payload"]["insertions"] += int(add) if add.isdigit() else 0
                current["payload"]["deletions"] += int(dele) if dele.isdigit() else 0
    return Collected("commit", records=records)


def _gh_available() -> tuple[bool, str]:
    if shutil.which("gh") is None:
        return False, "the gh CLI is not installed"
    code, _out, err = _run(["gh", "auth", "status"], timeout=30)
    if code != 0:
        return False, f"gh is not authenticated: {_clip(err, 100)}"
    return True, ""


def _gh_json(args: list[str], repo: Path) -> tuple[list[dict[str, Any]] | None, str]:
    code, out, err = _run(["gh", *args], cwd=repo)
    if code != 0:
        return None, _clip(err, 140)
    try:
        data = json.loads(out or "[]")
    except json.JSONDecodeError as exc:
        return None, f"unparseable gh output: {exc}"
    return (data if isinstance(data, list) else []), ""


def _gh_source(
    rtype: str, args: list[str], repo: Path, since: str, until: str,
    to_record: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> Collected:
    ok, why = _gh_available()
    if not ok:
        return Collected(rtype, available=False, reason=why)
    data, err = _gh_json(args, repo)
    if data is None:
        return Collected(rtype, available=False, reason=f"gh query failed: {err}")
    lo, hi = _iso(since), _iso(until)
    records = []
    for item in data:
        rec = to_record(item)
        if rec is None:
            continue
        ts = _iso(rec["timestamp"])
        if ts is None or (lo and ts < lo) or (hi and ts > hi):
            continue
        records.append(rec)
    return Collected(rtype, records=records)


def collect_pull_requests(repo: Path, since: str, until: str, limit: int = 300) -> Collected:
    def to_record(pr: dict[str, Any]) -> dict[str, Any] | None:
        ts = pr.get("mergedAt") or pr.get("createdAt")
        if not ts:
            return None
        return {
            "type": "pull_request", "ref": f"#{pr['number']}", "uri": pr.get("url", ""),
            "timestamp": ts, "summary": _clip(pr.get("title", "")),
            "payload": {"state": pr.get("state", ""),
                        "author": (pr.get("author") or {}).get("login", ""),
                        "merged": bool(pr.get("mergedAt"))},
        }
    return _gh_source("pull_request", [
        "pr", "list", "--state", "all", "--limit", str(limit),
        "--json", "number,title,url,createdAt,mergedAt,author,state",
    ], repo, since, until, to_record)


def collect_tickets(repo: Path, since: str, until: str, limit: int = 300) -> Collected:
    def to_record(it: dict[str, Any]) -> dict[str, Any] | None:
        if not it.get("createdAt"):
            return None
        return {
            "type": "ticket", "ref": f"#{it['number']}", "uri": it.get("url", ""),
            "timestamp": it["createdAt"], "summary": _clip(it.get("title", "")),
            "payload": {"state": it.get("state", ""),
                        "author": (it.get("author") or {}).get("login", "")},
        }
    return _gh_source("ticket", [
        "issue", "list", "--state", "all", "--limit", str(limit),
        "--json", "number,title,url,createdAt,state,author",
    ], repo, since, until, to_record)


def collect_ci_runs(repo: Path, since: str, until: str, limit: int = 300) -> Collected:
    def to_record(run: dict[str, Any]) -> dict[str, Any] | None:
        if not run.get("createdAt"):
            return None
        return {
            "type": "ci_run", "ref": str(run.get("databaseId", "")),
            "uri": run.get("url", ""), "timestamp": run["createdAt"],
            "summary": _clip(f"{run.get('workflowName','workflow')}: "
                             f"{run.get('conclusion') or run.get('status') or 'unknown'}"),
            "payload": {"conclusion": run.get("conclusion") or "",
                        "status": run.get("status") or "",
                        "head_sha": run.get("headSha", "")},
        }
    return _gh_source("ci_run", [
        "run", "list", "--limit", str(limit),
        "--json", "databaseId,workflowName,conclusion,status,createdAt,url,headSha",
    ], repo, since, until, to_record)


def collect_deploys(repo: Path, since: str, until: str, limit: int = 100) -> Collected:
    """Releases stand in for deploys. Named honestly in the coverage reason."""
    def to_record(rel: dict[str, Any]) -> dict[str, Any] | None:
        ts = rel.get("publishedAt") or rel.get("createdAt")
        if not ts:
            return None
        return {
            "type": "deploy", "ref": rel.get("tagName", ""),
            "timestamp": ts, "summary": _clip(rel.get("name") or rel.get("tagName", "release")),
            "payload": {"tag": rel.get("tagName", ""),
                        "prerelease": bool(rel.get("isPrerelease")),
                        "draft": bool(rel.get("isDraft"))},
        }
    # `gh release list` exposes no url field, unlike pr/issue/run. Asking for
    # one makes the whole query fail, which the coverage machinery would then
    # report as an unavailable source — an honest outcome, but the wrong one.
    got = _gh_source("deploy", [
        "release", "list", "--limit", str(limit),
        "--json", "tagName,name,publishedAt,createdAt,isDraft,isPrerelease",
    ], repo, since, until, to_record)
    if got.available and not got.records:
        got.available = False
        got.reason = ("no GitHub releases in range; releases are being used as a proxy for "
                      "deploys and no deployment system is wired in")
    return got


def collect_notes(path: Path | None) -> Collected:
    """Operator-supplied observations with no machine-retrievable source (§7.4).

    Legitimate substrate, and exactly as trustworthy as whoever wrote it, which
    is why §20 requires the summary to report how many confirmed findings rest
    on notes alone.
    """
    if path is None:
        return Collected("note", available=False,
                         reason="no notes file supplied; unlogged observations were not collected")
    if not path.exists():
        return Collected("note", available=False, reason=f"notes file {path} not found")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    records = []
    for n, item in enumerate(doc, start=1):
        if isinstance(item, str):
            item = {"summary": item}
        records.append({
            "type": "note", "ref": item.get("ref", f"note-{n}"),
            "timestamp": item.get("timestamp", datetime.now(timezone.utc).isoformat(timespec="seconds")),
            "summary": _clip(item.get("summary", "")),
            "payload": {"author": item.get("author", "unattributed")},
        })
    return Collected("note", records=records)


def _git_file_timestamp(repo: Path, rel: str, fallback: str) -> str:
    """When the file last changed, per git.

    Not the filesystem mtime: a fresh clone rewrites every mtime, which would
    make the substrate differ per machine and silently renumber records that
    earlier evidence already cites.
    """
    code, out, _err = _run(["git", "log", "-1", "--format=%aI", "--", rel], cwd=repo, timeout=30)
    return out.strip() if code == 0 and out.strip() else fallback


def _head_timestamp(repo: Path) -> str:
    code, out, _err = _run(["git", "log", "-1", "--format=%aI"], cwd=repo, timeout=30)
    return out.strip() if code == 0 and out.strip() else "1970-01-01T00:00:00+00:00"


def collect_ontology(
    repo: Path, *, scopes: list[str] | None = None, reasoner: bool = False
) -> tuple[Collected, Collected]:
    """Measure the ontology corpus, returning (documents, metrics).

    Every fact an agent might cite about the state of the ontology has to exist
    here first, or the grounding gate will refuse every finding about it.
    """
    try:
        import rdflib  # noqa: F401
    except ImportError:
        why = "rdflib not installed; the ontology corpus could not be measured"
        return (Collected("document", available=False, reason=why),
                Collected("metric", available=False, reason=why))

    paths = onto.discover(repo, scopes)
    if not paths:
        why = f"no ontology files found under {scopes or repo}"
        return (Collected("document", available=False, reason=why),
                Collected("metric", available=False, reason=why))

    head = _head_timestamp(repo)
    facts = [onto.measure_file(p, repo) for p in paths]

    documents = [{
        "type": "document", "ref": f.rel,
        "timestamp": _git_file_timestamp(repo, f.rel, head),
        "summary": f.summary(),
        "payload": {"group": f.group, "checksum": f.checksum, "bytes": f.bytes,
                    "parses": f.parses, "parse_error": f.parse_error,
                    "triples": f.triples, "classes": f.classes,
                    "imports": f.imports or [],
                    "undeclared_prefixes": f.undeclared_prefixes or [],
                    "vendored": f.vendored},
    } for f in facts]

    metrics = list(onto.group_metrics(facts))
    metrics += onto.suite_metrics(repo, facts)
    metrics += onto.shacl_metrics(repo)
    if reasoner:
        metrics += onto.reasoner_metrics(repo)

    metric_records = [{
        "type": "metric", "ref": m.ref, "timestamp": head, "summary": m.summary(),
        "payload": {"check": m.check, "scope": m.scope, "value": m.value,
                    "detail": m.detail, "tool": m.tool},
    } for m in metrics]

    return (Collected("document", records=documents),
            Collected("metric", records=metric_records))


#: Types with no automatic source. Declared unavailable with a standing reason
#: rather than quietly missing.
UNSOURCED: dict[str, str] = {
    "incident": "no incident tracker integration",
    "metric": "no metrics pipeline wired to the retrospective",
    "review": "review data not collected; gh does not expose it cheaply in list form",
    "document": "no document source configured",
}

#: Types the ontology source supplies when it is enabled.
ONTOLOGY_TYPES = ("document", "metric")


# ----------------------------------------------------------------------
# builder
# ----------------------------------------------------------------------

@dataclass
class BuildResult:
    document: dict[str, Any]
    counts: dict[str, int]
    coverage: list[dict[str, Any]]
    errors: list[str]

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def build(
    sprint_id: str,
    started: str,
    ended: str,
    *,
    repo: str | Path = ".",
    notes: str | Path | None = None,
    include_github: bool = True,
    ontology: bool = False,
    ontology_scopes: list[str] | None = None,
    reasoner: bool = False,
) -> BuildResult:
    """Assemble a conformant substrate document."""
    repo = Path(repo).resolve()
    collected: list[Collected] = [collect_commits(repo, started, ended)]

    if include_github:
        collected += [
            collect_pull_requests(repo, started, ended),
            collect_tickets(repo, started, ended),
            collect_ci_runs(repo, started, ended),
            collect_deploys(repo, started, ended),
        ]
    else:
        for t in ("pull_request", "ticket", "ci_run", "deploy"):
            collected.append(Collected(t, available=False,
                                       reason="GitHub collection disabled for this build"))

    collected.append(collect_notes(Path(notes) if notes else None))

    supplied = set()
    if ontology:
        docs, mets = collect_ontology(repo, scopes=ontology_scopes, reasoner=reasoner)
        collected += [docs, mets]
        supplied = set(ONTOLOGY_TYPES)
    for rtype, reason in UNSOURCED.items():
        if rtype in supplied:
            continue
        collected.append(Collected(rtype, available=False, reason=reason))

    # Deterministic ordering, then identifiers. Sorting before minting is what
    # keeps ids stable across re-runs, so evidence cited in an earlier
    # retrospective still resolves.
    records: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for got in sorted(collected, key=lambda c: RECORD_TYPES.index(c.type)):
        ordered = sorted(got.records, key=lambda r: (r["timestamp"], r["ref"]))
        prefix = ID_PREFIX[got.type]
        for n, rec in enumerate(ordered, start=1):
            rec = {"id": f"{prefix}-{n:04d}", **rec}
            if not rec.get("uri"):
                rec.pop("uri", None)
            records.append(rec)
        counts[got.type] = len(ordered)

    coverage = [
        {"type": c.type, "available": c.available, **({"reason": c.reason} if not c.available else {})}
        for c in sorted(collected, key=lambda c: RECORD_TYPES.index(c.type))
    ]

    document = {
        "sprint": {"id": sprint_id, "started": started, "ended": ended},
        "records": records,
        "coverage": coverage,
    }
    errors = validate_substrate(document)

    # Two records answering to one reference makes evidence citing it
    # ambiguous, and the schema cannot see it because the ids differ. Caught
    # here rather than discovered by a finding that resolves to the wrong fact.
    seen: dict[tuple[str, str], str] = {}
    for rec in records:
        key = (rec["type"], rec["ref"])
        if key in seen:
            errors.append(f"duplicate reference {rec['type']}:{rec['ref']} "
                          f"used by both {seen[key]} and {rec['id']}")
        seen[key] = rec["id"]

    return BuildResult(document, counts, coverage, errors)


def write(result: BuildResult, path: str | Path) -> Path:
    """Write the substrate, refusing to emit a document that does not validate."""
    if result.errors:
        raise ValueError(f"refusing to write a non-conformant substrate: {result.errors[0]}")
    p = Path(path)
    p.write_text(
        yaml.safe_dump(result.document, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    return p
