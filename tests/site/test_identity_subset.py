# SPDX-License-Identifier: Apache-2.0
"""No test disappeared while the site was being built.

The publication plan's gate asks that the pre-site canonical identity set
be a subset of the final one: adding tests is expected, losing one is not.
A digest cannot answer that -- it says two sets differ, not which member
went missing -- so the set itself is recorded in
`config/test-identity-baseline.json` and compared here.

Renames are the interesting case. A rename removes an identity and adds
another, which is indistinguishable from a deletion plus an unrelated
addition unless somebody writes down that they are the same test. Each
one is recorded with the commit that made it and what changed, and both
halves are checked: the old name must be gone and the new one must exist,
so a rename entry cannot quietly cover a genuine loss.
"""

from __future__ import annotations

import collections
import json
import os
import subprocess
import sys

import pytest

from marep import layout

REPO = layout.repository_root()
BASELINE = REPO / "config/test-identity-baseline.json"


@pytest.fixture(scope="module")
def baseline():
    return json.loads(BASELINE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def current():
    """The identity set of the tree as it stands, same reduction."""
    # sys.executable, not "python": the requirements-only gate runs the
    # suite from a virtual environment whose interpreter is not the one
    # on PATH, and collecting with the wrong one would compare this
    # tree's identities against a different environment's.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "-m", "slow or not slow"],
        cwd=str(REPO), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-2000:]
    out = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if "::" in line and not line.startswith(" "):
            out.append(os.path.basename(line))
    assert out, "collected nothing"
    return sorted(out)


def test_the_baseline_was_taken_before_the_site_work(baseline):
    """It has to predate Phase 0 or it is not a pre-site set."""
    commit = baseline["pre_site_commit"]
    kind = subprocess.run(["git", "cat-file", "-t", commit],
                          cwd=str(REPO), capture_output=True, text=True)
    assert kind.stdout.strip() == "commit"

    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=str(REPO), capture_output=True)
    assert ancestor.returncode == 0, "the baseline commit is not in history"

    touched = subprocess.run(
        ["git", "show", "--name-only", "--format=", commit],
        cwd=str(REPO), capture_output=True, text=True).stdout.split()
    assert not [p for p in touched if p.startswith("site/")], (
        "the baseline commit already touches site/, so it is not pre-site")


def test_every_pre_site_identity_survives(baseline, current):
    """The gate condition. Additions are expected; losses are not."""
    renamed = {r["was"] for r in baseline["renames"]}
    now = set(current)
    missing = sorted(set(baseline["identities"]) - now - renamed)
    assert not missing, (
        "%d pre-site test identity/identities are gone and unrecorded: %s"
        % (len(missing), missing))


def test_each_recorded_rename_is_a_rename_and_not_a_loss(baseline, current):
    """Both halves. A rename entry whose replacement does not exist is a
    deletion with an explanation attached."""
    now = set(current)
    for rename in baseline["renames"]:
        assert rename["was"] not in now, (
            "%s still exists, so recording it as renamed is wrong"
            % rename["was"])
        assert rename["now"] in now, (
            "%s was recorded as the replacement for %s but does not exist"
            % (rename["now"], rename["was"]))
        assert rename["was"] in set(baseline["identities"]), (
            "%s is recorded as a rename but was never in the pre-site set"
            % rename["was"])
        for field in ("commit", "why", "phase"):
            assert rename.get(field), (rename["was"], field)


def test_the_rename_commit_actually_made_the_rename(baseline):
    """Derived, not asserted: the named commit must contain both sides."""
    for rename in baseline["renames"]:
        diff = subprocess.run(
            ["git", "show", "--format=", rename["commit"]],
            cwd=str(REPO), capture_output=True, text=True).stdout
        old_name = rename["was"].split("::", 1)[1]
        new_name = rename["now"].split("::", 1)[1]
        assert "-def " + old_name in diff, (
            "%s does not remove %s" % (rename["commit"], old_name))
        assert "+def " + new_name in diff, (
            "%s does not add %s" % (rename["commit"], new_name))


def test_no_identity_collides(current):
    """Two tests reducing to one identity would make the count and the
    digest disagree with what actually ran."""
    duplicates = [i for i, n in collections.Counter(current).items() if n > 1]
    assert not duplicates, duplicates


def test_the_set_only_grew(baseline, current):
    """Recorded so the direction of travel is visible, and so a sudden
    contraction is a failure rather than a smaller number."""
    assert len(current) >= baseline["collected"], (
        "the suite collects %d tests, fewer than the %d recorded before the "
        "site work began" % (len(current), baseline["collected"]))


def test_the_baseline_is_not_regenerated_from_the_present(baseline, current):
    """It is historical. If it were rebuilt from today's tree the subset
    check would compare the present against itself and always pass."""
    added = set(current) - set(baseline["identities"])
    assert added, (
        "the baseline contains every current identity, which means it was "
        "regenerated from this tree rather than from the pre-site commit")
    assert len(baseline["identities"]) == baseline["collected"]
