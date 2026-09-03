# SPDX-License-Identifier: Apache-2.0
"""The Phase 6 quality gate, gathered into one reproducible record.

    python tools/site/quality_report.py            # everything but the clone
    python tools/site/quality_report.py --fresh-clone

Five sections the publication plan asks for as committed deliverables:
the link and schema report, the fresh-checkout build record, the final
suite comparison, the artifact inventory, and the owner's public-content
sign-off block.

Everything except the sign-off is measured here rather than transcribed.
The sign-off is left unsigned on purpose: it is the owner's statement
that the published content is what they want published, and a tool
cannot make it. What the tool can do is put the facts they would be
signing against on the same page, so the signature is informed rather
than ceremonial.

The fresh clone is real: it clones this repository into a temporary
directory, builds there with no `_site` present, and runs the site and
licensing suites. It is optional only because it takes a few minutes.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import importlib.util
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())

FORMAT_VERSION = 1
GENERATOR = "tools/site/quality_report.py"


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, _root / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=str(cwd or _root),
                            capture_output=True, text=True)
    if result.returncode:
        raise SystemExit("git " + " ".join(args) + ": "
                         + result.stderr.strip()[-300:])
    return result.stdout.strip()


# ------------------------------------------------------------- links


class Links(html.parser.HTMLParser):
    """Every href and src, and every id, with the page that carried it."""

    def __init__(self):
        super().__init__()
        self.found: list = []
        self.ids: set = set()

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.found.append((tag, value))
            if name == "id" and value:
                self.ids.add(value)


def link_report(artifact) -> dict:
    """Every internal reference, and whether the build serves it.

    Fragments are resolved rather than stripped. The first version
    discarded same-page fragments entirely and cut the fragment off
    cross-page ones, so a skip link pointing at an element that no longer
    existed produced "0 broken links" -- and the skip link is the single
    reference on this site whose whole purpose is the fragment.
    """
    # Resolved once, so page paths and reference targets are comparable.
    artifact = artifact.resolve()

    # Keyed by resolved absolute path. Keyed by the rglob path, every
    # cross-page fragment looked up an absolute path in a table of
    # relative ones, missed, and was recorded as "not an HTML page"
    # rather than checked -- so an invented anchor produced no finding.
    pages = {}
    for page in sorted(artifact.rglob("*.html")):
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        pages[page.resolve()] = parser

    rows, broken, external = [], [], []
    fragments_checked = 0
    for page, parser in pages.items():
        here = page.relative_to(artifact).as_posix()
        for tag, target in parser.found:
            if target.startswith(("http://", "https://", "mailto:")):
                external.append({"page": here, "target": target})
                continue

            path_part, _, fragment = target.partition("#")
            path_part = path_part.split("?", 1)[0]

            if not path_part and not fragment:
                continue

            if path_part:
                resolved = (page.parent / path_part).resolve()
                if resolved.is_dir() or path_part.endswith("/"):
                    resolved = resolved / "index.html"
                serves = resolved.is_file()
            else:
                resolved = page.resolve()   # same-page fragment
                serves = True

            row = {"page": here, "tag": tag, "target": target,
                   "resolves": serves, "fragment": fragment or None,
                   "fragment_resolves": None}

            if serves and fragment:
                fragments_checked += 1
                owner = pages.get(resolved)
                if owner is None:
                    # A fragment into something that is not an HTML page
                    # cannot be checked, and claiming otherwise would be
                    # the same overclaim this replaced.
                    row["fragment_resolves"] = None
                    row["note"] = "target is not an HTML page"
                else:
                    row["fragment_resolves"] = fragment in owner.ids
                    if not row["fragment_resolves"]:
                        serves = False
                        row["resolves"] = False

            rows.append(row)
            if not serves:
                broken.append(row)

    return {
        "internal_references": len(rows),
        "fragments_checked": fragments_checked,
        "broken": broken,
        "external_references": external,
        "note": ("Resolved against the built artifact, which is what is "
                 "served. A directory target resolves through its "
                 "index.html, the way a web server would, and a fragment "
                 "must name an id that exists on the page it lands on."),
        "passed": not broken,
    }


# ------------------------------------------------------------ schemas


def schema_report(artifact: Path) -> dict:
    from jsonschema import Draft7Validator

    site = json.loads((_root / "site/content/site.json")
                      .read_text(encoding="utf-8"))
    base = site["deployment"]["public_url"]

    documents = sorted((artifact / "data").glob("*.json"))
    schemas = sorted((artifact / "schemas").glob("*.json"))
    rows, problems = [], []

    for document in documents:
        expected = document.name.replace(".json", ".schema.json")
        schema_path = artifact / "schemas" / expected
        entry = {"document": "data/" + document.name,
                 "schema": "schemas/" + expected,
                 "schema_present": schema_path.is_file()}
        if not schema_path.is_file():
            problems.append("%s has no schema" % document.name)
            entry["valid"] = None
        else:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            entry["id"] = schema.get("$id")
            entry["id_matches_path"] = (
                schema.get("$id") == base + "schemas/" + expected)
            if not entry["id_matches_path"]:
                problems.append("%s $id does not match where it is served"
                                % expected)
            errors = sorted(
                Draft7Validator(schema).iter_errors(
                    json.loads(document.read_text(encoding="utf-8"))),
                key=lambda e: list(e.path))
            entry["valid"] = not errors
            entry["errors"] = ["%s: %s" % (
                "/".join(str(x) for x in e.path) or "(root)", e.message[:120])
                for e in errors[:3]]
            if errors:
                problems.append("%s does not validate" % document.name)
        rows.append(entry)

    described = {s.name.replace(".schema.json", ".json") for s in schemas}
    orphans = sorted(described - {d.name for d in documents})
    if orphans:
        problems.append("schemas describing nothing published: %s" % orphans)

    return {"documents": rows, "orphan_schemas": orphans,
            "problems": problems, "passed": not problems}


# --------------------------------------------------------- inventory


def inventory(artifact: Path) -> dict:
    files = sorted(p for p in artifact.rglob("*") if p.is_file())
    by_suffix: dict[str, int] = {}
    for path in files:
        by_suffix[path.suffix or "(none)"] = by_suffix.get(
            path.suffix or "(none)", 0) + 1
    return {
        "files": len(files),
        "by_suffix": dict(sorted(by_suffix.items())),
        "paths": [p.relative_to(artifact).as_posix() for p in files],
        "total_bytes": sum(p.stat().st_size for p in files),
    }


# ------------------------------------------------- suite comparison


def collect_identities(cwd: Path, python: str) -> list[str]:
    result = subprocess.run(
        [python, "-m", "pytest", "--collect-only", "-q",
         "-m", "slow or not slow"],
        cwd=str(cwd), capture_output=True, text=True)
    if result.returncode:
        raise SystemExit("collection failed:\n" + result.stdout[-1500:])
    return sorted(os.path.basename(line.strip())
                  for line in result.stdout.splitlines()
                  if "::" in line and not line.strip().startswith(" "))


def suite_comparison() -> dict:
    baseline = json.loads((_root / "config/test-identity-baseline.json")
                          .read_text(encoding="utf-8"))
    current = collect_identities(_root, sys.executable)
    renamed = {r["was"]: r for r in baseline["renames"]}
    pre = set(baseline["identities"])
    now = set(current)

    missing = sorted(pre - now - set(renamed))
    return {
        "pre_site_commit": baseline["pre_site_commit"],
        "pre_site_collected": baseline["collected"],
        "final_collected": len(current),
        "added": len(now - pre),
        "missing_unrecorded": missing,
        "renames": [{"was": r["was"], "now": r["now"],
                     "commit": r["commit"],
                     "adjudicated": r.get("adjudicated")}
                    for r in baseline["renames"]],
        "collisions": sorted({i for i in current
                              if current.count(i) > 1}),
        "passed": (not missing
                   and all(r.get("adjudicated") == "approved"
                           for r in baseline["renames"])),
    }


# ------------------------------------------------------ fresh clone


def fresh_clone_record(python: str) -> dict:
    """Clone, build with nothing present, run the suites, measure."""
    head = git("rev-parse", "HEAD")
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "valuenet"
        subprocess.run(["git", "clone", "--quiet", str(_root), str(target)],
                       check=True, capture_output=True)
        had_site = (target / "_site").exists()
        remotes = git("remote", cwd=target).split()

        build = subprocess.run([python, "tools/site/build_site.py"],
                               cwd=str(target), capture_output=True, text=True)
        digest = None
        for line in build.stdout.splitlines():
            if "tree digest" in line:
                digest = line.split()[-1]

        tests = subprocess.run(
            [python, "-m", "pytest", "tests/site/", "tests/licensing/",
             "-q", "-p", "no:randomly"],
            cwd=str(target), capture_output=True, text=True)
        summary = [l for l in tests.stdout.splitlines()
                   if " passed" in l or " failed" in l]

        bundle = target / "_site/downloads/bfo-aligned-valuenet.zip"
        bundle_sha = (hashlib.sha256(bundle.read_bytes()).hexdigest()
                      if bundle.is_file() else None)
        return {
            "commit": head,
            "clone_root_length": len(str(target)),
            "remotes": remotes,
            "site_present_before_build": had_site,
            "build_exit": build.returncode,
            "site_tree_digest": digest,
            "bundle_sha256": bundle_sha,
            "tests_exit": tests.returncode,
            "tests_summary": summary[-1] if summary else tests.stdout[-200:],
            "passed": (build.returncode == 0 and tests.returncode == 0
                       and not had_site and remotes == ["origin"]),
        }


# ---------------------------------------------------------- assemble


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="config/quality-report.json")
    ap.add_argument("--site", default="_site")
    ap.add_argument("--fresh-clone", action="store_true")
    args = ap.parse_args(argv)

    artifact = Path(args.site)
    artifact = artifact if artifact.is_absolute() else _root / artifact
    if not (artifact / "index.html").is_file():
        raise SystemExit("no built site at %s" % artifact)

    review_path = _root / "config/browser-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))

    record = {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "commit": git("rev-parse", "HEAD"),
        "operating_system": platform.platform(),
        "links": link_report(artifact),
        "schemas": schema_report(artifact),
        "artifact": inventory(artifact),
        "suite": suite_comparison(),
        "browser_review": {
            "record": "config/browser-review.json",
            "engines": [b["engine"] + " " + b.get("version", "?")
                        for b in review["browsers"]],
            "passed": review["passed"],
            "not_covered": sorted(review["not_covered"]),
        },
        "public_content_sign_off": {
            "status": "unsigned",
            "who": "repository owner",
            "note": ("A tool cannot make this statement. It is the owner "
                     "confirming that what the site publishes is what they "
                     "intend to publish, and that the licensing, "
                     "attribution and citation on it are correct. The "
                     "measured facts it rests on are in this record."),
            "asserts": [
                "the published Turtle is the authored corpus and nothing else",
                "no upstream material of unidentified licence is redistributed",
                "attribution and citation name the right people",
                "the licence statements on the site match LICENSE and "
                "THIRD_PARTY_NOTICES.md",
            ],
        },
    }
    if args.fresh_clone:
        record["fresh_clone"] = fresh_clone_record(sys.executable)

    # Two different questions, and conflating them let the record say
    # `passed: true` while the sign-off it requires was unsigned.
    #
    # measured_checks_passed is what this tool can determine. passed is
    # the gate, and the gate includes a statement only the owner can
    # make. An unsigned block is a true description of where the work
    # stands; a gate reporting success over one is not.
    sections = ["links", "schemas", "suite"]
    record["measured_checks_passed"] = (
        all(record[s]["passed"] for s in sections)
        and record["browser_review"]["passed"]
        and record.get("fresh_clone", {"passed": True})["passed"])

    signed = record["public_content_sign_off"]["status"] == "signed"
    record["passed"] = record["measured_checks_passed"] and signed
    if not signed:
        record["gate_blocked_by"] = (
            "public_content_sign_off is unsigned. Every measured check "
            "passed; the gate does not, because the owner has not stated "
            "that what the site publishes is what they intend to publish.")

    out = Path(args.out)
    out = out if out.is_absolute() else _root / out
    out.write_bytes(json.dumps(record, indent=2, sort_keys=True,
                               ensure_ascii=False).encode("utf-8") + b"\n")

    print("  links    %s  (%d internal, %d fragment, %d broken)"
          % ("ok  " if record["links"]["passed"] else "FAIL",
             record["links"]["internal_references"],
             record["links"]["fragments_checked"],
             len(record["links"]["broken"])))
    print("  schemas  %s  (%d document(s))"
          % ("ok  " if record["schemas"]["passed"] else "FAIL",
             len(record["schemas"]["documents"])))
    print("  suite    %s  (%d -> %d, %d added)"
          % ("ok  " if record["suite"]["passed"] else "FAIL",
             record["suite"]["pre_site_collected"],
             record["suite"]["final_collected"], record["suite"]["added"]))
    if "fresh_clone" in record:
        print("  clone    %s  (%s)"
              % ("ok  " if record["fresh_clone"]["passed"] else "FAIL",
                 record["fresh_clone"]["tests_summary"]))
    print("  browsers %s  (%s)"
          % ("ok  " if record["browser_review"]["passed"] else "FAIL",
             ", ".join(record["browser_review"]["engines"])))
    print()
    print("  measured checks: %s"
          % ("all passed" if record["measured_checks_passed"] else "FAILED"))
    print("  sign-off       : %s"
          % record["public_content_sign_off"]["status"])
    print("  gate           : %s"
          % ("passed" if record["passed"]
             else "blocked -- " + record.get("gate_blocked_by", "")[:60]))
    print("  wrote %s" % args.out)
    return 0 if record["measured_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
