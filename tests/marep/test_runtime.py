"""Conformance tests for the MAREP Runtime.

Each test names the MAREP v2.2 clause it exercises. These are not smoke tests:
the point is to pin the normative behaviour, especially the parts that were
wrong in v2.1 and the parts a careless implementation would get backwards.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from _support import ROSTER, issue, upd
from marep import Cause, Runtime, Substrate
from marep import transitions
from marep.errors import StateCorruption


# ======================================================================
# §7 substrate
# ======================================================================

def test_substrate_resolves_by_ref_and_type(substrate: Substrate):
    assert substrate.resolve({"type": "ci_run", "ref": "CI-1204"}) is True
    assert substrate.resolve({"type": "ci_run", "ref": "NOPE-1"}) is False


def test_substrate_rejects_type_mismatch(substrate: Substrate):
    """A ref that resolves to a record of another type is not verified.

    Otherwise the type field decays into decoration.
    """
    assert substrate.resolve({"type": "ci_run", "ref": "DEP-0311"}) is False


def test_substrate_coverage_declares_gaps(substrate: Substrate):
    assert set(substrate.unavailable_types()) == {"incident", "metric"}


def test_substrate_checksum_detects_tampering(substrate_path, substrate: Substrate):
    assert substrate.verify_checksum() is True
    substrate_path.write_text(substrate_path.read_text(encoding="utf-8") + "\n# edited\n",
                              encoding="utf-8")
    assert substrate.verify_checksum() is False


def test_substrate_rejects_duplicate_record_ids(tmp_path):
    import yaml
    from _support import SUBSTRATE_DOC
    doc = {**SUBSTRATE_DOC, "records": SUBSTRATE_DOC["records"] + [SUBSTRATE_DOC["records"][0]]}
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    with pytest.raises(StateCorruption):
        Substrate.load(p)


# ======================================================================
# §10 / §11 concurrency
# ======================================================================

def test_save_survives_a_locked_target(tmp_path, monkeypatch):
    """A live run died three phases in when os.replace hit a sharing violation.

    Write-to-temp-then-rename is atomic on POSIX and merely customary on
    Windows, where a sync client holding the target makes the rename fail.
    Losing an hour of model calls to that is the worse outcome.
    """
    from marep import state as st

    target = tmp_path / "STATE.yaml"
    calls = {"n": 0}
    real_replace = Path.replace

    def flaky(self, other):
        calls["n"] += 1
        raise PermissionError(5, "Access is denied")

    monkeypatch.setattr(Path, "replace", flaky)
    st.save({"retro": {"version": 1}}, target, retries=3)

    assert calls["n"] == 3, "it should retry before giving up on atomicity"
    assert target.exists(), "and still write the state rather than lose it"
    assert not target.with_suffix(".yaml.tmp").exists(), "temp file cleaned up"
    monkeypatch.setattr(Path, "replace", real_replace)


def test_a_rejection_is_falsy_which_makes_presence_checks_a_trap(rt: Runtime):
    """Pins the ergonomics that broke the Adjudicator's error path.

    `if result:` asking "did it work" is the intended reading. `if err:` asking
    "is there an error" is the trap: a rejection is falsy, so it never fires.
    """
    r = rt.submit(upd("U1", 999, {"issues": [issue()]}), "Developer")
    assert not r
    assert bool(r) is False, "a rejection is falsy"
    assert r is not None, "...so presence must be tested with `is not None`"


def test_cas_rejects_stale_base_version(rt: Runtime):
    assert rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    stale = rt.submit(upd("U2", 0, {"issues": [issue("PERF-001")]}), "QA")
    assert not stale
    assert stale.cause is Cause.VERSION_CONFLICT
    assert stale.version == rt.version, "conflict must return current version for rebase (§11.5)"
    assert stale.retryable


def test_parallel_appends_succeed_after_rebase(rt: Runtime):
    """§11.1 — appends are permitted concurrently; CAS serializes them."""
    assert rt.submit(upd("U1", rt.version, {"issues": [issue("DEPLOY-002")]}), "Developer")
    assert rt.submit(upd("U2", rt.version, {"issues": [issue("PERF-001")]}), "QA")
    assert {i["id"] for i in rt.state["issues"]} == {"DEPLOY-002", "PERF-001"}


def test_appends_need_no_lock(rt: Runtime):
    assert rt.state["turn"] is None
    assert rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    assert rt.state["turn"] is None, "an append must not acquire a lock (§11.1)"


def test_exclusive_lock_blocks_appends(rt: Runtime):
    assert rt.acquire_lock("compression", "Adjudicator")
    r = rt.submit(upd("U1", rt.version, {"issues": [issue()]}), "Developer")
    assert r.cause is Cause.EXCLUSIVE_OPERATION_IN_PROGRESS
    assert r.retryable
    assert rt.release_lock("Adjudicator")
    assert rt.submit(upd("U1", rt.version, {"issues": [issue()]}), "Developer")


def test_expired_lock_is_reclaimed(rt: Runtime):
    rt.acquire_lock("merge", "Adjudicator", ttl_seconds=-1)
    r = rt.submit(upd("U1", rt.version + 1, {"issues": [issue()]}), "Developer")
    assert rt.state["turn"] is None, "expired lock must be reclaimed (§19.2)"
    assert r.accepted or r.cause is Cause.VERSION_CONFLICT


def test_second_lock_refused(rt: Runtime):
    assert rt.acquire_lock("compression", "Adjudicator")
    assert not rt.acquire_lock("merge", "Runtime")


# ======================================================================
# §12 update semantics
# ======================================================================

def test_update_id_is_mandatory(rt: Runtime):
    r = rt.submit({"base_version": 0, "issues": [issue()]}, "Developer")
    assert r.cause is Cause.SCHEMA_VIOLATION


def test_replayed_update_id_is_a_noop(rt: Runtime):
    assert rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    v = rt.version
    replay = rt.submit(upd("U1", v, {"issues": [issue("OTHER-001")]}), "Developer")
    assert replay.cause is Cause.DUPLICATE_UPDATE
    assert rt.version == v, "replay must not advance state (§12)"


def test_rejected_update_leaves_no_trace(rt: Runtime):
    before = rt.version
    bad = issue(status="confirmed")  # ungrounded confirmation on entry
    r = rt.submit(upd("U1", before, {"issues": [bad]}), "Developer")
    assert not r
    assert rt.version == before
    assert rt.state["issues"] == [], "no partial application (§12)"


def test_schema_violation_rejected(rt: Runtime):
    bad = issue()
    bad["severity"] = "catastrophic"
    r = rt.submit(upd("U1", 0, {"issues": [bad]}), "Developer")
    assert r.cause is Cause.SCHEMA_VIOLATION


# ======================================================================
# §8.3 evidence and the grounding gate
# ======================================================================

def test_runtime_sets_verified_flag(rt: Runtime):
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    ev = rt.state["issues"][0]["evidence"][0]
    assert ev["verified"] is True, "Runtime resolves refs (§8.3)"


def test_unresolvable_ref_is_recorded_unverified_not_rejected(rt: Runtime):
    ev = [{"id": "EV-009", "claim": "Something nobody logged",
           "source": {"type": "ticket", "ref": "GHOST-1"}, "submitted_by": "QA"}]
    assert rt.submit(upd("U1", 0, {"issues": [issue(evidence=ev)]}), "QA")
    assert rt.state["issues"][0]["evidence"][0]["verified"] is False


def test_agent_cannot_set_verified(rt: Runtime):
    ev = [{"id": "EV-001", "claim": "Self-certified", "verified": True,
           "source": {"type": "ticket", "ref": "GHOST-1"}, "submitted_by": "QA"}]
    r = rt.submit(upd("U1", 0, {"issues": [issue(evidence=ev)]}), "QA")
    assert r.cause is Cause.OUT_OF_SCOPE


def test_cannot_confirm_without_verified_evidence(rt: Runtime):
    """§8.3.1 — the grounding gate. Agreement is not evidence."""
    ev = [{"id": "EV-009", "claim": "Unverifiable", "submitted_by": "QA",
           "source": {"type": "ticket", "ref": "GHOST-1"}}]
    rt.submit(upd("U1", 0, {"issues": [issue(evidence=ev)]}), "QA")
    rt.state["retro"]["phase"] = "analysis"
    r = rt.submit(upd("U2", rt.version,
                      {"issues": [{"id": "DEPLOY-002", "status": "confirmed"}]}), "QA")
    assert r.cause is Cause.UNGROUNDED_CONFIRMATION


def test_can_confirm_with_verified_evidence(rt: Runtime):
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    rt.state["retro"]["phase"] = "analysis"
    assert rt.submit(upd("U2", rt.version,
                         {"issues": [{"id": "DEPLOY-002", "status": "confirmed"}]}), "QA")


# ======================================================================
# §16.3 / §16.4 transitions and reopening
# ======================================================================

def test_true_but_unconfirmable_finding_has_an_honest_terminal_state(rt: Runtime):
    """§16.3 — the gap a live run found.

    An issue can be evaluated, uncontested, true, and unconfirmable for want of
    verified evidence. Every other edge from `proposed` says something false
    about it: `rejected` calls it untrue, `archived` calls it unevaluated,
    `contested` invents a disagreement.
    """
    ev = [{"id": "EV-900", "claim": "true but unverifiable", "submitted_by": "Skeptic",
           "source": {"type": "ticket", "ref": "NO-SUCH-RECORD"}}]
    rt.submit(upd("U1", rt.version, {"issues": [issue("DUP-001", evidence=ev)]}), "Skeptic")
    rt.state["retro"]["phase"] = "analysis"
    r = rt.submit(upd("U2", rt.version,
                      {"issues": [{"id": "DUP-001", "status": "unresolved"}]}), "Skeptic")
    assert r, r.detail
    ok_, unmet = rt.exit_ready()
    assert ok_, f"unresolved must settle analysis: {unmet}"


def test_transition_graph_matches_spec():
    assert transitions.outgoing("archived") == set()
    assert ("confirmed", "contested") in transitions.EDGES
    assert ("rejected", "contested") in transitions.EDGES
    assert ("unresolved", "contested") in transitions.EDGES
    assert ("proposed", "archived") in transitions.EDGES
    assert ("confirmed", "rejected") not in transitions.EDGES


def test_illegal_transition_rejected(rt: Runtime):
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    rt.state["retro"]["phase"] = "analysis"
    rt.submit(upd("U2", rt.version, {"issues": [{"id": "DEPLOY-002", "status": "confirmed"}]}), "QA")
    r = rt.submit(upd("U3", rt.version,
                      {"issues": [{"id": "DEPLOY-002", "status": "rejected"}]}), "QA")
    assert r.cause is Cause.ILLEGAL_TRANSITION


def test_new_issue_must_enter_as_proposed(rt: Runtime):
    r = rt.submit(upd("U1", 0, {"issues": [issue(status="contested")]}), "Developer")
    assert r.cause is Cause.ILLEGAL_TRANSITION


def _confirm(rt: Runtime, iid="DEPLOY-002"):
    rt.submit(upd("A", 0, {"issues": [issue(iid)]}), "Developer")
    rt.state["retro"]["phase"] = "analysis"
    rt.submit(upd("B", rt.version, {"issues": [{"id": iid, "status": "confirmed"}]}), "QA")


def test_reopening_requires_new_verified_evidence(rt: Runtime):
    _confirm(rt)
    r = rt.submit(upd("C", rt.version,
                      {"issues": [{"id": "DEPLOY-002", "status": "contested"}]}), "Skeptic")
    assert r.cause is Cause.REOPEN_BLOCKED


def test_reopening_succeeds_with_new_verified_evidence(rt: Runtime):
    _confirm(rt)
    fresh = {"id": "EV-050", "claim": "Divergence predates the release",
             "source": {"type": "ticket", "ref": "TIC-7781"}, "submitted_by": "Skeptic"}
    r = rt.submit(upd("C", rt.version, {"issues": [
        {"id": "DEPLOY-002", "status": "contested", "evidence": [fresh]}]}), "Skeptic")
    assert r, r.detail
    assert rt.state["issues"][0]["reopen_count"] == 1


def test_unverified_new_evidence_does_not_unlock_reopening(rt: Runtime):
    _confirm(rt)
    ghost = {"id": "EV-051", "claim": "Hearsay",
             "source": {"type": "ticket", "ref": "GHOST-9"}, "submitted_by": "Skeptic"}
    r = rt.submit(upd("C", rt.version, {"issues": [
        {"id": "DEPLOY-002", "status": "contested", "evidence": [ghost]}]}), "Skeptic")
    assert r.cause is Cause.REOPEN_BLOCKED


def test_reopen_ceiling_enforced(rt: Runtime):
    _confirm(rt)
    refs = ["TIC-7781", "CI-1300"]
    for n, ref in enumerate(refs, start=1):
        rt.submit(upd(f"R{n}", rt.version, {"issues": [{
            "id": "DEPLOY-002", "status": "contested",
            "evidence": [{"id": f"EV-{60+n:03d}",
                          "claim": ("PROJ-7781 records staging/prod runtime divergence"
                                    if ref.startswith("TIC")
                                    else "gh-actions/13000 shows a flaky integration suite"),
                          "source": {"type": "ticket" if ref.startswith("TIC") else "ci_run",
                                     "ref": ref},
                          "submitted_by": "Skeptic"}]}]}), "Skeptic")
        rt.submit(upd(f"K{n}", rt.version,
                      {"issues": [{"id": "DEPLOY-002", "status": "confirmed"}]}), "QA")
    assert rt.state["issues"][0]["reopen_count"] == 2
    r = rt.submit(upd("R3", rt.version, {"issues": [{
        "id": "DEPLOY-002", "status": "contested",
        "evidence": [{"id": "EV-099", "claim": "deploy/42.3 went to production",
                      "source": {"type": "deploy", "ref": "DEP-0311"},
                      "submitted_by": "Skeptic"}]}]}), "Skeptic")
    assert r.cause is Cause.REOPEN_BLOCKED
    assert "ceiling" in r.detail


# ======================================================================
# §18 anti-patterns
# ======================================================================

def test_persona_theater_rejected(rt: Runtime):
    bad = issue()
    bad["title"] = "Deployment instability, great catch @QA"
    r = rt.submit(upd("U1", 0, {"issues": [bad]}), "Developer")
    assert r.cause is Cause.PERSONA_THEATER


def test_conversational_opener_rejected(rt: Runtime):
    bad = issue()
    bad["evidence"][0]["claim"] = "Well, the rollback did not go smoothly"
    r = rt.submit(upd("U1", 0, {"issues": [bad]}), "Developer")
    assert r.cause is Cause.CONVERSATIONAL_ARTIFACT


def test_a_negation_is_not_a_conversational_opener(rt: Runtime):
    """A live run rejected six sound findings for opening with "No".

    "No upper ontology is imported" is a finding. "No, that's wrong" is a
    reply. The comma is what separates them, and the first version of the rule
    could not tell.
    """
    ok = issue()
    ok["title"] = "No upper ontology is imported by any class-bearing file"
    ok["evidence"][0]["claim"] = "No import graph connects the modules"
    assert rt.submit(upd("U1", 0, {"issues": [ok]}), "Developer"), "a negation is prose"

    bad = issue("OTHER-001")
    bad["evidence"][0]["claim"] = "No, that is not what the metric shows"
    r = rt.submit(upd("U2", rt.version, {"issues": [bad]}), "Developer")
    assert r.cause is Cause.CONVERSATIONAL_ARTIFACT, "a reply is still a reply"


def test_text_budget_enforced(rt: Runtime):
    bad = issue()
    bad["title"] = "Deployment " + "x" * 200
    r = rt.submit(upd("U1", 0, {"issues": [bad]}), "Developer")
    assert r.cause is Cause.TEXT_BUDGET_EXCEEDED


def test_non_substantive_update_rejected(rt: Runtime):
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    r = rt.submit(upd("U2", rt.version, {"issues": [issue()]}), "Developer")
    assert r.cause is Cause.NON_SUBSTANTIVE


def test_independent_convergence_is_recorded_not_suppressed(rt: Runtime):
    """§18.2 — the inversion v2.1 got wrong.

    A second agent reaching the same finding must be able to record it. This is
    the strongest signal a retrospective produces; similarity must never reject.
    """
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    rt.state["retro"]["phase"] = "analysis"
    r = rt.submit(upd("U2", rt.version, {"issues": [
        {"id": "DEPLOY-002", "confirmed_by": ["QA"]}]}), "QA")
    assert r, r.detail
    assert "QA" in rt.state["issues"][0]["confirmed_by"]


# ======================================================================
# §11.4 authorization
# ======================================================================

def test_agent_cannot_write_outside_phase_authority(rt: Runtime):
    r = rt.submit(upd("U1", 0, {"actions": [{
        "id": "ACT-001", "description": "Fix the pipeline", "owner": "Developer",
        "status": "proposed", "outcome_criteria": "Rollback succeeds"}]}), "Developer")
    assert r.cause is Cause.OUT_OF_SCOPE, "actions are not writable in gathering (§13.1)"


def test_agent_cannot_advance_phase(rt: Runtime):
    r = rt.submit({"update_id": "U1", "base_version": 0,
                   "retro": {"phase": "merge"}}, "Developer")
    assert r.cause is Cause.OUT_OF_SCOPE


def test_adjudicator_has_no_privileged_write_path(rt: Runtime):
    """§4.1.2 — the Adjudicator is validated exactly like any agent."""
    r = rt.submit(upd("U1", 0, {"issues": [issue()]}), "Adjudicator")
    assert r.cause is Cause.OUT_OF_SCOPE, "Adjudicator may not write issues in gathering"


# ======================================================================
# §13 phases
# ======================================================================

def test_phase_exit_blocked_until_roster_submits(rt: Runtime):
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    r = rt.advance_phase()
    assert r.cause is Cause.PHASE_EXIT_UNSATISFIED
    assert "QA" in r.detail


def test_silent_agent_can_decline_and_unblock_phase_1(rt: Runtime):
    """§13.1 — without a declination path one quiet agent deadlocks gathering."""
    for n, agent in enumerate(["Developer", "QA", "Architect"], start=1):
        rt.submit(upd(f"S{n}", rt.version, {"issues": [issue(
            f"AAA-{n:03d}",
            evidence=[{"id": f"EV-{n:03d}", "claim": "Rollback needed manual work",
                       "source": {"type": "ci_run", "ref": "CI-1204"},
                       "submitted_by": agent}])]}), agent)
    blocked = rt.advance_phase()
    assert blocked.cause is Cause.PHASE_EXIT_UNSATISFIED and "Skeptic" in blocked.detail

    assert rt.submit(upd("S9", rt.version, {"decisions": [{
        "id": "DEC-001", "type": "declination", "subject": "AGENT:Skeptic",
        "outcome": "declined", "basis": "Skeptic"}]}), "Skeptic"), "declination must be writable"
    assert rt.advance_phase(), "declination should satisfy the exit criterion"
    assert rt.phase == "merge"


def test_unevaluated_issue_would_deadlock_analysis_but_is_archived(rt: Runtime):
    """§13.3 — the v2.1 deadlock: `proposed` had no exit edge."""
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    rt.state["retro"]["phase"] = "analysis"
    ok_, unmet = rt.exit_ready()
    assert not ok_ and "DEPLOY-002" in unmet[0]
    r = rt.advance_phase(archive_unevaluated=True)
    assert r, r.detail
    assert rt.state["issues"][0]["status"] == "archived"
    assert any(d["type"] == "unevaluated_archive" for d in rt.state["decisions"])


def test_consensus_exit_accepts_unresolved(rt: Runtime):
    """§13.4 — `unresolved` is terminal and must not be forced."""
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    rt.state["retro"]["phase"] = "analysis"
    rt.submit(upd("U2", rt.version,
                  {"issues": [{"id": "DEPLOY-002", "status": "contested"}]}), "Skeptic")
    rt.state["retro"]["phase"] = "consensus"
    ok_, unmet = rt.exit_ready()
    assert not ok_
    rt.submit(upd("U3", rt.version,
                  {"issues": [{"id": "DEPLOY-002", "status": "unresolved"}]}), "Adjudicator")
    ok_, unmet = rt.exit_ready()
    assert ok_, unmet


# ======================================================================
# §10 audit, §20 reporting
# ======================================================================

def test_audit_is_append_only_and_complete(rt: Runtime):
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    rt.submit(upd("U2", rt.version, {"issues": [issue("PERF-001")]}), "QA")
    versions = [e["version"] for e in rt.state["audit"]]
    assert versions == [1, 2]
    assert all(e["update_id"] for e in rt.state["audit"])


def test_report_surfaces_coverage_and_unresolved(rt: Runtime):
    rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer")
    rep = rt.report()
    assert set(rep["unavailable_types"]) == {"incident", "metric"}
    assert rep["counts"]["proposed"] == 1


def test_report_flags_note_only_confirmations(rt: Runtime):
    ev = [{"id": "EV-100", "claim": "Review load felt heavy",
           "source": {"type": "note", "ref": "NOTE-001"}, "submitted_by": "QA"}]
    rt.submit(upd("U1", 0, {"issues": [issue("PROC-001", evidence=ev)]}), "QA")
    rt.state["retro"]["phase"] = "analysis"
    rt.submit(upd("U2", rt.version,
                  {"issues": [{"id": "PROC-001", "status": "confirmed"}]}), "QA")
    assert rt.report()["confirmed_note_only"] == ["PROC-001"]


# ======================================================================
# §14.1 tokens
# ======================================================================

def test_per_turn_context_ceiling(rt: Runtime):
    r = rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer", tokens=99_999)
    assert r.cause is Cause.BUDGET_EXHAUSTED


def test_reserve_is_withheld_from_ordinary_turns(rt: Runtime):
    led = rt.ledger
    assert led.budget.spendable() == 80_000
    rt.state["token_ledger"]["consumed_total"] = 80_000
    r = rt.submit(upd("U1", 0, {"issues": [issue()]}), "Developer", tokens=100)
    assert r.cause is Cause.BUDGET_EXHAUSTED


def test_scoped_read_excludes_unauthorized_sections(rt: Runtime):
    view = rt.read("Developer")
    assert set(view) == {"retro", "issues", "decisions"}, (
        "gathering authorizes issues plus decisions, the latter so an agent can "
        "record a declination (§13.1)")
    assert "votes" not in view and "archive" not in view
