# SPDX-License-Identifier: Apache-2.0
"""Tests for the substrate builder (MAREP v2.2 §7).

Built against a throwaway git repository with fixed commit dates, so the
assertions are about the builder rather than about whatever this repo happens
to contain today.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from marep import ingest, validate_substrate
from marep.substrate import RECORD_TYPES, Substrate


def _git(repo: Path, *args: str, when: str | None = None) -> None:
    """Run git with identity supplied inline.

    Identity comes from -c rather than the environment so the test does not
    depend on, or disturb, whatever global git config the machine has. Dates
    are pinned so commit ordering is a property of the fixture, not the clock.
    """
    import os

    env = dict(os.environ)
    if when:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    cmd = ["git", "-c", "user.name=Tester", "-c", "user.email=t@example.com", *args]
    subprocess.run(cmd, cwd=repo, check=True, capture_output=True, env=env)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    for n, (msg, when) in enumerate([
        ("Add the widget", "2026-03-02T10:00:00+00:00"),
        ("Fix the widget rollback", "2026-03-03T11:30:00+00:00"),
        ("Out of range change", "2026-05-01T09:00:00+00:00"),
    ], start=1):
        (r / f"f{n}.txt").write_text(f"content {n}\n", encoding="utf-8")
        _git(r, "add", "-A", when=when)
        _git(r, "commit", "-q", "-m", msg, when=when)
    return r


def test_collects_commits_in_range(repo: Path):
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31",
                          repo=repo, include_github=False)
    assert result.counts["commit"] == 2, "the May commit is outside the range"
    assert not result.errors


def test_output_validates_against_the_schema(repo: Path):
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31",
                          repo=repo, include_github=False)
    assert validate_substrate(result.document) == []


def test_identifiers_are_stable_across_runs(repo: Path):
    a = ingest.build("sprint-1", "2026-03-01", "2026-03-31", repo=repo, include_github=False)
    b = ingest.build("sprint-1", "2026-03-01", "2026-03-31", repo=repo, include_github=False)
    assert a.document == b.document, "same inputs must give the same substrate"
    ids = [r["id"] for r in a.document["records"]]
    assert ids == ["CMT-0001", "CMT-0002"]


def test_records_sorted_before_ids_are_minted(repo: Path):
    """Sorting first is what keeps ids stable, so cited evidence keeps resolving."""
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31", repo=repo, include_github=False)
    stamps = [r["timestamp"] for r in result.document["records"]]
    assert stamps == sorted(stamps)


def test_coverage_is_exhaustive(repo: Path):
    """§7.3 — every record type gets an entry, present or not."""
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31", repo=repo, include_github=False)
    declared = {c["type"] for c in result.document["coverage"]}
    assert declared == set(RECORD_TYPES)


def test_unavailable_types_state_a_reason(repo: Path):
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31", repo=repo, include_github=False)
    for c in result.document["coverage"]:
        if not c["available"]:
            assert c.get("reason"), f"{c['type']} is unavailable with no reason"


def test_disabling_github_is_recorded_not_hidden(repo: Path):
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31", repo=repo, include_github=False)
    gaps = {c["type"]: c.get("reason", "") for c in result.document["coverage"] if not c["available"]}
    for t in ("pull_request", "ticket", "ci_run", "deploy"):
        assert "disabled" in gaps[t]


def test_non_git_directory_is_an_honest_gap(tmp_path: Path):
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31",
                          repo=tmp_path, include_github=False)
    entry = next(c for c in result.document["coverage"] if c["type"] == "commit")
    assert entry["available"] is False and "not a git repository" in entry["reason"]


def test_notes_are_collected_when_supplied(repo: Path, tmp_path: Path):
    notes = tmp_path / "notes.yaml"
    notes.write_text(yaml.safe_dump([
        {"summary": "Review load felt heavy", "author": "QA",
         "timestamp": "2026-03-04T09:00:00+00:00"},
        "Standups ran long",
    ]), encoding="utf-8")
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31",
                          repo=repo, notes=notes, include_github=False)
    assert result.counts["note"] == 2
    entry = next(c for c in result.document["coverage"] if c["type"] == "note")
    assert entry["available"] is True


def test_write_refuses_a_non_conformant_document(repo: Path, tmp_path: Path):
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31", repo=repo, include_github=False)
    result.document["records"][0].pop("summary")
    result.errors = validate_substrate(result.document)
    with pytest.raises(ValueError, match="non-conformant"):
        ingest.write(result, tmp_path / "out.yaml")


def test_built_substrate_loads_and_resolves(repo: Path, tmp_path: Path):
    """The point of the whole module: evidence can verify against real data."""
    result = ingest.build("sprint-1", "2026-03-01", "2026-03-31", repo=repo, include_github=False)
    path = ingest.write(result, tmp_path / "SPRINT_INPUT.yaml")
    substrate = Substrate.load(path)
    assert len(substrate) == 2
    assert substrate.resolve({"type": "commit", "ref": "CMT-0001"}) is True
    assert substrate.resolve({"type": "ticket", "ref": "CMT-0001"}) is False
    assert substrate.resolve({"type": "commit", "ref": "CMT-9999"}) is False
