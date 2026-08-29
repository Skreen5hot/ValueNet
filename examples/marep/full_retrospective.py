"""All six phases, the full roster, the real ontology corpus, no model.

This is the composition test. Every part has unit tests; none of that shows
whether five agents, an Adjudicator and a Runtime get from Phase 1 to Phase 6
without deadlocking each other. Scripted backends make that answerable for
nothing, which is the point of having them.

The findings are seeded from substrate records looked up at run time, so they
cite whatever the corpus actually measures today rather than refs frozen into
this file.

Run: python examples/marep/full_retrospective.py [--scope BFO]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Repository root and run-artifact directory come from the layout
# contract, not from counting parents. parents[1] silently becomes
# examples/ once this file moves a level deeper -- a wrong root that
# raises nothing and reads the wrong tree.
_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

from marep import layout  # noqa: E402
from marep import (  # noqa: E402
    Adjudicator, Assessment, CompressionProposal, EvidenceRef, Finding,
    MergeProposal, Runtime, ScriptedAgentBackend, ScriptedBackend, Substrate,
    TieBreak, build_roster, ingest,
)
from marep.agents import ONTOLOGY_ROSTER  # noqa: E402


def show(label: str, results) -> None:
    if not isinstance(results, list):
        results = [results]
    for r in results:
        mark = "OK  " if r.accepted else "XX  "
        print(f"  {mark}{label:<40} {r}")


def find_metric(records, check: str, scope: str | None = None) -> str | None:
    for r in records:
        if r["type"] != "metric" or r["payload"]["check"] != check:
            continue
        if scope is None or r["payload"]["scope"] == scope:
            return r["ref"]
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default=None, help="limit the ontology scan, e.g. BFO")
    args = ap.parse_args(argv)

    out = layout.run_artifacts_dir()
    out.mkdir(exist_ok=True)
    repo = layout.repository_root()

    built = ingest.build("valuenet-audit", "2026-08-20", "2026-08-26", repo=repo,
                         ontology=True,
                         ontology_scopes=[args.scope] if args.scope else None)
    if built.errors:
        print(f"substrate invalid: {built.errors[0]}", file=sys.stderr)
        return 2
    sub_path = ingest.write(built, out / "AUDIT_INPUT.yaml")
    substrate = Substrate.load(sub_path)
    recs = built.document["records"]

    print(f"\nSUBSTRATE  {len(substrate)} records "
          f"({built.counts.get('document', 0)} document, "
          f"{built.counts.get('metric', 0)} metric, {built.counts.get('commit', 0)} commit)")
    print(f"           gaps: {substrate.unavailable_types()}")

    parse_ref = find_metric(recs, "files_not_parsing", "thats-all-folks") \
        or find_metric(recs, "files_not_parsing", "bfo-layer")
    prefix_ref = find_metric(recs, "files_with_undeclared_prefixes", "thats-all-folks") \
        or find_metric(recs, "files_with_undeclared_prefixes", "bfo-layer")
    ground_ref = find_metric(recs, "classes_reaching_bfo_root")
    label_ref = find_metric(recs, "classes_missing_label")
    if not all([parse_ref, prefix_ref, ground_ref, label_ref]):
        print("expected metrics missing; run without --scope", file=sys.stderr)
        return 2
    print(f"           agents will cite {parse_ref}, {prefix_ref}, {ground_ref}")

    roster = [r.name for r in ONTOLOGY_ROSTER]
    rt = Runtime.initialize("valuenet-audit", substrate, roster=roster,
                            state_path=out / "AUDIT_STATE.yaml")

    # ---- Phase 1 -------------------------------------------------------
    print("\nPHASE 1  gathering — five perspectives in parallel under CAS")
    agent_backend = ScriptedAgentBackend(findings={
        "Corpus": [
            Finding("PARSE", "A large share of one module cannot be loaded standalone",
                    "critical",
                    [EvidenceRef("Files in the group fail to parse on their own",
                                 "metric", parse_ref)]),
            Finding("FRAG", "The same files omit prefix declarations entirely", "high",
                    [EvidenceRef("Prefixes are used that the files never declare",
                                 "metric", prefix_ref)]),
        ],
        "Interoperability": [
            Finding("FRAG", "Fragment files cannot be consumed by a standard loader",
                    "high",
                    [EvidenceRef("Undeclared prefixes make the files invalid Turtle",
                                 "metric", prefix_ref)]),
        ],
        "Realist": [
            Finding("GROUND", "Class grounding in the BFO layer is complete", "low",
                    [EvidenceRef("Every class reaches a BFO root", "metric", ground_ref)]),
        ],
        # Lexicographer and Skeptic have nothing to raise unprompted.
    })
    for agent in build_roster(rt, agent_backend):
        show(f"{agent.name} gathers", agent.gather(tokens=2500))
    show("advance to merge", rt.advance_phase())

    # ---- Phase 2 -------------------------------------------------------
    print("\nPHASE 2  merge — two agents raised the same fragment problem")
    ids = [i["id"] for i in rt.state["issues"]]
    dupes = [i for i in ids if i.startswith("FRAG")]
    adj_backend = ScriptedBackend(
        merges=[MergeProposal(dupes[0], dupes[1],
                              "Both describe the missing prefix declarations")]
        if len(dupes) > 1 else [],
        contradictions=[],
        compression=CompressionProposal("Gathering and analysis history archived.",
                                        [{"kind": "history", "note": "phase 1-4 detail"}]),
    )
    adj = Adjudicator(rt, adj_backend)
    show("Adjudicator merges", adj.run_for_phase(tokens=3000))
    show("advance to analysis", rt.advance_phase())

    # ---- Phase 3 -------------------------------------------------------
    print("\nPHASE 3  analysis — and one contest, which holds consensus open")
    parse_id = next(i["id"] for i in rt.state["issues"] if i["id"].startswith("PARSE"))
    ground_id = next(i["id"] for i in rt.state["issues"] if i["id"].startswith("GROUND"))
    eval_backend = ScriptedAgentBackend(assessments={
        "Realist": [Assessment(parse_id, "confirm", "the measurement is unambiguous")],
        "Interoperability": [Assessment(parse_id, "confirm", "consistent with the prefix metric")],
        "Skeptic": [Assessment(ground_id, "contest",
                               "This restates a metric without saying what follows from it")],
    })
    for agent in build_roster(rt, eval_backend):
        show(f"{agent.name} evaluates", agent.evaluate(tokens=2000) or
             [type("R", (), {"accepted": True, "__str__": lambda s: "no position"})()])
    ready, unmet = rt.exit_ready()
    print(f"       exit blocked by: {unmet}")
    show("advance, archiving unevaluated", rt.advance_phase(archive_unevaluated=True))

    # ---- Phase 4 -------------------------------------------------------
    print("\nPHASE 4  consensus — the contested issue must be settled")
    contested = [i["id"] for i in rt.state["issues"] if i["status"] == "contested"]
    for iid in contested:
        show(f"resolve {iid} unresolved", rt.submit({
            "update_id": f"C-{iid}", "base_version": rt.version,
            "issues": [{"id": iid, "status": "unresolved"}]}, "Adjudicator"))
    show("advance to actions", rt.advance_phase())

    # ---- Phase 5 -------------------------------------------------------
    print("\nPHASE 5  actions — every confirmed issue needs one or a waiver")
    confirmed = [i["id"] for i in rt.state["issues"] if i["status"] == "confirmed"]
    from marep import ActionProposal
    act_backend = ScriptedAgentBackend(actions={"Corpus": [
        ActionProposal("Document the fragment convention, or add prefixes and a build step",
                       "Every file in the group parses standalone, or a README states why not",
                       confirmed)]})
    for agent in build_roster(rt, act_backend):
        res = agent.propose_actions(tokens=1500)
        if res:
            show(f"{agent.name} proposes", res)
    acts = [a["id"] for a in rt.state.get("actions") or []]
    for aid in acts:
        show(f"accept {aid}", rt.submit({
            "update_id": f"A-{aid}", "base_version": rt.version,
            "actions": [{"id": aid, "status": "accepted"}]}, "Corpus"))
    ready, unmet = rt.exit_ready()
    if unmet:
        print(f"       exit blocked by: {unmet}")
    show("advance to compression", rt.advance_phase())

    # ---- Phase 6 -------------------------------------------------------
    print("\nPHASE 6  compression")
    show("Adjudicator archives", Adjudicator(rt, adj_backend).run_for_phase(tokens=4000))
    show("advance to complete", rt.advance_phase())

    # ---- report --------------------------------------------------------
    rep = rt.report()
    print("\nREPORT")
    print(f"  phase                {rt.phase}")
    print(f"  status counts        {rep['counts']}")
    print(f"  unresolved           {rep['unresolved']}")
    print(f"  coverage gaps        {rep['unavailable_types']}")
    print(f"  tokens consumed      {rep['tokens_consumed']:,}")
    print(f"  version              {rt.version}")
    print(f"  rejections           {[r.cause.value for r in rt.rejections]}")
    print("\n  confirmed findings and the records behind them:")
    for i in rt.state["issues"]:
        if i["status"] != "confirmed":
            continue
        for e in i["evidence"]:
            print(f"    {i['id']:12} <- {e['source']['ref']}  verified={e['verified']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
