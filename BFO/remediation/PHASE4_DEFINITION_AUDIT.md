# Phase 4 Core Definition Audit

**Reviewed:** 2026-08-25  
**Decision basis:** D-001  
**Ontology:** `BFO/valuenet-core.ttl`

## Authoritative category basis

The review used the supplied BFO 2020 declarations and elucidations for:

- `BFO_0000017` — realizable entity;
- `BFO_0000016` — disposition / internally-grounded realizable entity;
- `BFO_0000023` — role / externally-grounded realizable entity;
- `BFO_0000197` — inheres in; and
- `BFO_0000055` — realizes.

CCO `ont00001017` (Agent), `ont00000958` (Information Content Entity), and
`ont00000253` (Information Bearing Entity) are supplied by the pinned CCO 2.2
extract. No external or guessed ontology term was used.

## Value-model boundary

For this project, a **standing evaluative orientation** is a stable basis by
which kinds of actions, relationships, states, or outcomes are treated as good,
right, worthy, or preferable. This phrase records the domain differentia; it is
not introduced as an OWL class or individual.

The boundary excludes:

- transient desires, occurrent judgments, emotions, and choices;
- ordinary capabilities and dispositions with no evaluative orientation;
- information content entities that describe or prescribe values;
- agents, groups, and organizations themselves; and
- ordinary position roles whose characteristic realization has no evaluative
  differentia.

D-001 recognizes exactly two ways such an orientation is borne as a realizable
entity: an internally grounded disposition or an externally grounded role. The
ontology now makes this extension explicit:

`ValueRelatedRealizableEntity ≡ ValueDisposition or ValueRole`.

Because BFO declares disposition and role disjoint, this also preserves their
grounding distinction. It does not make `MoralValueDisposition` and
`PersonalValueDisposition` disjoint; those classifications answer different
questions and may overlap.

## Root value definitions

| Class | Genus and intended extension | Clarity | Inclusiveness | Exclusiveness | BFO/formal alignment |
| --- | --- | --- | --- | --- | --- |
| `ValueRelatedRealizableEntity` | Realizable entities inhering in agents whose characteristic realizations express a standing evaluative orientation | Pass: identifies a specifically dependent continuant, its bearer, and characteristic realization | Includes cognition, emotion, choice, and action; includes internally and externally grounded cases | Excludes transient occurrents, information content, ordinary capabilities, and non-evaluative roles | `BFO_0000017`, `inheres in some Agent`, and the disposition/role union are asserted |
| `ValueDisposition` | Dispositions whose characteristic realizations express the bearer's standing evaluative orientation | Pass: genus is BFO disposition and the differentia is realization-based | Includes self- and other-regarding, moral and non-moral orientations | Excludes temporary preference states and ordinary biological or technical dispositions | Asserted under both `ValueRelatedRealizableEntity` and `BFO_0000016`; agent inheritance follows from the parent |
| `ValueRole` | Roles attached to contingent social/institutional circumstances whose realizations exemplify conduct evaluated as good, right, or worthy for that circumstance | Pass: separates the evaluative facet from the agent or position itself | Includes good-citizen, professionalism, accountability, and similar normative roles | Excludes the person, organization, position, and ordinary role facets without the evaluative condition | Asserted under both `ValueRelatedRealizableEntity` and `BFO_0000023`; agent inheritance follows from the parent |
| `MoralValueDisposition` | Value dispositions whose realizations appraise or govern conduct as right, wrong, obligatory, permitted, or forbidden | Pass: replaces “pertains to” with a realization criterion | Includes moral appraisal and morally governed conduct, including care and justice cases | Excludes merely preferred ends that make no moral assessment | Immediate parent is `ValueDisposition`; differentia remains textual because no supplied relation safely represents moral status |
| `PersonalValueDisposition` | Value dispositions whose realizations select or pursue preferred ends or means across situations | Pass: “personal” is explained as guidance of the bearer, not self-interest | Includes other-regarding and moral ends when they also guide trans-situational choice | Excludes one-off desires and preferences with no standing disposition | Immediate parent is `ValueDisposition`; no unsupported goal/preference relation is asserted |

### Formalization ceiling

The supplied source ontologies contain no verified object property whose
semantics are “has standing evaluative orientation,” “treats as good,” or
“governs as morally obligatory.” Creating such a convenience relation would
violate the reuse-first relation policy and would require a separate account of
the relevant information content, mental states, and appraisal processes.
Accordingly, Phase 4 formalizes the verified BFO category, bearer, exhaustive
disposition/role extension, and process relations; the domain differentiae
remain controlled natural-language criteria.

No new CCO/BFO object properties are required.

## Remaining core class definitions

| Class | Immediate asserted genus | Intended extension and audit result |
| --- | --- | --- |
| `ValueRealizationProcess` | BFO process | Exactly processes that realize some `ValueRelatedRealizableEntity`; definition now matches the equivalent-class axiom verbatim in substance |
| `ValueViolationProcess` | BFO process | Exactly processes that contravene some `ValueRelatedRealizableEntity`; definition now matches the equivalent-class axiom and preserves non-disjointness with realization |
| `EvidenceSource` | CCO Information Content Entity | ICEs used as the subject of an assertion that they supply evidence for a process; excludes carriers and processes |
| `TextualRepresentation` | CCO Information Content Entity | Exact version-specific Unicode code-point sequences used as selector coordinate sources |
| `TextSpan` | `EvidenceSource` | Evidence-source content that is a continuant part of one textual representation and is a substring of it; genus now matches the nearest asserted parent |
| `TextSpanSelector` | CCO Information Content Entity | ICEs identifying one span in one representation by a code-point interval |
| `ValueEvidenceAnnotation` | `EvidenceSource` | Evidence-source records joining one span, its selector, and one process target; genus now matches the nearest asserted parent |

All twelve named project classes in the core module have exactly one English
`skos:definition` and pass the automated genus-prefix and weak-phrase controls.

## Folk-cluster leaf sampling

The following asserted leaf classes were checked for a complete subclass path to
`ValueRelatedRealizableEntity` and BFO disposition. Each remains a leaf in the
current folk graph.

| Folk cluster | Sample leaf |
| --- | --- |
| Foundational Concepts | `folk:KindnessDisposition` |
| Achievement & Growth | `folk:DiligenceDisposition` |
| Community & Social Connection | `folk:CharityDisposition` |
| Integrity & Principle | `folk:CandorDisposition` |
| Security & Stability | `folk:CleanlinessDisposition` |
| Freedom & Autonomy | `folk:PrivacyDisposition` |
| Well-being & Harmony | `folk:MindfulnessDisposition` |
| Justice & Fairness | `folk:EquityDisposition` |
| Power & Influence | `folk:StatusDisposition` |
| Experiential & Stimulation | `folk:ExplorationDisposition` |
| Discipline & Restraint | `folk:ChastityDisposition` |
| Intellectual | `folk:UnderstandingDisposition` |

Two additional controls cover the other core branches:

- `folk:ProfessionalismRole` reaches BFO role through `ValueRole`; and
- `vn-mf:CareDisposition` reaches BFO disposition through
  `MoralValueDisposition`.

## Definition validation result

- **Clarity:** Pass. Every root definition names an appropriate genus and an
  entity-level differentia.
- **Inclusiveness:** Pass for D-001's approved agent-borne disposition/role
  scope. Group and artificial-agent value bearing remain explicitly deferred.
- **Exclusiveness:** Pass at the documented modeling boundary; ordinary
  dispositions, ordinary position roles, occurrents, ICEs, and carriers are
  excluded.
- **BFO category:** Pass. Continuant/occurrent and internal/external grounding
  distinctions are preserved.
- **Formal alignment:** Pass within the verified vocabulary ceiling. Asserted
  parents, bearer restriction, exhaustive union, and process equivalences match
  their definitions; unverified evaluative relations were not invented.
