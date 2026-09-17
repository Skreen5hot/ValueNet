# Open items

What is known to be unfinished or deliberately left, in one place. Living document: items are added when they are found and moved to the log below when they close.

**This document is checked, not trusted.** `tests/bfo/test_open_items.py` re-derives what can be re-derived: every path named here exists, every decision named here exists and has its reopen condition, and every figure in the table matches what the tools measure now. An item that has been fixed fails the test until it is moved to the log, and a figure that moves fails it until the row is updated. Three things the test cannot check are marked *unchecked* in the table, and each says why.

This supersedes the open half of `docs/bfo/remediation/OPEN_ISSUES_PROPOSALS_2026-09-16.md`, which stays as the record of what was proposed on that date. O1 to O4 there are done.

## Open

| id | item | where | what would close it |
|---|---|---|---|
| OI-1 | The evidence measure `bfo_layer_classes` is defined as "named classes in the HermiT scope" and counts anonymous class expressions too. Formerly O5 | `tools/marep/build_semantic_baseline.py` | Correct the definition to say named and anonymous, bump `TOOL_VERSION`, and regenerate the evidence in the same commit. Counting named classes only would change every earlier record's figure |
| OI-2 | The competency-question document gives corpus sizes as of 2026-08-25. Both moved in phases C to E. Neither is checked. Formerly O6 | `ontology/bfo/extensions/moral-epistemics/valuenet-moral-epistemics-CQ.md` | Drop the counts and keep the list of files each query loads. `tests/integration/test_competency_questions.py` already runs every query |
| OI-3 | Stale worktree records under `.git/worktrees`, which `git worktree prune` cannot remove while OneDrive holds file locks. *Unchecked:* machine state, not repository content | the working copy | Pause OneDrive sync, prune, resume. Longer term, keep the working copy outside a synced folder |
| OI-4 | `TextualRepresentation` and `TextSpan` reach none of the explorer's four category roots, so the class index files them under "other". Standing decision: no change. Formerly O8 | `tools/site/build_class_index.py`, `docs/bfo/remediation/OPEN_ISSUES_PROPOSALS_2026-09-16.md` | A later module adding more form-level classes, which would make a fifth category worth its cost |
| OI-5 | 38 `rdfs:seeAlso` back-links in the folk module name a folk value the corpus does not have. A link that reads as provenance and resolves to nothing is worse than no link | `ontology/bfo/core/valuenet-folk.ttl`, reported by `tools/bfo/folk_coverage.py` | Repoint or remove each one, and lower `DANGLING_BACK_LINKS` in `tests/bfo/test_folk_coverage.py` in the same commit |
| OI-6 | 37 corpus values have a trigger lexicon and no class in `folk.ttl`, so the annotation pipeline can evoke a value the ontology cannot express. This is a defect in the upstream corpus, not in the BFO layer | `ThatsAllFolks/`, reported by `tools/bfo/folk_coverage.py` | A decision on each under D-014's M1–M7, or a recorded reason to leave the corpus as it is |
| OI-7 | Consent, intention and the other private attitudes Phase 6 unbundled are still unmodelled, on purpose | `docs/bfo/remediation/PHASE6_EXIT_REVIEW.md`, D-014 item 11 | An authoritative mental-functioning ontology with identity criteria, or a recorded competency question that needs the distinction. D-014 names `ConsentDisposition` as the case to watch |
| OI-8 | Two folk classes sit under a Schwartz value the corpus itself does not place them under: `CreativityDisposition` is under Stimulation where the corpus says Self-Direction, and `RespectDisposition` is under Universalism where the corpus says Conformity. The first stays inside openness to change; the second crosses from self-transcendence to conservation | `ontology/bfo/core/valuenet-folk.ttl`, `ThatsAllFolks/folk.ttl` | A decision on each, either way, recorded with its reason. Placement follows the class's definition, not the corpus's grouping, so agreeing with the corpus is not automatic |
| OI-9 | `ThatsAllFolks/MFRC_1k_ESWC.zip` is deliberately not remediated, and its digest is recorded so that it can be seen not to have changed. Standing decision | `config/remediation-record.json` | Nothing. It would reopen only if the archive had to be read or rewritten |

## Conditions that would reopen a decision

Each decision in `docs/bfo/remediation/DECISION_RECORDS.md` ends with "Reopen when". They are triggers rather than work, and are not repeated here. The ones most likely to fire:

- **D-014** — a competency question that needs `ImpactDisposition`, `DiscretionDisposition`, `ResourcefulnessDisposition` or a `ConsentDisposition`; a reviewer disagreeing with M1–M7; or the folk corpus being re-imported.
- **D-005 and D-011** — a competency question needing text that is at once form and content.
- **D-013** — a revision of RULES 2.0, or a term category outside classes and properties.
- **D-001** — organizational values, or artificial agents bearing values.

## Closed

| id | item | closed |
|---|---|---|
| O1 | The explorer tests needed the pinned Node | 2026-09-17. Node 24.20.0, verified against nodejs.org's SHA-256, is kept in a per-project folder under Local AppData and put on PATH for the process that needs it. The machine's Node is untouched |
| O2 | The public-content sign-off predated the remediation | 2026-09-17. Re-signed against `dda2b84`, after the fresh-clone check was fixed so that it no longer runs the tests of the record it replaces |
| O3 | The reviewer had not seen the decisions taken after their sign-off | 2026-09-17. They confirmed it and accepted D-011 and D-014 as breaking (`docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF_2.md`) |
| O4 | The remediation branch was unpushed | 2026-09-17. Merged to `main` as `8e39b2a` through pull request 1, and deployed |
| R15–R18 | Folk membership was undecided, so folk curation was blocked | 2026-09-17. D-014 decided membership; the curation pass then took the genus and annotation gates to zero in every module |
