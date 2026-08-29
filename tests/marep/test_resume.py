"""Resuming a run must preserve what was verified, or refuse.

Run 2 reached version 117 with 28 findings, every one carrying verified
evidence, and stopped mid-vote because the API credit ran out. The only way
forward was `Runtime.initialize`, which discards all of it and re-derives the
same findings for the same 366,000 tokens. Interruption is not exotic for a run
making hundreds of calls over an hour.

The guard that matters is the substrate checksum. Every piece of evidence was
verified against the substrate current when it was submitted, and the grounding
gate's whole guarantee is that a citation resolves to the record it was checked
against. Resuming onto a different substrate would carry 28 `verified` flags
onto records that may no longer say what they said — a worse outcome than
losing the run, because it would look sound.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml
from _support import ROSTER, SUBSTRATE_DOC

from marep import Runtime, Substrate, state as st


def substrate_at(tmp_path: Path, name: str, extra: str | None = None) -> Substrate:
    """The shared fixture document, optionally with one record added.

    Reusing conftest's document rather than hand-rolling YAML: the schema
    requires a sprint object, record ids, timestamps and summaries, and a
    fixture that drifts from it tests the validator instead of the resume.
    """
    doc = copy.deepcopy(SUBSTRATE_DOC)
    if extra:
        doc["records"].append({
            "id": extra, "type": "note", "ref": "extra/" + extra,
            "timestamp": "2026-08-14T17:00:00Z", "summary": "an added record"})
    p = tmp_path / (name + ".yaml")
    p.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return Substrate.load(p)


def test_resume_restores_phase_version_and_issues(tmp_path: Path):
    sub = substrate_at(tmp_path, "base")
    rt = Runtime.initialize("t", sub, roster=ROSTER, state_path=tmp_path / "s.yaml")
    rt.state["issues"].append({"id": "X-001", "title": "t", "status": "confirmed",
                               "severity": "high", "evidence": []})
    rt.state["retro"]["phase"] = "consensus"
    rt.state["retro"]["version"] = 117
    st.save(rt.state, tmp_path / "s.yaml")

    back = Runtime.resume(tmp_path / "s.yaml", sub, roster=ROSTER)
    assert back.phase == "consensus"
    assert back.version == 117
    assert [i["id"] for i in back.state["issues"]] == ["X-001"]


def test_resume_refuses_a_different_substrate(tmp_path: Path):
    """The guard. Without it, verified evidence silently outlives its source."""
    original = substrate_at(tmp_path, "base")
    rt = Runtime.initialize("t", original, roster=ROSTER, state_path=tmp_path / "s.yaml")
    st.save(rt.state, tmp_path / "s.yaml")

    changed = substrate_at(tmp_path, "changed", extra="NOTE-999")
    assert changed.checksum != original.checksum
    with pytest.raises(ValueError) as exc:
        Runtime.resume(tmp_path / "s.yaml", changed, roster=ROSTER)
    assert "cannot resume" in str(exc.value)
    assert "verified against the old substrate" in str(exc.value)


def test_resume_keeps_writing_to_the_file_it_resumed_from(tmp_path: Path):
    """Otherwise a resumed run's progress goes nowhere and the next
    interruption loses everything again."""
    sub = substrate_at(tmp_path, "base")
    rt = Runtime.initialize("t", sub, roster=ROSTER, state_path=tmp_path / "s.yaml")
    st.save(rt.state, tmp_path / "s.yaml")
    back = Runtime.resume(tmp_path / "s.yaml", sub, roster=ROSTER)
    assert back.state_path == tmp_path / "s.yaml"


def test_an_explicit_state_path_still_wins(tmp_path: Path):
    sub = substrate_at(tmp_path, "base")
    rt = Runtime.initialize("t", sub, roster=ROSTER, state_path=tmp_path / "s.yaml")
    st.save(rt.state, tmp_path / "s.yaml")
    back = Runtime.resume(tmp_path / "s.yaml", sub, roster=ROSTER,
                          state_path=tmp_path / "other.yaml")
    assert back.state_path == tmp_path / "other.yaml"
