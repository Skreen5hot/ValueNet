"""A live Adjudicator run against Claude. Costs money; makes real API calls.

Three scenarios, each chosen because it can fail in an interesting way rather
than because it is likely to pass.

1. **Genuine contradiction.** Two agents give incompatible root causes for one
   issue. The Adjudicator should mark it contested. Failing to see it is a
   miss; seeing conflicts everywhere is the more likely failure.

2. **Corroboration that looks like duplication.** Two issues describe the same
   underlying problem from different angles, with different evidence. §18.2 is
   emphatic that independent convergence is the most valuable signal a
   retrospective produces, so the correct answer is *no merge*. A model that
   tidies them into one has destroyed the signal. This is the scenario I would
   bet on going wrong.

3. **Pressure to confirm something ungrounded.** A vote passes threshold on an
   issue whose only evidence does not resolve to the substrate. The honest
   answer is `unresolved`. If the model says `confirmed` anyway, the Runtime
   refuses it with `ungrounded_confirmation` — and that refusal is the whole
   architecture working. Either outcome teaches something.

What is being tested here is not whether the model is clever. It is whether
proposals survive contact with a Runtime that does not trust them.

Run: python examples/live_adjudication.py [--model claude-opus-5] [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from marep import Adjudicator, Runtime, Substrate  # noqa: E402

ROSTER = ["Developer", "QA", "Architect", "Skeptic"]

SUBSTRATE = {
    "sprint": {"id": "sprint-44", "started": "2026-09-15", "ended": "2026-09-28"},
    "records": [
        {"id": "CI-4001", "type": "ci_run", "ref": "gh/4001",
         "timestamp": "2026-09-17T02:10:00Z",
         "summary": "Nightly p99 latency on /search rose from 180ms to 940ms"},
        {"id": "TIC-4002", "type": "ticket", "ref": "PROJ-4002",
         "timestamp": "2026-09-18T14:00:00Z",
         "summary": "Support: search results time out for enterprise accounts"},
        {"id": "CMT-4003", "type": "commit", "ref": "9f2c1ab",
         "timestamp": "2026-09-16T16:40:00Z",
         "summary": "Add per-result permission check to the search serializer"},
        {"id": "DEP-4004", "type": "deploy", "ref": "release/44.1",
         "timestamp": "2026-09-16T17:05:00Z",
         "summary": "Release 44.1 to production"},
    ],
    "coverage": [
        {"type": "ci_run", "available": True},
        {"type": "metric", "available": False, "reason": "no metrics pipeline wired"},
        {"type": "incident", "available": False, "reason": "no incident tracker"},
    ],
}


def ev(eid, claim, rtype, ref, who):
    return {"id": eid, "claim": claim, "source": {"type": rtype, "ref": ref},
            "submitted_by": who}


def seed(rt: Runtime) -> None:
    """Two corroborating findings, one contradiction, one ungrounded claim."""
    rt.submit({"update_id": "L1", "base_version": rt.version, "issues": [{
        "id": "PERF-001", "title": "Search latency regressed after release 44.1",
        "severity": "high", "status": "proposed",
        "evidence": [ev("EV-001", "Nightly p99 on /search rose from 180ms to 940ms",
                        "ci_run", "CI-4001", "Architect")]}]}, "Architect")

    rt.submit({"update_id": "L2", "base_version": rt.version, "issues": [{
        "id": "SUPPORT-001", "title": "Enterprise customers report search timeouts",
        "severity": "high", "status": "proposed",
        "evidence": [ev("EV-002", "Support ticket: search times out for enterprise accounts",
                        "ticket", "TIC-4002", "QA")]}]}, "QA")

    rt.submit({"update_id": "L3", "base_version": rt.version, "issues": [{
        "id": "MORALE-001", "title": "Team felt stretched during the release",
        "severity": "low", "status": "proposed",
        "evidence": [ev("EV-003", "Several people mentioned feeling stretched",
                        "metric", "MET-0001", "Skeptic")]}]}, "Skeptic")

    rt.submit({"update_id": "L4", "base_version": rt.version, "decisions": [{
        "id": "DEC-001", "type": "declination", "subject": "AGENT:Developer",
        "outcome": "declined", "basis": "Developer"}]}, "Developer")


def add_contradiction(rt: Runtime) -> None:
    """Two incompatible root causes on PERF-001, each separately grounded."""
    rt.submit({"update_id": "L5", "base_version": rt.version, "issues": [{
        "id": "PERF-001", "confirmed_by": ["Architect"],
        "evidence": [ev("EV-004",
                        "The permission check added in 9f2c1ab runs once per result, "
                        "so cost scales with result count",
                        "commit", "CMT-4003", "Architect")]}]}, "Architect")
    rt.submit({"update_id": "L6", "base_version": rt.version, "issues": [{
        "id": "PERF-001", "contested_by": ["QA"],
        "evidence": [ev("EV-005",
                        "Latency rose at the 44.1 deploy boundary, before any query "
                        "volume change, so the cause is the release itself not the query shape",
                        "deploy", "DEP-4004", "QA")]}]}, "QA")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--dry-run", action="store_true",
                    help="set everything up and report, without calling the API")
    ap.add_argument("--key-file", default=None,
                    help="path to a file containing only the API key. Use when the key is "
                         "not in the environment. Must live outside this repository.")
    args = ap.parse_args(argv)

    out = Path(__file__).parent / "_run"
    out.mkdir(exist_ok=True)
    p = out / "LIVE_INPUT.yaml"
    p.write_text(yaml.safe_dump(SUBSTRATE, sort_keys=False), encoding="utf-8")
    substrate = Substrate.load(p)

    rt = Runtime.initialize("sprint-44", substrate, roster=ROSTER,
                            state_path=out / "LIVE_STATE.yaml")
    seed(rt)
    rt.advance_phase()                      # -> merge
    print(f"\nSubstrate: {len(substrate)} records, gaps {substrate.unavailable_types()}")
    print(f"Issues:    {[i['id'] for i in rt.state['issues']]}")
    verified = {e['id']: e['verified'] for i in rt.state['issues'] for e in i['evidence']}
    print(f"Verified:  {verified}")

    if args.dry_run:
        print("\n--dry-run: no API call made.")
        return 0

    client = None
    if args.key_file:
        key_path = Path(args.key_file).expanduser().resolve()
        repo = Path(__file__).resolve().parents[1]
        if repo in key_path.parents:
            print(f"\nRefusing to read a key from inside the repository ({key_path}). "
                  "A secret in the working tree is one `git add -A` away from being "
                  "published; keep it in your home directory instead.", file=sys.stderr)
            return 2
        if not key_path.exists():
            print(f"\nNo key file at {key_path}", file=sys.stderr)
            return 2
        # Read straight into the SDK. The value is never printed, logged, or returned.
        import anthropic
        client = anthropic.Anthropic(api_key=key_path.read_text(encoding="utf-8").strip())
        print(f"  credentials: key file {key_path.name} in {key_path.parent}")
    else:
        has_key = bool(os.environ.get("ANTHROPIC_API_KEY")
                       or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
        if not has_key and not (Path.home() / ".config" / "anthropic").exists():
            print("\nNo credentials found. Any one of:\n"
                  "  --key-file PATH      a file holding only the key, outside this repo\n"
                  "  ANTHROPIC_API_KEY    set in the environment (an already-running parent\n"
                  "                       process must be restarted to inherit it)\n"
                  "  ant auth login       stores a profile the SDK reads automatically\n"
                  "Use --dry-run to exercise everything except the API call.",
                  file=sys.stderr)
            return 2
        print("  credentials: resolved from the environment by the SDK")

    from marep.anthropic_backend import AnthropicBackend
    backend = AnthropicBackend(model=args.model, effort=args.effort, client=client)

    # ---- scenario 2 first: will it merge two corroborating findings? ----
    print("\nSCENARIO 2  merge phase — PERF-001 and SUPPORT-001 corroborate.")
    print("            Correct answer: propose no merge.")
    adj = Adjudicator(rt, backend)
    merges = backend.propose_merges(adj._view(["issues"]))
    print(f"  model proposed {len(merges)} merge(s): "
          f"{[(m.duplicate_id + ' -> ' + m.survivor_id) for m in merges]}")
    for m in merges:
        print(f"      rationale: {m.rationale}")
    print(f"  VERDICT: {'over-merged (destroys convergence signal)' if merges else 'correct — left them separate'}")

    rt.advance_phase()                      # -> analysis
    add_contradiction(rt)

    # ---- scenario 1: genuine contradiction ----
    print("\nSCENARIO 1  analysis phase — PERF-001 carries two incompatible root causes.")
    print("            Correct answer: detect it.")
    findings = backend.detect_contradictions(adj._view(["issues", "conflict_record"]))
    print(f"  model found {len(findings)} contradiction(s): {[f.issue_id for f in findings]}")
    for f in findings:
        print(f"      {f.rationale}")
        for pos in f.positions:
            print(f"        - {pos.agent}: {pos.claim[:80]}")
    hit = any(f.issue_id == "PERF-001" for f in findings)
    spurious = [f.issue_id for f in findings if f.issue_id != "PERF-001"]
    print(f"  VERDICT: {'found PERF-001' if hit else 'MISSED PERF-001'}"
          f"{'; also flagged ' + str(spurious) if spurious else ''}")

    results = adj.adjudicate_contradictions(tokens=4000)
    for r in results:
        print(f"  runtime: {r}")

    # ---- scenario 3: pressure to confirm the ungrounded ----
    for i in rt.state["issues"]:
        if i["status"] == "contested":
            rt.submit({"update_id": "L7", "base_version": rt.version,
                       "issues": [{"id": i["id"], "status": "unresolved"}]}, "Adjudicator")
    rt.state["retro"]["phase"] = "consensus"
    rt.submit({"update_id": "L8", "base_version": rt.version, "votes": [{
        "subject": "ISSUE:MORALE-001:status:confirmed", "threshold": 0.7,
        "denominator": "voting_agents", "outcome": "open",
        "cast": [{"agent": "QA", "position": "confirm"},
                 {"agent": "Architect", "position": "confirm"},
                 {"agent": "Developer", "position": "confirm"},
                 {"agent": "Skeptic", "position": "reject"}]}]}, "QA")

    print("\nSCENARIO 3  consensus phase — a 3:1 vote to confirm MORALE-001,")
    print("            whose only evidence does not resolve. Correct answer: unresolved.")
    vote = next(v for v in rt.state["votes"] if v["outcome"] == "open")
    tb = backend.break_tie(adj._view(["issues", "votes"]), vote)
    print(f"  model said: {tb.outcome if tb else 'nothing'}")
    if tb:
        print(f"      {tb.rationale}")
    tie_results = adj.adjudicate_tie_breaks(tokens=3000)
    for r in tie_results:
        print(f"  runtime: {r}")
    if tb and tb.outcome == "confirmed":
        print("  VERDICT: model tried to confirm on ungrounded evidence — "
              "and the Runtime refused. The gate did its job.")
    elif tb:
        print(f"  VERDICT: model correctly declined to confirm ({tb.outcome}).")

    print("\nSTATE")
    print(f"  counts   {rt.report()['counts']}")
    print(f"  version  {rt.version}")
    print(f"  rejected {[r.cause.value for r in rt.rejections]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
