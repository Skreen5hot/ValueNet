# SPDX-License-Identifier: Apache-2.0
"""Check the deployed site, and record what was found.

    python tools/site/verify_deployment.py

A green workflow says the build succeeded and the artifact uploaded. It
does not say the site serves, that a nested page resolves under the
project subpath, that a downloaded ontology is the file in this
repository, or that the checksums beside it verify what a visitor
actually receives. Those are questions about production, and the only way
to answer them is to fetch production.

Everything is compared against the repository rather than against the
local build directory: the point is that what is served matches what is
authored, and a local artifact is an intermediate step that could agree
with the deployment while both differ from the source.

The browser section loads the explorer at the public URL and fails on any
console error. A page that renders while logging a failed fetch is a page
whose search is broken for every visitor and looks fine in a screenshot.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import platform
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())

FORMAT_VERSION = 1
GENERATOR = "tools/site/verify_deployment.py"

#: Where the person who performed the manual checks records what they
#: did. Read rather than hardcoded: with the statuses in this file,
#: closing Phase 7 meant editing Python, which is a strange way to record
#: that somebody listened to a screen reader -- and it made "performed" a
#: one-word change with no evidence attached.
MANUAL_CHECKS_PATH = "config/manual-checks.yaml"
MANUAL_CHECKS_SCHEMA = "config/manual-checks.schema.json"


def manual_checks() -> dict:
    """The recorded evidence, validated before it is believed."""
    import yaml
    from jsonschema import Draft7Validator

    path = _root / MANUAL_CHECKS_PATH
    if not path.is_file():
        raise SystemExit(
            MANUAL_CHECKS_PATH + " is missing. It records the checks a tool "
            "cannot make, and without it their status is unknown rather "
            "than passed.")
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    # YAML parses an unquoted 2026-09-03 into a date object, so a
    # correctly filled form failed a schema asking for a string. Dates
    # are normalised to ISO text rather than requiring the person filling
    # this in to remember quotation marks.
    import datetime

    def as_text(node):
        if isinstance(node, dict):
            return {k: as_text(v) for k, v in node.items()}
        if isinstance(node, list):
            return [as_text(v) for v in node]
        if isinstance(node, (datetime.date, datetime.datetime)):
            return node.isoformat()[:10]
        return node

    document = as_text(document)
    schema = json.loads((_root / MANUAL_CHECKS_SCHEMA)
                        .read_text(encoding="utf-8"))
    errors = sorted(Draft7Validator(schema).iter_errors(document),
                    key=lambda e: list(e.path))
    if errors:
        raise SystemExit(
            "%s does not satisfy its schema: %s" % (
                MANUAL_CHECKS_PATH, "; ".join(
                    "%s: %s" % ("/".join(str(x) for x in e.path) or "(root)",
                                e.message[:140]) for e in errors[:4])))
    return document["checks"]


#: Every page the site publishes, so a missing one is a finding rather
#: than a page nobody happened to open.
PAGES = ("", "explore/", "models/", "modules/", "downloads/",
         "documentation/", "about/")

DATA = ("data/class-index.json", "data/coverage.json", "data/downloads.json",
        "schemas/class-index.schema.json", "schemas/coverage.schema.json",
        "schemas/downloads.schema.json")


def verifier_identity(allow_uncommitted: bool) -> dict:
    """Which bytes asked the questions, bound to something checkable.

    A bare digest in a record is unfalsifiable: any 64 hex characters
    satisfy a length check, and nothing ties them to a file anybody can
    read. So the commit is recorded too, and the digest is required to be
    the digest of this file *as committed there* -- which a test can
    recompute from git.

    That also enforces the sequence this phase learned the hard way: the
    first record was produced by a tool absent from the commit it
    measured. Running an uncommitted verifier is still possible for
    development, and says so in the record rather than passing quietly.
    """
    own = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    relative = Path(__file__).resolve().relative_to(_root).as_posix()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(_root),
                          capture_output=True, text=True).stdout.strip()
    blob = subprocess.run(["git", "cat-file", "blob",
                           "%s:%s" % (head, relative)],
                          cwd=str(_root), capture_output=True)
    committed = (hashlib.sha256(blob.stdout).hexdigest()
                 if blob.returncode == 0 else None)
    matches = own == committed

    if not matches and not allow_uncommitted:
        raise SystemExit(
            "the verifier differs from %s:%s, so the record would name a "
            "digest nobody can recompute. Commit it first, or pass "
            "--allow-uncommitted-verifier and accept that the record says "
            "so." % (head[:12], relative))

    return {
        "verifier_path": relative,
        "verifier_sha256": own,
        "verifier_commit": head,
        "verifier_matches_commit": matches,
    }


def public_url() -> str:
    site = json.loads((_root / "site/content/site.json")
                      .read_text(encoding="utf-8"))
    return site["deployment"]["public_url"]


def fetch(url: str, timeout: int = 45) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url, headers={"User-Agent": "valuenet-deployment-check"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, b""


def check_pages(base: str) -> dict:
    """Every page, fetched at the public subpath."""
    rows = []
    for page in PAGES:
        status, body = fetch(base + page)
        rows.append({"path": "/" + page, "status": status,
                     "bytes": len(body),
                     "is_html": b"<!doctype html>" in body[:80].lower()})
    return {"pages": rows,
            "passed": all(r["status"] == 200 and r["is_html"] for r in rows)}


class References(html.parser.HTMLParser):
    """Every href and src on a page, kept as written."""

    def __init__(self):
        super().__init__()
        self.found: list = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.found.append((tag, name, value))


def check_relative_paths(base: str) -> dict:
    """A root-absolute reference resolves locally and 404s in production.

    This is the failure the whole relative-URL rule exists to prevent, and
    it only appears once the site is served from a subpath.

    Every page is parsed, and the attributes are read from the parser
    rather than matched in the text. The first version looked at
    /explore/ alone and only at double-quoted attributes, while the
    record it produced was phrased as a statement about the site.
    """
    rows, offenders = [], []
    for page in PAGES:
        status, body = fetch(base + page)
        parser = References()
        parser.feed(body.decode("utf-8", "replace"))
        bad = []
        for tag, attribute, value in parser.found:
            if value.startswith("//"):
                bad.append({"tag": tag, "attribute": attribute,
                            "value": value, "why": "protocol-relative"})
            elif value.startswith("/"):
                bad.append({"tag": tag, "attribute": attribute,
                            "value": value, "why": "root-absolute"})
        rows.append({"path": "/" + page, "status": status,
                     "references": len(parser.found),
                     "root_absolute": bad})
        offenders.extend(bad)
    return {
        "pages_scanned": len(rows),
        "per_page": rows,
        "root_absolute_references": offenders,
        "passed": (all(r["status"] == 200 for r in rows)
                   and not offenders
                   and all(r["references"] > 0 for r in rows)),
    }


def check_downloads(base: str) -> dict:
    """Deployed Turtle against the repository, byte for byte."""
    status, body = fetch(base + "data/downloads.json")
    if status != 200:
        return {"passed": False, "error": "downloads.json returned %d" % status}
    manifest = json.loads(body.decode("utf-8"))

    rows, mismatched = [], []
    for record in manifest["modules"]:
        code, served = fetch(base + "downloads/" + record["filename"])
        source = (_root / record["source"]).read_bytes()
        digest = hashlib.sha256(served).hexdigest() if served else None
        row = {"filename": record["filename"], "status": code,
               "bytes_served": len(served), "bytes_in_repository": len(source),
               "matches_repository": served == source,
               "matches_manifest_sha256": digest == record["sha256"]}
        rows.append(row)
        if not (row["matches_repository"] and row["matches_manifest_sha256"]):
            mismatched.append(record["filename"])

    bundle_name = manifest["bundle"]["filename"]
    bundle_status, bundle = fetch(base + "downloads/" + bundle_name)
    bundle_sha = hashlib.sha256(bundle).hexdigest() if bundle else None
    bundle_ok = (bundle_status == 200
                 and bundle_sha == manifest["bundle"]["sha256"]
                 and len(bundle) == manifest["bundle"]["bytes"])

    # A separate name. `code` was reused for both responses, so the
    # bundle's status in the record was really the checksum file's.
    checksums_status, sums = fetch(base + "downloads/SHA256SUMS")
    listed, unverified = {}, []
    if checksums_status == 200:
        for line in sums.decode("utf-8").strip().split(chr(10)):
            digest, name = line.split("  ", 1)
            listed[name] = digest
        for name, digest in sorted(listed.items()):
            got, data = fetch(base + "downloads/" + name)
            if got != 200 or hashlib.sha256(data).hexdigest() != digest:
                unverified.append(name)

    # Membership, not just verification. Every listed entry verifying
    # says nothing about whether the right entries are listed: a wrong
    # set of twelve would have passed.
    expected = {record["filename"] for record in manifest["modules"]}
    expected.add(bundle_name)
    missing = sorted(expected - set(listed))
    unexpected = sorted(set(listed) - expected)

    return {
        "modules": rows,
        "mismatched": mismatched,
        "bundle": {"status": bundle_status, "sha256_matches": bundle_ok,
                   "bytes": len(bundle)},
        "published_checksums": {
            "status": checksums_status,
            "entries": len(listed),
            "expected_entries": len(expected),
            "missing": missing,
            "unexpected": unexpected,
            "unverified": unverified,
        },
        "passed": (not mismatched and bundle_ok
                   and checksums_status == 200
                   and bool(listed) and not unverified
                   and not missing and not unexpected),
    }


def check_in_browser(base: str) -> dict:
    """The explorer, loaded from production, with the console watched."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"passed": False,
                "error": "playwright is not installed; see "
                         "requirements-browser.txt"}

    findings: dict = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            context = browser.new_context(viewport={"width": 1440,
                                                    "height": 900})
            page = context.new_page()
            errors, failed = [], []
            page.on("console", lambda m: errors.append(m.text)
                    if m.type == "error" else None)
            page.on("requestfailed",
                    lambda r: failed.append(r.url + " " +
                                            str(r.failure)))

            page.goto(base + "explore/", wait_until="networkidle")
            page.wait_for_selector("a.result", timeout=20000)
            total = page.locator("a.result").count()

            page.locator("#q").fill("betrayal")
            page.wait_for_timeout(400)
            searched = page.locator("a.result").count()
            first = (page.locator("a.result .result-id").first.inner_text()
                     if searched else None)

            page.goto(base + "explore/?class=core:ValueDisposition",
                      wait_until="networkidle")
            page.wait_for_selector("#detail:not([hidden])", timeout=20000)
            heading = page.locator("#detail .detail-label").inner_text()

            page.goto(base + "models/", wait_until="networkidle")
            diagrams = page.locator("svg.diagram").count()

            findings = {
                "console_errors": errors,
                "failed_requests": failed,
                "classes_rendered": total,
                "search_betrayal_results": searched,
                "search_first_result": first,
                "deep_link_heading": heading,
                "diagrams_rendered": diagrams,
                "browser": browser.version,
            }
            context.close()
        finally:
            browser.close()

    findings["passed"] = (
        not findings.get("console_errors")
        and not findings.get("failed_requests")
        and findings.get("classes_rendered", 0) >= 180
        and findings.get("search_betrayal_results", 0) >= 1
        and findings.get("search_first_result")
        == "moral-foundations:BetrayalProcess"
        and bool(findings.get("deep_link_heading"))
        and findings.get("diagrams_rendered") == 3)
    return findings


def deployed_commit(base: str) -> dict:
    """What the served pages say they were built from."""
    import re

    status, body = fetch(base)
    match = re.search(r'<code data-build="commit">([0-9a-f]+)</code>',
                      body.decode("utf-8", "replace"))
    stamped = match.group(1) if match else None
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(_root),
                          capture_output=True, text=True).stdout.strip()

    # Ancestry, not equality. Requiring the deployed commit to equal HEAD
    # made the record true for exactly as long as nobody committed
    # afterwards -- including the commit this record lands in. What
    # matters is that the site is serving something from this history,
    # and how far back it is, which is a fact worth recording rather than
    # a failure.
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", stamped or "HEAD", "HEAD"],
        cwd=str(_root), capture_output=True).returncode == 0 if stamped else False
    behind = None
    if ancestor:
        behind = subprocess.run(
            ["git", "rev-list", "--count", stamped + "..HEAD"],
            cwd=str(_root), capture_output=True, text=True).stdout.strip()
        behind = int(behind) if behind.isdigit() else None

    # Named for the moment it describes. A record is immutable and the
    # branch is not, so a field called commits_behind_head would start
    # lying the moment anything else was committed -- including the
    # commit carrying the record. This says how far behind the
    # measurement's own HEAD the deployment was, which stays true.
    # Current lag is a question for whoever is asking, and is recomputed
    # rather than read out of a file.
    return {"stamped_on_the_site": stamped,
            "local_head": head,
            "in_this_history": ancestor,
            "commits_behind_measurement_head": behind,
            "is_head": bool(stamped) and head.startswith(stamped)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="config/deployment-record.json")
    ap.add_argument("--url", default=None)
    ap.add_argument("--skip-browser", action="store_true")
    ap.add_argument("--allow-uncommitted-verifier", action="store_true",
                    help="record a run made with a modified verifier. The "
                         "record says so, and the automated verdict fails.")
    args = ap.parse_args(argv)

    base = args.url or public_url()
    if not base.endswith("/"):
        base += "/"

    record = {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        **verifier_identity(args.allow_uncommitted_verifier),
        "public_url": base,
        "operating_system": platform.platform(),
        "commit": deployed_commit(base),
        "pages": check_pages(base),
        "relative_paths": check_relative_paths(base),
        "downloads": check_downloads(base),
    }
    if not args.skip_browser:
        record["browser"] = check_in_browser(base)

    sections = [k for k in ("pages", "relative_paths", "downloads", "browser")
                if k in record]
    # is_head, not merely ancestry, and only here. At capture time the
    # question is whether production is serving what this checkout has:
    # running the verifier months later against an arbitrarily stale
    # deployment would satisfy ancestry and prove nothing. Once the
    # record is committed the branch moves on, so the repository tests
    # ask for ancestry instead. Two moments, two questions.
    record["automated_checks_passed"] = (
        all(record[s]["passed"] for s in sections)
        and record["commit"]["in_this_history"]
        and record["commit"]["is_head"]
        and record["verifier_matches_commit"])

    # Two checks need a person, and neither has been done. Reporting the
    # phase as passed over them would be the same overclaim the browser
    # record was corrected for -- and the site is already serving, so the
    # deployment is described as provisional rather than verified.
    checks = manual_checks()
    record["manual_checks"] = checks
    record["manual_checks_source"] = MANUAL_CHECKS_PATH
    blockers = sorted(name for name, check in checks.items()
                      if check["status"] != "performed")
    record["blocked_by"] = blockers
    record["deployment_status"] = ("provisional" if blockers else "verified")
    record["passed"] = record["automated_checks_passed"] and not blockers

    out = Path(args.out)
    out = out if out.is_absolute() else _root / out
    out.write_bytes(json.dumps(record, indent=2, sort_keys=True,
                               ensure_ascii=False).encode("utf-8") + b"\n")

    print("  url      %s" % base)
    commit = record["commit"]
    print("  commit   %s  (%s, %s behind this checkout)"
          % (commit["stamped_on_the_site"],
             "serving this checkout" if commit["is_head"]
             else ("in this history" if commit["in_this_history"]
                   else "NOT IN THIS HISTORY"),
             commit["commits_behind_measurement_head"]))
    for section in sections:
        print("  %-9s %s" % (section,
                             "ok  " if record[section]["passed"] else "FAIL"))
    if "downloads" in record:
        d = record["downloads"]
        print("           %d module(s) byte-identical to the repository, "
              "%d checksum entries verified"
              % (len(d["modules"]) - len(d["mismatched"]),
                 d["published_checksums"]["entries"]
                 - len(d["published_checksums"]["unverified"])))
    print()
    print("  automated checks : %s"
          % ("all passed" if record["automated_checks_passed"] else "FAILED"))
    print("  deployment       : %s" % record["deployment_status"])
    for name in record["blocked_by"]:
        print("  blocked by       : %s (not performed)" % name)
    print("  phase 7 verdict  : %s"
          % ("passed" if record["passed"] else "open"))
    print()
    print("  wrote %s" % args.out)
    return 0 if record["automated_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
