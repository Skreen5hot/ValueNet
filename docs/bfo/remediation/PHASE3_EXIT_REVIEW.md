# Phase 3 Exit Review — Evidence and Information Modeling

**Phase:** 3 — Repair Evidence and Information Modeling  
**Closed:** 2026-08-25  
**Findings closed:** ALN-003, ALN-005  
**Decision adopted:** D-004

## Outcome

Phase 3 is complete. The ontology and scenario no longer conflate textual
content, exact representations, carriers, coordinate selectors, and evidence
annotation records. SHACL now enforces the documented evidence-source and
process-target contract and validates offset identity against a canonical source
string.

## Authoritative dependency extension

The checksum-verified CCO 2.2 extract was regenerated from the same pinned
source artifact and commit to add:

- `cco:ont00000253` — Information Bearing Entity; and
- `cco:ont00000958` — Information Content Entity.

| Extract property | Result |
| --- | --- |
| Version IRI | `https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-25` |
| Triples | 195 |
| SHA-256 | `be14d627b9aeb0d4335d152637d4e55371f4f3c859e4266c47ae3b138b223035` |
| Generator version | 2 |
| Manifest/schema validation | Pass |

The core module imports the revised version IRI. External logical dependency
closure reports zero unknown terms.

## Implemented information pattern

- `TextualRepresentation` is an information content entity with one exact,
  version-specific canonical string.
- `TextSpan` is an information content part of exactly one textual representation.
- `TextSpanSelector` is a separate information content entity containing the
  source link, selected span, and complete offset pair.
- `ValueEvidenceAnnotation` is a separate information content entity joining one
  span, selector, and process target.
- Physical or digital carriers are CCO Information Bearing Entity individuals
  linked to representations by BFO `is carrier of` (`BFO_0000101`).
- `isTextSpanOf` specializes BFO `continuant part of` (`BFO_0000176`) and no
  longer ranges over every generically dependent continuant.
- No invalid carrier-to-content `concretizes` assertion is made; BFO reserves
  the concretizer position for a process or specifically dependent continuant.

## SHACL contract

The core shapes now enforce:

- one canonical string and at least one distinct named carrier for each exact
  textual representation;
- one span string and exactly one exact source representation;
- offsets only on selectors;
- exactly one start and end offset per selector;
- zero-based, end-exclusive Unicode code-point bounds;
- end greater than start and no greater than source-string length;
- equality of the selected substring and recorded span text;
- identity between the selector source and span source;
- a named `TextSpan` or `ValueEvidenceAnnotation` evidence subject;
- a named BFO process evidence target; and
- source/selector identity within a reified evidence annotation.

## Regression controls

| Control | Expected | Result |
| --- | --- | --- |
| Direct named TextSpan evidence source and process target | Conforms | Pass |
| Reified evidence annotation with valid selector | Conforms | Pass |
| Migrated moral-epistemics scenario | Conforms | Pass |
| Non-span/non-annotation evidence source | Violation with source-type message | Pass |
| Non-process evidence target | Violation with process-target message | Pass |
| Untyped evidence source and target | Both intended violations | Pass |
| Blank-node evidence source | Named-subject violation | Pass |
| Blank-node evidence target | Named-target violation | Pass |
| Generic GDC used instead of exact representation | Exact-source violation | Pass |
| Offsets asserted on TextSpan | Selector-placement violation | Pass |
| Incomplete offset pair | Missing-offset violation | Pass |
| End offset beyond source length | Bounds violation | Pass |
| Selector and span use different source representations | Source-identity violation | Pass |
| Offsets select text different from span content | Substring-identity violation | Pass |
| Evidence annotation selector selects another span | Evidence-join violation | Pass |
| Carrier and textual representation conflated | Carrier/content violation | Pass |

The three former ALN-003 strict expected failures are now ordinary passing
regressions and assert the intended report messages.

## Validation evidence

### Focused Phase 3 controls

- 27 passed
- 0 expected failures
- Runtime: 8.04 seconds

### Full repository suite

- 505 passed
- 2 skipped
- 5 deselected
- 0 expected failures
- 9 existing RDFLib deprecation warnings
- Runtime: 150.43 seconds

### HermiT

| Scope | Files | Triples | Declared classes | Consistent | Unsatisfiable named classes |
| --- | ---: | ---: | ---: | --- | ---: |
| TBox | 7 | 2,612 | 290 | Yes | 0 |
| TBox plus scenario | 8 | 2,702 | 290 | Yes | 0 |

## Exit criteria

- [x] No scenario or current annotation example treats carrier and information
  content as the same individual.
- [x] Exact representation identity and code-point offset conventions are explicit.
- [x] Both offsets are present together on selectors and checked against source length.
- [x] `isEvidenceFor` source, target, and named-individual violations are detected.
- [x] `isTextSpanOf` has a reviewed BFO parthood parent and a narrow range.
- [x] The worked scenario exercises the carrier/content/selector distinction.
- [x] Full-suite and HermiT gates pass.

## Next phase boundary

Phase 4 reviews and rewrites core definitions. Mapping adjudication (D-003) and
repository-wide historical documentation cleanup remain outside this phase.
