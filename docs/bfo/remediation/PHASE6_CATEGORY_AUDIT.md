# Phase 6 Moral Epistemics Category Audit

## Status

**Complete on 2026-08-25.** Category decisions were implemented and passed the focused, full-suite, SHACL, competency-question, and HermiT gates recorded in `PHASE6_EXIT_REVIEW.md`. The authoritative comparison source is the pinned CCO 2.2 merged release identified in `SOURCE_SELECTION.md`; BFO categories and relations are taken from the supplied BFO 2020 core.

## Sense Table

The table separates senses that the former `InteriorMoralState` label collapsed. A row marked “not modeled” is deliberately absent from the ontology: no class is minted merely to give an ambiguous word a parent.

| Lexical item and intended sense | Entity kind | Verified parent or reuse candidate | Phase 6 treatment |
| --- | --- | --- | --- |
| Intention as prescriptive plan content | Information content entity | CCO Plan (`ont00000974`), a Prescriptive ICE | Reuse CCO Plan when this sense enters scope; do not create a local “intention state” class |
| Intention as a private cognitive attitude | Unresolved without a mental-functioning ontology | No adequate class in supplied BFO/CCO | Not modeled; BFO `specifically dependent continuant` is too broad to serve as a definition |
| Act of intending as forming a plan | Process | CCO Act of Planning (`ont00000511`) | Reuse when needed; distinguish it from both the resulting Plan and the later Planned Act |
| Planned performance sometimes called an “intentional act” | Process | CCO Planned Act (`ont00000228`; alternative label “Intentional Act”) | Reuse directly; it is not the intention or plan content |
| Consent as a present private attitude or decision | Unresolved cognitive sense | No adequate class in supplied BFO/CCO | Not modeled; do not force it under quality, role, or disposition |
| A standing propensity to consent | Realizable entity | BFO disposition (`BFO_0000016`) | Model only if the propensity itself becomes a requirement; it is a disposition **to consent**, not consent itself |
| Act of granting consent that changes what is permitted | Process | CCO Act of Declarative Communication (`ont00001374`) | Reuse or specialize when a consent workflow is added |
| Communicative commitment to do or refrain from a future act | Process | CCO Act of Commissive Communication (`ont00001162`) | Keep distinct from granting permission; reuse only for the commissive sense |
| Permission content created or endorsed by consent | Information content entity | CCO Action Permission (`ont00000751`), a Process Regulation and Prescriptive ICE | Reuse directly when permission content is modeled |
| Record that an act of consenting occurred | Information content entity | CCO Descriptive ICE (`ont00000853`) | A record describes the consent act; it is not the permission content or the act |
| Culpability ascription | Information content entity | ValueNet `CulpabilityAscriptionICE`, now under CCO Descriptive ICE | The ICE describes an agent as culpable; false or unwarranted ascription does not entail actual culpability |
| Actual moral culpability or accountability status | Externally grounded realizable entity | ValueNet `MoralCulpabilityRole` under BFO role (`BFO_0000023`) | Separate bearer-dependent normative status, realizable in accountability, censure, restitution, or sanction processes |
| Observational evidence | Information content entity | ValueNet `ObservationalEvidenceICE` under CCO Descriptive ICE | Evidence is a record/content entity, not the observation act or physical carrier |
| Evidential warrant | Relation between information content entities | ValueNet `isWarrantedBy` | Warrant is represented as support from an evidence ICE to a moral-assessment ICE, not as a quality of an ICE |
| Warranted assessment status | Defined information-content class | `MoralAssessmentICE and isWarrantedBy some ObservationalEvidenceICE` | `WarrantedMoralAssessmentICE` provides the open-world logical classification; missing warrant remains a SHACL concern |

## `InteriorMoralState` Decision

`InteriorMoralState` is removed. It had no common differentia capable of including an intention, consent, and culpability while preserving their categories. In particular:

- a plan or permission can be generically dependent information content;
- planning, consenting, and assessing are processes;
- a standing propensity is a disposition;
- a consent record or culpability ascription is descriptive information content; and
- actual culpability is treated here as an externally grounded role, not as the content that claims it exists.

The class was unused by the scenario and no logical axiom depended on it. Removing it therefore eliminates ambiguity without deleting asserted instance data.

## Repaired Moral-Assessment Pattern

The ontology distinguishes five layers:

1. `MoralAssessmentAct` — an occurrent appraisal performed by an agent.
2. `MoralAssessmentICE` — the descriptive output of the act.
3. `cco:describes` — the relation from the output to the agent or conduct assessed.
4. `MoralCulpabilityRole` — an actual normative status borne by an agent, asserted only when independently warranted.
5. `isWarrantedBy` — the relation from an assessment output to observational evidence.

`CulpabilityAscriptionICE` is not restricted to describe a `MoralCulpabilityRole`; such an existential restriction would create a status individual even for a false ascription. It instead describes an Agent. A true ascription may be accompanied by an independently asserted role individual and bearer relation.

`BehavioralObservationICE` describes an `AgentBehaviorProcess`; `ActOfBehavioralObservation` reuses CCO Act of Observation (`ont00000037`) and produces that record. This keeps the observed process, observation act, and observation record distinct.

## Discernment and Rash Judgment

The former `RashJudgmentAct owl:disjointWith MoralDiscernmentAct` axiom is removed. Both are subtypes of `MoralAssessmentAct`, and one larger or temporally extended assessment can produce both:

- a warranted `SafetyAssessmentICE`; and
- an unwarranted `CulpabilityAscriptionICE`.

Class-level disjointness would make that mixed process inconsistent even though its two outputs are individually intelligible. The distinction is therefore output-relative:

- discernment requires a warranted safety-assessment output;
- rash judgment requires a culpability-ascription output lacking recorded warrant under the closed-world annotation profile.

`MixedMoralAssessmentAct` is a named subclass of both act classes so HermiT must demonstrate that their intersection remains satisfiable. OWL states the positive output types and defines warranted assessment. SHACL enforces recorded-warrant completeness and the absence-based rash-judgment criterion. No OWL complement is used to pretend that missing triples are negative facts.

## CCO Reuse Decisions

| ValueNet class | CCO reuse | Decision |
| --- | --- | --- |
| `ActOfBehavioralObservation` | Act of Observation (`ont00000037`) | Formal superclass; every instance is a planned sensory information-acquisition act |
| `MoralAssessmentAct` | Act of Appraisal (`ont00000636`) | Formal superclass; every instance evaluates or judges conduct or an agent |
| `MoralAssessmentICE` | Descriptive ICE (`ont00000853`) | Formal superclass |
| `CulpabilityAscriptionICE` | Descriptive ICE (`ont00000853`) | Inherited through `MoralAssessmentICE`; no local duplicate of generic descriptive content |
| `MoralNormICE` | Prescriptive ICE (`ont00000965`) | Existing formal superclass retained |

The Phase 6 CCO extract adds only Act of Observation as a new logical root. The consent and intention candidates remain documented reuse decisions and are not added to the local closure until an ontology axiom uses them.
