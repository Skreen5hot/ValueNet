# Open items

What is known to be unfinished or deliberately left, in one place, ordered by what should be done next. Living document: items are added when they are found, and moved to the log when they close.

Four kinds of thing were mixed together in the first version of this register, which made the backlog look larger than it is. They are separated here:

- **Work** — P0, then P1, then P2. Ontology and evidence work with a defined end state.
- **Operational** — machine housekeeping, not ontology.
- **Accepted and deferred** — deliberate limits of scope. Not work; each says what would reopen it.

**This document is checked, not trusted.** `tests/bfo/test_open_items.py` re-derives what can be re-derived: every path named here exists, every decision named here exists and keeps its reopen condition, and every figure matches what the tools measure now. An item that has been fixed fails the test until it moves to the log; a figure that moves fails it until the row is updated. Items the repository cannot check are marked *unchecked* with a reason, and that marking is checked too.

This supersedes the open half of `docs/bfo/remediation/OPEN_ISSUES_PROPOSALS_2026-09-16.md`, which stays as the record of what was proposed on that date.

## P0 — next

| id | item | where | what would close it |
|---|---|---|---|
| OI-8 | Two folk classes sit under a Schwartz value the corpus itself does not place them under: `CreativityDisposition` under Stimulation where the corpus says Self-Direction, and `RespectDisposition` under Universalism where the corpus says Conformity. The only remaining item that changes subsumption | `ontology/bfo/core/valuenet-folk.ttl`, `ThatsAllFolks/folk.ttl` | A decision record carrying both moves. The recommendation on the table: Creativity to `schwartz-values:SelfDirectionDisposition`, whose defining goal is independent thought and action and whose items include creativity, with a related match to Stimulation if the novelty link is worth keeping; Respect to `core:PersonalValueDisposition`, because no single Schwartz value covers regard for others' feelings, wishes, rights *and* traditions, with annotation-only matches to the Schwartz values it overlaps. Definitions decide subsumption; corpus grouping and survey items decide mappings |
| OI-5 | 38 `rdfs:seeAlso` back-links in the folk module name a folk value the corpus does not have. Public provenance links that resolve to nothing are actively misleading | `ontology/bfo/core/valuenet-folk.ttl`, reported by `tools/bfo/folk_coverage.py` | Repoint a link only where the target is demonstrably the source entity the class derives from; otherwise remove it. A merely similar corpus term is a mapping under D-014, not provenance. Lower `DANGLING_BACK_LINKS` in `tests/bfo/test_folk_coverage.py` in the same commit |

## P1 — soon

| id | item | where | what would close it |
|---|---|---|---|
| OI-10 | No machine-readable migration manifest. Consumers have to reconstruct six breaking changes from decision records: removed IRIs, the renamed text property, changed parents, new disjointness, and the CCO replacements, each with its replacement or an explicit "none" | `docs/bfo/remediation/DECISION_RECORDS.md` today | A generated manifest listing every breaking change with its replacement, checked against the decision records, and published with the downloads |
| OI-11 | No semantic-diff release gate. The evidence ledger records what changed during this remediation; nothing protects the next release. An unrecorded change to `subClassOf`, equivalence, disjointness, domain or range, the property hierarchy or imports would pass CI | `tools/marep/`, `.github/workflows/pages.yml` | A gate comparing the previous release with the candidate, failing when a semantic change is absent from the migration manifest or a decision record |
| OI-13 | Every module still declares `owl:versionIRI …/1.0/…` after six breaking changes, there is no release tag, and the downloads carry no release identifier. Version drift is expensive once consumers exist | the five module files, `config/quality-report.json`, the site's downloads page | A release identity: version IRIs, a signed-off tag, the downloads and the site's release label all naming the same release, and a check that they agree |
| OI-14 | Nine corpus values that D-014 excludes still carry trigger lexicons, so the annotation pipeline can fire on a value the BFO layer deliberately does not represent: Anticipation, BadHealth, Feasibility, Ferocious, Happyness, LifeIsMeaningless, Management, OtherPeopleCannotBeTrusted, Willingness | `ThatsAllFolks/`, `tools/bfo/folk_coverage.py` | A pipeline decision: either keep the upstream annotation and mark it deliberately unmapped, or suppress those triggers in BFO-aligned output. Not a reason to mint classes |
| OI-1 | The evidence measure `bfo_layer_classes` is defined as "named classes in the HermiT scope" and counts anonymous class expressions too. Formerly O5 | `tools/marep/build_semantic_baseline.py` | Correct the definition to say named and anonymous, bump `TOOL_VERSION`, and regenerate the evidence in the same commit. Counting named classes only would change every earlier record's figure |
| OI-2 | The competency-question document gives corpus sizes as of 2026-08-25. Both moved in phases C to E, and neither is checked. Formerly O6 | `ontology/bfo/extensions/moral-epistemics/valuenet-moral-epistemics-CQ.md` | Drop the counts and keep the list of files each query loads. `tests/integration/test_competency_questions.py` already runs every query |

## P2 — when convenient

| id | item | where | what would close it |
|---|---|---|---|
| OI-12 | Nothing stops a new local object property being added where CCO or ERO has one. D-013 requires a CCO search for classes; properties have no equivalent guard, which is how `hasInformationalInput` happened | `tools/bfo/`, `tests/bfo/` | A check that each authored object property names a decision record or an explicit reuse justification |

## Operational

| id | item | where | what would close it |
|---|---|---|---|
| OI-3 | Stale worktree records under `.git/worktrees`, which `git worktree prune` cannot remove while OneDrive holds file locks. *Unchecked:* machine state, not repository content. Not ontology work | the working copy | Pause OneDrive sync, prune, resume. Longer term, keep the working copy outside a synced folder |

## Accepted and deferred — not work

| id | item | where | what would reopen it |
|---|---|---|---|
| OI-4 | `TextualRepresentation` and `TextSpan` reach none of the explorer's four category roots, so the class index files them under "other", which is accurate. Formerly O8 | `tools/site/build_class_index.py` | A later module adding more form-level classes, which would make a fifth category worth its cost |
| OI-7 | Consent, intention and the other private attitudes Phase 6 unbundled are unmodelled, on purpose | `docs/bfo/remediation/PHASE6_EXIT_REVIEW.md`, D-014 item 11 | An authoritative mental-functioning ontology with identity criteria, or a recorded competency question that needs the distinction. D-014 names `ConsentDisposition` as the case to watch |
| OI-9 | `ThatsAllFolks/MFRC_1k_ESWC.zip` is deliberately not remediated, and its digest is recorded so that it can be seen not to have changed | `config/remediation-record.json` | Nothing to do. It would reopen only if the archive had to be read or rewritten |

## Conditions that would reopen a decision

Each decision in `docs/bfo/remediation/DECISION_RECORDS.md` ends with "Reopen when". They are triggers rather than work, and are not repeated here. The ones most likely to fire:

- **D-014** — a competency question that needs `ImpactDisposition`, `DiscretionDisposition`, `ResourcefulnessDisposition` or a `ConsentDisposition`; a reviewer disagreeing with M1–M7; or the folk corpus being re-imported.
- **D-005 and D-011** — a competency question needing text that is at once form and content.
- **D-013** — a revision of RULES 2.0, or a term category outside classes and properties.
- **D-001** — organizational values, or artificial agents bearing values.

## Closed

| id | item | closed |
|---|---|---|
| OI-6 | "37 corpus values have a trigger lexicon and no class in `folk.ttl`" was written against the pre-D-014 invariant, which assumed a corpus value needs its own class | 2026-09-17. D-014 replaced that invariant: a value is carried by an exact class, an alternative label, a correspondence, or an explicit exclusion. Restated as reachability — every value with a trigger lexicon reaches a BFO-aligned class or is excluded — it already holds: of the 37, seven have an exact class, one is an alternative label, 27 reach one through a mapping, and two are excluded. Pinned by `test_every_value_with_a_trigger_lexicon_is_reachable_or_excluded` in `tests/bfo/test_folk_coverage.py`. The residue, excluded values that still carry lexicons, is OI-14 |
| O1 | The explorer tests needed the pinned Node | 2026-09-17. Node 24.20.0, verified against nodejs.org's SHA-256, is kept in a per-project folder under Local AppData and put on PATH for the process that needs it. The machine's Node is untouched |
| O2 | The public-content sign-off predated the remediation | 2026-09-17. Re-signed against `dda2b84`, after the fresh-clone check was fixed so that it no longer runs the tests of the record it replaces |
| O3 | The reviewer had not seen the decisions taken after their sign-off | 2026-09-17. They confirmed it and accepted D-011 and D-014 as breaking (`docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF_2.md`) |
| O4 | The remediation branch was unpushed | 2026-09-17. Merged to `main` as `8e39b2a` through pull request 1, and deployed |
| R15–R18 | Folk membership was undecided, so folk curation was blocked | 2026-09-17. D-014 decided membership; the curation pass then took the genus and annotation gates to zero in every module |
