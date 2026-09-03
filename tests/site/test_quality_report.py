# SPDX-License-Identifier: Apache-2.0
"""The Phase 6 quality record, checked rather than trusted.

The record is committed because the plan asks for it as a deliverable and
because parts of it -- the fresh clone especially -- take minutes to
produce. That makes it the same kind of artifact as the evidence files:
generated deliberately, and policed on every run.

The cheap sections are re-measured here against a fresh build, so a
report claiming zero broken links cannot survive a link breaking. The
expensive ones are checked for completeness and for having passed, and
the commit they name must be in this history.

The sign-off is checked for being explicit, not for saying yes. An
unsigned block is a true statement about where the work stands; a block
that had quietly acquired a signature nobody gave would not be.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess

import pytest

from marep import layout

REPO = layout.repository_root()
RECORD_PATH = REPO / "config/quality-report.json"

REQUIRED_SECTIONS = {"links", "schemas", "artifact", "suite",
                     "browser_review", "public_content_sign_off"}


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def record():
    assert RECORD_PATH.is_file(), (
        "no quality report. Run tools/site/quality_report.py --fresh-clone")
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def artifact(tmp_path_factory):
    build = _load("qr_build_site", "tools/site/build_site.py")
    out = tmp_path_factory.mktemp("qr") / "_site"
    assert build.main(["-o", str(out)]) == 0
    return out


def test_the_record_is_complete(record):
    assert REQUIRED_SECTIONS <= set(record), sorted(
        REQUIRED_SECTIONS - set(record))
    assert record["operating_system"]
    assert record["measured_checks_passed"] is True


def test_the_gate_is_not_passed_while_the_sign_off_is_unsigned(record):
    """Two different questions, and conflating them let the record report
    `passed: true` over a sign-off nobody had made.

    measured_checks_passed is what the tool can determine. passed is the
    gate, and the gate includes a statement only the owner can make.
    """
    signed = record["public_content_sign_off"]["status"] == "signed"
    assert record["passed"] == (record["measured_checks_passed"] and signed)
    if not signed:
        assert record["passed"] is False, (
            "the gate reports success over an unsigned sign-off")
        assert record.get("gate_blocked_by"), (
            "the record must say why the gate is not passed")
        assert "sign_off" in record["gate_blocked_by"]


def test_the_record_was_made_in_this_history(record):
    """A report from a branch nobody merged describes nothing here."""
    kind = subprocess.run(["git", "cat-file", "-t", record["commit"]],
                          cwd=str(REPO), capture_output=True, text=True)
    assert kind.stdout.strip() == "commit", record["commit"]
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", record["commit"], "HEAD"],
        cwd=str(REPO), capture_output=True)
    assert ancestor.returncode == 0, (
        "the quality report names a commit that is not an ancestor of HEAD")


def test_the_link_report_still_holds(record, artifact):
    """Re-measured, not trusted. Cheap enough to check every run."""
    tool = _load("qr_tool", "tools/site/quality_report.py")
    now = tool.link_report(artifact)
    assert not now["broken"], now["broken"]
    assert now["fragments_checked"] >= 7, (
        "fragments are being discarded rather than resolved; the skip "
        "link is the reference whose whole purpose is its fragment")
    assert now["internal_references"] == record["links"]["internal_references"], (
        "the report counted %d internal references and the build now has %d"
        % (record["links"]["internal_references"], now["internal_references"]))


def test_the_schema_report_still_holds(record, artifact):
    tool = _load("qr_tool_schemas", "tools/site/quality_report.py")
    now = tool.schema_report(artifact)
    assert not now["problems"], now["problems"]
    assert len(now["documents"]) == len(record["schemas"]["documents"])
    for entry in now["documents"]:
        assert entry["schema_present"], entry
        assert entry["valid"], entry
        assert entry["id_matches_path"], entry


def test_the_link_report_would_notice_a_break(artifact):
    """Guards the check above: a link report that resolved everything by
    construction would pass on a site with no links at all."""
    tool = _load("qr_tool_break", "tools/site/quality_report.py")
    page = artifact / "explore/index.html"
    original = page.read_text(encoding="utf-8")
    page.write_text(
        original.replace('href="../modules/"',
                         'href="../modules-that-do-not-exist/"', 1),
        encoding="utf-8", newline="")
    try:
        broken = tool.link_report(artifact)["broken"]
        assert broken, "a deliberately broken link was not detected"
    finally:
        page.write_text(original, encoding="utf-8", newline="")


def test_the_suite_comparison_records_no_unexplained_loss(record):
    suite = record["suite"]
    assert not suite["missing_unrecorded"], suite["missing_unrecorded"]
    assert not suite["collisions"], suite["collisions"]
    assert suite["final_collected"] > suite["pre_site_collected"]
    for rename in suite["renames"]:
        assert rename["adjudicated"] == "approved", rename


def test_the_fresh_clone_record_is_present_and_clean(record):
    """The plan asks for a fresh-checkout build record, and the record
    has to show the conditions it was taken under."""
    assert "fresh_clone" in record, (
        "the report was generated without --fresh-clone, so the "
        "fresh-checkout build record the plan asks for is missing")
    clone = record["fresh_clone"]
    assert clone["passed"], clone
    assert clone["site_present_before_build"] is False, (
        "the clone already had a _site, so it did not prove a clean build")
    assert clone["remotes"] == ["origin"], clone["remotes"]
    assert clone["build_exit"] == 0 and clone["tests_exit"] == 0
    assert clone["site_tree_digest"] and clone["bundle_sha256"]


def test_the_browser_review_is_referenced_and_passed(record):
    review = record["browser_review"]
    assert review["passed"]
    assert len(review["engines"]) == 5, review["engines"]
    assert set(review["not_covered"]) == {"safari", "screen_reader"}, (
        review["not_covered"])


def test_the_sign_off_is_explicit_about_being_unsigned(record):
    """It is the owner's statement. The record must say plainly whether
    it has been made, and must not drift into looking made."""
    sign_off = record["public_content_sign_off"]
    assert sign_off["status"] in ("unsigned", "signed"), sign_off["status"]
    assert sign_off["who"]
    assert len(sign_off["asserts"]) >= 4
    if sign_off["status"] == "signed":
        assert sign_off.get("signed_by"), (
            "a signed sign-off must name who signed it")
        assert sign_off.get("signed_at"), (
            "a signed sign-off must say when")


def test_a_broken_same_page_fragment_is_caught(artifact):
    """The skip link, pointed at an id that no longer exists."""
    tool = _load("qr_frag_same", "tools/site/quality_report.py")
    page = artifact / "explore/index.html"
    original = page.read_text(encoding="utf-8")
    page.write_text(
        original.replace('<main id="main" tabindex="-1">',
                         '<main id="renamed" tabindex="-1">', 1),
        encoding="utf-8", newline="")
    try:
        broken = tool.link_report(artifact)["broken"]
        assert any(b["target"] == "#main" for b in broken), broken
    finally:
        page.write_text(original, encoding="utf-8", newline="")


def test_a_broken_cross_page_fragment_is_caught(artifact):
    """The case that was silently unchecked. The page table was keyed by
    the rglob path while targets resolved to absolute paths, so every
    cross-page fragment missed the lookup and was recorded as "not an
    HTML page" instead of being verified."""
    tool = _load("qr_frag_cross", "tools/site/quality_report.py")
    page = artifact / "models/index.html"
    original = page.read_text(encoding="utf-8")
    mutated = original.replace('href="../about/"',
                               'href="../about/#no-such-anchor"', 1)
    assert mutated != original, "the mutation did not apply"
    page.write_text(mutated, encoding="utf-8", newline="")
    try:
        broken = tool.link_report(artifact)["broken"]
        assert any(b["fragment"] == "no-such-anchor" for b in broken), broken
    finally:
        page.write_text(original, encoding="utf-8", newline="")


def test_no_fragment_is_recorded_as_unverifiable(record):
    """A fragment the report could not check is a fragment nobody
    checked. Every one on this site lands on an HTML page.

    This read record["links"]["rows"], which link_report never returned,
    so it examined an empty list on every run and would have passed with
    any number of unverifiable fragments. The tool now reports them
    explicitly and counts them as a failure.
    """
    links = record["links"]
    assert "unverifiable_fragments" in links, (
        "the report does not say whether any fragment went unverified")
    assert not links["unverifiable_fragments"], links["unverifiable_fragments"]
    assert links["fragments_verified"] == links["fragments_checked"], (
        "%d fragments were counted as checked but only %d resolved"
        % (links["fragments_checked"], links["fragments_verified"]))


def test_a_fragment_on_a_non_html_target_is_reported(artifact):
    """The case that was counted as checked and left successful: a
    fragment into a JSON file cannot be resolved, and saying nothing
    about it is how it stayed invisible."""
    tool = _load("qr_frag_nonhtml", "tools/site/quality_report.py")
    page = artifact / "explore/index.html"
    original = page.read_text(encoding="utf-8")
    mutated = original.replace('href="../data/class-index.json"',
                               'href="../data/class-index.json#nope"', 1)
    assert mutated != original, "the mutation did not apply"
    page.write_text(mutated, encoding="utf-8", newline="")
    try:
        report = tool.link_report(artifact)
        assert report["unverifiable_fragments"], (
            "a fragment into a non-HTML file was not reported")
        assert not report["passed"], (
            "the link report passed with an unverifiable fragment")
    finally:
        page.write_text(original, encoding="utf-8", newline="")


def test_the_allowance_list_is_empty_and_policed(record):
    """An allowance is a decision somebody has to defend. Empty means
    every fragment on this site is genuinely resolved."""
    tool = _load("qr_allow", "tools/site/quality_report.py")
    assert tool.ALLOWED_UNVERIFIABLE_FRAGMENTS == ()
