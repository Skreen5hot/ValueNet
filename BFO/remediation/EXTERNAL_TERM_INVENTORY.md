# External Term Inventory

## Status

**Phase 1 logical closure, Phase 5 mapping adjudication, and Phase 6 moral-epistemics reuse review complete.** This inventory records external classes and properties used in logical or mapping positions by the BFO layer. Logical CCO dependencies are supplied by the pinned extract. Legacy value correspondences remain annotation-only and canonical SKOS mapping properties are not asserted.

## Logical Dependencies

| IRI | Intended term | Use | Current support | Verification status | Required action |
| --- | --- | --- | --- | --- | --- |
| `https://www.commoncoreontologies.org/ont00001017` | CCO Agent | Parent restriction filler, ABox type, SHACL class | Partial local stub removed in Phase 1 | **Verified and supplied** — CCO 2.2 defines Agent as a material entity bearing some Agent Capability (`ont00001379`); the complete selected description is in the pinned extract | Reuse the canonical CCO IRI and retained defining closure |
| `https://www.commoncoreontologies.org/ont00000253` | CCO Information Bearing Entity | Phase 3 carrier ABox type and SHACL class | None before Phase 3 | **Verified and supplied** — CCO 2.2 defines it as an object on which an ICE generically depends; included with its equivalence and dependencies in the 2026-08-25 extract revision | Use for physical or digital carrier individuals; link carrier to ICE with BFO `BFO_0000101` |
| `https://www.commoncoreontologies.org/ont00000958` | CCO Information Content Entity | Superclass/range for textual representations, spans, selectors, evidence records, and informational input/output | None before Phase 3 | **Verified and supplied** — CCO 2.2 defines it as a GDC about some entity; included with its equivalence and aboutness dependency | Use as the verified information-content genus; do not type carriers as ICEs |
| `https://www.commoncoreontologies.org/ont00001921` | CCO has input | Superproperty of `hasInformationalInput` | Added in Phase 1 | **Verified, supplied, and reused** — CCO ERO permits continuant, process, or GDC input | Retain; the local subproperty narrows the range to ICE |
| `https://www.commoncoreontologies.org/ont00001986` | CCO has output | Superproperty of `hasInformationalOutput` | Added in Phase 1 | **Verified, supplied, and reused** — CCO ERO permits continuant, process, or GDC output | Retain; the local subproperty narrows the range to ICE |
| `https://www.commoncoreontologies.org/ont00001982` | CCO describes | Aboutness relation used by observation and assessment outputs | Added to assertions in Phase 6 | **Verified, supplied, and reused** — CCO defines it as a subproperty of `is about` whose subject is a Descriptive ICE | Use from the information output to the observed process or assessed Agent |

The superseded RO `has input` (`RO_0002233`), RO `has output` (`RO_0002234`), and IAO `definition` (`IAO_0000115`) stubs were removed in Phase 1. They are not dependencies of the current closure.

## CCO Mapping Targets

| IRI | Claimed alignment | Current support | Verification status | Required action |
| --- | --- | --- | --- | --- |
| `https://www.commoncoreontologies.org/ont00000037` | Act of Observation | Phase 6 superclass of `ActOfBehavioralObservation` | **Verified, supplied, and reused** — Planned Act of acquiring information about an entity by using the senses | Retain the strict subclass axiom; equivalence is not asserted |
| `https://www.commoncoreontologies.org/ont00000636` | Act of Appraisal | Phase 6 superclass of `MoralAssessmentAct`, inherited by discernment and rash judgment | **Verified, supplied, and reused** — Act of Measuring that evaluates or judges nature, value, importance, condition, or quality | Retain the superclass path; equivalence rejected because the CCO extension is broader |
| `https://www.commoncoreontologies.org/ont00000853` | Descriptive Information Content Entity | Superclass of `ObservationalEvidenceICE` and `MoralAssessmentICE`, inherited by safety assessments and culpability ascriptions | **Verified, supplied, and reused** — defined as an ICE that describes some entity; disjoint with Prescriptive ICE | Retain the superclass paths and imported disjointness |
| `https://www.commoncoreontologies.org/ont00000965` | Prescriptive Information Content Entity | Phase 5 superclass of `MoralNormICE` | **Verified, supplied, and reused** — defined as an ICE that prescribes some entity; alternate label Directive ICE | Retain `MoralNormICE rdfs:subClassOf` this class; equivalence rejected because non-moral prescriptions are also included |

## Mapping Properties

| IRI | Observed assertions | Current support | Verification status | Required action |
| --- | ---: | --- | --- | --- |
| `http://www.w3.org/2004/02/skos/core#broadMatch` | 60 before Phase 5; 0 after | Canonical SKOS object property with `skos:Concept` semantics | **Removed from BFO assertions** | Replaced by 45 `vn-core:hasBroaderConceptualMatch` and 15 `vn-core:historicallyCorrespondsTo` annotations |
| `http://www.w3.org/2004/02/skos/core#closeMatch` | 6 before Phase 5; 0 after | Canonical SKOS object property with `skos:Concept` semantics | **Removed from BFO assertions** | Four mappings promoted to reviewed CCO subclass axioms; two converted to historical annotations |
| `http://www.w3.org/2004/02/skos/core#relatedMatch` | 5 before Phase 5; 0 after | Canonical SKOS object property with `skos:Concept` semantics | **Removed from BFO assertions** | Replaced by five `vn-core:hasRelatedConceptualMatch` annotations |
| `https://fandaws.com/ontology/bfo/valuenet-core#hasBroaderConceptualMatch` | 45 | Project declaration in `valuenet-core.ttl` | **Verified annotation-only** | Retain for non-logical broader conceptual organization |
| `https://fandaws.com/ontology/bfo/valuenet-core#hasRelatedConceptualMatch` | 5 | Project declaration in `valuenet-core.ttl` | **Verified annotation-only** | Retain for non-hierarchical conceptual associations |
| `https://fandaws.com/ontology/bfo/valuenet-core#historicallyCorrespondsTo` | 17 | Project declaration in `valuenet-core.ttl` | **Verified annotation-only** | Retain for legacy/provenance query continuity |

## Legacy Value Mapping Targets Declared Elsewhere in the Repository

The following targets have local declarations outside `BFO/`. Phase 5 classified all links to them as annotation-only historical or conceptual correspondences; they are not logical dependencies of the BFO closure:

- `http://www.ontologydesignpatterns.org/ont/values/CurryMoralMolecules.owl#Fairness`
- `http://www.ontologydesignpatterns.org/ont/values/valuecore_with_value_frames.owl#Value`
- `https://w3id.org/spice/SON/HaidtValues#Authority`
- `https://w3id.org/spice/SON/HaidtValues#Betrayal`
- `https://w3id.org/spice/SON/HaidtValues#Care`
- `https://w3id.org/spice/SON/HaidtValues#Cheating`
- `https://w3id.org/spice/SON/HaidtValues#Degradation`
- `https://w3id.org/spice/SON/HaidtValues#Fairness`
- `https://w3id.org/spice/SON/HaidtValues#Harm`
- `https://w3id.org/spice/SON/HaidtValues#Liberty`
- `https://w3id.org/spice/SON/HaidtValues#Loyalty`
- `https://w3id.org/spice/SON/HaidtValues#Oppression`
- `https://w3id.org/spice/SON/HaidtValues#Sanctity`
- `https://w3id.org/spice/SON/HaidtValues#Subversion`
- `https://w3id.org/spice/SON/HaidtValues#Violation`
- `https://w3id.org/spice/SON/HaidtValues#opposedTo`
- `https://w3id.org/spice/SON/HaidtValues#violates`

## Next Phase 1 Actions

1. [x] Select exact upstream versions for CCO, RO/ERO, IAO, and SKOS.
2. [x] Record redistribution and attribution requirements for committed MIREOT extracts.
3. [x] Resolve full release commit hashes and inspected source-artifact checksums.
4. [x] Inspect the CCO 2.2 Extended Relation Ontology before retaining or replacing the RO input/output relations.
5. [x] Create the extract manifest schema.
6. [x] Create the repeatable extraction script.
7. [x] Generate a source-complete CCO extract for Agent and the two ERO relations; do not extract the superseded RO terms unless retained for comparison.
8. [x] Verify the three opaque CCO mapping targets before using their labels or recommending reuse.
9. [x] Add an automated closure test that distinguishes declared, mapped-only, and completely unknown external terms.
