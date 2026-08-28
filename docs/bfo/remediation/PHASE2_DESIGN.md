# Phase 2 Realization Integrity Design

**Adopted:** 2026-08-25  
**Finding addressed:** ALN-002  
**Decision dependency:** D-001

## Contract

For every asserted `bfo:realizes` link whose object is an instance of
`vn-core:ValueRelatedRealizableEntity`:

1. the object is an individual value instance, not a value class IRI;
2. at least one bearer is explicitly recorded with `bfo:bearer_of`
   (`BFO_0000196`) or its inverse `bfo:inheres_in` (`BFO_0000197`);
3. every explicitly recorded bearer checked through those directions is typed as
   CCO `Agent` (`cco:ont00001017`); and
4. at least one recorded bearer is linked to the realizing process by
   `bfo:has_participant` (`BFO_0000057`).

OWL states the open-world universal structure. SHACL states the closed-world
annotation completeness and identity join.

## Bearer cardinality and collective realization

BFO does not declare `bearer_of` or `inheres_in` functional, so ValueNet does
not add a maximum cardinality. The bearer-participant check is existential: if
data integration records more than one bearer for one value instance, at least
one recorded bearer must participate in the realizing process.

The normative annotation pattern remains one value instance per agent. Group-
and organization-level value bearing is outside D-001 and requires a later CCO
group-model review. The existential merge behavior is therefore not an
assertion that a single specifically dependent continuant collectively inheres
in several agents.

## Class definition

`ValueRealizationProcess` is a defined class equivalent to the intersection of:

- `bfo:process`; and
- `bfo:realizes some ValueRelatedRealizableEntity`.

This is necessary and sufficient for reasoner classification. The
bearer-participant identity join is intentionally not part of the OWL
definition because it is a closed-world data-integrity requirement.

`ValueRealizationProcess` remains non-disjoint with `ValueViolationProcess`.
One process may realize one value and contravene another.

## Validation outcomes

The Phase 2 regression suite locks the following behavior:

- single bearer and participant: conforming;
- inverse `inheres_in` recording: conforming;
- several values borne by one participant: conforming;
- several recorded bearers with at least one participant: conforming;
- realizing one value and contravening another: conforming;
- bearer/participant mismatch: violation;
- missing recorded bearer: violation; and
- value class IRI used where an instance is required: violation.
