# SPDX-License-Identifier: Apache-2.0
"""The browser review record, held to what it claims.

The review itself needs four browsers and a few hundred megabytes of
them, so it is run deliberately and its result committed, the way the
evidence artifacts are. These tests run every time and check the record:
that it covers what it must, that every observed result passed, that it
describes the site currently in the tree rather than an older one, and
that it does not claim coverage it does not have.

The last is the reason this file exists. A review record is a document
asserting that somebody looked, and the cheapest failure mode in the
whole project is a document that says a thing was checked when it was
not. Two gaps are real here -- Safari and a screen reader -- and the
record is required to keep naming them.
"""

from __future__ import annotations

import importlib.util
import json

import pytest

from marep import layout

REPO = layout.repository_root()
RECORD_PATH = REPO / "config/browser-review.json"

REQUIRED_CHECKS = {"deep_link_keyboard", "live_regions",
                   "hostile_ontology_text", "diagrams"}
REQUIRED_VIEWPORTS = {"narrow", "wide", "high-zoom-400pct"}
#: Edge is a distinct product with its own release train even though it
#: shares Chromium's engine, and the plan names it. Chromium and Chrome
#: were standing in for it, which is not the same as running it.
REQUIRED_ENGINES = {"chromium", "chrome", "edge", "firefox",
                    "playwright-webkit"}


@pytest.fixture(scope="module")
def record():
    assert RECORD_PATH.is_file(), (
        "no browser review record. Run tools/site/browser_review.py; the "
        "browser gate cannot be satisfied by the source-level tests.")
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def test_the_record_describes_the_site_in_the_tree(record, tmp_path):
    """Freshness. A record measured against an older build certifies a
    site nobody is shipping, and nothing about it looks stale."""
    spec = importlib.util.spec_from_file_location(
        "review_build_site", REPO / "tools/site/build_site.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)

    out = tmp_path / "_site"
    assert build.main(["-o", str(out)]) == 0

    spec = importlib.util.spec_from_file_location(
        "review_tool", REPO / "tools/site/browser_review.py")
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)

    assert tuple(record["reviewed_files"]) == review.REVIEWED_FILES, (
        "the record covers a different set of files than the review loads")
    assert set(record["reviewed_files"]) == {
        p.relative_to(out).as_posix() for p in review.reviewed_files(out)}

    # The set is small and named, so it is pinned: silently shrinking it
    # would leave a stable digest describing less than it claims.
    assert "explore/index.html" in record["reviewed_files"]
    assert "models/index.html" in record["reviewed_files"]
    assert "data/class-index.json" in record["reviewed_files"]

    assert review.tree_digest(out) == record["reviewed_files_sha256"], (
        "the browser review was measured against a different build. Re-run "
        "tools/site/browser_review.py after changing the site.")


def test_every_engine_was_exercised(record):
    engines = {b["engine"] for b in record["browsers"]}
    assert engines == REQUIRED_ENGINES, sorted(engines ^ REQUIRED_ENGINES)
    for browser in record["browsers"]:
        assert browser.get("version"), browser["engine"]
        assert "error" not in browser, browser.get("error")


def test_every_required_check_ran_in_every_engine(record):
    for browser in record["browsers"]:
        assert set(browser["checks"]) == REQUIRED_CHECKS, browser["engine"]
        viewports = set(browser["checks"]["diagrams"])
        assert viewports == REQUIRED_VIEWPORTS, browser["engine"]


def test_every_observed_result_passed(record):
    failures = []
    for browser in record["browsers"]:
        for name, check in browser["checks"].items():
            if name == "diagrams":
                for viewport, result in check.items():
                    if not result["passed"]:
                        failures.append("%s/%s/%s" % (browser["engine"],
                                                      name, viewport))
            elif not check["passed"]:
                failures.append("%s/%s" % (browser["engine"], name))
    assert not failures, failures
    assert record["passed"]


def test_the_environment_is_recorded(record):
    """A review nobody can reproduce is an anecdote."""
    assert record["operating_system"]
    assert record["deep_link_class"]
    for viewport in REQUIRED_VIEWPORTS:
        box = record["viewports"][viewport]
        assert box["width"] > 0 and box["height"] > 0


def test_the_hostile_text_was_actually_hostile(record):
    """Guards the payload: a check that injected nothing would pass."""
    for browser in record["browsers"]:
        hostile = browser["checks"]["hostile_ontology_text"]
        payloads = hostile["payloads"]
        assert any("<script" in v for v in payloads.values())
        assert any("onerror" in v for v in payloads.values())
        assert any("onload" in v for v in payloads.values())
        # The payload must have reached the page as text, or the check
        # proved only that an absent string cannot execute.
        assert hostile["label_rendered_as_text"] == payloads["label"]
        assert hostile["window_flag_set"] is None
        assert hostile["elements_injected"] == {"img": 0, "svg": 0,
                                                "script": 0}


def test_the_deep_link_check_had_a_list_to_cross(record):
    """The bypass matters because the list is long. A run that rendered
    two results would pass while proving nothing."""
    for browser in record["browsers"]:
        keyboard = browser["checks"]["deep_link_keyboard"]
        assert keyboard["results_rendered"] >= 100, keyboard
        assert keyboard["tab_stops_to_bypass"] is not None
        assert keyboard["focus_after_activation"] == "detail"


def test_webkit_reaches_the_bypass_despite_skipping_anchors(record):
    """The finding this phase turned up.

    WebKit's default keyboard model puts no anchor in the tab order, so
    the bypass was unreachable by Tab there while working in the other
    three engines. It is a button now. The measurement is kept because
    the same platform behaviour still applies to the skip link and to
    every result link, which is a property of the browser rather than
    something this site can fix.
    """
    by_engine = {b["engine"]: b["checks"]["deep_link_keyboard"]
                 for b in record["browsers"]}
    webkit = by_engine["playwright-webkit"]
    assert webkit["anchors_in_tab_order"] == 0, (
        "WebKit now tabs to anchors; the bypass no longer needs to be a "
        "button for that reason, though it is still the right element")
    assert webkit["tab_stops_to_bypass"] is not None
    for engine in ("chromium", "chrome", "firefox"):
        assert by_engine[engine]["anchors_in_tab_order"] > 0, engine


def test_the_record_does_not_claim_safari(record):
    """Playwright's WebKit is not Safari, and a record saying otherwise
    would be worse than one admitting the gap."""
    blob = json.dumps(record).lower()
    engines = {b["engine"] for b in record["browsers"]}
    assert "safari" not in engines
    assert "safari" in record["not_covered"], (
        "the record must say Safari was not tested")
    assert "not tested" in record["not_covered"]["safari"].lower()
    # The word may appear only inside the not-covered explanation.
    outside = json.dumps({k: v for k, v in record.items()
                          if k != "not_covered"}).lower()
    assert "safari" not in outside, "Safari is named as if it were covered"
    assert blob.count("playwright-webkit") >= 1


def test_the_record_does_not_claim_a_screen_reader(record):
    """The live-region checks read the accessibility tree. A screen
    reader consuming it is a different, unrun test."""
    assert "screen_reader" in record["not_covered"]
    assert "not run" in record["not_covered"]["screen_reader"].lower()
    for browser in record["browsers"]:
        live = browser["checks"]["live_regions"]
        assert live["screen_reader_used"] is None
        assert "no screen reader" in live["note"].lower()


# ============================================== the second live region


def test_the_copy_result_region_is_a_live_region_too(record):
    """The one created at runtime, and therefore the one that can be
    created without its role while nothing static notices."""
    for browser in record["browsers"]:
        copy = browser["checks"]["live_regions"]["copy_result"]
        assert copy["role"] == "status", browser["engine"]
        assert copy["aria_live"] == "polite", browser["engine"]
        assert copy["exposed_as_status_role"], browser["engine"]


def test_the_copy_result_region_announced_something(record):
    """Either outcome is acceptable and one of them must happen. A copy
    button that silently does nothing is the failure the visible refusal
    was written to prevent."""
    for browser in record["browsers"]:
        copy = browser["checks"]["live_regions"]["copy_result"]
        assert copy["text_before_click"] == "", browser["engine"]
        assert copy["text_after_click"], (
            "%s: the copy button changed nothing a screen reader could "
            "announce" % browser["engine"])
        assert copy["text_changed"]
        spoken = copy["text_after_click"].lower()
        assert ("copied" in spoken or "refused" in spoken
                or "unavailable" in spoken), copy["text_after_click"]


# ================================================== diagram internals


def test_diagram_internals_were_measured_not_just_the_frame(record):
    """Whole-SVG visibility says the figure is on the page. It says
    nothing about what is inside it."""
    for browser in record["browsers"]:
        for viewport, result in browser["checks"]["diagrams"].items():
            assert len(result["diagrams"]) == 3, (browser["engine"], viewport)
            for diagram in result["diagrams"]:
                where = (browser["engine"], viewport, diagram["index"])
                assert diagram["elements"]["rect"] > 0, where
                assert diagram["elements"]["text"] > 0, where
                assert diagram["labels_measured"] > 0, where


def test_nothing_is_clipped_or_collides_in_any_viewport(record):
    for browser in record["browsers"]:
        for viewport, result in browser["checks"]["diagrams"].items():
            for diagram in result["diagrams"]:
                where = "%s/%s/diagram %d" % (browser["engine"], viewport,
                                              diagram["index"])
                assert not diagram["clipped"], (where, diagram["clipped"])
                assert not diagram["overlapping_labels"], (
                    where, diagram["overlapping_labels"])
                assert not diagram["zero_length_paths"], where


def test_the_relation_paths_and_arrowheads_rendered(record):
    """A diagram of boxes with no arrows between them is a different
    diagram from the one the alternative describes."""
    for browser in record["browsers"]:
        for viewport, result in browser["checks"]["diagrams"].items():
            arrows = result["arrowheads"]
            assert arrows["markers"] >= 3, (browser["engine"], viewport)
            assert arrows["paths_with_marker_end"] >= 10, (
                browser["engine"], viewport, arrows)


def test_a_screenshot_exists_for_every_engine_and_viewport(record):
    """Reviewed by eye, not by assertion -- but it has to be there, and
    it has to be the image the record names."""
    import hashlib

    seen = set()
    for browser in record["browsers"]:
        for viewport, result in browser["checks"]["diagrams"].items():
            shot = result["screenshot"]
            path = REPO / shot["path"]
            assert path.is_file(), shot["path"]
            data = path.read_bytes()
            assert len(data) == shot["bytes"], shot["path"]
            assert hashlib.sha256(data).hexdigest() == shot["sha256"], (
                "%s does not match the digest recorded for it" % shot["path"])
            seen.add((browser["engine"], viewport))
    assert len(seen) == len(REQUIRED_ENGINES) * len(REQUIRED_VIEWPORTS), seen
