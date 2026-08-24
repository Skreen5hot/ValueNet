"""Run 2 of MAREP_VALUENET_PLAN: what the corpus should assert and does not.

Rescoped from a BFO-layer calibration pass. The reasoner survey supplied that
calibration more cheaply: all seven groups are consistent with zero
unsatisfiable classes, and for four of them the result was guaranteed before
HermiT started, because 143,717 of the corpus's triples contain no
disjointness, cardinality, functionality or complement at all.

A corpus that cannot be found inconsistent is not thereby correct. It is
unconstrained. So this run asks what the corpus treats as true without ever
saying so, and sorts each candidate into OWL, SHACL, or intentionally
unconstrained. The third is a real answer: folk value vocabularies are built to
overlap, and the roster carries an agent whose job is to defend absences.

Scope is the whole corpus, unlike Run 1. The question is cross-cutting and the
instruments now cover every group.

Run: python examples/run2_constraints.py --key-file PATH [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from marep import Adjudicator, Runtime, Substrate, build_roster, ingest  # noqa: E402
from marep.agents import CONSTRAINT_ROSTER  # noqa: E402

#: The checks a constraint finding can cite. Printed before the run so that a
#: substrate missing them is visible before any tokens are spent, rather than
#: as a run that produces nothing and looks like agent failure.
CONSTRAINT_CHECKS = (
    "properties_without_domain", "properties_without_range",
    "properties_without_characteristics", "predicates_used_but_not_declared",
    "sibling_sets_without_disjointness", "classes_without_necessary_conditions",
    "populated_classes_without_a_shape", "reasoner_contradiction_axioms",
    "shacl_focus_nodes", "classes_rooted_in_nothing",
)


def show(label, results):
    if not isinstance(results, list):
        results = [results]
    if not results:
        print(f"  --  {label:<34} no position")
    for r in results:
        print(f"  {'OK  ' if r.accepted else 'XX  '}{label:<34} {r}")


def client_from(args, repo: Path):
    if args.key_file:
        kp = Path(args.key_file).expanduser().resolve()
        if repo in kp.parents:
            print(f"\nRefusing to read a key from inside the repository ({kp}).",
                  file=sys.stderr)
            return None, 2
        if not kp.exists():
            print(f"\nNo key file at {kp}", file=sys.stderr)
            return None, 2
        raw = kp.read_text(encoding="utf-8-sig").strip().strip("'\"")
        if not raw.startswith("sk-ant-"):
            print(f"\n{kp} does not look like an API key ({len(raw)} chars).",
                  file=sys.stderr)
            return None, 2
        import anthropic
        print(f"CREDENTIALS key file {kp.name} ({len(raw)} chars)")
        return anthropic.Anthropic(api_key=raw), 0
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        print("CREDENTIALS resolved from the environment")
        return None, 0
    print("\nNo credentials. Pass --key-file PATH.", file=sys.stderr)
    return None, 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-file", default=None)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-reasoner", action="store_true",
                    help="skip HermiT; repository-root alone takes 23 minutes")
    args = ap.parse_args(argv)

    out = Path(__file__).parent / "_run"
    out.mkdir(exist_ok=True)
    repo = Path(__file__).resolve().parents[1]

    built = ingest.build("valuenet-run2", "2026-08-20", "2026-08-26", repo=repo,
                         ontology=True, include_github=False,
                         reasoner=not args.no_reasoner)
    if built.errors:
        print(f"substrate invalid: {built.errors[0]}", file=sys.stderr)
        return 2
    sub_path = ingest.write(built, out / "RUN2_INPUT.yaml")
    substrate = Substrate.load(sub_path)

    print("\nRUN 2  what the corpus should assert and does not")
    print(f"  substrate  {len(substrate)} records "
          f"({built.counts.get('document', 0)} document, "
          f"{built.counts.get('metric', 0)} metric)")
    print(f"  gaps       {substrate.unavailable_types()}")

    records = [r for r in built.document["records"] if r["type"] == "metric"]
    present = {r["payload"]["check"] for r in records}
    missing = [c for c in CONSTRAINT_CHECKS if c not in present]
    print(f"\n  constraint evidence available: "
          f"{len(CONSTRAINT_CHECKS) - len(missing)}/{len(CONSTRAINT_CHECKS)} checks")
    if missing:
        print(f"  MISSING, so no finding can cite them: {', '.join(missing)}")
    for r in records:
        if r["payload"]["check"] in CONSTRAINT_CHECKS:
            print(f"    {r['ref']:<58} {r['payload']['value']}")

    if args.dry_run:
        print("\n--dry-run: no API call made.")
        return 0

    client, code = client_from(args, repo)
    if code:
        return code

    from marep.anthropic_agents import AnthropicAgentBackend
    from marep.anthropic_backend import AnthropicBackend
    backend = AnthropicAgentBackend(model=args.model, effort=args.effort, client=client)
    adj_backend = AnthropicBackend(model=args.model, effort=args.effort, client=client)

    roster = [r.name for r in CONSTRAINT_ROSTER]
    rt = Runtime.initialize("valuenet-run2", substrate, roster=roster,
                            state_path=out / "RUN2_STATE.yaml")
    adj = Adjudicator(rt, adj_backend)

    def agents():
        return build_roster(rt, backend, CONSTRAINT_ROSTER)

    # ---- Phase 1 -------------------------------------------------------
    print("\nPHASE 1  gathering")
    for agent in agents():
        findings, err = agent.ask("gather", agent.substrate_view(), rt.read(agent.name))
        if err is not None:
            print(f"  XX  {agent.name}: {err}")
            continue
        print(f"  --  {agent.name}: {len(findings)} finding(s)")
        for f in findings:
            print(f"        [{f.severity}] {f.title[:88]}")
            for e in f.evidence:
                print(f"           cites {e.source_type}:{e.source_ref}")
        show(f"{agent.name} submits", agent.gather(tokens=4500, findings=findings))

    r = rt.advance_phase()
    show("advance to merge", r)
    if not r:
        print("  phase 1 did not close; stopping.")
        return 1

    # ---- Phase 2 -------------------------------------------------------
    print("\nPHASE 2  merge")
    merges, err = adj.propose("propose_merges", adj._view(["issues"]))
    if err is None:
        print(f"  --  Adjudicator proposes {len(merges)} merge(s)")
        for m in merges:
            print(f"        {m.duplicate_id} -> {m.survivor_id}: {m.rationale[:80]}")
        show("merges", adj.adjudicate_merges(tokens=4000) if merges else [])
    else:
        print(f"  XX  {err}")
    show("advance to analysis", rt.advance_phase())

    # ---- Phase 3 -------------------------------------------------------
    print("\nPHASE 3  analysis")
    for agent in agents():
        assessments, err = agent.ask("evaluate", agent.substrate_view(), rt.read(agent.name))
        if err is not None:
            print(f"  XX  {agent.name}: {err}")
            continue
        acting = [a for a in assessments if a.position != "abstain"]
        print(f"  --  {agent.name}: {len(acting)} position(s)")
        for a in acting:
            print(f"        {a.position:8} {a.issue_id}  {a.rationale[:74]}")
        show(f"{agent.name} submits", agent.evaluate(tokens=4000, assessments=assessments))

    findings, err = adj.propose("detect_contradictions",
                                adj._view(["issues", "conflict_record"]))
    if err is None and findings:
        print(f"  --  Adjudicator finds {len(findings)} contradiction(s)")
        show("contradictions", adj.adjudicate_contradictions(tokens=3500, findings=findings))

    ready, unmet = rt.exit_ready()
    if unmet:
        print(f"  --  exit blocked by: {unmet[0][:100]}")
    show("advance to consensus", rt.advance_phase(archive_unevaluated=True))

    # ---- Phase 4 -------------------------------------------------------
    print("\nPHASE 4  consensus")
    contested = [i["id"] for i in rt.state["issues"] if i["status"] == "contested"]
    for iid in contested:
        show(f"open vote on {iid}", rt.submit({
            "update_id": f"V-{iid}", "base_version": rt.version,
            "votes": [{"subject": f"ISSUE:{iid}:status:confirmed", "threshold": 0.7,
                       "denominator": "voting_agents", "outcome": "open", "cast": []}]},
            "Adjudicator"))
    for agent in agents():
        res = agent.cast_votes(tokens=1500)
        if res:
            show(f"{agent.name} votes", res)
    for vote in [v for v in rt.state.get("votes", []) if v["outcome"] == "open"]:
        tb, err = adj.propose("break_tie", adj._view(["issues", "votes"]), vote)
        if err is None and tb:
            print(f"  --  Adjudicator: {tb.outcome} - {tb.rationale[:100]}")
            show("tie-break", adj.adjudicate_tie_breaks(
                tokens=3000, decisions={tb.subject: tb}))
    show("advance to actions", rt.advance_phase())

    # ---- Phase 5 -------------------------------------------------------
    print("\nPHASE 5  actions")
    for agent in agents():
        res = agent.propose_actions(tokens=3000)
        if res:
            show(f"{agent.name} proposes", res)
    for a in list(rt.state.get("actions") or []):
        show(f"accept {a['id']}", rt.submit({
            "update_id": f"ACC-{a['id']}", "base_version": rt.version,
            "actions": [{"id": a["id"], "status": "accepted"}]}, "Grounding"))
    ready, unmet = rt.exit_ready()
    if unmet:
        print(f"  --  {unmet[0][:110]}")
        for i in rt.state["issues"]:
            if i["status"] == "confirmed":
                n = len(rt.state.get("decisions") or []) + 1
                show(f"waive {i['id']}", rt.submit({
                    "update_id": f"W-{i['id']}", "base_version": rt.version,
                    "decisions": [{"id": f"DEC-{n:03d}", "type": "no_action_required",
                                   "subject": f"ISSUE:{i['id']}",
                                   "outcome": "no action this cycle",
                                   "basis": "adjudicator"}]}, "Adjudicator"))
    show("advance to compression", rt.advance_phase())

    # ---- Phase 6 -------------------------------------------------------
    print("\nPHASE 6  compression")
    show("archive", adj.adjudicate_compression(tokens=4000))
    show("advance to complete", rt.advance_phase())

    # ---- report --------------------------------------------------------
    rep = rt.report()
    print("\nREPORT")
    print(f"  phase              {rt.phase}")
    print(f"  counts             {rep['counts']}")
    print(f"  unresolved         {rep['unresolved']}")
    print(f"  coverage gaps      {rep['unavailable_types']}")
    print(f"  tokens (declared)  {rep['tokens_consumed']:,}")
    print(f"  version            {rt.version}")
    print(f"  rejections         {[r.cause.value for r in rt.rejections]}")
    print("\n  findings:")
    for i in rt.state["issues"]:
        ver = [e for e in i["evidence"] if e.get("verified")]
        print(f"    {i['id']:14} {i['status']:11} {len(ver)}/{len(i['evidence'])} verified  "
              f"{i['title'][:60]}")
    print(f"\n  state {out / 'RUN2_STATE.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
