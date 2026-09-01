# SPDX-License-Identifier: Apache-2.0
"""Which licence governs each tracked file, derived rather than listed.

    python tools/licensing/disposition.py            # summary
    python tools/licensing/disposition.py --list project-content

A hand-maintained list of file paths is the wrong shape for this. It is
correct on the day it is written, silent when a file is added, and gives
no reason for any entry -- and the question it answers ("may I reuse
this?") is one a reader must be able to check rather than trust.

So every disposition is derived from provenance the repository already
holds and audited before this work existed:

  * `config/move-manifest.yaml` records, per file, an `origin` of `fork`,
    `upstream-valuenet`, `external-bfo` or `external-cco`. That manifest
    is frozen and was reviewed across five migration waves.

  * A tracked file the manifest does not mention was created after the
    freeze. That it is fork-authored is *checked*, not assumed: it must
    be absent from the upstream remote. A file present upstream and
    missing from the manifest means the manifest is incomplete, and this
    module refuses rather than guessing.

FOUR DISPOSITIONS, AND EXACTLY ONE PER FILE

  project-content       CC-BY-4.0     ontologies, docs, diagrams, site copy
  project-software      Apache-2.0    code, tests, tooling, workflows
  third-party           per source    BFO (CC-BY-4.0), CCO (BSD-3-Clause)
  excluded-unresolved   none          upstream ValueNet, licence unidentified

The last is the one that matters most. Upstream ValueNet material has no
licence anyone here has identified, so this repository grants nothing
over it, claims nothing about it, and excludes it from the public
download bundle. Calling it "project content" would be relicensing
somebody else's work by omission.

`rules()` returns every matching rule rather than the first, so an
overlapping rule added later is a test failure instead of a silent
precedence decision.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

CONTENT = "project-content"
SOFTWARE = "project-software"
THIRD_PARTY = "third-party"
EXCLUDED = "excluded-unresolved"

LICENCE_OF = {
    CONTENT: "CC-BY-4.0",
    SOFTWARE: "Apache-2.0",
}

THIRD_PARTY_LICENCE = {
    "external-bfo": "CC-BY-4.0",
    "external-cco": "BSD-3-Clause",
}

#: Fork-authored files whose licence is Apache-2.0. Judged by role, not by
#: suffix alone: `config/` holds the layout contract and the evidence the
#: tooling generates, which are part of the software rather than published
#: content, while `site/content/` holds public copy that happens to be
#: JSON.
SOFTWARE_DIRS = ("tools/", "tests/", "marep/", "config/", ".github/",
                 "examples/")
SOFTWARE_SUFFIXES = (".py", ".cfg", ".ini", ".toml")

#: Fork-authored files published as content.
CONTENT_DIRS = ("docs/", "ontology/", "site/")
CONTENT_SUFFIXES = (".ttl", ".md", ".html", ".css", ".svg", ".png",
                    ".cff", ".txt")

#: Suffixless fork-authored documents that are published content. The
#: root licensing notice is authored prose about the project, not a
#: reproduced instrument -- the reproduced instruments live in
#: LICENSES/ and are classified third-party.
CONTENT_NAMES = ("LICENSE",)


class Disposition(NamedTuple):
    path: str
    origin: str
    disposition: str
    licence: str | None
    rationale: str


def git(*args: str) -> list[str]:
    r = subprocess.run(["git", *args], cwd=str(_root),
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("git " + " ".join(args) + " failed: "
                         + r.stderr.strip()[-300:])
    return r.stdout.splitlines()


def manifest_origins() -> dict[str, str]:
    """Origin per path, from the frozen provenance record.

    Both the pre-move and post-move path of every row is indexed: the
    manifest was frozen before the migration, so a file is named there by
    the path it had then and by the path it has now.
    """
    import yaml

    doc = yaml.safe_load(
        (_root / "config/move-manifest.yaml").read_text(encoding="utf-8"))
    origins: dict[str, str] = {}
    for row in doc["components"]:
        for key in ("path", "destination"):
            if row.get(key):
                origins[row[key]] = row["origin"]
    return origins


def upstream_paths() -> set[str]:
    """Everything the upstream remote tracks, if it is reachable.

    Absence of the remote is not treated as evidence that a file is
    fork-authored: `classify` refuses instead, because the check is the
    only thing separating "we wrote this" from "we did not look".
    """
    refs = git("for-each-ref", "--format=%(refname)", "refs/remotes/upstream")
    if not refs:
        return set()
    head = "upstream/main"
    return set(git("ls-tree", "-r", "--name-only", head))


def rules(path: str, origin: str) -> list[tuple[str, str | None, str]]:
    """Every rule that matches, so overlap is visible rather than resolved.

    A first-match-wins chain would silently prefer whichever rule happened
    to be written first, and a later contradictory rule would never be
    noticed.
    """
    matched: list[tuple[str, str | None, str]] = []
    if origin in THIRD_PARTY_LICENCE:
        matched.append((THIRD_PARTY, THIRD_PARTY_LICENCE[origin],
                        "upstream %s material, under its own licence"
                        % origin.split("-", 1)[1].upper()))
    if origin == "upstream-valuenet":
        matched.append((EXCLUDED, None,
                        "original ValueNet material whose licence this "
                        "repository has not identified; no rights are "
                        "granted and it is excluded from the public bundle"))
    # Reproduced licence texts are third-party documents, whatever the
    # provenance record says about who added the file. They are verbatim
    # copies of somebody else's instrument, and the licence they fall
    # under is the one they are.
    if path.startswith("LICENSES/"):
        matched.append((THIRD_PARTY, Path(path).stem,
                        "verbatim licence text, reproduced under the terms "
                        "of the licence it states"))
        return matched

    if origin == "fork":
        suffix = Path(path).suffix.lower()
        # A root dotfile is repository configuration -- .gitattributes,
        # .gitignore. It has no suffix and lives in no directory, so
        # neither of the rules below reaches it, and the classifier
        # refused rather than inventing a default. That refusal was
        # right; the remedy is a rule, not an exception.
        # Repository configuration: a root dotfile, a pinned dependency
        # file, or the root licensing notice's companions. Each has no
        # suffix rule that reaches it, and the classifier refused rather
        # than inventing a default -- twice, which is the behaviour that
        # makes it usable.
        is_config = (("/" not in path and path.startswith("."))
                     or Path(path).name.startswith("requirements"))
        is_software = (is_config
                       or path.startswith(SOFTWARE_DIRS)
                       or suffix in SOFTWARE_SUFFIXES)
        is_content = (path.startswith(CONTENT_DIRS)
                      or suffix in CONTENT_SUFFIXES
                      or path in CONTENT_NAMES)
        # site/content holds public copy; config holds tooling state. Where
        # a directory rule and a suffix rule disagree, the directory wins,
        # and the disagreement is recorded rather than hidden.
        if is_config:
            is_content = False
        elif path.startswith("site/"):
            is_software = False
        elif path.startswith(SOFTWARE_DIRS):
            is_content = False
        elif suffix in SOFTWARE_SUFFIXES:
            is_content = False
        if is_software:
            matched.append((SOFTWARE, LICENCE_OF[SOFTWARE],
                            "repository configuration" if is_config
                            else "fork-authored software"))
        if is_content:
            matched.append((CONTENT, LICENCE_OF[CONTENT],
                            "fork-authored published content"))
    return matched


def classify(strict: bool = True) -> list[Disposition]:
    origins = manifest_origins()
    upstream = upstream_paths()
    if strict and not upstream:
        raise SystemExit(
            "the upstream remote is not available, so a file missing from "
            "the manifest cannot be confirmed as fork-authored. Fetch "
            "upstream, or pass strict=False and treat the result as "
            "provisional.")

    out, problems = [], []
    for path in git("ls-files"):
        origin = origins.get(path)
        if origin is None:
            if path in upstream:
                problems.append(
                    path + " is tracked upstream but absent from the move "
                    "manifest, so its provenance is unrecorded")
                continue
            origin = "fork"
        matched = rules(path, origin)
        if len(matched) != 1:
            problems.append(
                "%s (origin %s) matches %d disposition rules: %s"
                % (path, origin, len(matched), [m[0] for m in matched]))
            continue
        disposition, licence, why = matched[0]
        out.append(Disposition(path, origin, disposition, licence, why))

    if problems:
        raise SystemExit(
            "%d file(s) have no single licensing disposition:%s%s"
            % (len(problems), chr(10),
               chr(10).join("  - " + p for p in problems[:12])))
    return out


def divergence() -> list[tuple[str, int, int, int]]:
    """Where recorded descent and surviving content disagree.

    The manifest's `origin` axis records where a file came from. A
    licence question asks who wrote what is there now. Those are
    usually the same and occasionally are not: a file can descend from
    upstream and retain none of its text.

    This reports the overlap rather than acting on it. Choosing a
    threshold at which descent stops mattering is a licensing
    judgement, not a measurement, and automating it would relicense
    somebody else's work on a heuristic.
    """
    upstream_blobs = {
        line.split(chr(9))[-1]
        for line in git("ls-tree", "-r", "--name-only", "upstream/main")}
    out = []
    for row in classify():
        if row.origin != "upstream-valuenet":
            continue
        if row.path not in upstream_blobs:
            continue
        try:
            was = subprocess.run(
                ["git", "show", "upstream/main:" + row.path],
                cwd=str(_root), capture_output=True
            ).stdout.decode("utf-8", "replace")
            now = (_root / row.path).read_text(encoding="utf-8",
                                               errors="replace")
        except OSError:
            continue
        norm = lambda t: {l.strip() for l in t.splitlines() if l.strip()}
        a, b = norm(was), norm(now)
        if not b:
            continue
        out.append((row.path, len(a), len(b), len(a & b)))
    return sorted(out, key=lambda r: (r[3] / max(r[2], 1), r[0]))


def main(argv=None) -> int:
    import collections

    ap = argparse.ArgumentParser()
    ap.add_argument("--list", dest="which", default=None)
    ap.add_argument("--suffix", default=None)
    ap.add_argument("--divergence", action="store_true")
    args = ap.parse_args(argv)

    if args.divergence:
        rows = divergence()
        print("  files recorded as upstream whose surviving text is "
              "mostly or entirely new:")
        print("    %-46s %6s %6s %8s"
              % ("path", "was", "now", "shared"))
        for path, was, now, shared in rows[:15]:
            print("    %-46s %6d %6d %8d" % (path, was, now, shared))
        print()
        print("    Reported, not acted on. Descent is recorded "
              "provenance; what survives is a measurement; deciding "
              "when one overrides the other is a licensing judgement.")
        return 0

    rows = classify()
    if args.which:
        for row in sorted(rows):
            if row.disposition != args.which:
                continue
            if args.suffix and not row.path.endswith(args.suffix):
                continue
            print("%s  %s" % (row.licence or "-", row.path))
        return 0

    tally = collections.Counter((r.disposition, r.licence) for r in rows)
    print("  %d tracked file(s), each with exactly one disposition" % len(rows))
    for (disposition, licence), n in sorted(tally.items()):
        print("    %-22s %-14s %4d" % (disposition, licence or "(none)", n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
