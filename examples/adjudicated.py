"""The full control plane: Runtime plus Adjudicator, with no model involved.

MAREP v2.2 §4.1.2 claims the Adjudicator holds no privileged write path. That
claim is only worth anything if a badly-behaved Adjudicator is demonstrably
refused, so this script scripts one and shows what happens.

Run: python examples/adjudicated.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from marep import (  # noqa: E402
    Adjudicator, CompressionProposal, ContradictionFinding, MergeProposal,
    NullBackend, Position, Runtime, ScriptedBackend, Substrate, TieBreak,
)

ROSTER = ["Developer", "QA", "Architect", "Skeptic"]

SUBSTRATE = {
    "sprint": {"id": "sprint-43", "started": "2026-09-01", "ended": "2026-09-14"},
    "records": [
        {"id": "CI-2001", "type": "ci_run", "ref": "gh/2001",
         "timestamp": "2026-09-03T10:00:00Z", "summary": "API latency regression in nightly"},
        {"id": "TIC-3001", "type": "ticket", "ref": "PROJ-3001",
         "timestamp": "2026-09-04T09:00:00Z", "summary": "Slow endpoint reported by support"},
    ],
    "coverage": [{"type": "metric", "available": False, "reason": "no metrics pipeline"}],
}


def show(label, result):
    print(f"  {'OK  ' if result.accepted else 'XX  '}{label:<42} {result}")


def main() -> int:
    out = Path(__file__).parent / "_run"
    out.mkdir(exist_ok=True)
    p = out / "ADJ_INPUT.yaml"
    p.write_text(yaml.safe_dump(SUBSTRATE, sort_keys=False), encoding="utf-8")
    substrate = Substrate.load(p)
    rt = Runtime.initialize("sprint-43", substrate, roster=ROSTER,
                            state_path=out / "ADJ_STATE.yaml")

    def ev(eid, claim, t, ref, who):
        return {"id": eid, "claim": claim, "source": {"type": t, "ref": ref},
                "submitted_by": who}

    print("\nSETUP  two grounded findings and one that cites nothing real")
    show("Architect: PERF-001", rt.submit({
        "update_id": "U1", "base_version": rt.version,
        "issues": [{"id": "PERF-001", "title": "API latency regressed", "severity": "high",
                    "status": "proposed",
                    "evidence": [ev("EV-001", "Nightly run shows latency regression",
                                    "ci_run", "CI-2001", "Architect")]}]}, "Architect"))
    show("QA: PERF-002 (a duplicate)", rt.submit({
        "update_id": "U2", "base_version": rt.version,
        "issues": [{"id": "PERF-002", "title": "Endpoint is slow", "severity": "high",
                    "status": "proposed",
                    "evidence": [ev("EV-002", "Support ticket reports a slow endpoint",
                                    "ticket", "TIC-3001", "QA")]}]}, "QA"))
    show("Skeptic: MORALE-001 (ungrounded)", rt.submit({
        "update_id": "U3", "base_version": rt.version,
        "issues": [{"id": "MORALE-001", "title": "Pace felt heavy", "severity": "low",
                    "status": "proposed",
                    "evidence": [ev("EV-003", "Team felt stretched",
                                    "metric", "MET-9999", "Skeptic")]}]}, "Skeptic"))
    show("Developer declines", rt.submit({
        "update_id": "U4", "base_version": rt.version,
        "decisions": [{"id": "DEC-001", "type": "declination", "subject": "AGENT:Developer",
                       "outcome": "declined", "basis": "Developer"}]}, "Developer"))
    show("advance to merge", rt.advance_phase())

    print("\nPHASE 2  merge — the Adjudicator folds a duplicate")
    adj = Adjudicator(rt, ScriptedBackend(merges=[
        MergeProposal("PERF-001", "PERF-002", "Same latency regression, reported twice")]))
    for r in adj.run_for_phase():
        show("merge PERF-002 -> PERF-001", r)
    survivor = next(i for i in rt.state["issues"] if i["id"] == "PERF-001")
    print(f"       survivor evidence: {[e['id'] for e in survivor['evidence']]}"
          f"  (the duplicate's grounding was carried, not discarded)")
    show("advance to analysis", rt.advance_phase())

    print("\nPHASE 3  analysis — contradiction, then a hallucinating backend")
    adj = Adjudicator(rt, ScriptedBackend(contradictions=[
        ContradictionFinding("PERF-001", [
            Position("Architect", "Caused by an N+1 query pattern", ["EV-001"]),
            Position("QA", "Caused by network egress saturation", ["EV-002"])],
            "incompatible root causes")]))
    for r in adj.run_for_phase():
        show("mark PERF-001 contested", r)

    bad = Adjudicator(rt, ScriptedBackend())
    show("...tries to advance a phase", bad._submit("x", {"retro": {"phase": "actions"}}))
    show("...tries to set verified", bad._submit("y", {"issues": [{"id": "MORALE-001",
        "evidence": [{"id": "EV-003", "claim": "Team felt stretched", "verified": True,
                      "source": {"type": "metric", "ref": "MET-9999"},
                      "submitted_by": "Skeptic"}]}]}))
    show("...tries to archive a live issue", bad._submit("z", {"issues": [
        {"id": "MORALE-001", "status": "archived"}]}))

    show("Skeptic rejects the ungrounded one", rt.submit({
        "update_id": "U5", "base_version": rt.version,
        "issues": [{"id": "MORALE-001", "status": "rejected"}]}, "Skeptic"))
    show("advance to consensus", rt.advance_phase(archive_unevaluated=True))

    print("\nPHASE 4  consensus — a tie-break, and one the gate refuses")
    show("open a vote", rt.submit({
        "update_id": "U6", "base_version": rt.version,
        "votes": [{"subject": "ISSUE:PERF-001:status:confirmed", "threshold": 0.7,
                   "denominator": "voting_agents", "outcome": "open",
                   "cast": [{"agent": "Architect", "position": "confirm"},
                            {"agent": "QA", "position": "confirm"},
                            {"agent": "Skeptic", "position": "reject"}]}]}, "QA"))
    adj = Adjudicator(rt, ScriptedBackend(tie_breaks={
        "ISSUE:PERF-001:status:confirmed": TieBreak(
            "ISSUE:PERF-001:status:confirmed", "confirmed",
            "Both positions describe the same regression; evidence is verified.")}))
    for r in adj.run_for_phase():
        show("tie-break PERF-001 -> confirmed", r)

    print("\nDEGRADED  §19.5 — the backend dies, the retrospective does not")
    broken = Adjudicator(rt, ScriptedBackend(fail_with=RuntimeError("model unreachable")))
    for r in broken.adjudicate_contradictions():
        show("adjudication attempt", r)
    show("agents keep appending", rt.submit({
        "update_id": "U7", "base_version": rt.version,
        "votes": [{"subject": "ISSUE:PERF-001:note", "threshold": 0.7,
                   "denominator": "voting_agents", "outcome": "unresolved",
                   "cast": [{"agent": "QA", "position": "abstain"}]}]}, "QA"))
    quiet = Adjudicator(rt, NullBackend())
    print(f"       NullBackend proposals: {quiet.adjudicate_contradictions()}")

    rep = rt.report()
    print("\nREPORT")
    print(f"  status counts        {rep['counts']}")
    print(f"  coverage gaps        {rep['unavailable_types']}")
    print(f"  version              {rt.version}")
    print(f"  rejections logged    {len(rt.rejections)}")
    for r in rt.rejections:
        print(f"      - {r.cause.value}")
    adj_writes = [e for e in rt.state["audit"] if e["agent"] == "Adjudicator"]
    print(f"\n  Adjudicator writes in the audit log: {len(adj_writes)}")
    for e in adj_writes:
        print(f"      v{e['version']}  {e['diff_summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
