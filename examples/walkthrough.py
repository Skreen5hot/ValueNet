"""A complete retrospective, driven end to end through the Runtime.

No model is involved. Every agent here is a hard-coded dict, which is the
point: it isolates what the Runtime does from what the agents would do, and
shows that phase control, grounding, and the transition graph hold up without
anything intelligent behind them.

Run: python examples/walkthrough.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Repository root and run-artifact directory come from the layout
# contract, not from counting parents. parents[1] silently becomes
# examples/ once this file moves a level deeper -- a wrong root that
# raises nothing and reads the wrong tree.
_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

from marep import layout  # noqa: E402
from marep import Runtime, Substrate, TokenBudget  # noqa: E402

ROSTER = ["Developer", "QA", "Architect", "Skeptic"]

SUBSTRATE = {
    "sprint": {"id": "sprint-42", "started": "2026-08-01", "ended": "2026-08-14"},
    "records": [
        {"id": "CI-1204", "type": "ci_run", "ref": "gh-actions/12841",
         "timestamp": "2026-08-09T11:04:00Z", "summary": "Release 42.3 rollback failed"},
        {"id": "DEP-0311", "type": "deploy", "ref": "deploy/42.3",
         "timestamp": "2026-08-09T10:55:00Z", "summary": "Release 42.3 to production"},
        {"id": "TIC-7781", "type": "ticket", "ref": "PROJ-7781",
         "timestamp": "2026-08-10T09:00:00Z", "summary": "Staging/prod runtime divergence"},
        {"id": "CI-1300", "type": "ci_run", "ref": "gh-actions/13000",
         "timestamp": "2026-08-12T08:00:00Z", "summary": "Integration suite flaked 6 of 20 runs"},
        {"id": "NOTE-001", "type": "note", "ref": "retro-note-1",
         "timestamp": "2026-08-14T16:00:00Z", "summary": "Review load felt heavy"},
    ],
    "coverage": [
        {"type": "ci_run", "available": True},
        {"type": "deploy", "available": True},
        {"type": "incident", "available": False, "reason": "no incident tracker integration"},
        {"type": "metric", "available": False, "reason": "metrics pipeline not wired to retro"},
    ],
}

STEP = 0


def show(label: str, result) -> None:
    global STEP
    STEP += 1
    mark = "OK  " if result.accepted else "XX  "
    print(f"  {mark}{label:<46} {result}")


def ev(eid, claim, rtype, ref, agent):
    return {"id": eid, "claim": claim, "source": {"type": rtype, "ref": ref},
            "submitted_by": agent}


def main() -> int:
    out = layout.run_artifacts_dir()
    out.mkdir(exist_ok=True)
    sub_path = out / "SPRINT_INPUT.yaml"
    sub_path.write_text(yaml.safe_dump(SUBSTRATE, sort_keys=False), encoding="utf-8")

    substrate = Substrate.load(sub_path)
    rt = Runtime.initialize(
        "sprint-42", substrate, roster=ROSTER,
        state_path=out / "RETRO_STATE.yaml",
        budget=TokenBudget(per_turn_context=16_000, per_retrospective_total=400_000,
                           compression_reserve=80_000),
    )
    print(f"\nSubstrate frozen: {len(substrate)} records, checksum {substrate.checksum[:19]}...")
    print(f"Coverage gaps declared: {substrate.unavailable_types()}\n")

    # ---------------- Phase 1: independent gathering (parallel) ----------
    print("PHASE 1  gathering — agents append in parallel under CAS")
    show("Developer proposes DEPLOY-002", rt.submit({
        "update_id": "U-001", "base_version": rt.version,
        "issues": [{"id": "DEPLOY-002", "title": "Rollback path is not exercised",
                    "severity": "high", "status": "proposed",
                    "evidence": [ev("EV-001", "Rollback of 42.3 required manual intervention",
                                    "ci_run", "CI-1204", "Developer")]}]}, "Developer", tokens=4200))

    stale = rt.submit({
        "update_id": "U-002", "base_version": 0,
        "issues": [{"id": "QUAL-001", "title": "Integration suite is flaky",
                    "severity": "medium", "status": "proposed",
                    "evidence": [ev("EV-002", "Suite flaked on 6 of 20 runs",
                                    "ci_run", "CI-1300", "QA")]}]}, "QA")
    show("QA submits against a stale version", stale)

    show("QA rebases and resubmits", rt.submit({
        "update_id": "U-002", "base_version": rt.version,
        "issues": [{"id": "QUAL-001", "title": "Integration suite is flaky",
                    "severity": "medium", "status": "proposed",
                    "evidence": [ev("EV-002", "Suite flaked on 6 of 20 runs",
                                    "ci_run", "CI-1300", "QA")]}]}, "QA", tokens=3800))

    show("Architect proposes ARCH-001", rt.submit({
        "update_id": "U-003", "base_version": rt.version,
        "issues": [{"id": "ARCH-001", "title": "Staging and production diverge",
                    "severity": "high", "status": "proposed",
                    "evidence": [ev("EV-003", "Runtime version differs between environments",
                                    "ticket", "TIC-7781", "Architect")]}]}, "Architect", tokens=5100))

    show("Skeptic cites an unlogged claim", rt.submit({
        "update_id": "U-004", "base_version": rt.version,
        "issues": [{"id": "PROC-001", "title": "Review load is uneven",
                    "severity": "low", "status": "proposed",
                    "evidence": [ev("EV-004", "Reviews concentrated on two people",
                                    "metric", "MET-999", "Skeptic")]}]}, "Skeptic", tokens=2600))
    unver = rt.state["issues"][-1]["evidence"][0]["verified"]
    print(f"       -> accepted, but recorded verified={unver} (ref does not resolve)")

    show("Developer repeats himself", rt.submit({
        "update_id": "U-005", "base_version": rt.version,
        "issues": [{"id": "DEPLOY-002", "title": "Rollback path is not exercised",
                    "severity": "high", "status": "proposed"}]}, "Developer"))

    show("advance to merge", rt.advance_phase())

    # ---------------- Phase 2: canonical merge ---------------------------
    print("\nPHASE 2  merge — Adjudicator works under an exclusive lock")
    show("Adjudicator acquires lock", rt.acquire_lock("merge", "Adjudicator", ttl_seconds=120))
    show("Developer append during lock", rt.submit({
        "update_id": "U-006", "base_version": rt.version,
        "issues": [{"id": "X-001", "title": "late", "severity": "low", "status": "proposed",
                    "evidence": []}]}, "Developer"))
    show("Adjudicator releases", rt.release_lock("Adjudicator"))
    show("advance to analysis", rt.advance_phase())

    # ---------------- Phase 3: structured analysis -----------------------
    print("\nPHASE 3  analysis — grounding gate and independent convergence")
    show("QA tries to confirm the ungrounded issue", rt.submit({
        "update_id": "U-007", "base_version": rt.version,
        "issues": [{"id": "PROC-001", "status": "confirmed"}]}, "QA"))

    show("Developer confirms DEPLOY-002", rt.submit({
        "update_id": "U-008", "base_version": rt.version,
        "issues": [{"id": "DEPLOY-002", "status": "confirmed", "confirmed_by": ["Developer"]}]},
        "Developer", tokens=3100))

    show("Architect converges on the same finding", rt.submit({
        "update_id": "U-009", "base_version": rt.version,
        "issues": [{"id": "DEPLOY-002", "confirmed_by": ["Architect"]}]}, "Architect", tokens=900))

    show("Architect confirms ARCH-001", rt.submit({
        "update_id": "U-010", "base_version": rt.version,
        "issues": [{"id": "ARCH-001", "status": "confirmed", "confirmed_by": ["Architect"]}]},
        "Architect", tokens=2400))

    show("Skeptic contests QUAL-001", rt.submit({
        "update_id": "U-011", "base_version": rt.version,
        "issues": [{"id": "QUAL-001", "status": "contested", "contested_by": ["Skeptic"]}],
        "conflict_record": [{"issue_id": "QUAL-001", "positions": [
            {"agent": "QA", "claim": "Suite is flaky", "evidence": ["EV-002"]},
            {"agent": "Skeptic", "claim": "Six failures were one bad fixture", "evidence": []}]}]},
        "Skeptic", tokens=2900))

    ready, unmet = rt.exit_ready()
    print(f"       exit blocked by: {unmet}")
    show("advance, archiving unevaluated", rt.advance_phase(archive_unevaluated=True))

    # ---------------- Phase 4: consensus ---------------------------------
    print("\nPHASE 4  consensus — a sub-threshold vote lands on unresolved")
    show("Adjudicator records the vote", rt.submit({
        "update_id": "U-012", "base_version": rt.version,
        "votes": [{"subject": "ISSUE:QUAL-001:status:confirmed", "threshold": 0.7,
                   "denominator": "voting_agents", "outcome": "unresolved",
                   "cast": [{"agent": "QA", "position": "confirm"},
                            {"agent": "Developer", "position": "confirm"},
                            {"agent": "Skeptic", "position": "reject"},
                            {"agent": "Architect", "position": "abstain"}]}],
        "issues": [{"id": "QUAL-001", "status": "unresolved"}]}, "Adjudicator", tokens=1800))
    show("advance to actions", rt.advance_phase())

    # ---------------- Phase 5: actions -----------------------------------
    print("\nPHASE 5  actions — every confirmed issue needs one or a waiver")
    show("Developer proposes ACT-001", rt.submit({
        "update_id": "U-013", "base_version": rt.version,
        "actions": [{"id": "ACT-001", "description": "Add a rollback rehearsal to the release job",
                     "owner": "Developer", "status": "accepted",
                     "outcome_criteria": "A failed release rolls back with no manual step",
                     "addresses": ["DEPLOY-002"]}]}, "Developer", tokens=2200))
    ready, unmet = rt.exit_ready()
    print(f"       exit blocked by: {unmet}")
    show("Architect waives ARCH-001", rt.submit({
        "update_id": "U-014", "base_version": rt.version,
        "decisions": [{"id": "DEC-010", "type": "no_action_required",
                       "subject": "ISSUE:ARCH-001", "outcome": "no action this sprint",
                       "rationale": "Environment parity work is already scheduled.",
                       "basis": "adjudicator", "decided_at": "2026-08-15T10:00:00+00:00"}]},
        "Architect", tokens=1100))
    show("advance to compression", rt.advance_phase())

    # ---------------- Phase 6: compression -------------------------------
    print("\nPHASE 6  compression")
    show("Adjudicator archives", rt.submit({
        "update_id": "U-015", "base_version": rt.version,
        "archive": [{"kind": "analysis_history", "note": "Phase 3 turn-by-turn detail"}]},
        "Adjudicator", tokens=6400))
    show("advance to complete", rt.advance_phase())

    # ---------------- Report ---------------------------------------------
    print("\nREPORT (§20)")
    rep = rt.report()
    print(f"  status counts        {rep['counts']}")
    print(f"  unresolved           {rep['unresolved']}")
    print(f"  coverage gaps        {rep['unavailable_types']}")
    print(f"  note-only confirmed  {rep['confirmed_note_only']}")
    print(f"  reopened             {rep['reopened']}")
    print(f"  tokens consumed      {rep['tokens_consumed']:,}")
    print(f"\n  final version        {rt.version}")
    print(f"  audit entries        {len(rt.state['audit'])}")
    print(f"  rejections logged    {len(rt.rejections)}")
    for r in rt.rejections:
        print(f"      - {r.cause.value}")
    print(f"\n  state written to     {out / 'RETRO_STATE.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
