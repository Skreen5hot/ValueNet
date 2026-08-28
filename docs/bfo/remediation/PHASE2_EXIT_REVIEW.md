# Phase 2 Exit Review — Core Realization Pattern

**Phase:** 2 — Repair the Core Realization Pattern  
**Closed:** 2026-08-25  
**Finding closed:** ALN-002  
**Decision adopted:** D-001

## Outcome

Phase 2 is complete. The instance graph described by the annotation guide is now
enforced by SHACL, while the corresponding open-world process class is defined
in OWL. A conforming realization records an individual value, its agent bearer,
and that bearer as a participant in the realizing process.

## Implemented semantics

- Retained the verified BFO relations `BFO_0000196` (`bearer_of`),
  `BFO_0000197` (`inheres_in`), `BFO_0000057` (`has_participant`), and
  `BFO_0000055` (`realizes`).
- Defined `ValueRealizationProcess` as `bfo:process and bfo:realizes some
  ValueRelatedRealizableEntity` using `owl:equivalentClass`.
- Kept `ValueRealizationProcess` and `ValueViolationProcess` non-disjoint.
- Added closed-world SHACL checks that:
  - reject a value class IRI in the realized-individual position;
  - require a recorded bearer using either bearer relation direction;
  - require a recorded bearer to be typed as CCO `Agent`; and
  - require at least one recorded bearer to participate in the same process.
- Adopted existential handling for merged data with multiple recorded bearers;
  no functionality or maximum-cardinality axiom was added to BFO relations.
- Kept collective and group-level value bearing outside D-001.

The detailed rationale and multiple-bearer policy are recorded in
`PHASE2_DESIGN.md`.

## Regression controls

| Control | Expected | Result |
| --- | --- | --- |
| Single bearer participates in realization | Conforms | Pass |
| Bearer recorded with inverse `inheres_in` | Conforms | Pass |
| Multiple values have the same participant bearer | Conforms | Pass |
| Multiple recorded bearers include a participant | Conforms | Pass |
| One process realizes one value and contravenes another | Conforms | Pass |
| Bearer differs from every process participant | Violation with bearer/participant message | Pass |
| Realized value has no recorded bearer | Violation with missing-bearer message | Pass |
| Process realizes a value class IRI | Violation with class-IRI message | Pass |
| Process plus realization classifies as `ValueRealizationProcess` | Entailed under OWL RL | Pass |
| Realization and violation process classes are not disjoint | No disjointness assertion | Pass |

The three repaired ALN-002 tests were converted from strict expected failures to
ordinary regression tests. Each negative test asserts the intended SHACL report
message, so a violation caused by an unrelated constraint cannot close the
control accidentally.

## Validation evidence

### Focused Phase 2 controls

- 12 passed
- 3 expected failures, all explicitly reserved for ALN-003 / Phase 3
- Runtime: 4.48 seconds

### Full repository suite

- 490 passed
- 2 skipped
- 5 deselected
- 3 expected failures, all explicitly reserved for ALN-003 / Phase 3
- 9 existing RDFLib deprecation warnings
- Runtime: 157.32 seconds

### HermiT

| Scope | Files | Triples | Declared classes | Consistent | Unsatisfiable named classes |
| --- | ---: | ---: | ---: | --- | ---: |
| TBox | 7 | 2,512 | 282 | Yes | 0 |
| TBox plus scenario | 8 | 2,586 | 282 | Yes | 0 |

The additional declared class is the anonymous OWL intersection expression used
to define `ValueRealizationProcess`; it is not a new named project class.

## Exit criteria

- [x] The annotation guide's value–bearer–participant–process graph is enforced.
- [x] Valid single- and multiple-value patterns conform.
- [x] A process may realize one value and contravene another.
- [x] Mismatched bearer/participant data is rejected for the intended reason.
- [x] Missing bearer data is rejected for the intended reason.
- [x] Class IRIs used instead of value instances are rejected for the intended reason.
- [x] Defined-class classification is covered by an entailment regression.
- [x] Full-suite and HermiT gates pass.

## Deferred scope

The remaining three strict expected failures concern the subject, target, and
typing contract for `isEvidenceFor`. They are unchanged and form the negative
control set for Phase 3.
