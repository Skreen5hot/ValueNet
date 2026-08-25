# Phase 4 Exit Review — Core Definitions

**Phase:** 4 — Rewrite and Validate Core Definitions  
**Closed:** 2026-08-25  
**Finding closed:** ALN-004  
**Decision basis:** D-001

## Outcome

Phase 4 is complete. The core value definitions no longer define a value by
saying that it “is a value,” “corresponds to” a value, or “pertains to” a topic.
Each named core class now has one reviewable English definition whose genus
matches an asserted immediate or nearest parent and whose differentia preserves
the relevant BFO category.

The complete clarity, inclusiveness, exclusiveness, category, intended-extension,
and formal-alignment record is in `PHASE4_DEFINITION_AUDIT.md`.

## Definition changes

- `ValueRelatedRealizableEntity` now uses agent inherence, characteristic
  realization, and a standing evaluative orientation as its non-circular
  differentia.
- `ValueDisposition` is defined as a BFO disposition with an internally grounded
  evaluative realization differentia.
- `ValueRole` is defined as a BFO role grounded in a contingent social or
  institutional circumstance whose realization exemplifies conduct evaluated
  as good, right, or worthy for that circumstance.
- `MoralValueDisposition` is distinguished through characteristic realization
  that appraises or governs conduct as right, wrong, obligatory, permitted, or
  forbidden.
- `PersonalValueDisposition` is distinguished through trans-situational
  selection or pursuit of preferred ends or means; “personal” does not mean
  exclusively self-regarding.
- Process definitions now state the same relations used by their equivalent-
  class axioms.
- Phase 3 information-class definitions were reconciled with their nearest
  asserted genera, especially `TextSpan` and `ValueEvidenceAnnotation` under
  `EvidenceSource`.
- Inconsistent capitalization in the five root value labels was normalized.

## Formal alignment

D-001's approved extension is now explicit:

`ValueRelatedRealizableEntity ≡ ValueDisposition or ValueRole`.

The existing `inheres in some cco:Agent` restriction remains in force. BFO's
disjointness of disposition and role preserves the internally/externally
grounded distinction. `MoralValueDisposition` and `PersonalValueDisposition`
remain non-disjoint because a disposition may satisfy both differentiae.

The supplied vocabulary contains no verified relation for “has standing
evaluative orientation” or “treats as morally obligatory.” Phase 4 therefore
did not invent an object property or reify an underspecified mental/information
entity. The domain differentiae remain controlled natural language while the
verified BFO categories, bearer restriction, exhaustive extension, and process
relations are formalized.

## Automated controls

`tests/test_bfo_core_definitions.py` verifies:

- exactly twelve named project classes in the core and exactly one English
  definition for each;
- the expected genus prefix for every definition;
- absence of circular or weak phrases including `corresponds to`, `pertains to`,
  `related to`, `associated with`, and `is a value`;
- the exact disposition/role union;
- BFO disposition, role, realizable-entity, and CCO Agent alignment;
- agreement between process definitions and equivalent-class restrictions;
- continued non-disjointness of moral and personal dispositions;
- one asserted leaf from each of twelve folk-value clusters;
- a folk value-role specialization; and
- a moral-foundation disposition specialization.

## Leaf sampling

The following current leaves all retain paths to
`ValueRelatedRealizableEntity` and BFO disposition:

- Kindness, Diligence, Charity, Candor, Cleanliness, Privacy;
- Mindfulness, Equity, Status, Exploration, Chastity, and Understanding.

`ProfessionalismRole` separately retains its path to BFO role, and the moral-
foundations `CareDisposition` retains its path through
`MoralValueDisposition` to BFO disposition.

## Validation evidence

### Focused Phase 4 controls

- 35 passed
- 0 expected failures
- Runtime: 12.25 seconds

### Full repository suite

- 513 passed
- 2 skipped
- 5 deselected
- 0 expected failures
- 9 existing RDFLib deprecation warnings
- Runtime: 271.50 seconds

### HermiT

| Scope | Files | Triples | Declared classes | Consistent | Unsatisfiable named classes |
| --- | ---: | ---: | ---: | --- | ---: |
| TBox | 7 | 2,622 | 291 | Yes | 0 |
| TBox plus scenario | 8 | 2,712 | 291 | Yes | 0 |

The additional declared class relative to Phase 3 is the anonymous union class
that makes the D-001 extension explicit, not a new named project category.

## Exit criteria

- [x] No named core-class definition is circular or label-repeating.
- [x] No named core-class definition depends on prohibited weak differentiae.
- [x] Every definition's genus matches an asserted immediate or nearest parent.
- [x] The intended extension of every named core class is documented.
- [x] Clarity, inclusiveness, exclusiveness, BFO category, and formal alignment
  are explicitly reviewed.
- [x] Every folk-value cluster has a tested leaf specialization.
- [x] Role and moral-disposition branches have separate controls.
- [x] Full-suite and HermiT gates pass.

## Next phase boundary

Phase 5 adjudicates SKOS and class-mapping semantics under D-003. Historical
documentation parsing and the broader moral-epistemics sense refactor remain in
their assigned later phases.
