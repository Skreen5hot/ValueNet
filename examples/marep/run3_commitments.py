"""Run 3 of MAREP_VALUENET_PLAN: commitments that exist outside the axioms.

Run 2 asked what the corpus should assert. Run 3 asks the wider question: what
does it already commit to in its naming, its file layout, its mapping targets
and its documentation, without ever saying so where a machine could check.

Scoped to the three areas Run 2 did not reach - sense ambiguity, IRI ownership,
external mapping quality - plus the question of which of those commitments
belong in SHACL. That last is not a coverage exercise: reconciling
VALIDATION-001 showed that repairing 127 files moved SHACL violations from 0 to
0, because the shapes load 6 of 165 files and target classes the folk corpus
never instantiates.

Run 1's findings in these areas enter as `note` records, not metrics. MAREP
treats a note as exactly as trustworthy as whoever wrote it, which is the right
standing for them: Run 1 read the alignment layer from files that did not
parse, and undercounted badly. They are hypotheses to test, and the
reconciliation dispositions travel with them so no agent builds on a finding
already refuted.

Run: python examples/marep/run3_commitments.py --key-file PATH [--dry-run] [--resume]
"""

from __future__ import annotations

import argparse
import os
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
from marep import Adjudicator, Runtime, Substrate, build_roster, ingest  # noqa: E402
from marep.agents import COMMITMENT_ROSTER  # noqa: E402

#: The checks a commitment finding can cite. Printed before the run so that a
#: substrate missing them is visible before any tokens are spent, rather than
#: as a run that produces nothing and looks like agent failure.
COMMITMENT_CHECKS = (
    "trigger_statements", "trigger_source_hosts",
    "triggers_with_foreign_subject", "triggers_with_foreign_object",
    "wiktionary_language_editions", "wiktionary_non_english_triggers",
    "class_iris_declared_across_groups", "namespaces_minting_classes",
    "foreign_iris_used_as_subjects", "classes_without_definition_text",
    "local_names_colliding_on_normalisation",
    "populated_classes_without_a_shape", "shacl_focus_nodes",
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
        # The key file's name and length are not diagnostic, and a run
        # report is an artefact that gets committed and shared. Confirm
        # that credentials resolved; say nothing about which.
        print("CREDENTIALS resolved from a key file")
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
    ap.add_argument("--resume", action="store_true",
                    help="continue from RUN3_STATE.yaml rather than starting over; "
                         "phases already closed are skipped")
    args = ap.parse_args(argv)

    out = layout.run_artifacts_dir()
    out.mkdir(exist_ok=True)
    repo = layout.repository_root()

    sub_path = out / "RUN3_INPUT.yaml"
    if args.resume:
        # Reuse the exact substrate the run was built against rather than
        # rebuilding one and hoping it matches. It will not match: any change
        # to a metric's detail string changes the checksum, and the first
        # thing this run produced was a reason to change one. Rebuilding also
        # costs three minutes to re-derive a file already on disk.
        if not sub_path.exists():
            print("--resume needs " + str(sub_path) + ", which is missing",
                  file=sys.stderr)
            return 2
        built = None
        substrate = Substrate.load(sub_path)
        print("REUSING substrate " + sub_path.name + " (" + substrate.checksum[:19]
              + "...), not rebuilding")
    else:
        built = ingest.build("valuenet-run3", "2026-08-20", "2026-08-26", repo=repo,
                             ontology=True, include_github=False,
                             notes=out / "RUN3_NOTES.yaml",
                             reasoner=not args.no_reasoner)
        if built.errors:
            print(f"substrate invalid: {built.errors[0]}", file=sys.stderr)
            return 2
        sub_path = ingest.write(built, sub_path)
        substrate = Substrate.load(sub_path)

    print("\nRUN 3  commitments that exist outside the axioms")
    if built:
        print(f"  substrate  {len(substrate)} records "
              f"({built.counts.get('document', 0)} document, "
              f"{built.counts.get('metric', 0)} metric)")
    else:
        print(f"  substrate  {len(substrate)} records, loaded from disk")
    print(f"  gaps       {substrate.unavailable_types()}")

    # Read the records from the substrate itself, not from the build result.
    # Taking them from `built` meant a resumed run had none to read and the
    # pre-flight announced "0/11 checks -- MISSING, so no finding can cite
    # them" over a substrate holding all eleven. That is the exact failure
    # this pre-flight exists to prevent, produced by the pre-flight.
    records = [r for r in substrate.to_dict().get("records", [])
               if r.get("type") == "metric"]
    present = {r["payload"]["check"] for r in records}
    missing = [c for c in COMMITMENT_CHECKS if c not in present]
    print(f"\n  commitment evidence available: "
          f"{len(COMMITMENT_CHECKS) - len(missing)}/{len(COMMITMENT_CHECKS)} checks")
    if missing:
        print(f"  MISSING, so no finding can cite them: {', '.join(missing)}")
    for r in records:
        if r["payload"]["check"] in COMMITMENT_CHECKS:
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

    roster = [r.name for r in COMMITMENT_ROSTER]
    state_path = out / "RUN3_STATE.yaml"
    if args.resume:
        if not state_path.exists():
            print("--resume given but no state at " + str(state_path), file=sys.stderr)
            return 2
        rt = Runtime.resume(state_path, substrate, roster=roster)
        print("RESUMED at phase " + rt.phase + ", version " + str(rt.version)
              + ", " + str(len(rt.state["issues"])) + " issue(s) carried")
    else:
        rt = Runtime.initialize("valuenet-run3", substrate, roster=roster,
                                state_path=state_path)
    adj = Adjudicator(rt, adj_backend)

    #: Phases run in order, so anything before the one we resumed into is
    #: closed. Re-running a closed phase would re-ask agents questions they
    #: have already answered, and the no-new-content rule would reject the
    #: answers -- after paying for them.
    ORDER = ["gathering", "merge", "analysis", "consensus", "actions",
             "compression", "complete"]

    def done(phase: str) -> bool:
        if rt.phase not in ORDER or phase not in ORDER:
            return False
        return ORDER.index(rt.phase) > ORDER.index(phase)

    def agents():
        return build_roster(rt, backend, COMMITMENT_ROSTER)

    # ---- Phase 1 -------------------------------------------------------
    if done("gathering"):
        print("\nGATHERING - already closed on the saved state, skipping")
    else:
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
    if done("merge"):
        print("\nMERGE - already closed on the saved state, skipping")
    else:
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
    if done("analysis"):
        print("\nANALYSIS - already closed on the saved state, skipping")
    else:
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
    if done("consensus"):
        print("\nCONSENSUS - already closed on the saved state, skipping")
    else:
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
    if done("actions"):
        print("\nACTIONS - already closed on the saved state, skipping")
    else:
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
    if done("compression"):
        print("\nCOMPRESSION - already closed on the saved state, skipping")
    else:
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
    print(f"\n  state {out / 'RUN3_STATE.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
