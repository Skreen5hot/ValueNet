# Phase 5 Exit Review — Mapping Semantics

Review date: 2026-08-25  
Finding: ALN-006  
Decision: D-003

## Outcome

**Phase 5 is complete.** All 71 pre-remediation SKOS mapping assertions were inventoried and adjudicated. The BFO modules now contain 67 explicitly annotation-only correspondences and four reviewed universal-to-universal CCO superclass axioms. They contain no canonical SKOS mapping assertions and no undocumented class/individual or property/individual punning.

## Mapping Disposition

| Original assertions | Count | Final representation | Count |
| --- | ---: | --- | ---: |
| `skos:broadMatch` | 60 | `vn-core:hasBroaderConceptualMatch` | 45 |
|  |  | `vn-core:historicallyCorrespondsTo` | 15 |
| `skos:closeMatch` | 6 | `rdfs:subClassOf` to verified CCO class | 4 |
|  |  | `vn-core:historicallyCorrespondsTo` | 2 |
| `skos:relatedMatch` | 5 | `vn-core:hasRelatedConceptualMatch` | 5 |
| **Total** | **71** | Annotation-only / logical | **67 / 4** |

No `skos:exactMatch`, `skos:narrowMatch`, or candidate equivalence assertion existed. No mapping was promoted to `owl:equivalentClass` or `owl:equivalentProperty` because necessary-and-sufficient extension identity was not established.

The complete inventory, including every folk, Schwartz, Haidt, Curry, ValueCore, property, and CCO assertion, is in `PHASE5_MAPPING_AUDIT.md`.

## Implemented Semantic Changes

### Annotation-only mapping vocabulary

`valuenet-core.ttl` now declares:

- `vn-core:ontologyEntityMapping`;
- `vn-core:hasBroaderConceptualMatch`;
- `vn-core:hasRelatedConceptualMatch`; and
- `vn-core:historicallyCorrespondsTo`.

Each is an `owl:AnnotationProperty`; the three concrete predicates are subproperties of `ontologyEntityMapping`. They have no OWL domain/range, are absent from restrictions, and assert no class, property, or individual identity.

### Reviewed logical alignments

Four former CCO `skos:closeMatch` assertions now state justified extension inclusion:

| ValueNet universal | CCO parent | Inclusion basis |
| --- | --- | --- |
| `me:ObservationalEvidenceICE` | Descriptive Information Content Entity (`ont00000853`) | Every instance records—and therefore describes—what was perceptually available |
| `me:SafetyAssessmentICE` | Descriptive Information Content Entity (`ont00000853`) | Every instance describes a risk |
| `me:MoralNormICE` | Prescriptive Information Content Entity (`ont00000965`) | Every instance prescribes conduct |
| `me:MoralDiscernmentAct` | Act of Appraisal (`ont00000636`) | Every instance evaluates or assesses conduct and risk |

The local definitions were revised to state the imported genus. Equivalence was rejected because each CCO parent has a broader extension than the ValueNet child.

### Pinned closure revision

| Field | Phase 5 value |
| --- | --- |
| Source | CCO 2.2 merged release at commit `0bc7d33e1bc09fd4693366119ab4e03cb0340042` |
| Extract version IRI | `https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-25-phase5` |
| Generator | `BFO/remediation/generate_cco_extract.py`, version 3 |
| Triples | 324 |
| SHA-256 | `f255212d6b5ec905f84c961909589bf44017ed977d6fc5bafa7504d783840838` |

The expanded extract includes complete selected descriptions and recursive logical dependencies for Act of Appraisal, Descriptive ICE, and Prescriptive ICE. It preserves the pinned source release, checksum, attribution, and license.

## Query and Documentation Repairs

- Moral epistemics CQ6 now follows `vn-core:historicallyCorrespondsTo` from a BFO disposition to a legacy Haidt value.
- The redundant-mapping sanity query now compares `vn-core:hasBroaderConceptualMatch` with `rdfs:subClassOf`.
- Core comments, the scenario, annotation guide, linguistic-grounding guide, BFO overview, and folk integration plan no longer instruct consumers to use canonical SKOS mappings directly on OWL classes.
- Queries therefore do not depend on an undeclared SKOS mapping predicate or on class-as-individual treatment.

## Automated Controls

`tests/test_bfo_mapping_semantics.py` adds nine Phase 5 controls:

1. canonical SKOS mapping predicates have no assertions;
2. annotation counts are exactly 45 broader, 5 related, and 17 historical;
3. each project mapping predicate is annotation-only and has ontology-entity subjects and IRI objects;
4. the four CCO promotions are subclass rather than equivalence axioms;
5. class, object-property, datatype-property, and annotation-property declaration sets do not overlap;
6. every restriction property is a declared logical property;
7. every class IRI used in individual position is reported;
8. every property IRI used in individual position is reported; and
9. a synthetic negative control proves that the individual-position reporter detects a class used as an object-property assertion subject.

The external-closure test now treats the project mapping predicates as mapping-only annotations, loads `valuenet-mappings.ttl`, and requires the three newly logical CCO targets to be declared in the authoritative closure.

## Verification Results

### Focused Phase 5 suite

Command scope:

- `tests/test_bfo_mapping_semantics.py`
- `tests/test_bfo_external_closure.py`
- `tests/test_bfo_cco_extract.py`
- `tests/test_competency_questions.py`
- slow tests deselected

Result: **47 passed, 1 deselected in 8.21 seconds**.

### Full repository suite

Result: **522 passed, 2 skipped, 5 deselected, 9 warnings in 149.74 seconds**.

The nine warnings are the existing RDFLib `Dataset.default_context` deprecation warnings exercised by ontology-source negative controls.

### HermiT — TBox closure

| Metric | Result |
| --- | ---: |
| Files | 7 |
| Triples | 2,762 |
| Declared classes | 302 |
| Consistency | Consistent |
| Unsatisfiable named classes | 0 |

### HermiT — TBox plus scenario

| Metric | Result |
| --- | ---: |
| Files | 8 |
| Triples | 2,852 |
| Declared classes | 302 |
| Consistency | Consistent |
| Unsatisfiable named classes | 0 |

## Exit Criteria

- [x] The mapping layer's logical status is explicit.
- [x] Every pre-remediation SKOS mapping assertion has a recorded disposition.
- [x] No canonical SKOS mapping property is asserted on OWL entities.
- [x] No undocumented class/individual or property/individual punning remains in the tested ontology scope.
- [x] Formal subclass axioms are limited to reviewed universal inclusion.
- [x] No equivalence was asserted from lexical similarity.
- [x] Queries use declared project annotations rather than accidental SKOS predicates.
- [x] Focused tests, full regression tests, and both reasoner scopes pass.

## Finding Closure Record

```yaml
finding_id: ALN-006
status: closed
decision_record: D-003
changed_artifacts:
  - BFO/valuenet-core.ttl
  - BFO/valuenet-folk.ttl
  - BFO/valuenet-moral-foundations.ttl
  - BFO/valuenet-moral-epistemics.ttl
  - BFO/valuenet-mappings.ttl
  - BFO/imports/cco-valuenet-extract.ttl
  - BFO/imports/cco-valuenet-extract.manifest.json
  - BFO/remediation/generate_cco_extract.py
  - BFO/remediation/PHASE5_MAPPING_AUDIT.md
  - tests/test_bfo_mapping_semantics.py
authoritative_sources:
  - ontology_iri: https://www.commoncoreontologies.org/cco
    version: v2.2
    source_commit: 0bc7d33e1bc09fd4693366119ab4e03cb0340042
    local_artifact: BFO/imports/cco-valuenet-extract.ttl
  - specification: W3C SKOS Reference
    version: 2009-08-18 Recommendation
tests_added:
  - tests/test_bfo_mapping_semantics.py
positive_controls:
  - exact 67 annotation / 4 subclass disposition
  - four declared CCO superclass targets
negative_controls:
  - canonical SKOS assertion rejection
  - synthetic class-in-individual-position detection
reasoner_result: consistent; zero unsatisfiable named classes in TBox and scenario scopes
shacl_result: unchanged; full suite passes
residual_risks:
  - conceptual mappings remain deliberately non-logical until separately reviewed for extension inclusion
  - consumers requiring canonical SKOS must introduce distinct skos:Concept individuals and an explicit concept scheme
reviewer: Codex
review_date: 2026-08-25
```

