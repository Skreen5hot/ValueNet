# Phase 5 Mapping Semantics Audit

## Status

Phase 5 adjudication implemented on 2026-08-25. Validation results are recorded in `PHASE5_EXIT_REVIEW.md`.

## Decision and Profile

D-003 is adopted. ValueNet does not introduce a SKOS concept scheme in this phase. Canonical `skos:broadMatch`, `skos:closeMatch`, `skos:relatedMatch`, `skos:exactMatch`, and `skos:narrowMatch` are OWL object properties intended for `skos:Concept` individuals, so none is asserted directly between ValueNet OWL entities.

Three project-local properties declared in `valuenet-core.ttl` carry non-logical mappings:

| Annotation property | Intended use | Logical commitment |
| --- | --- | --- |
| `vn-core:hasBroaderConceptualMatch` | Target is a broader organizing concept for the source | No class inclusion or SKOS concept assertion |
| `vn-core:hasRelatedConceptualMatch` | Reviewed non-hierarchical conceptual association | No identity or extension relation |
| `vn-core:historicallyCorrespondsTo` | Legacy, predecessor, or provenance correspondence | No class, property, or individual identity |

All three are `owl:AnnotationProperty` subproperties of `vn-core:ontologyEntityMapping`. They have no OWL domain or range and cannot be used in restrictions. Annotation assertions on class or property IRIs therefore do not place those IRIs in OWL individual position.

## Inventory Summary

The pre-remediation BFO directory contained 71 canonical SKOS mapping assertions:

| Original predicate | Count | Phase 5 disposition |
| --- | ---: | --- |
| `skos:broadMatch` | 60 | 45 broader conceptual annotations; 15 historical annotations |
| `skos:closeMatch` | 6 | 4 reviewed subclass axioms; 2 historical annotations |
| `skos:relatedMatch` | 5 | 5 related conceptual annotations |
| `skos:exactMatch` | 0 | None |
| `skos:narrowMatch` | 0 | None |

Post-remediation totals are 67 annotation assertions and four `rdfs:subClassOf` axioms. No candidate met the necessary-and-sufficient threshold for `owl:equivalentClass`, and no assertion remains insufficiently supported: uncertain extension claims were retained only as explicitly non-logical conceptual annotations.

## Folk-to-Schwartz Inventory — 44 Assertions

Every assertion in this table was a `skos:broadMatch`, is classified as a **conceptual mapping**, and is now `vn-core:hasBroaderConceptualMatch`. The mapping organizes folk-value vocabulary without claiming universal inclusion.

| Target | Count | Source classes |
| --- | ---: | --- |
| `schwartz:AchievementDisposition` | 1 | `folk:CompetitionDisposition` |
| `schwartz:BenevolenceDisposition` | 1 | `folk:CooperationDisposition` |
| `schwartz:ConformityDisposition` | 5 | `folk:CleanlinessDisposition`, `folk:ConsistencyDisposition`, `folk:DisciplineDisposition`, `folk:OrderDisposition`, `folk:ResponsibilityDisposition` |
| `schwartz:HedonismDisposition` | 2 | `folk:HumorDisposition`, `folk:JoyDisposition` |
| `schwartz:PowerDisposition` | 1 | `folk:AssertivenessDisposition` |
| `schwartz:SecurityDisposition` | 4 | `folk:CalmnessDisposition`, `folk:OrderDisposition`, `folk:PrivacyDisposition`, `folk:ThriftDisposition` |
| `schwartz:SelfDirectionDisposition` | 13 | `folk:AssertivenessDisposition`, `folk:AuthenticityDisposition`, `folk:DecisivenessDisposition`, `folk:FlexibilityDisposition`, `folk:LearningDisposition`, `folk:LogicDisposition`, `folk:OpenMindednessDisposition`, `folk:OpennessDisposition`, `folk:PrivacyDisposition`, `folk:PurposeDisposition`, `folk:SelfRespectDisposition`, `folk:UniquenessDisposition`, `folk:VisionDisposition` |
| `folk:SelfRespectDisposition` | 1 | `folk:DignityDisposition` |
| `schwartz:StimulationDisposition` | 3 | `folk:CourageDisposition`, `folk:OpennessDisposition`, `folk:ResourcefulnessDisposition` |
| `schwartz:TraditionDisposition` | 1 | `folk:HumilityDisposition` |
| `schwartz:UniversalismDisposition` | 12 | `folk:BeautyDisposition`, `folk:BelongingDisposition`, `folk:ContributionDisposition`, `folk:CooperationDisposition`, `folk:HarmonyDisposition`, `folk:OpenMindednessDisposition`, `folk:ResponsibilityDisposition`, `folk:SpiritualityDisposition`, `folk:SustainabilityDisposition`, `folk:UnderstandingDisposition`, `folk:UnityDisposition`, `folk:WisdomDisposition` |

## Moral Epistemics Inventory — 10 Assertions

| Source | Original predicate | Target | Classification | Phase 5 disposition |
| --- | --- | --- | --- | --- |
| `me:PrudenceDisposition` | `skos:broadMatch` | `folk:WisdomDisposition` | Conceptual mapping | `vn-core:hasBroaderConceptualMatch` |
| `me:PrudenceDisposition` | `skos:relatedMatch` | `folk:DiscretionDisposition` | Conceptual mapping | `vn-core:hasRelatedConceptualMatch` |
| `me:PrudenceDisposition` | `skos:relatedMatch` | `schwartz:SecurityDisposition` | Conceptual mapping | `vn-core:hasRelatedConceptualMatch` |
| `me:RashJudgmentAct` | `skos:relatedMatch` | `haidt:Cheating` | Conceptual mapping | `vn-core:hasRelatedConceptualMatch` |
| `me:RashJudgmentAct` | `skos:relatedMatch` | `haidt:Harm` | Conceptual mapping | `vn-core:hasRelatedConceptualMatch` |
| `me:ProtectiveAction` | `skos:relatedMatch` | `haidt:Care` | Conceptual mapping | `vn-core:hasRelatedConceptualMatch` |
| `me:ObservationalEvidenceICE` | `skos:closeMatch` | `cco:ont00000853` Descriptive ICE | Asserted subclass relation | `rdfs:subClassOf`; every instance describes what was perceptually available |
| `me:SafetyAssessmentICE` | `skos:closeMatch` | `cco:ont00000853` Descriptive ICE | Asserted subclass relation | `rdfs:subClassOf`; every instance describes a risk |
| `me:MoralNormICE` | `skos:closeMatch` | `cco:ont00000965` Prescriptive ICE | Asserted subclass relation | `rdfs:subClassOf`; every instance prescribes conduct |
| `me:MoralDiscernmentAct` | `skos:closeMatch` | `cco:ont00000636` Act of Appraisal | Asserted subclass relation | `rdfs:subClassOf`; every instance evaluates or assesses conduct and risk |

The four CCO targets are universals supplied with their complete selected descriptions and dependency closure in the pinned CCO 2.2 extract. Each ValueNet source is narrower than its target. Equivalence was rejected because the CCO targets also include non-observational descriptions, non-safety descriptions, non-moral prescriptions, or non-moral appraisals.

## Legacy ValueNet Inventory — 15 Assertions

Every assertion in this table was a `skos:broadMatch`, is classified as a **lexical/historical cross-reference**, and is now `vn-core:historicallyCorrespondsTo`.

| Source | Target | Review note |
| --- | --- | --- |
| `mf:CareDisposition` | `haidt:Care` | BFO disposition corresponding to the legacy value entity |
| `mf:FairnessDisposition` | `haidt:Fairness` | BFO disposition corresponding to the legacy value entity |
| `mf:FairnessDisposition` | `curry:Fairness` | Cross-theory historical correspondence only |
| `mf:LoyaltyDisposition` | `haidt:Loyalty` | BFO disposition corresponding to the legacy value entity |
| `mf:AuthorityDisposition` | `haidt:Authority` | BFO disposition corresponding to the legacy value entity |
| `mf:SanctityDisposition` | `haidt:Sanctity` | BFO disposition corresponding to the legacy value entity |
| `mf:LibertyDisposition` | `haidt:Liberty` | BFO disposition corresponding to the legacy value entity |
| `vn-core:ValueRelatedRealizableEntity` | `vcvf:Value` | Realist refactor of a legacy description-model category |
| `mf:HarmProcess` | `haidt:Harm` | Process-to-legacy-value correspondence crosses BFO categories |
| `mf:CheatingProcess` | `haidt:Cheating` | Process-to-legacy-value correspondence crosses BFO categories |
| `mf:BetrayalProcess` | `haidt:Betrayal` | Process-to-legacy-value correspondence crosses BFO categories |
| `mf:SubversionProcess` | `haidt:Subversion` | Process-to-legacy-value correspondence crosses BFO categories |
| `mf:DegradationProcess` | `haidt:Degradation` | Process-to-legacy-value correspondence crosses BFO categories |
| `mf:OppressionProcess` | `haidt:Oppression` | Process-to-legacy-value correspondence crosses BFO categories |
| `vn-core:ValueViolationProcess` | `haidt:Violation` | Process-to-legacy-value correspondence crosses BFO categories |

The category-crossing rows cannot be class equivalences or subclass axioms. The annotation is retained for provenance and the MFTriggers query path only.

## Property Correspondence Inventory — 2 Assertions

| Source | Original predicate | Target | Classification | Phase 5 disposition |
| --- | --- | --- | --- | --- |
| `vn-core:contravenes` | `skos:closeMatch` | `haidt:violates` | Lexical/historical cross-reference | `vn-core:historicallyCorrespondsTo` |
| `mf:dyadicOppositeOf` | `skos:closeMatch` | `haidt:opposedTo` | Lexical/historical cross-reference | `vn-core:historicallyCorrespondsTo` |

Neither row asserts `rdfs:subPropertyOf` or `owl:equivalentProperty`: the legacy property semantics and the refactored BFO property semantics have not been shown to have extension inclusion or identity.

## Query and Profile Consequences

- Moral epistemics CQ6 now follows `vn-core:historicallyCorrespondsTo`; it does not depend on an undeclared SKOS predicate.
- The redundant-mapping sanity query now checks `vn-core:hasBroaderConceptualMatch` against `rdfs:subClassOf`.
- `tests/test_bfo_mapping_semantics.py` fixes the 67/4 adjudication count, rejects all canonical SKOS mapping assertions, verifies annotation-property declarations, verifies the four CCO subclass decisions, and reports every class or property IRI used in OWL individual position.
- The profile guard separately checks entity-kind separation and that every `owl:onProperty` target is a declared logical property.

## Namespace Key

- `vn-core:` `https://fandaws.com/ontology/bfo/valuenet-core#`
- `mf:` `https://fandaws.com/ontology/bfo/valuenet-moral-foundations#`
- `folk:` `https://fandaws.com/ontology/bfo/valuenet-folk#`
- `schwartz:` `https://fandaws.com/ontology/bfo/valuenet-schwartz-values#`
- `me:` `https://fandaws.com/ontology/bfo/valuenet-moral-epistemics#`
- `cco:` `https://www.commoncoreontologies.org/`
- `haidt:` `https://w3id.org/spice/SON/HaidtValues#`
- `curry:` `http://www.ontologydesignpatterns.org/ont/values/CurryMoralMolecules.owl#`
- `vcvf:` `http://www.ontologydesignpatterns.org/ont/values/valuecore_with_value_frames.owl#`

