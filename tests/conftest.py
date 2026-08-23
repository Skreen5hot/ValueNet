"""Shared fixtures. A small but complete sprint substrate and a fresh Runtime."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from marep import Runtime, Substrate, TokenBudget  # noqa: E402

ROSTER = ["Developer", "QA", "Architect", "Skeptic"]

SUBSTRATE_DOC = {
    "sprint": {"id": "sprint-42", "started": "2026-08-01", "ended": "2026-08-14"},
    "records": [
        {"id": "CI-1204", "type": "ci_run", "ref": "gh-actions/12841",
         "timestamp": "2026-08-09T11:04:00Z", "summary": "Release 42.3 rollback failed"},
        {"id": "DEP-0311", "type": "deploy", "ref": "deploy/42.3",
         "timestamp": "2026-08-09T10:55:00Z", "summary": "Release 42.3 to production"},
        {"id": "TIC-7781", "type": "ticket", "ref": "PROJ-7781",
         "timestamp": "2026-08-10T09:00:00Z", "summary": "Staging/prod runtime divergence"},
        {"id": "NOTE-001", "type": "note", "ref": "retro-note-1",
         "timestamp": "2026-08-14T16:00:00Z", "summary": "Team felt review load was heavy"},
        {"id": "CI-1300", "type": "ci_run", "ref": "gh-actions/13000",
         "timestamp": "2026-08-12T08:00:00Z", "summary": "Flaky integration suite"},
    ],
    "coverage": [
        {"type": "incident", "available": False, "reason": "no incident tracker integration"},
        {"type": "metric", "available": False, "reason": "metrics pipeline not wired to retro"},
        {"type": "ci_run", "available": True},
    ],
}


@pytest.fixture
def substrate_path(tmp_path: Path) -> Path:
    p = tmp_path / "SPRINT_INPUT.yaml"
    p.write_text(yaml.safe_dump(SUBSTRATE_DOC, sort_keys=False), encoding="utf-8")
    return p


@pytest.fixture
def substrate(substrate_path: Path) -> Substrate:
    return Substrate.load(substrate_path)


@pytest.fixture
def rt(substrate: Substrate, tmp_path: Path) -> Runtime:
    return Runtime.initialize(
        "sprint-42", substrate, roster=ROSTER,
        state_path=tmp_path / "RETRO_STATE.yaml",
        budget=TokenBudget(per_turn_context=8000, per_retrospective_total=100_000,
                           compression_reserve=20_000),
    )


def issue(iid="DEPLOY-002", status="proposed", evidence=None, **kw):
    ev = evidence if evidence is not None else [{
        "id": "EV-001",
        "claim": "Rollback of release 42.3 required manual intervention",
        "source": {"type": "ci_run", "ref": "CI-1204"},
        "submitted_by": "Developer",
    }]
    out = {"id": iid, "title": "Deployment instability", "severity": "medium",
           "status": status, "evidence": ev}
    out.update(kw)
    return out


def upd(uid, base, agent_sections):
    """Build an update envelope."""
    d = {"update_id": uid, "base_version": base}
    d.update(agent_sections)
    return d
