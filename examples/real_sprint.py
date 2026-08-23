"""A retrospective grounded in this repository's real git history.

`walkthrough.py` proves the Runtime's mechanics against data written to exercise
them. This proves something different and harder: that the grounding gate works
when the substrate is built from a source nobody authored for the occasion.

Every verified claim below resolves to a commit that is actually in this
repository. The one unverifiable claim is accepted and recorded, then refused
confirmation, which is the whole point of MAREP v2.2 §8.3.1.

Run: python examples/real_sprint.py [--since ISO] [--until ISO]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from marep import Runtime, Substrate, ingest  # noqa: E402

ROSTER = ["Developer", "QA", "Architect", "Skeptic"]


def show(label: str, result) -> None:
    print(f"  {'OK  ' if result.accepted else 'XX  '}{label:<44} {result}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-08-20")
    ap.add_argument("--until", default="2026-08-24")
    ap.add_argument("--sprint", default="valuenet-aug")
    args = ap.parse_args(argv)

    out = Path(__file__).parent / "_run"
    out.mkdir(exist_ok=True)
    repo_root = Path(__file__).resolve().parents[1]

    # ---- 1. build the substrate from real history -----------------------
    print(f"\nINGEST  {repo_root.name}  {args.since} .. {args.until}")
    built = ingest.build(args.sprint, args.since, args.until, repo=repo_root)
    if built.errors:
        print(f"  substrate does not validate: {built.errors[0]}", file=sys.stderr)
        return 2
    sub_path = ingest.write(built, out / "SPRINT_INPUT.yaml")
    substrate = Substrate.load(sub_path)
    print(f"  {len(substrate)} records  {[k for k, v in built.counts.items() if v]}")
    print(f"  coverage gaps: {substrate.unavailable_types()}")

    commits = [r for r in built.document["records"] if r["type"] == "commit"]
    if len(commits) < 2:
        print(f"\n  Only {len(commits)} commits in range; widen --since/--until.")
        return 1

    # Pick real records to cite. Biggest churn and most files touched.
    by_churn = sorted(commits, key=lambda r: -(r["payload"]["insertions"] + r["payload"]["deletions"]))
    biggest, second = by_churn[0], by_churn[1]
    print(f"\n  citing {biggest['id']} ({biggest['payload']['deletions']} deletions)"
          f" and {second['id']} ({second['payload']['files_changed']} files)")

    # ---- 2. run the retrospective ---------------------------------------
    rt = Runtime.initialize(args.sprint, substrate, roster=ROSTER,
                            state_path=out / "REAL_STATE.yaml")

    print("\nPHASE 1  gathering")
    show("grounded: large mechanical change", rt.submit({
        "update_id": "R-001", "base_version": rt.version,
        "issues": [{"id": "CHURN-001",
                    "title": "A single commit removed a whole directory",
                    "severity": "medium", "status": "proposed",
                    "evidence": [{"id": "EV-001",
                                  "claim": f"{biggest['payload']['deletions']} deletions in one commit: "
                                           f"{biggest['summary'][:70]}",
                                  "source": {"type": "commit", "ref": biggest["id"]},
                                  "submitted_by": "Architect"}]}]}, "Architect", tokens=3000))

    show("grounded: broad blast radius", rt.submit({
        "update_id": "R-002", "base_version": rt.version,
        "issues": [{"id": "SCOPE-001",
                    "title": "Changes spanned many files at once",
                    "severity": "low", "status": "proposed",
                    "evidence": [{"id": "EV-002",
                                  "claim": f"{second['payload']['files_changed']} files touched in "
                                           f"one commit",
                                  "source": {"type": "commit", "ref": second["id"]},
                                  "submitted_by": "QA"}]}]}, "QA", tokens=2400))

    show("ungrounded: no such record", rt.submit({
        "update_id": "R-003", "base_version": rt.version,
        "issues": [{"id": "MORALE-001",
                    "title": "Sustained pace felt heavy",
                    "severity": "low", "status": "proposed",
                    "evidence": [{"id": "EV-003", "claim": "Team reported fatigue",
                                  "source": {"type": "metric", "ref": "MET-0001"},
                                  "submitted_by": "Skeptic"}]}]}, "Skeptic", tokens=1500))

    flags = {e["id"]: e["verified"]
             for i in rt.state["issues"] for e in i["evidence"]}
    print(f"       Runtime resolution: {flags}")

    show("Developer declines explicitly", rt.submit({
        "update_id": "R-004", "base_version": rt.version,
        "decisions": [{"id": "DEC-001", "type": "declination",
                       "subject": "AGENT:Developer", "outcome": "declined",
                       "rationale": "Nothing to add beyond findings already recorded.",
                       "basis": "Developer"}]}, "Developer", tokens=600))
    show("advance to merge", rt.advance_phase())
    show("advance to analysis", rt.advance_phase())

    print("\nPHASE 3  analysis — the gate, against real data")
    show("confirm the grounded finding", rt.submit({
        "update_id": "R-005", "base_version": rt.version,
        "issues": [{"id": "CHURN-001", "status": "confirmed"}]}, "Architect", tokens=2100))
    show("confirm the ungrounded finding", rt.submit({
        "update_id": "R-006", "base_version": rt.version,
        "issues": [{"id": "MORALE-001", "status": "confirmed"}]}, "Skeptic", tokens=900))
    show("reject it instead", rt.submit({
        "update_id": "R-007", "base_version": rt.version,
        "issues": [{"id": "MORALE-001", "status": "rejected"}]}, "Skeptic", tokens=700))
    show("confirm SCOPE-001", rt.submit({
        "update_id": "R-008", "base_version": rt.version,
        "issues": [{"id": "SCOPE-001", "status": "confirmed"}]}, "QA", tokens=1200))
    show("advance", rt.advance_phase(archive_unevaluated=True))

    # ---- 3. report -------------------------------------------------------
    rep = rt.report()
    print("\nREPORT")
    print(f"  status counts        {rep['counts']}")
    print(f"  coverage gaps        {rep['unavailable_types']}")
    print(f"  tokens consumed      {rep['tokens_consumed']:,}")
    print(f"  version              {rt.version}")
    print("\n  Confirmed findings and the commits behind them:")
    for issue in rt.state["issues"]:
        if issue["status"] != "confirmed":
            continue
        for e in issue["evidence"]:
            rec = substrate.get(e["source"]["ref"])
            sha = rec.payload.get("short_sha", "?") if rec and rec.payload else "?"
            print(f"    {issue['id']:12} <- {e['source']['ref']}  {sha}  {rec.summary[:52]}")
    print(f"\n  substrate  {sub_path}")
    print(f"  state      {out / 'REAL_STATE.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
