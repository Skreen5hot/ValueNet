# BFO/CCO Alignment Remediation Plan

## Status

**In execution.** This plan converts the findings from the August 2026 BFO alignment review into sequenced, testable remediation work. It does not authorize changes to upstream BFO, CCO, RO, IAO, or SKOS artifacts.

## Execution Status

Execution started on 2026-08-24.

| Gate or phase | Status | Evidence |
| --- | --- | --- |
| Decisions D-001–D-004 | All adopted and implemented | `remediation/DECISION_RECORDS.md` |
| Phase 0 — Preserve and Measure the Baseline | Complete | `remediation/BASELINE_2026-08-24.md`; `tests/test_bfo_alignment_remediation.py` |
| Phase 1 — Authoritative Vocabulary Closure | Complete | `remediation/PHASE1_EXIT_REVIEW.md`; `imports/cco-valuenet-extract.ttl`; `tests/test_bfo_external_closure.py` |
| Phase 2 — Repair the Core Realization Pattern | Complete | `remediation/PHASE2_DESIGN.md`; `remediation/PHASE2_EXIT_REVIEW.md`; `valuenet-core-shapes.ttl`; `tests/test_bfo_alignment_remediation.py` |
| Phase 3 — Repair Evidence and Information Modeling | Complete | `remediation/PHASE3_DESIGN.md`; `remediation/PHASE3_EXIT_REVIEW.md`; `valuenet-moral-epistemics-scenario.ttl`; `tests/test_bfo_alignment_remediation.py` |
| Phase 4 — Rewrite and Validate Core Definitions | Complete | `remediation/PHASE4_DEFINITION_AUDIT.md`; `remediation/PHASE4_EXIT_REVIEW.md`; `tests/test_bfo_core_definitions.py` |
| Phase 5 — Normalize Mapping Semantics | Complete | `remediation/PHASE5_MAPPING_AUDIT.md`; `remediation/PHASE5_EXIT_REVIEW.md`; `tests/test_bfo_mapping_semantics.py` |
| Phase 6 — Refactor Moral Epistemics Categories | Complete | `remediation/PHASE6_CATEGORY_AUDIT.md`; `remediation/PHASE6_EXIT_REVIEW.md`; `tests/test_bfo_moral_epistemics_categories.py` |
| Phases 7–8 | Not started | Documentation/example repair begins in Phase 7 |

Phase 0 closed with two positive controls passing and six confirmed defects captured as strict expected failures. The full default suite after adding the controls reports 474 passed, 2 skipped, 5 deselected, and 6 expected failures.

Phase 1 pinned CCO 2.2, RO 2025-12-17, IAO 2026-03-30, and the W3C SKOS Recommendation. Artifact inspection found CCO ERO parents for the two informational input/output properties, replacing the earlier RO dependency. A 139-triple, checksum-verified CCO extract was generated reproducibly, passed the external-closure gate, and is now imported by the core module through an explicit version IRI.

Phase 2 made `ValueRealizationProcess` a defined class and added SHACL enforcement of the value-instance, recorded-bearer, and bearer-participant identity contract. All three ALN-002 expected failures are now ordinary passing regressions. The full suite reports 490 passed, 2 skipped, 5 deselected, and 3 expected failures reserved for Phase 3; both HermiT scopes are consistent with zero unsatisfiable named classes.

Phase 3 adopted D-004 and separated information-bearing carriers, exact textual representations, text spans, selectors, and evidence annotation records. The pinned CCO extract now supplies the authoritative Information Bearing Entity and Information Content Entity classes. SHACL enforces approved named evidence sources, BFO process targets, complete and bounded code-point offsets, source identity, and selected-substring equality. The full suite reports 505 passed, 2 skipped, 5 deselected, and no expected failures; both HermiT scopes remain consistent with zero unsatisfiable named classes.

Phase 4 rewrote every named core-class definition in genus-differentia form where needed, removed circular and weak value differentiae, documented the intended extension of all twelve core classes, and formalized D-001's value-related extension as exactly `ValueDisposition or ValueRole`. Automated controls sample one leaf from every folk-value cluster and separately cover the role and moral-disposition branches. The full suite reports 513 passed, 2 skipped, 5 deselected, and no expected failures; both HermiT scopes remain consistent with zero unsatisfiable named classes.

Phase 5 adopted D-003 and adjudicated all 71 canonical SKOS mapping assertions. Sixty-seven now use explicit project annotation properties and four narrower moral-epistemics universals now use verified CCO superclass axioms; no equivalence was asserted. Canonical SKOS mapping predicates are absent from BFO assertions, competency queries use the declared project mapping vocabulary, and profile controls report any ontology entity used in OWL individual position. The pinned CCO 2.2 extract now contains 324 triples under a distinct Phase 5 version IRI. The full suite reports 522 passed, 2 skipped, 5 deselected, and no expected failures; both HermiT scopes are consistent with zero unsatisfiable named classes.

Phase 6 removed the indefensible `InteriorMoralState` umbrella and recorded separate senses for intention, consent, culpability, evidence, and warrant. Assessment and observation acts, their descriptive information outputs, their aboutness targets, actual culpability as a BFO role, and evidential warrant are now distinct. CCO Act of Observation is included in the 330-triple pinned extract, discernment and rash judgment are no longer falsely disjoint, and the named overlap class remains satisfiable. The full suite reports 532 passed, 2 skipped, 5 deselected, and no expected failures; both HermiT scopes are consistent with zero unsatisfiable named classes.

## Objective

Bring the ValueNet BFO layer to a state that can be approved under the repository's strict ontology-engineering rules:

1. Every external IRI used by the suite is verified against a supplied, version-pinned authoritative source.
2. Every asserted BFO/CCO category and relation is semantically compatible with its source definition and axioms.
3. Core definitions are non-circular, genus-differentia definitions that pass clarity, inclusiveness, and exclusiveness review.
4. OWL axioms and SHACL constraints enforce the documented instance pattern, including the connection among a value, its bearer, and its realization process.
5. Information content, textual spans, physical or digital carriers, and annotation records remain ontologically distinct.
6. Mapping assertions have an explicit and consistent logical status.
7. Automated tests include negative controls capable of detecting each repaired defect.

## Scope

### In scope

- `valuenet-core.ttl` and its SHACL shapes.
- `valuenet-folk.ttl`.
- `valuenet-schwartz-values.ttl`.
- `valuenet-moral-foundations.ttl`.
- `valuenet-moral-epistemics.ttl`, its shapes, scenario, and competency questions.
- `valuenet-mappings.ttl`.
- BFO-layer documentation and examples.
- Version-pinned external ontology extracts needed to validate the above modules.
- Tests that validate the BFO layer.

### Out of scope unless separately authorized

- Editing the supplied `bfo-core.ttl` artifact.
- Editing upstream CCO, RO, IAO, or SKOS content.
- Reworking legacy DUL modules except where mapping verification requires inspection.
- Adding new value classes unrelated to an alignment finding.
- Broad cleanup of the trigger corpus.

## Governing Constraints

- Reuse verified BFO/CCO/RO terms before proposing project-local terms.
- Search the Extended Relation Ontology before retaining or adding any project-local object property.
- Do not infer CCO or RO semantics from labels or opaque identifiers.
- Do not use an external IRI unless its relevant source axioms are available in the repository's validation closure.
- Keep upstream artifacts immutable; place extracts and project axioms in clearly separated files.
- Do not use `owl:equivalentClass` or `owl:equivalentProperty` without extension-level identity or necessary-and-sufficient conditions.
- Treat every passing reasoner or SHACL result as meaningful only when a corresponding negative control can fail.

## Remediation Register

| ID | Priority | Finding | Primary artifacts | Exit condition |
| --- | --- | --- | --- | --- |
| ALN-001 | P1 | CCO, RO, and IAO terms are absent or represented by incomplete, unversioned stubs | `valuenet-core.ttl`, `valuenet-moral-epistemics.ttl`, `valuenet-folk.ttl` | Every external term resolves to a pinned source or documented MIREOT extract containing the required axioms |
| ALN-002 | P1 | The realization pattern does not ensure that the bearer of a realized value participates in the realizing process | `valuenet-core.ttl`, `valuenet-core-shapes.ttl` | Mismatched-bearer and missing-bearer negative controls fail validation |
| ALN-003 | P1 | `isEvidenceFor` shapes do not enforce the documented `TextSpan -> process` contract | `valuenet-core-shapes.ttl` | Untyped sources, non-span sources, untyped targets, and non-process targets fail validation |
| ALN-004 | P2 | Core value definitions are circular or use vague differentiae | `valuenet-core.ttl` | All core definitions pass documented clarity, inclusiveness, exclusiveness, and parent-alignment review |
| ALN-005 | P2 | Text content, textual representation, carrier, source document, and offsets are conflated | `valuenet-core.ttl`, shapes, annotation documentation | A reviewed ICE/IBE/concretization pattern is implemented and offsets are anchored to an exact representation |
| ALN-006 | P2 | **Closed in Phase 5.** SKOS mappings had no declared local semantics and conflicted with the suite's stated punning policy | `valuenet-mappings.ttl` and mapping assertions in other modules | Every mapping is explicitly annotation-only, conceptual, or logical; profile tests confirm the intended treatment |
| ALN-007 | P2 | `InteriorMoralState` groups ontologically ambiguous senses | `valuenet-moral-epistemics.ttl` | Intention, consent, culpability, and related senses have been separated or the umbrella has a defensible common parent and differentia |
| ALN-008 | P3 | Documentation incorrectly says class/individual punning is outside OWL 2 DL and contains non-self-contained Turtle snippets | `annotationGuide.md`, `Phase4_LinguisticGrounding.md`, `RefactorPlan.md` | Technical explanation is correct and every Turtle example parses with its displayed prefixes |

## Required Decisions Before Ontology Editing

These decisions materially affect the class model and must be recorded before implementation.

### D-001 — What counts as a value in the realist model?

Choose and document the intended extension of `ValueRelatedRealizableEntity`.

Questions:

- Are all modeled values necessarily realizable entities borne by agents?
- Are beliefs, goals, norms, and value concepts represented only as information content about values, rather than as values themselves?
- Are organizational or group-level values in scope?
- Can an artificial agent bear a value, or is the ontology restricted to human biological agents?

**Recommended default:** Retain the disposition/role architecture for agent-borne values, represent value concepts and normative statements as information content entities, and document group-level value bearing as out of scope until a verified CCO group model is added.

### D-002 — External ontology dependency strategy

Choose between:

1. Version-pinned imports of the necessary CCO/RO/IAO modules.
2. Version-pinned MIREOT extracts stored under `BFO/imports/`, with source ontology IRI, version IRI, retrieval date, and extraction manifest.

**Recommended default:** Use small, reproducible MIREOT extracts because the suite currently seeks a limited dependency footprint. An extract must include more than label and parent: include definition, superclass hierarchy to BFO, domain, range, inverse, superproperties, logical characteristics, and any restrictions required to interpret the term.

### D-003 — Mapping semantics

Decide whether mappings are:

- annotations between ontology entities,
- SKOS conceptual mappings between separate `skos:Concept` individuals, or
- formal OWL subclass/equivalence axioms.

**Recommended default:** Use annotation-only cross-references for lexical or historical correspondences. Use formal OWL axioms only after extension-level comparison. If canonical SKOS mappings are required, create a separate concept scheme rather than silently using OWL classes as SKOS individuals.

### D-004 — Text span identity

Decide what a `TextSpan` instance denotes:

- a piece of abstract linguistic content,
- a part of a particular textual information content entity,
- a region in one concrete carrier or serialization, or
- an annotation record identifying offsets in a source representation.

**Recommended default:** Model the span as information content tied to an exact textual representation/version; model the document carrier separately; put offsets on an annotation or selector entity whose source is that exact representation.

## Work Plan

## Phase 0 — Preserve and Measure the Baseline

**Execution status:** Complete on 2026-08-24.

### Tasks

1. Record current file hashes, triple counts, ontology IRIs, version IRIs, and import graph.
2. Record the current test and reasoner results without treating them as semantic approval.
3. Add executable negative-control fixtures for the defects already demonstrated:
   - value borne by Agent A but realized in a process whose only participant is Agent B;
   - realized value with no recorded bearer;
   - `isEvidenceFor` asserted by a non-`TextSpan`;
   - `isEvidenceFor` pointing to a non-process;
   - untyped evidence source and target;
   - class-to-class use of a property intended for individuals.
4. Confirm that each negative control passes under the current defective implementation, establishing that the new tests are capable of detecting the intended change.

### Deliverables

- Baseline validation report.
- Negative-control data fixtures.
- Tests marked as expected failures until the relevant phase is complete.

### Exit criteria

- The baseline is reproducible from a clean checkout.
- Each reported defect has at least one machine-executable reproducer.

## Phase 1 — Establish Authoritative Vocabulary Closure — Complete

**Execution status:** In progress. The initial external-term inventory is recorded in `remediation/EXTERNAL_TERM_INVENTORY.md`.

### Tasks

1. Select and record exact versions of CCO, the Extended Relation Ontology/RO, IAO or the CCO Information Entity Ontology, and SKOS where used normatively.
2. Create a term inventory for every external IRI used in logical or mapping positions.
3. For each external class, record:
   - label and definition;
   - asserted and inferred parents needed for BFO grounding;
   - relevant equivalence or restriction axioms;
   - source ontology and version.
4. For each external property, record:
   - label and definition;
   - domain and range;
   - inverse;
   - superproperty hierarchy;
   - transitivity, symmetry, functionality, or other characteristics;
   - source ontology and version.
5. Replace the ad hoc CCO Agent and RO input/output stubs with verified imports or complete MIREOT extracts.
6. Resolve `IAO_0000115`: either supply its authoritative declaration or remove the unverified subproperty assertion.
7. Verify CCO mapping targets used in moral epistemics before retaining their IRIs or labels.
8. Add an automated source-closure test that fails when a class or property used in a logical position lacks a declaration in the merged import closure.

### Relation review

After the source files are available, re-evaluate every project-local object property in this order:

1. `contravenes`
2. `isTextSpanOf`
3. `evokesFrame`
4. `hasInformationalInput`
5. `hasInformationalOutput`
6. `isWarrantedBy`

For each, document the closest ERO, CCO, BFO, or IAO property and why reuse, specialization, or a new project-local property is justified.

### Deliverables

- `BFO/imports/` or equivalent source directory.
- External-term manifest.
- Import/source-closure tests.
- Relation decision record.

### Exit criteria

- No external logical IRI is supported only by a label or comment.
- All external terms are traceable to an exact source version.
- The reasoner closure includes the relevant source axioms rather than partial, undocumented stand-ins.

## Phase 2 — Repair the Core Realization Pattern

### Tasks

1. Retain the verified BFO relations:
   - `BFO_0000196` bearer of;
   - `BFO_0000197` inheres in;
   - `BFO_0000057` has participant;
   - `BFO_0000055` realizes.
2. Add a SHACL constraint targeting every process that realizes a `ValueRelatedRealizableEntity`.
3. Require each realized value instance to have a recorded bearer or `inheres in` target.
4. Require at least one recorded bearer of that value to be a participant in the same process.
5. Decide and document how multiple bearers or collective realization are handled.
6. Decide whether `ValueRealizationProcess` should remain primitive or become a defined class equivalent to `process and realizes some ValueRelatedRealizableEntity`.
7. If equivalence is adopted, add entailment tests showing classification from the realization relation alone.
8. Keep `ValueRealizationProcess` and `ValueViolationProcess` non-disjoint unless contrary evidence justifies a change.

### Required tests

- Valid single-bearer realization passes.
- Multiple values borne by the same participant pass.
- A process realizing one value while contravening another passes.
- Mismatched bearer/participant fails.
- Missing bearer fails under the annotation validation profile.
- Realizing a class IRI rather than a value instance fails the annotation validation profile.

### Exit criteria

- The instance graph required by the annotation guide is enforced, not merely illustrated.
- All new negative controls fail for the intended reason.

## Phase 3 — Repair Evidence and Information Modeling

### Tasks

1. Add SHACL constraints enforcing:
   - the subject of `isEvidenceFor` is a `TextSpan` or another explicitly approved evidence class;
   - the object is a BFO process, normally a `ValueRealizationProcess` or `ValueViolationProcess`;
   - subject and target are named individuals when required by the annotation workflow.
2. Implement decision D-004 and separate:
   - information content entity;
   - information-bearing entity or carrier;
   - exact textual representation/version;
   - text span or selector;
   - annotation assertion or evidence record.
3. Replace the loose statement that a GDC is "borne" by an information-bearing entity with verified BFO/CCO dependency and concretization relations.
4. Review `isTextSpanOf` against BFO continuant parthood and CCO information-part relations. Reuse or specialize an existing property if its semantics fit.
5. Narrow the source range from all generically dependent continuants to the verified information-content class.
6. Anchor start/end offsets to one exact representation and specify encoding and indexing convention where interoperability requires it.
7. Add a constraint requiring both offsets together or neither, unless partial spans are an explicit use case.
8. Add a constraint ensuring the end offset does not exceed the source text length when the canonical text is present.
9. Update the worked scenario to exercise the carrier/content distinction.

### Exit criteria

- No example treats a physical/digital carrier and its information content as the same individual.
- Offsets remain meaningful when a document has multiple copies, renderings, or versions.
- `isEvidenceFor` domain and range violations are detected by SHACL.

## Phase 4 — Rewrite and Validate Core Definitions

### Tasks

1. Write a non-circular differentia for `ValueRelatedRealizableEntity` based on decision D-001.
2. Define `ValueDisposition` as a type of disposition using an internally grounded differentia, without saying merely that it "is a value."
3. Define `ValueRole` as a type of role using its externally grounded social or institutional context and normative realization conditions.
4. Rewrite `MoralValueDisposition` and `PersonalValueDisposition` to avoid vague "pertains to" clauses.
5. Align the stated genus in every definition with the asserted immediate parent.
6. Review every root definition using the following record:

| Check | Question |
| --- | --- |
| Clarity | Does the differentia identify one unambiguous kind of entity? |
| Inclusiveness | Does it include all intended value dispositions or roles? |
| Exclusiveness | Does it exclude ordinary dispositions and roles that are not values? |
| BFO category | Does the definition preserve continuant/occurrent and dependency distinctions? |
| Formal alignment | Do the OWL axioms express the same necessary conditions as the definition? |

7. Sample at least one leaf class from each folk-value cluster to confirm it remains a valid specialization of the revised core.

### Exit criteria

- No definition is circular, label-repeating, or dependent on "corresponds to," "pertains to," "related to," or similarly weak language without an explicit relation.
- The intended extension of each core class is documented and reviewable.

## Phase 5 — Normalize Mapping Semantics

**Execution status:** Complete on 2026-08-25. See `remediation/PHASE5_MAPPING_AUDIT.md` and `remediation/PHASE5_EXIT_REVIEW.md`.

### Tasks

1. Inventory every `skos:broadMatch`, `skos:closeMatch`, `skos:relatedMatch`, and any future `skos:exactMatch` assertion.
2. Classify each mapping as:
   - lexical/historical cross-reference;
   - conceptual mapping;
   - asserted subclass relation;
   - candidate equivalence;
   - insufficiently supported.
3. Apply decision D-003 consistently.
4. If mappings remain annotation-only, use a verified annotation vocabulary and ensure they create no unintended OWL individual layer.
5. If a SKOS concept scheme is adopted, mint separate concept individuals and explicitly link them to the OWL classes they denote or index.
6. Use `rdfs:subClassOf` only where the source and target are universals and extension inclusion is justified.
7. Use `owl:equivalentClass` only after necessary-and-sufficient comparison; lexical synonymy is not sufficient.
8. Add an OWL profile test and a test that reports every class IRI used in individual position.

### Exit criteria

- The mapping layer's logical status is explicit.
- No undocumented class/individual or property/individual punning remains.
- Queries no longer depend on accidental treatment of undeclared SKOS predicates.

## Phase 6 — Refactor Moral Epistemics Categories

**Execution status:** Complete on 2026-08-25. See `remediation/PHASE6_CATEGORY_AUDIT.md` and `remediation/PHASE6_EXIT_REVIEW.md`.

### Tasks

1. Create a sense table for:
   - intention;
   - act of intending;
   - consent as a mental state or disposition;
   - act of consenting;
   - consent record or assertion;
   - culpability ascription;
   - culpability or moral status;
   - evidence and warrant.
2. Assign each sense a verified BFO/CCO parent.
3. Determine whether `InteriorMoralState` has a genuine common differentia or should be removed in favor of separate classes.
4. Reuse CCO information-content and appraisal classes where definitions match; do not retain local duplicates merely to avoid an import.
5. Reassess `RashJudgmentAct owl:disjointWith MoralDiscernmentAct`. Test whether one larger cognitive process can contain or produce both warranted assessment and unwarranted ascription.
6. Distinguish acts, their outputs, the entities those outputs are about, and normative or epistemic status.
7. Re-run all competency questions and update them if the repaired categories change the intended graph pattern.

### Exit criteria

- Each modeled sense belongs to one defensible BFO category.
- A process is not classified as an information entity, role, quality, or state for lexical convenience.
- Existing CCO classes are reused where adequate.

## Phase 7 — Documentation and Example Repair

### Tasks

1. Correct the explanation of OWL 2 punning:
   - punning is permitted in OWL 2 DL;
   - the class and individual interpretations are semantically independent;
   - the instance pattern is required here because `realizes` relates particulars, not because all punning is outside OWL 2 DL.
2. Give every Turtle code block a complete, locally correct prefix block.
3. Use one prefix convention for BFO IRIs, preferably `obo:BFO_...`, matching the ontology files.
4. Update annotation examples to show:
   - a verified Agent;
   - a value instance borne by that Agent;
   - the same Agent participating in the realization process;
   - separate text content and carrier entities;
   - an evidence link whose source and target satisfy the new shapes.
5. Update `BFOizing ValueNet.md` so statements about beliefs, plans, intentions, and information content distinguish content from mental state and carrier.
6. Replace stale test counts in `RefactorPlan.md` and other reports with generated results or clearly dated snapshots.
7. Add a test that extracts and parses every Turtle example in BFO documentation.

### Exit criteria

- Documentation teaches exactly the graph pattern enforced by OWL and SHACL.
- Every displayed Turtle example parses independently.
- No documentation claim contradicts the selected OWL profile or supplied source ontology.

## Phase 8 — Integrated Verification and Release Gate

### Required validation sequence

1. Parse every `.ttl` file independently.
2. Resolve the local import closure without network access.
3. Verify that every logical class and property IRI is declared in that closure.
4. Verify namespace and ontology/version IRI consistency.
5. Run the OWL profile checker.
6. Run HermiT over the complete TBox closure.
7. Run HermiT with the scenario and all negative/positive ABox fixtures appropriate for open-world reasoning.
8. Run SHACL over the positive scenario.
9. Run every SHACL negative control and require the intended violation.
10. Run all competency questions with their declared scopes and expected polarity.
11. Run definition-quality review on the core classes and sampled leaf classes.
12. Confirm that no upstream ontology file was modified.

### Release acceptance criteria

- All ontology files parse independently.
- Import closure is complete, local, and version-pinned.
- No dangling logical IRIs.
- All BFO/CCO property uses are domain/range compatible.
- HermiT reports consistency and zero unsatisfiable project classes.
- Positive scenario conforms to SHACL except explicitly documented warnings.
- Every negative control produces its expected failure.
- All competency questions return their expected result polarity.
- No undocumented punning.
- No circular core definitions.
- Information content and carrier entities remain distinct in axioms and examples.
- The review findings ALN-001 through ALN-008 are closed with evidence.

## Recommended Execution Order

1. Approve D-001 through D-004.
2. Complete Phase 0 baseline and negative controls.
3. Complete Phase 1 authoritative vocabulary closure.
4. Repair core realization and evidence constraints in Phases 2 and 3.
5. Rewrite core definitions in Phase 4.
6. Normalize mappings in Phase 5.
7. Refactor moral epistemics in Phase 6.
8. Repair documentation in Phase 7.
9. Run the Phase 8 release gate and record a new alignment review.

Phases 2 through 6 must not finalize ontology terms before Phase 1 supplies the authoritative vocabulary needed to compare candidates.

## Completion Evidence Template

Each closed remediation item should record:

```yaml
finding_id: ALN-000
status: closed
decision_record: D-000
changed_artifacts: []
authoritative_sources:
  - ontology_iri: ""
    version_iri: ""
    local_artifact: ""
tests_added: []
positive_controls: []
negative_controls: []
reasoner_result: ""
shacl_result: ""
definition_review:
  clarity: pass
  inclusiveness: pass
  exclusiveness: pass
residual_risks: []
reviewer: ""
review_date: ""
```

## Definition of Done

The remediation is complete only when the ontology is not merely parseable and consistent, but when its source closure, definitions, axioms, validation constraints, mappings, examples, and competency questions all express the same reviewed BFO/CCO model.
