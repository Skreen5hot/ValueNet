"""Tests for the Adjudicator (MAREP v2.2 §4.1.2).

The tests that matter most are the negative ones. §4.1.2's central claim is
that the Adjudicator holds no privileged write path, which is only worth
believing if a backend proposing something illegitimate is demonstrably
refused. Several tests below script exactly that.
"""

from __future__ import annotations

import pytest

from conftest import ROSTER, issue, upd
from marep import Cause, Runtime
from marep.adjudicator import (
    Adjudicator,
    CompressionProposal,
    ContradictionFinding,
    MergeProposal,
    NullBackend,
    Position,
    ScriptedBackend,
    TieBreak,
)


def _seed(rt: Runtime, *ids: str, phase: str = "analysis") -> None:
    for n, iid in enumerate(ids, start=1):
        rt.submit(upd(f"SEED{n}", rt.version, {"issues": [issue(
            iid, evidence=[{"id": f"EV-{n:03d}", "claim": "Rollback needed manual work",
                            "source": {"type": "ci_run", "ref": "CI-1204"},
                            "submitted_by": "Developer"}])]}), "Developer")
    rt.state["retro"]["phase"] = phase


# ======================================================================
# the no-privileged-write-path property
# ======================================================================

def test_adjudicator_writes_go_through_the_runtime(rt: Runtime):
    _seed(rt, "PERF-001")
    adj = Adjudicator(rt, ScriptedBackend(contradictions=[
        ContradictionFinding("PERF-001", [
            Position("Architect", "N+1 query pattern", ["EV-001"]),
            Position("QA", "network egress saturation", []),
        ], "incompatible root causes")]))
    results = adj.adjudicate_contradictions()
    assert all(r.accepted for r in results), [r.detail for r in results]
    assert rt.state["issues"][0]["status"] == "contested"
    assert rt.state["conflict_record"][0]["issue_id"] == "PERF-001"
    assert rt.state["audit"][-1]["agent"] == "Adjudicator", "audited under its own identity"


def test_adjudicator_cannot_confirm_an_ungrounded_issue(rt: Runtime):
    """The grounding gate binds the Adjudicator exactly as it binds an agent."""
    rt.submit(upd("S1", rt.version, {"issues": [issue(
        "GHOST-001", evidence=[{"id": "EV-900", "claim": "unverifiable",
                                "source": {"type": "ticket", "ref": "NOPE-1"},
                                "submitted_by": "Skeptic"}])]}), "Skeptic")
    rt.state["retro"]["phase"] = "consensus"
    rt.submit(upd("S2", rt.version, {"votes": [{
        "subject": "ISSUE:GHOST-001:status:confirmed", "threshold": 0.7,
        "denominator": "voting_agents", "outcome": "open",
        "cast": [{"agent": "QA", "position": "confirm"}]}]}), "QA")

    adj = Adjudicator(rt, ScriptedBackend(tie_breaks={
        "ISSUE:GHOST-001:status:confirmed": TieBreak(
            "ISSUE:GHOST-001:status:confirmed", "confirmed", "looks right to me")}))
    results = adj.adjudicate_tie_breaks()
    assert results and not results[0].accepted
    assert results[0].cause is Cause.UNGROUNDED_CONFIRMATION
    assert rt.state["issues"][0]["status"] == "proposed", "state untouched"


def test_adjudicator_cannot_make_an_illegal_transition(rt: Runtime):
    _seed(rt, "PERF-001")
    rt.submit(upd("C1", rt.version, {"issues": [{"id": "PERF-001", "status": "confirmed"}]}), "QA")
    rt.state["retro"]["phase"] = "consensus"
    rt.submit(upd("V1", rt.version, {"votes": [{
        "subject": "ISSUE:PERF-001:status:confirmed", "threshold": 0.7,
        "denominator": "voting_agents", "outcome": "open",
        "cast": [{"agent": "QA", "position": "reject"}]}]}), "QA")
    adj = Adjudicator(rt, ScriptedBackend(tie_breaks={
        "ISSUE:PERF-001:status:confirmed": TieBreak(
            "ISSUE:PERF-001:status:confirmed", "rejected", "changed my mind")}))
    results = adj.adjudicate_tie_breaks()
    assert results and results[0].cause is Cause.ILLEGAL_TRANSITION
    assert rt.state["issues"][0]["status"] == "confirmed"


def test_adjudicator_cannot_write_out_of_phase(rt: Runtime):
    _seed(rt, "PERF-001", phase="actions")
    adj = Adjudicator(rt, ScriptedBackend(contradictions=[
        ContradictionFinding("PERF-001", [Position("QA", "x", [])], "y")]))
    results = adj.adjudicate_contradictions()
    assert results and results[0].cause is Cause.OUT_OF_SCOPE


def test_adjudicator_cannot_advance_a_phase(rt: Runtime):
    _seed(rt, "PERF-001")
    adj = Adjudicator(rt, ScriptedBackend())
    r = adj._submit("probe", {"retro": {"phase": "consensus"}})
    assert r.cause is Cause.OUT_OF_SCOPE


def test_adjudicator_cannot_set_verified(rt: Runtime):
    _seed(rt, "PERF-001")
    adj = Adjudicator(rt, ScriptedBackend())
    r = adj._submit("probe", {"issues": [{"id": "PERF-001", "evidence": [
        {"id": "EV-900", "claim": "self-certified", "verified": True,
         "source": {"type": "ticket", "ref": "NOPE"}, "submitted_by": "Adjudicator"}]}]})
    assert r.cause is Cause.OUT_OF_SCOPE


def test_contradiction_rationale_is_recorded(rt: Runtime):
    """The live run discarded ~1,900 characters of reasoning per contradiction.

    An issue marked contested with no record of why anyone thought so is a
    worse artifact than no adjudication at all.
    """
    _seed(rt, "PERF-001")
    adj = Adjudicator(rt, ScriptedBackend(contradictions=[
        ContradictionFinding("PERF-001", [Position("QA", "egress saturation", ["EV-001"])],
                             "The two positions cannot both hold.")]))
    assert all(r.accepted for r in adj.adjudicate_contradictions())
    dec = [d for d in rt.state["decisions"] if d["subject"] == "ISSUE:PERF-001"]
    assert dec and dec[0]["rationale"] == "The two positions cannot both hold."
    assert dec[0]["basis"] == "adjudicator"


def test_supplied_findings_skip_the_backend(rt: Runtime):
    """Inspecting a proposal then acting on it must not cost two model calls."""
    _seed(rt, "PERF-001")
    backend = ScriptedBackend()
    adj = Adjudicator(rt, backend)
    finding = ContradictionFinding("PERF-001", [Position("QA", "x", ["EV-001"])], "y")
    assert all(r.accepted for r in adj.adjudicate_contradictions(findings=[finding]))
    assert backend.calls == [], "the backend must not be consulted a second time"


def test_conflict_evidence_must_be_ids_not_prose(rt: Runtime):
    """The live model filled this field with sentences; the schema now refuses."""
    _seed(rt, "PERF-001")
    adj = Adjudicator(rt, ScriptedBackend())
    r = adj._submit("probe", {
        "issues": [{"id": "PERF-001", "status": "contested"}],
        "conflict_record": [{"issue_id": "PERF-001", "positions": [
            {"agent": "QA", "claim": "contests it",
             "evidence": ["EV-001 (verified, ci_run CI-4001): latency rose"]}]}]})
    assert r.cause is Cause.SCHEMA_VIOLATION


# ======================================================================
# §13.2 merge
# ======================================================================

def test_merge_carries_evidence_then_archives_the_duplicate(rt: Runtime):
    _seed(rt, "DUP-001", "DUP-002", phase="merge")
    adj = Adjudicator(rt, ScriptedBackend(merges=[
        MergeProposal("DUP-001", "DUP-002", "same finding, different wording")]))
    results = adj.adjudicate_merges()
    assert all(r.accepted for r in results), [r.detail for r in results]
    by_id = {i["id"]: i for i in rt.state["issues"]}
    assert by_id["DUP-002"]["status"] == "archived"
    assert {e["id"] for e in by_id["DUP-001"]["evidence"]} == {"EV-001", "EV-002"}, (
        "the duplicate's evidence must survive the merge, or deduplication "
        "silently weakens grounding")
    assert any(d["type"] == "merged" for d in rt.state["decisions"])


def test_merge_takes_and_releases_the_exclusive_lock(rt: Runtime):
    _seed(rt, "DUP-001", "DUP-002", phase="merge")
    adj = Adjudicator(rt, ScriptedBackend(merges=[
        MergeProposal("DUP-001", "DUP-002", "duplicate")]))
    adj.adjudicate_merges()
    assert rt.state["turn"] is None, "the lock must be released even after work"


def test_merge_naming_a_missing_issue_is_refused(rt: Runtime):
    _seed(rt, "DUP-001", phase="merge")
    adj = Adjudicator(rt, ScriptedBackend(merges=[
        MergeProposal("DUP-001", "NOT-REAL-001", "hallucinated")]))
    results = adj.adjudicate_merges()
    assert results and not results[0].accepted
    assert "does not exist" in results[0].detail


def test_agents_cannot_archive_a_proposed_issue(rt: Runtime):
    """The merge archive edge is control-plane only; agents stay barred."""
    _seed(rt, "PERF-001", phase="merge")
    rt.state["retro"]["phase"] = "analysis"
    r = rt.submit(upd("X1", rt.version,
                      {"issues": [{"id": "PERF-001", "status": "archived"}]}), "QA")
    assert r.cause is Cause.ILLEGAL_TRANSITION


# ======================================================================
# §14 compression, §19.5 degradation
# ======================================================================

def test_compression_archives_under_lock(rt: Runtime):
    _seed(rt, "PERF-001", phase="compression")
    adj = Adjudicator(rt, ScriptedBackend(compression=CompressionProposal(
        summary="Analysis history archived.",
        archive_entries=[{"kind": "analysis_history", "note": "turn detail"}])))
    results = adj.adjudicate_compression()
    assert all(r.accepted for r in results), [r.detail for r in results]
    assert rt.state["archive"][0]["kind"] == "analysis_history"
    assert rt.state["turn"] is None


def test_null_backend_proposes_nothing_and_state_is_untouched(rt: Runtime):
    _seed(rt, "PERF-001")
    before = rt.version
    adj = Adjudicator(rt, NullBackend())
    assert adj.adjudicate_contradictions() == []
    assert rt.version == before


def test_backend_failure_degrades_rather_than_corrupts(rt: Runtime):
    """§19.5 — an unavailable Adjudicator must not take the retrospective with it."""
    _seed(rt, "PERF-001")
    before = rt.version
    adj = Adjudicator(rt, ScriptedBackend(fail_with=RuntimeError("model unreachable")))
    results = adj.adjudicate_contradictions()
    assert results and not results[0].accepted
    assert results[0].cause is Cause.ADJUDICATOR_UNAVAILABLE
    assert results[0].retryable, "the work is worth retrying once the backend is back"
    assert "model unreachable" in results[0].detail
    assert rt.version == before, "a failed backend must leave state untouched"
    # and the Runtime keeps working for everyone else
    assert rt.submit(upd("A1", rt.version, {"issues": [
        {"id": "PERF-001", "confirmed_by": ["QA"]}]}), "QA")


def test_propose_protects_inspection_calls(rt: Runtime):
    """The first live run died because inspecting a proposal bypassed §19.5.

    Reaching for adjudicator.backend directly gets the proposal and loses the
    protection. propose() is the supported way to look before acting.
    """
    _seed(rt, "PERF-001")
    adj = Adjudicator(rt, ScriptedBackend(fail_with=RuntimeError("credit exhausted")))

    with pytest.raises(RuntimeError):
        adj.backend.detect_contradictions({})           # unprotected, as before

    value, err = adj.propose("detect_contradictions", {})   # protected
    assert value is None
    assert err is not None and err.cause is Cause.ADJUDICATOR_UNAVAILABLE
    assert err.retryable
    assert "credit exhausted" in err.detail


def test_long_rationale_is_clipped_not_dropped(rt: Runtime):
    """A live run lost a correct contradiction to a 600-character budget.

    The finding matters more than the tail of its explanation, so an
    over-budget rationale is clipped and says so, rather than taking the whole
    update down with it.
    """
    _seed(rt, "PERF-001")
    adj = Adjudicator(rt, ScriptedBackend(contradictions=[
        ContradictionFinding("PERF-001", [Position("QA", "conflicting account", ["EV-001"])],
                             "x" * 5000)]))
    results = adj.adjudicate_contradictions()
    assert all(r.accepted for r in results), [r.detail for r in results]
    dec = next(d for d in rt.state["decisions"] if d["subject"] == "ISSUE:PERF-001")
    assert dec["rationale"].endswith("[clipped]")
    assert len(dec["rationale"]) <= 2000
    assert rt.state["issues"][0]["status"] == "contested", "the finding survived"


def test_run_for_phase_dispatches_by_phase(rt: Runtime):
    _seed(rt, "DUP-001", "DUP-002", phase="merge")
    backend = ScriptedBackend(merges=[MergeProposal("DUP-001", "DUP-002", "dup")])
    adj = Adjudicator(rt, backend)
    adj.run_for_phase()
    assert backend.calls == ["propose_merges"]
    rt.state["retro"]["phase"] = "actions"
    adj.run_for_phase()
    assert backend.calls == ["propose_merges"], "no adjudication is due in actions"


# ======================================================================
# the Anthropic adapter — shape only, no network
# ======================================================================

def test_anthropic_backend_satisfies_the_protocol_without_a_key():
    from marep.adjudicator import AdjudicatorBackend
    from marep.anthropic_backend import DEFAULT_MODEL, AnthropicBackend

    class FakeClient:
        def __init__(self): self.calls = []
        class _Messages:
            def __init__(self, outer): self.outer = outer
            def create(self, **kw):
                self.outer.calls.append(kw)
                class B: type = "text"; text = '{"merges": []}'
                class R: content = [B()]; stop_reason = "end_turn"
                return R()
        @property
        def messages(self): return self._Messages(self)
        @property
        def beta(self):
            outer = self
            class _Beta:
                messages = outer._Messages(outer)
            return _Beta()

    fake = FakeClient()
    backend = AnthropicBackend(client=fake)
    assert isinstance(backend, AdjudicatorBackend)
    assert backend.propose_merges({"issues": []}) == []
    sent = fake.calls[0]
    assert sent["model"] == DEFAULT_MODEL == "claude-opus-5"
    assert sent["thinking"] == {"type": "adaptive"}
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert "budget_tokens" not in json_dumps(sent), "budget_tokens is rejected on Opus 5"


def json_dumps(obj) -> str:
    import json
    return json.dumps(obj, default=str)


def test_anthropic_backend_raises_on_refusal():
    from marep.anthropic_backend import AnthropicBackend

    class _Refusing:
        def create(self, **kw):
            class D:
                category = "cyber"

            class R:
                content = []
                stop_reason = "refusal"
                stop_details = D()

            return R()

    class _Beta:
        messages = _Refusing()

    class RefusingClient:
        messages = _Refusing()
        beta = _Beta()

    backend = AnthropicBackend(client=RefusingClient())
    with pytest.raises(RuntimeError, match="declined"):
        backend.propose_merges({"issues": []})
