# SPDX-License-Identifier: Apache-2.0
"""Render a MAREP state file as a readable findings report.

`RETRO_STATE.yaml` is the canonical record and is not meant to be read by a
person: Run 2's is 118 KB of YAML, and `examples/_run/` is gitignored, so the
only durable account of a run that cost 412,000 tokens was a log nobody would
open twice. This turns one into a document that can be committed and reviewed.

It reads only the state file. Proposer attribution comes from the first
evidence item's `submitted_by` rather than the audit trail, because the audit
records which agent wrote each version but not which issue that version
created, and reconstructing the mapping by position would break the first time
an update carried two issues.

    python tools/marep/report_run.py examples/_run/RUN2_STATE.yaml -o REPORT.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("needs pyyaml: pip install pyyaml")

#: Ordered so the report opens with what was agreed and closes with what was
#: not. `unresolved` is last because it is the status that needs a human.
STATUS_ORDER = ("confirmed", "contested", "unresolved", "proposed",
                "rejected", "archived")

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def proposer(issue: dict) -> str:
    for e in issue.get("evidence") or []:
        who = e.get("submitted_by")
        if who:
            return who
    return "unknown"


#: How a superseded finding is flagged, and how loudly. A reader scanning the
#: report has to be stopped before they act on an obsolete finding, so the
#: banner sits directly under the title rather than at the end of the entry.
DISPOSITION_LABEL = {
    "resolved": "RESOLVED - fixed since this run",
    "superseded-vindicated": "SUPERSEDED - was right, no longer applies",
    "superseded-partly-wrong": "SUPERSEDED - partly wrong, no longer applies",
    "conclusion-upheld-cause-refuted":
        "CAUSE REFUTED - the conclusion stands, the stated cause does not",
    "superseded": "SUPERSEDED - a better finding covers this",
    "premise-false-conclusion-survives":
        "PREMISE FALSE - the conclusion stands, a supporting claim does not",
    "unresolved-rewrite":
        "UNRESOLVED, TO BE REWRITTEN - the subject is real, this proposition is not",
    "reformulate-as-fact-plus-action":
        "MIS-SHAPED - a recommendation in a finding's place; split into fact and action",
    "premise-false-conclusion-survives":
        "PREMISE FALSE - the conclusion stands, a supporting claim does not",
    "rewritten": "REWRITTEN - the subject held, the proposition did not",
    "upheld-and-extended": "UPHELD - and extended by cases found since",
}


def render(state: dict, source: str, reconciliation: dict | None = None) -> str:
    retro = state.get("retro") or {}
    issues = state.get("issues") or []
    recon = {f["id"]: f for f in ((reconciliation or {}).get("findings") or [])}
    by_status: dict[str, list] = {}
    for i in issues:
        by_status.setdefault(i.get("status", "unknown"), []).append(i)

    out: list[str] = []
    add = out.append

    add(f"# {retro.get('sprint', 'MAREP run')} — findings")
    add("")
    add(f"Rendered from `{source}` by `tools/marep/report_run.py`. "
        "The state file is the record; this is a view of it.")
    add("")
    add("**Two kinds of statement appear below and are never merged.** "
        "Finding titles, severities and evidence are exactly what the run "
        "concluded from the substrate it was given, reproduced unedited. "
        "Anything inside a `⚠ RECONCILIATION` block was established *after* "
        "the run, sometimes contradicting it, and is never folded back into "
        "the finding. The state file itself is not modified by reconciliation.")
    add("")
    add(f"- **phase** {retro.get('phase')}, **version** {retro.get('version')}")
    add(f"- **substrate** `{retro.get('sprint_input_checksum', '')[:26]}…`")
    counts = ", ".join(f"{len(v)} {k}" for k, v in sorted(
        by_status.items(), key=lambda kv: STATUS_ORDER.index(kv[0])
        if kv[0] in STATUS_ORDER else 99))
    add(f"- **findings** {len(issues)} — {counts}")
    ledger = state.get("token_ledger") or {}
    add(f"- **tokens declared** {ledger.get('consumed_total', 0):,}")
    total_ev = sum(len(i.get("evidence") or []) for i in issues)
    verified = sum(1 for i in issues for e in (i.get("evidence") or [])
                   if e.get("verified"))
    add(f"- **evidence** {verified}/{total_ev} verified against the substrate")
    if recon:
        add(f"- **reconciled** against the tree at "
            f"`{(reconciliation or {}).get('reconciled_at_commit', '?')}` — "
            f"{len(recon)} finding(s) superseded or resolved; "
            f"the state file itself is unmodified")
    add("")

    for status in STATUS_ORDER:
        group = by_status.get(status)
        if not group:
            continue
        group.sort(key=lambda i: (SEVERITY_ORDER.get(i.get("severity"), 9),
                                  i.get("id", "")))
        add(f"## {status} ({len(group)})")
        add("")
        for i in group:
            add(f"### {i.get('id')} — {i.get('title')}")
            add("")
            r = recon.get(i.get("id"))
            if r:
                label = DISPOSITION_LABEL.get(r.get("disposition"),
                                              r.get("disposition", "").upper())
                add(f"> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION")
                add(">")
                add(f"> **{label}**")
                add(">")
                add("> " + " ".join((r.get("summary") or "").split()))
                for line in r.get("evidence") or []:
                    add("> - " + " ".join(str(line).split()))
                rw = r.get("rewritten_as") or r.get("reformulated_as")
                if rw:
                    add(">")
                    add(f"> **Restated as:** {' '.join(str(rw.get('title','')).split())}")
                    for k in ("consequence", "then_action"):
                        if rw.get(k):
                            add(f"> **{k.replace('_', ' ').title()}:** "
                                + " ".join(str(rw[k]).split()))
                add("")
                add("_Everything below this line is what the run itself "
                    "concluded, unedited._")
                add("")
            add(f"*{i.get('severity', '?')} · proposed by {proposer(i)}*")
            for key, label in (("confirmed_by", "confirmed by"),
                               ("contested_by", "contested by")):
                if i.get(key):
                    add(f" · {label} {', '.join(i[key])}")
            add("")
            for e in i.get("evidence") or []:
                src = e.get("source") or {}
                ref = f"{src.get('type', '?')}:{src.get('ref', '?')}"
                # `verified` means the record supports the claim, not that the
                # citation resolves. Where a run predates that rule, the
                # grounding verdict is absent and the flag is reported as-is.
                grounding = e.get("grounding")
                if grounding:
                    mark = {"supported": "verified (record supports the claim)",
                            "unsupported": "UNSUPPORTED (figures do not match the record)",
                            "resolves_only": "WEAK — citation resolves, claim unchecked",
                            "unresolved": "UNRESOLVED (no such record)"}.get(
                                grounding, grounding)
                else:
                    mark = "verified" if e.get("verified") else "UNVERIFIED"
                add(f"- {e.get('claim', '')}")
                add(f"  <br/>`{ref}` — {mark}")
            add("")

    conflicts = state.get("conflict_record") or []
    if conflicts:
        add(f"## contest rationales ({len(conflicts)})")
        add("")
        add("Why an agent disputed a finding. Kept because the reasoning is "
            "often worth more than the verdict: three agents contested INV-001 "
            "on the ground that its premise was falsified by its own evidence, "
            "and they were right.")
        add("")
        for c in conflicts:
            add(f"**{c.get('issue_id')}**")
            add("")
            positions = c.get("positions")
            if isinstance(positions, str):
                add(f"> {positions}")
            else:
                for p in positions or []:
                    add(f"> **{p.get('agent')}** — {p.get('claim', '')}")
                    add(">")
            add("")

    decisions = state.get("decisions") or []
    if decisions:
        add(f"## decisions ({len(decisions)})")
        add("")
        for d in decisions:
            add(f"- **{d.get('id')}** {d.get('type')} on `{d.get('subject')}` "
                f"— {d.get('outcome')} ({d.get('basis')})")
        add("")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("state", help="path to a RETRO/RUN state YAML")
    ap.add_argument("-o", "--out", default=None,
                    help="write here instead of stdout")
    ap.add_argument("--reconcile", default=None,
                    help="a reconciliation YAML; its dispositions are rendered "
                         "under the findings they supersede")
    args = ap.parse_args(argv)

    path = Path(args.state)
    if not path.exists():
        sys.exit(f"no state file at {path}")
    state = yaml.safe_load(path.read_text(encoding="utf-8"))
    recon = None
    if args.reconcile:
        rp = Path(args.reconcile)
        if not rp.exists():
            sys.exit(f"no reconciliation file at {rp}")
        recon = yaml.safe_load(rp.read_text(encoding="utf-8"))
    text = render(state, path.name, recon)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {args.out} ({len(text):,} chars)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
