"""Tests for the analytical agents (MAREP v2.2 §4.2).

An agent is the only component that decides what is worth saying, which makes
it the component most able to put nonsense into canonical state. These tests
are mostly about what the Runtime refuses to let it do, and about the two
places where an agent's own code has to be careful: grounding and identifiers.
"""

from __future__ import annotations

import pytest

from conftest import ROSTER, upd
from marep import Cause, Runtime
from marep.agents import (
    ONTOLOGY_ROSTER,
    ActionProposal,
    Agent,
    AgentRole,
    Assessment,
    EvidenceRef,
    Finding,
    ScriptedAgentBackend,
    SilentAgentBackend,
    build_roster,
)

REAL = EvidenceRef("Rollback of 42.3 needed manual work", "ci_run", "CI-1204")
GHOST = EvidenceRef("Something nobody logged", "metric", "MET-9999")


def _agent(rt: Runtime, name: str, backend) -> Agent:
    role = next((r for r in ONTOLOGY_ROSTER if r.name == name),
                AgentRole(name, "test", "test"))
    return Agent(rt, role, backend)


# ======================================================================
# §4 roster
# ======================================================================

def test_roster_perspectives_are_distinct():
    """§4 forbids two agents covering the same ground under different names."""
    names = [r.name for r in ONTOLOGY_ROSTER]
    focuses = [r.focus for r in ONTOLOGY_ROSTER]
    assert len(names) == len(set(names))
    assert len(focuses) == len(set(focuses))


def test_build_roster_produces_one_agent_per_role(rt: Runtime):
    agents = build_roster(rt, SilentAgentBackend())
    assert [a.name for a in agents] == [r.name for r in ONTOLOGY_ROSTER]


# ======================================================================
# §13.1 gathering
# ======================================================================

def test_gathering_produces_a_grounded_issue(rt: Runtime):
    backend = ScriptedAgentBackend(findings={"Corpus": [
        Finding("PARSE", "A committed file does not parse", "critical", [REAL])]})
    results = _agent(rt, "Corpus", backend).gather()
    assert all(r.accepted for r in results), [r.detail for r in results]
    issue = rt.state["issues"][0]
    assert issue["id"] == "PARSE-001"
    assert issue["evidence"][0]["verified"] is True


def test_an_ungroundable_finding_is_recorded_unverified(rt: Runtime):
    """Not rejected. An unverifiable observation is still worth having; it just
    cannot ground a confirmation."""
    backend = ScriptedAgentBackend(findings={"Corpus": [
        Finding("HUNCH", "Something feels wrong", "low", [GHOST])]})
    results = _agent(rt, "Corpus", backend).gather()
    assert all(r.accepted for r in results)
    assert rt.state["issues"][0]["evidence"][0]["verified"] is False


def test_an_agent_with_nothing_to_say_declines(rt: Runtime):
    """§13.1 — silence blocks the phase; a declination does not."""
    results = _agent(rt, "Realist", SilentAgentBackend()).gather()
    assert all(r.accepted for r in results)
    dec = rt.state["decisions"][0]
    assert dec["type"] == "declination"
    assert dec["subject"] == "AGENT:Realist"


def test_parallel_agents_do_not_collide_on_identifiers(rt: Runtime):
    """Two agents proposing in the same domain must not both mint PARSE-001."""
    b1 = ScriptedAgentBackend(findings={"Corpus": [
        Finding("PARSE", "First finding", "high", [REAL])]})
    b2 = ScriptedAgentBackend(findings={"Realist": [
        Finding("PARSE", "Second finding", "high", [REAL])]})
    assert all(r.accepted for r in _agent(rt, "Corpus", b1).gather())
    assert all(r.accepted for r in _agent(rt, "Realist", b2).gather())
    ids = sorted(i["id"] for i in rt.state["issues"])
    assert ids == ["PARSE-001", "PARSE-002"]


def test_evidence_ids_are_unique_within_an_issue(rt: Runtime):
    backend = ScriptedAgentBackend(findings={"Corpus": [
        Finding("MULTI", "Several supports", "medium",
                [REAL, EvidenceRef("Second support", "ci_run", "CI-1300")])]})
    assert all(r.accepted for r in _agent(rt, "Corpus", backend).gather())
    ids = [e["id"] for e in rt.state["issues"][0]["evidence"]]
    assert ids == ["EV-001", "EV-002"]


# ======================================================================
# §13.3 analysis — the grounding gate binds agents too
# ======================================================================

def _seed(rt: Runtime, evidence=REAL, iid="PARSE-001") -> None:
    backend = ScriptedAgentBackend(findings={"Corpus": [
        Finding(iid.split("-")[0], "A finding", "high", [evidence])]})
    _agent(rt, "Corpus", backend).gather()
    rt.state["retro"]["phase"] = "analysis"


def test_confirming_a_grounded_issue_works(rt: Runtime):
    _seed(rt)
    backend = ScriptedAgentBackend(assessments={"Realist": [
        Assessment("PARSE-001", "confirm", "the evidence supports it")]})
    results = _agent(rt, "Realist", backend).evaluate()
    assert all(r.accepted for r in results), [r.detail for r in results]
    assert rt.state["issues"][0]["status"] == "confirmed"
    assert "Realist" in rt.state["issues"][0]["confirmed_by"]


def test_confirming_an_ungrounded_issue_records_support_without_the_status(rt: Runtime):
    """The endorsement is worth keeping even when the status change is barred.

    Proposing the status anyway would have the Runtime refuse the whole update,
    losing the agent's position along with it.
    """
    _seed(rt, evidence=GHOST, iid="HUNCH-001")
    backend = ScriptedAgentBackend(assessments={"Realist": [
        Assessment("HUNCH-001", "confirm", "I believe it")]})
    results = _agent(rt, "Realist", backend).evaluate()
    assert all(r.accepted for r in results), [r.detail for r in results]
    issue = rt.state["issues"][0]
    assert issue["status"] == "proposed", "the gate still bars confirmation"
    assert "Realist" in issue["confirmed_by"], "but the position is recorded"


def test_one_contest_moves_an_issue_and_blocks_consensus(rt: Runtime):
    """The Skeptic's real power (§13.4), which no vote share would give it."""
    _seed(rt)
    backend = ScriptedAgentBackend(assessments={"Skeptic": [
        Assessment("PARSE-001", "contest", "the finding outruns its evidence")]})
    assert all(r.accepted for r in _agent(rt, "Skeptic", backend).evaluate())
    assert rt.state["issues"][0]["status"] == "contested"
    assert rt.state["conflict_record"][0]["positions"][0]["agent"] == "Skeptic"

    rt.state["retro"]["phase"] = "consensus"
    ready, unmet = rt.exit_ready()
    assert not ready and "PARSE-001" in unmet[0], "one dissenter holds the phase open"


def test_abstaining_writes_nothing(rt: Runtime):
    _seed(rt)
    before = rt.version
    backend = ScriptedAgentBackend(assessments={"Realist": [
        Assessment("PARSE-001", "abstain", "no view")]})
    assert _agent(rt, "Realist", backend).evaluate() == []
    assert rt.version == before


def test_assessing_a_nonexistent_issue_is_refused(rt: Runtime):
    _seed(rt)
    backend = ScriptedAgentBackend(assessments={"Realist": [
        Assessment("NOPE-999", "confirm", "hallucinated")]})
    results = _agent(rt, "Realist", backend).evaluate()
    assert results and not results[0].accepted
    assert "does not exist" in results[0].detail


# ======================================================================
# an agent has no more authority than anyone else
# ======================================================================

def test_agents_cannot_set_verified(rt: Runtime):
    _seed(rt)
    a = _agent(rt, "Realist", SilentAgentBackend())
    r = a._submit("probe", {"issues": [{"id": "PARSE-001", "evidence": [
        {"id": "EV-900", "claim": "self-certified", "verified": True,
         "source": {"type": "metric", "ref": "MET-9999"},
         "submitted_by": "Realist"}]}]})
    assert r.cause is Cause.OUT_OF_SCOPE


def test_agents_cannot_write_outside_their_phase(rt: Runtime):
    a = _agent(rt, "Realist", SilentAgentBackend())
    r = a._submit("probe", {"actions": [{
        "id": "ACT-001", "description": "do a thing", "owner": "Realist",
        "status": "proposed", "outcome_criteria": "the thing is done"}]})
    assert r.cause is Cause.OUT_OF_SCOPE, "actions are not writable during gathering"


def test_agents_cannot_advance_a_phase(rt: Runtime):
    a = _agent(rt, "Realist", SilentAgentBackend())
    assert a._submit("probe", {"retro": {"phase": "merge"}}).cause is Cause.OUT_OF_SCOPE


# ======================================================================
# §19.5 and §14.1
# ======================================================================

def test_backend_failure_degrades(rt: Runtime):
    backend = ScriptedAgentBackend(fail_with=RuntimeError("model unreachable"))
    results = _agent(rt, "Realist", backend).gather()
    assert results and results[0].cause is Cause.ADJUDICATOR_UNAVAILABLE
    assert results[0].retryable
    assert rt.version == 0, "a failed backend leaves state untouched"


def test_substrate_view_is_scoped_to_the_role(rt: Runtime):
    """§14.1 — an agent sees the record types its perspective needs, as summaries."""
    realist = _agent(rt, "Realist", SilentAgentBackend())
    corpus = _agent(rt, "Corpus", SilentAgentBackend())
    assert set(realist.role.substrate_types) == {"metric", "document"}
    assert "commit" in corpus.role.substrate_types
    view = corpus.substrate_view()
    assert all(set(r) == {"id", "type", "ref", "summary"} for r in view), \
        "summaries only; a finding cites a record rather than quoting it"


def test_run_for_phase_dispatches(rt: Runtime):
    backend = ScriptedAgentBackend(findings={"Corpus": [
        Finding("X", "a finding", "low", [REAL])]})
    a = _agent(rt, "Corpus", backend)
    a.run_for_phase()
    assert backend.calls == ["gather:Corpus"]
    rt.state["retro"]["phase"] = "merge"
    a.run_for_phase()
    assert backend.calls == ["gather:Corpus"], "agents do not act during merge"
