<!--
Provenance (added on recording; not part of what was sent)

  sent         2026-09-17, by the project owner, to the reviewer
  replying to  FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF.md
  answered by  FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF_2.md
  version      the owner's best recollection is that the reviewer received
               this text. A later draft added two points that, on that
               recollection, did not reach the reviewer: that nothing uses
               ValueNet's IRIs, and that D-014 records the CCO search and
               checks for its six added classes (committed as 4e77820). The
               reviewer's reply is consistent with this version.

Recorded as sent. Nothing below this comment has been edited.
-->

# ValueNet formal review of 2026-09-16: what changed after your sign-off

**From:** the ValueNet project owner
**Date:** 2026-09-17
**Replying to:** your sign-off on the response and remediation plan (`FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF.md`)
**Branch:** `formal-review-remediation`

## Summary

Your sign-off named items 1–4 as the required breaking-change set, and said when items 5 and 6 would be breaking. All six are done as you described them.

After your sign-off, four more decisions were taken — D-011 to D-014 — and the folk module was curated to RULES 2.0. **Two of these are breaking changes by your own test, and outside the set you signed off:**

- **D-011** makes `TextualRepresentation` and `TextSpan` disjoint with Information Content Entity: a new OWL condition.
- **D-014** removes seven folk class IRIs, and four folk classes stop being subsumed by Schwartz Power.

D-013 also adopts your RULES 2.0 with three readings you did not state.

Four questions are in §4. If none of this changes your position, nothing further is needed from you.

## 1. The six items from your sign-off

| item | done | breaking |
|---|---|---|
| 1. D-005 text layer | `TextualRepresentation` and `TextSpan` are generically dependent continuants; `hasTextValue` is `hasTextualSequenceValue`; no deprecated alias. Commit `d57388a` | yes, as you said |
| 2. `EvidenceSource` retired | Retired; `TextSpanSelector` is a Designative ICE and `ValueEvidenceAnnotation` a Descriptive ICE. `d57388a` | yes, as you said |
| 3. `hasInformationalInput`/`Output` retired | Restrictions, shapes and queries use CCO `has input` and `has output` directly (D-007). `d57388a` | yes, as you said |
| 4. `MoralAssessmentAct` re-parented | `MoralAssessmentAct ⊑ Act`; `MoralDiscernmentAct ⊑ Act of Appraisal`. Regression tests in `tests/bfo/test_moral_assessment_commitments.py`, including `test_a_rash_judgment_is_an_act_and_is_not_entailed_to_be_planned` (D-008). `90f5b6f` | yes, as you said |
| 5. `MoralCulpabilityRole` | Redefined by the agent's conduct; no OWL condition changed (D-009). `90f5b6f` | no, by your test |
| 6. `contravenes` | Retained, with the justification recorded against competency questions 1 and 5 (D-010). `90f5b6f` | no, by your test |

## 2. Decisions after your sign-off

### 2.1 D-011 — form-level text is disjoint with information content (breaking)

CCO 2.2 defines Information Content Entity as *equivalent to* a generically dependent continuant that is about something. Both form-level classes from D-005 are generically dependent continuants. So asserting aboutness of either one — through `is about`, `designates` or `describes` — silently re-classified it as information content, and nothing reported it. D-011 makes that an inconsistency:

```turtle
@prefix owl:     <http://www.w3.org/2002/07/owl#> .
@prefix cco:     <https://www.commoncoreontologies.org/> .
@prefix vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#> .

vn-core:TextualRepresentation owl:disjointWith cco:ont00000958 .  # Information Content Entity
vn-core:TextSpan              owl:disjointWith cco:ont00000958 .
```

No disjointness is asserted between the two form classes.

**Why it is breaking:** it is a new OWL condition on class membership, the test you gave for item 5. Data asserting that a representation or span is about something was consistent before and is inconsistent now.

**What it does not break:** a selector designating a span is aboutness *of* the span, and stays consistent. `tests/bfo/test_text_layer_follows_d005.py` runs HermiT on four cases, each a carrier and its representation with a process beside them:
- no aboutness asserted: consistent;
- a selector designating a span: consistent;
- a representation asserted to be about a process: inconsistent;
- a span asserted to designate a process: inconsistent.

HermiT finds the modules and the worked scenario consistent.

Commit `74e7a6f`.

### 2.2 D-014 — folk membership (breaking)

This answers the folk-membership question our response raised as R15. It sets membership criteria (M1–M7), reports coverage of the folk corpus by kind, and decides every folk corpus value with no class and every folk class with no corpus value. The criteria:

- **M1:** a member is a value disposition or a value role borne by an agent.
- **M2:** a word that names a class's concept becomes a `skos:altLabel`, but only if substituting it for the preferred label leaves the referent unchanged. A word that only evokes or indicates the value becomes an annotation-only related match.
- **M3:** a value-survey item indicates a value; it is not a synonym or subclass on that ground alone.
- **M4:** a new class needs a differentia no existing class covers, and examples that separate it from its siblings.
- **M5:** emotional states and trait words are related matches, not labels.
- **M6:** a class with no corpus value stays only if a named source or value research attests it, it is a role, or a recorded competency question needs it.

**Removed — an IRI break, with no deprecated alias, as for items 2 and 3.** All seven are in `https://fandaws.com/ontology/bfo/valuenet-folk#`:

| IRI | why |
|---|---|
| `PowerDisposition`, `SecurityDisposition`, `TraditionDisposition` | repeated the Schwartz classes of the same name, as their subclasses, with no differentia |
| `OpennessDisposition` | polysemous (a Big Five trait, a VIA strength, Schwartz's openness to change); no corpus value or value item carries it. It had been narrowed by D-012 the day before |
| `ImpactDisposition`, `DiscretionDisposition`, `ResourcefulnessDisposition` | no attestation M6 accepts, and no recorded competency question |

**Re-parented — a change to subsumption:**

| class | was under | now under |
|---|---|---|
| `StatusDisposition` | folk `PowerDisposition` | `schwartz-values:PowerDisposition` |
| `ControlDisposition`, `LeadershipDisposition`, `InfluenceDisposition`, `RecognitionDisposition` | folk `PowerDisposition` | `core:PersonalValueDisposition` |

Folk Power was a subclass of Schwartz Power. So Control, Leadership, Influence and Recognition are **no longer entailed to be Schwartz Power dispositions**, and that is the logical break. Each was checked against Schwartz Power's definition: "to seek social status and prestige, and control or dominance over people and resources". Only Status satisfies it. Control fails because "or the course of events" is not control over people or resources, and its definition was not narrowed to fit. The overlap is kept as annotation-only related matches: Control, Leadership and the new `WealthDisposition` to Power, and Recognition to Power and Achievement.

**Not breaking:**
- **Added:** `HealthDisposition`, `IntelligenceDisposition`, `ModerationDisposition` and `WealthDisposition` under `PersonalValueDisposition`, plus `PatriotismDisposition ⊑ LoyaltyDisposition` and `WorkLifeBalanceDisposition ⊑ BalanceDisposition`.
- **Labels:** nine alternative labels, such as "Frugality" on `ThriftDisposition`.
- **Related matches:** 150 annotation-only related matches from classes to folk corpus value IRIs, in `valuenet-mappings.ttl`. The project's mapping annotations now number 42 broader, 159 related and 17 historical.
- **Prudence:** `moral-epistemics:PrudenceDisposition` loses its related match to the removed `DiscretionDisposition`.

Over the 278 folk corpus values, 98 have an exact class, 9 are alternative labels, 146 are linked by those related matches (four to two classes each) and 25 are excluded, with none undecided. A test checks the ontology against the decision record's own tables.

Commit `7e71a93`.

### 2.3 D-012 — Faith and Openness each define one disposition (not breaking)

`FaithDisposition` and `OpennessDisposition` each kept their IRI with a narrowed, single-sense definition. `ReligionDisposition` was added for the religious sense taken out of Faith, and Openness's candour sense already belonged to `CandorDisposition` and `TransparencyDisposition`. No OWL condition changed. Openness was later removed by D-014.

Commit `74e7a6f`.

### 2.4 D-013 — RULES 2.0 adopted, with three readings

RULES 2.0 is ValueNet's standard for definitions and annotations, applied to every authored class and property. Three readings are ours, not yours:

1. **Definition form.** "b is a c that d's" is met when the definition opens with an asserted immediate parent as genus. A disposition's differentia may be phrased "to …", as in "a moral value disposition to protect others from harm", so about 148 definitions phrased that way were not rewritten to "that".
2. **Process.** Searching CCO before choosing a parent, and the clarity, inclusiveness and exclusiveness checks, are required. Web search with citations (step 2) is optional.
3. **Scope.** Sections 6 and 7, which describe the reviewing tool itself, add no requirement, and section 4's equivalence handling applies only on request.

### 2.5 Folk curation under D-013 (not breaking)

Your sign-off called definition and documentation curation non-breaking. This is that work; no OWL condition changed.

- All 75 remaining folk definitions whose genus was not their asserted parent now open with it: "a benevolence disposition to …".
- Every folk term now has an `rdfs:comment` and a `skos:example`, and so does every term in the other modules. The genus and annotation checks report none missing.
- Eight definitions changed more than their opening words. Two of them change what the definition says:
  - **`IntuitionDisposition`:** "a personal value disposition to favor intuitive judgment, understanding reached immediately without conscious reasoning, as a guide to belief and action". It now values intuitive judgment rather than relying on an ability.
  - **`EquityDisposition`:** "a justice disposition to distribute resources and opportunities according to individuals' needs and other materially relevant differences, so that the outcome is fair rather than identical". This separates it from `EqualityDisposition`, identical treatment.
- The other six are wording fixes:
  - `StrengthDisposition` and `ExcellenceDisposition` valued "possessing" something, and now value or strive for it;
  - glosses were dropped from `PeaceDisposition`, `BoldnessDisposition` and `LeisureDisposition`;
  - `ForgivenessDisposition` no longer uses "you".

Commit `8cd48be`.

## 3. Verification

- **Reasoner.** HermiT finds the BFO layer consistent, with no unsatisfiable classes, after D-014 and again after the curation.
- **Evidence.** The remediation record lists the exact triples each change added and removed:
  - D-014: 220 added, 56 removed;
  - curation: 340 added, 84 removed.
  The ledger names each change and its reason.
- **Tests.** Every ontology, mapping and competency-question test passes.

## 4. Questions

1. **D-011.** Do you agree it is breaking by your item-5 test, and is anything needed beyond the four reasoner cases in §2.1?
2. **D-014, the removals and re-parenting.** Are removing seven folk IRIs without deprecated aliases, and ending Schwartz Power subsumption for four classes, acceptable on the same footing as items 2 and 3?
3. **D-014, the criteria.** Are M1–M7 an acceptable membership test for the folk module?
4. **D-013.** Are the three readings of RULES 2.0 in §2.4 acceptable?

## Where to find it

| what | path |
|---|---|
| decision records D-005 to D-014 | `docs/bfo/remediation/DECISION_RECORDS.md` |
| our response, with the status of R1–R18 in §11 | `docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_RESPONSE.md` |
| folk membership: criteria, research, and a row for every decided value and class | `docs/bfo/remediation/R15_FOLK_MEMBERSHIP_PROPOSAL.md` |
| RULES 2.0, as recorded | `docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_RULES_2.0.md` |
