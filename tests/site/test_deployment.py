# SPDX-License-Identifier: Apache-2.0
"""The deployment record, checked rather than trusted.

Verifying production means fetching production, so the check is run
deliberately and its result committed -- the same arrangement as the
browser review and the quality report. These tests run every time and
hold the record to what it claims.

The record is about a moment: the site as served at one commit. So the
strongest thing these tests can do is refuse a record that describes a
different commit from the one it is committed beside, and refuse one
whose sections are missing, empty, or passing for the wrong reason. A
downloads check that fetched nothing would pass every naive assertion.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from marep import layout

REPO = layout.repository_root()
RECORD_PATH = REPO / "config/deployment-record.json"

REQUIRED_SECTIONS = {"pages", "relative_paths", "downloads", "browser"}


@pytest.fixture(scope="module")
def record():
    assert RECORD_PATH.is_file(), (
        "no deployment record. Run tools/site/verify_deployment.py after "
        "the Pages workflow has published.")
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def test_every_automated_section_passed(record):
    assert REQUIRED_SECTIONS <= set(record), sorted(
        REQUIRED_SECTIONS - set(record))
    for section in REQUIRED_SECTIONS:
        assert record[section]["passed"], (section, record[section])
    assert record["automated_checks_passed"] is True


def test_the_phase_verdict_waits_on_the_manual_checks(record):
    """Two checks need a person. Reporting the phase as passed over them
    would be the overclaim the browser record was corrected for, and the
    site is already serving, so the deployment is provisional rather than
    verified until they are done.
    """
    manual = record["manual_checks"]
    assert set(manual) == {"safari_on_macos", "chrome_nvda_listening_pass"}
    outstanding = sorted(name for name, check in manual.items()
                         if check["status"] != "performed")
    assert record["blocked_by"] == outstanding
    assert record["passed"] == (record["automated_checks_passed"]
                                and not outstanding)
    if outstanding:
        assert record["passed"] is False
        assert record["deployment_status"] == "provisional"
    for name, check in manual.items():
        assert check["why"], name
        assert check["required_before_phase7_sign_off"], name


def test_the_record_names_the_public_url_the_site_declares(record):
    site = json.loads(
        (layout.component("site.content").resolve() / "site.json")
        .read_text(encoding="utf-8"))
    assert record["public_url"] == site["deployment"]["public_url"]
    assert record["public_url"].endswith("/ValueNet/"), record["public_url"]


def test_the_deployed_commit_is_in_this_history(record):
    """A record describing a commit nobody has is a record of nothing."""
    stamped = record["commit"]["stamped_on_the_site"]
    assert stamped, "the served pages carry no build stamp"
    kind = subprocess.run(["git", "cat-file", "-t", stamped],
                          cwd=str(REPO), capture_output=True, text=True)
    assert kind.stdout.strip() == "commit", stamped
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", stamped, "HEAD"],
        cwd=str(REPO), capture_output=True)
    assert ancestor.returncode == 0, (
        "the deployed commit %s is not an ancestor of HEAD" % stamped)
    assert record["commit"]["in_this_history"] is True


def test_the_deployment_was_current_when_measured(record):
    """Two moments, two questions.

    At capture time the verifier requires the deployed commit to be this
    checkout's HEAD, because running it later against an arbitrarily
    stale deployment would satisfy ancestry and prove nothing. Once the
    record is committed the branch moves on, so what a repository test
    can still ask is whether the deployment was current at the moment it
    was measured -- which is a fixed fact the record carries.

    Current lag is a live question and is recomputed by whoever asks,
    never read out of a file that cannot know the answer.
    """
    commit = record["commit"]
    assert commit["commits_behind_measurement_head"] == 0, (
        "the deployment was already %s commits behind when it was measured"
        % commit["commits_behind_measurement_head"])
    assert commit["is_head"] is True
    assert commit["local_head"].startswith(commit["stamped_on_the_site"]), (
        "local_head is the measurement commit and must be the one served")


def test_the_record_identifies_the_verifier_that_produced_it(record):
    """The tool can postdate the commit it measures -- it did, on the
    first run -- so the record says which bytes asked the questions."""
    digest = record.get("verifier_sha256")
    assert digest and len(digest) == 64, digest


def test_every_page_was_fetched_and_served(record):
    """Guards the section: an empty page list passes `all()`."""
    pages = record["pages"]["pages"]
    assert len(pages) >= 7, pages
    served = {p["path"] for p in pages}
    for required in ("/", "/explore/", "/models/", "/modules/",
                     "/downloads/", "/about/"):
        assert required in served, required
    for page in pages:
        assert page["status"] == 200, page
        assert page["is_html"], page
        assert page["bytes"] > 500, page


def test_no_reference_on_any_page_is_root_absolute(record):
    """The failure the relative-URL rule exists to prevent, and the one
    that only appears once the site is served from a subpath.

    Every page, not one. The first version scanned /explore/ alone while
    the record it produced was phrased as a claim about the site.
    """
    relative = record["relative_paths"]
    assert relative["root_absolute_references"] == []
    assert relative["pages_scanned"] == len(record["pages"]["pages"])
    for page in relative["per_page"]:
        assert page["status"] == 200, page
        assert page["references"] > 0, (
            "%s was scanned for references and had none, so finding none "
            "root-absolute proves nothing" % page["path"])
        assert page["root_absolute"] == [], page


def test_every_module_was_compared_against_the_repository(record):
    """The check that matters: what is served is what is authored.

    Asserted on the rows rather than on the summary, because a run that
    fetched nothing would report no mismatches.
    """
    downloads = record["downloads"]
    rows = downloads["modules"]
    assert len(rows) == 11, len(rows)
    assert not downloads["mismatched"], downloads["mismatched"]
    for row in rows:
        assert row["status"] == 200, row
        assert row["bytes_served"] > 0, row
        assert row["bytes_served"] == row["bytes_in_repository"], row
        assert row["matches_repository"], row
        assert row["matches_manifest_sha256"], row


def test_the_published_checksums_are_the_right_set_and_verified(record):
    """Membership as well as verification.

    Every listed entry verifying says nothing about whether the right
    entries are listed: a wrong set of twelve would have satisfied the
    first version of this check.
    """
    checksums = record["downloads"]["published_checksums"]
    assert checksums["status"] == 200, checksums
    assert checksums["entries"] == 12, checksums
    assert checksums["expected_entries"] == 12, checksums
    assert not checksums["missing"], checksums["missing"]
    assert not checksums["unexpected"], checksums["unexpected"]
    assert not checksums["unverified"], checksums["unverified"]

    bundle = record["downloads"]["bundle"]
    assert bundle["status"] == 200, (
        "the bundle status was overwritten by the checksum file's before "
        "these were kept apart")
    assert bundle["sha256_matches"]
    assert bundle["bytes"] > 10000, bundle


def test_the_explorer_worked_in_production(record):
    """Loaded from the public URL, not from a local build."""
    browser = record["browser"]
    assert browser["console_errors"] == [], browser["console_errors"]
    assert browser["failed_requests"] == [], browser["failed_requests"]
    assert browser["classes_rendered"] >= 180, browser["classes_rendered"]
    assert browser["search_betrayal_results"] >= 1
    assert browser["search_first_result"] == "moral-foundations:BetrayalProcess"
    assert browser["deep_link_heading"], "the deep link opened nothing"
    assert browser["diagrams_rendered"] == 3


def test_a_console_error_would_have_failed_the_check(record):
    """Guards the assertion above. A page that renders while logging a
    failed fetch has a search that is broken for every visitor and looks
    correct in a screenshot, so the console is part of the verdict."""
    browser = record["browser"]
    recomputed = (not browser["console_errors"]
                  and not browser["failed_requests"]
                  and browser["classes_rendered"] >= 180)
    assert recomputed == browser["passed"], (
        "the browser verdict does not follow from what was observed")
