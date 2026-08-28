# Phase 6 Exit Review — Moral Epistemics Categories

Review date: 2026-08-25  
Phase: 6 — Refactor Moral Epistemics Categories

## Outcome

**Phase 6 is complete.** The moral-epistemics module now separates assessment and observation acts, their information-content outputs, the agents or conduct those outputs describe, evidential warrant, and actual normative status. The unsupported umbrella `InteriorMoralState` has been removed. Each retained modeled sense has a defensible BFO/CCO category, and ambiguous private mental-state senses remain explicitly out of scope rather than being forced beneath an overly broad continuant class.

The complete intention, consent, culpability, evidence, and warrant sense table is in `PHASE6_CATEGORY_AUDIT.md`.

## Category Decisions

| Sense | Phase 6 representation | Category basis |
| --- | --- | --- |
| Moral or safety assessment act | `MoralAssessmentAct` | Subclass of CCO Act of Appraisal (`ont00000636`) |
| Assessment output | `MoralAssessmentICE` | Subclass of CCO Descriptive ICE (`ont00000853`) |
| Culpability claim | `CulpabilityAscriptionICE` | Descriptive assessment ICE that describes an Agent |
| Actual culpability | `MoralCulpabilityRole` | BFO role (`BFO_0000023`) inhering in an Agent |
| Observation act | `ActOfBehavioralObservation` | Subclass of CCO Act of Observation (`ont00000037`) |
| Observation output | `BehavioralObservationICE` | Descriptive evidence ICE that describes an `AgentBehaviorProcess` |
| Evidential warrant | `isWarrantedBy` | Relation from a moral-assessment ICE to an observational-evidence ICE |
| Warranted assessment | `WarrantedMoralAssessmentICE` | Positive defined class: assessment and warranted by some observational evidence |

`CulpabilityAscriptionICE` deliberately has no existential restriction to `MoralCulpabilityRole`. An ascription can be false or unwarranted; merely recording the claim must not entail that a culpability-status individual exists. A true status is asserted independently as a role borne by the Agent.

`hasInformationalInput` and `hasInformationalOutput` now range over CCO Information Content Entity (`ont00000958`), rather than the broader BFO generically dependent continuant. This preserves the act/output category boundary throughout the module.

## `InteriorMoralState` and Unmodeled Senses

`InteriorMoralState` was removed because intention, consent, culpability, evidence, and warrant have no single defensible common differentia:

- plans, permission contents, records, and ascriptions are information content;
- planning, consenting, observing, and assessing are processes;
- a propensity to consent is a disposition;
- actual culpability is treated as an externally grounded role; and
- private cognitive attitudes lack an adequate class in the supplied BFO/CCO sources.

The ontology therefore does not mint a generic intention or consent “state.” The audit records verified CCO reuse candidates for plan content, planning, planned acts, declarative and commissive communication, and action permission. They will enter the logical closure only if those senses become modeled requirements.

## Discernment and Rash Judgment

The former disjointness between `MoralDiscernmentAct` and `RashJudgmentAct` was removed. Both are moral-assessment acts, and a larger process can intelligibly produce both:

- a warranted `SafetyAssessmentICE`; and
- an unwarranted `CulpabilityAscriptionICE`.

`MixedMoralAssessmentAct` is explicitly a subclass of both. Its satisfiability is therefore checked directly by HermiT rather than inferred merely from the absence of a disjointness axiom.

OWL states the positive class and output conditions. It does not use a complement to treat missing warrant triples as negative facts. SHACL enforces that a `RashJudgmentAct` has at least one culpability-ascription output with no recorded `isWarrantedBy` value.

## CCO Closure Revision

| Field | Phase 6 value |
| --- | --- |
| Source | CCO 2.2 merged release at commit `0bc7d33e1bc09fd4693366119ab4e03cb0340042` |
| Added logical root | Act of Observation (`ont00000037`) |
| Extract version IRI | `https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-25-phase6` |
| Generator | `BFO/remediation/generate_cco_extract.py`, version 4 |
| Triples | 330 |
| SHA-256 | `70add8bd654ede359575e1fdd3e1beac7b39fc09775d3c8474f8272e8896b421` |

The source release, source checksum, attribution, BSD-3-Clause license, and recursive selected-closure policy are unchanged. The manifest and source-selection record identify the expanded artifact.

An independent regeneration into a fresh temporary directory produced the same byte-level SHA-256 as the workspace artifact.

## SHACL, Scenario, and Competency Questions

The moral-epistemics shapes now require:

1. every moral-assessment act to produce a `MoralAssessmentICE`;
2. every behavioral-observation record to describe an `AgentBehaviorProcess`;
3. every culpability ascription to describe a CCO Agent; and
4. every rash judgment to produce at least one culpability ascription without a recorded warrant.

The supplied scenario conforms with warnings allowed. Its rash culpability ascription produces the expected warning because it records no evidential warrant. Three deliberately invalid fixtures prove that the required observed process, described Agent, and unwarranted rash output are enforced. A positive mixed-assessment fixture with warranted and unwarranted outputs conforms.

All six moral-epistemics competency questions pass. CQ2 now joins assessment and observation outputs through CCO `describes` to the same conduct. CQ3 returns the Agent described by the unwarranted culpability ascription. The recorded asserted-graph scopes are 1,604 triples for CQ1–CQ5 and 11,769 triples for CQ6 with its two MFTriggers files.

## Automated Controls

`tests/test_bfo_moral_epistemics_categories.py` adds ten Phase 6 controls:

1. the obsolete umbrella class is absent;
2. acts, outputs, targets, status, input/output ranges, and warrant domain have the intended categories;
3. a culpability ascription describes an Agent without entailing a culpability role;
4. OWL RL classifies a positively warranted assessment;
5. discernment/rash disjointness is absent and the named overlap class has both parents;
6. the scenario conforms with its expected warning;
7. an observation record missing its observed process fails;
8. an ascription that does not describe an Agent fails;
9. a rash judgment with only warranted ascriptions fails; and
10. a mixed assessment with warranted and unwarranted outputs conforms.

The Phase 5 alignment regression was also generalized to follow named subclass paths. This preserves the four reviewed CCO extension-inclusion decisions after Phase 6 introduced the intermediate `MoralAssessmentAct`, `MoralAssessmentICE`, and warranted-assessment classes.

## Verification Results

### Focused Phase 6 suite

Scope: Phase 6 category controls, CCO extract, external closure, mapping semantics, and competency questions, with slow tests deselected.

Result: **57 passed, 1 deselected in 41.59 seconds**.

### Full repository suite

Result: **532 passed, 2 skipped, 5 deselected, 9 warnings in 172.24 seconds**.

The warnings are the existing RDFLib `Dataset.default_context` deprecations exercised by ontology-source negative controls.

### HermiT

| Scope | Files | Triples | Declared classes | Consistent | Unsatisfiable named classes |
| --- | ---: | ---: | ---: | --- | ---: |
| TBox | 7 | 2,804 | 306 | Yes | 0 |
| TBox plus scenario | 8 | 2,897 | 306 | Yes | 0 |

Because `MixedMoralAssessmentAct` is a named subclass of both discernment and rash judgment, the zero-unsatisfiable result directly covers the repaired overlap.

## Exit Criteria

- [x] Every retained modeled sense has a defensible BFO/CCO category.
- [x] No process is classified as information content, role, quality, or state for lexical convenience.
- [x] Acts, outputs, aboutness targets, evidential warrant, and normative status are distinct.
- [x] `InteriorMoralState` is removed because it lacks a genuine common differentia.
- [x] Adequate CCO observation, appraisal, and information-content classes and relations are reused.
- [x] The discernment/rash overlap is represented without false OWL negation and is satisfiable.
- [x] All six competency questions pass with the repaired graph pattern.
- [x] Focused tests, full regression tests, and both reasoner scopes pass.

## Residual Boundaries

- Private intention and consent attitudes remain unmodeled until an authoritative mental-functioning ontology and intended identity criteria are supplied.
- `MoralCulpabilityRole` records the selected externally grounded account of actual culpability; applications using culpability as a relational quality would require a separately approved domain commitment.
- Absence of recorded warrant is intentionally a SHACL/query criterion, not an OWL entailment under the open-world assumption.
- Documentation-wide example repair and historical count cleanup remain assigned to Phase 7.
