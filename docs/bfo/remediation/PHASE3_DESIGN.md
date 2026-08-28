# Phase 3 Evidence and Information Design

**Adopted:** 2026-08-25  
**Findings addressed:** ALN-003, ALN-005  
**Decision dependency:** D-004

## Authoritative source selection

The CCO 2.2 merged release at commit
`0bc7d33e1bc09fd4693366119ab4e03cb0340042` supplies the two genera used by
the repaired pattern:

| IRI | CCO label | Phase 3 use |
| --- | --- | --- |
| `cco:ont00000958` | Information Content Entity | Genus for textual representations, spans, selectors, and evidence annotations |
| `cco:ont00000253` | Information Bearing Entity | Type for physical or digital carrier individuals |

The checksum-verified ValueNet CCO extract was regenerated as version
`2.2-2026-08-25`. It now contains 195 triples and retains the complete selected
descriptions plus recursive logical closure.

## Entity pattern

The annotation pattern uses five distinct individuals:

1. an information-bearing carrier (`cco:ont00000253`);
2. an exact, version-specific `TextualRepresentation` with one canonical string;
3. a `TextSpan` that is content within that representation;
4. a `TextSpanSelector` containing the span's coordinate pair; and
5. a `ValueEvidenceAnnotation` that joins the span, selector, and target process.

`TextualRepresentation`, `TextSpan`, `TextSpanSelector`, and
`ValueEvidenceAnnotation` are subclasses of CCO Information Content Entity.
The carrier is an independent continuant and must be a different individual.

## Verified relations

The carrier links to its exact textual representation with BFO `is carrier of`
(`BFO_0000101`). CCO uses this relation in the definition of Information
Bearing Entity.

The model deliberately does **not** assert BFO `concretizes` directly from the
carrier to the representation. BFO `concretizes` has a process-or-specifically-
dependent-continuant domain; an information-bearing object is neither. Under
the BFO account, a specifically dependent concretization inheres in the carrier,
but the current annotation profile need not mint that additional individual.

`isTextSpanOf` is now a subproperty of BFO `continuant part of`
(`BFO_0000176`) and ranges over `TextualRepresentation`, not every generically
dependent continuant.

## Offset convention

Offsets belong to `TextSpanSelector`, never to the `TextSpan` content entity.
They are interpreted as:

- zero-based Unicode code-point indexes;
- start inclusive and end exclusive;
- measured against the exact `xsd:string` on the selector's
  `hasSourceRepresentation`; and
- free of implicit Unicode normalization, encoding conversion, or line-ending
  transformation.

Both offsets are required. SHACL checks ordering, source length, source identity,
and equality between the selected substring and the span's recorded text.
A changed source string requires a newly identified `TextualRepresentation`.

## Evidence relation profile

`isEvidenceFor` remains an annotation property so it creates no OWL domain or
range commitment beyond its documentary axioms. SHACL requires:

- a named subject typed as `TextSpan` or `ValueEvidenceAnnotation`; and
- a named target typed as a BFO process.

The simple profile permits a direct `TextSpan -> process` link without offsets.
The coordinate-bearing profile uses `ValueEvidenceAnnotation`, which must have
exactly one text span, selector, and process target, and whose selector must
select that same span.

## Scenario migration

The moral-epistemics scenario now separates the transcript carrier from the
exact transcript string. Each of its two spans has a selector and reified
evidence annotation. The scenario conforms to the core SHACL graph as part of
the Phase 3 regression suite.
