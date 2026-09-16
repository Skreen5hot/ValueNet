# R15 — Folk Value Membership: Proposal

**Status:** Proposal, revision 3, 2026-09-16. The owner has signed off on M2–M7 and on separating ontological from correspondence coverage, subject to the corrections this revision makes. Once those are confirmed, R15 is adopted as D-014 in `DECISION_RECORDS.md`, as the governing membership and coverage policy.
**Question (R15 of the formal review response):** which folk values belong in `valuenet-folk.ttl`, before its genus corrections and its comments and examples are written (D-013).
**Evidence:**
- web research carried out 2026-09-16, with every quotation checked against its source;
- the repository's folk corpus (`ThatsAllFolks/folk.ttl` and its trigger lexicons);
- `tools/bfo/folk_coverage.py`;
- the owner's reviews of revisions 1 and 2.

## Revision 3: what changed and why

The owner's second review accepted the architecture:
- classes represent value-related realizable entities;
- labels express identity of concept;
- mappings express weaker conceptual relationships;
- triggers support annotation without asserting identity;
- survey placement is evidence, not taxonomy.

What remained was applying those rules consistently.

| review point | change in this revision |
|---|---|
| M1 must not define roles as if they were dispositions | M1 now distinguishes the two. A value disposition concerns what its bearer treats as important. A value role's external grounding is value- or norm-relevant, whatever the bearer's own valuation — as CCO roles such as Organization Member Role are grounded in expected responsibilities |
| Make M2 durable with a substitution test | M2 now requires it: a candidate is an alternative label only if substituting it for the preferred label leaves the referent class unchanged, not merely because dictionaries call the ordinary-language nouns synonyms |
| Tighten A1 | Fourteen of the 23 "lexical synonyms" fail the substitution test and are now correspondences: Composure, Serenity, Tranquility, Perseverance, Dutiful, Morality, Impartial, Inner peace, Timeliness, Intuitive, Intuitiveness, plus Forgiving (no label would be added), Valor (narrower: courage in battle) and Inquisitive (the label would be a different word). Respect for self now adds its own words as the label. 9 remain |
| Management and Risk-management contradict M1 | Moved from excluded to pending: their sources' senses are unchecked, and M1 forbids exclusion before that check |
| Experience cannot map to a retired class | Pending, with Variety, Adventure or Enjoyment as candidates; Scott Jeffrey lists it under Enjoyment Values |
| ControlDisposition: choose the general parent | Decided in §6: general parent with a correspondence to Schwartz Power, and no definition narrowed to fit a hierarchy |
| Do not keep Mindfulness on related words | Pending under M6. The same strictness now applies to Calmness, Duty and Intuition, which lost their naming corpus values in this revision and have no direct attestation |
| Draft definitions | Intelligence: "to seek the development, possession, or exercise of intellectual ability", no longer circular. Wealth: "the acquisition or retention of financial and material wealth". Moderation's examples must show moderation without an externally imposed rule |

## Revision 2: what changed and why

Revision 1 used `skos:altLabel` as the one mechanism for "this corpus word points roughly here". The owner's review showed why that is wrong: many of those words evoke, indicate or operationalize a value without naming it, and an alternative label asserts that they name it. This revision adopts the review's points:

| review point | change in this revision |
|---|---|
| State M1 in ontological terms; exclude cultural orientations for the right reason | M1 now speaks of value-related realizable entities borne by an Agent. Cultural orientations are excluded as culture-level analytical constructs outside the bearer-level pattern, not because their bearer is not a person — CCO Agents include organizations |
| Split "synonym" into three kinds | M2 separates lexical synonyms (alternative labels), correspondences (mapping and trigger layer) and narrower values (subclass candidates). Every former synonym was re-sorted: 23 are lexical synonyms, 122 are correspondences, 2 are narrower values |
| A survey item is an indicator, not a synonym or subclass | M3 rewritten. Survey items are recorded as correspondences to Schwartz classes. `WealthDisposition` moves under the general personal-value parent. Folk Power's five subclasses are reviewed one by one (§6) instead of being moved wholesale |
| Source count is provenance, not a membership test | M4 now requires the M1 test, a differentia no existing class covers, and paradigmatic examples that separate the class from its siblings; evidence supports a class that passes |
| Emotional states and trait terms are not labels of dispositions | M5 rewritten: Happiness, Contentment, Satisfaction, Smart, Genius, Vitality, Lively and similar words are correspondences |
| Resolve the M4/M6 contradiction | M6 retains a class with no corpus value only if a named source or value research attests it, it is a value role, or a recorded competency question requires it. Discretion, Equity and Resourcefulness become explicit decisions, with their dependencies listed (§7). The stricter split also left 14 classes that no corpus value names; each was checked for direct attestation, 12 are attested, and Decisiveness and Mindfulness join the decisions |
| Do not make bare "Openness" a label | Openness is still retired, but the word goes to the correspondence layer, not to `OpenMindednessDisposition`'s labels |
| Impact is a decision, not an automatic merge | Impact and Influence have different definitions (§7), so no merge is proposed; Impact is decided under M6 |
| Tighter treatment of the new classes | Draft definitions with differentiae; the health and intelligence trait and state words become correspondences; Moderation is distinguished from Discipline |
| Report coverage as several numbers | §4 reports exact classes, lexical synonyms, correspondences, exclusions and pending decisions separately |
| Keep trigger lexicons apart from ontology labels | §5 describes the two layers and the existing vocabulary for the correspondence layer |
| Move Consent to owner judgement; apply the same sense check to Management and Risk-management | Consent moved. Management and Risk-management stay excluded for now, marked as not yet checked against their source's intended sense |
| Say whether value roles count | Module membership is value dispositions and value roles; corpus coverage is measured over corpus values, which include no roles, and roles are reported separately |
| Remove the Schwartz copies only after reviewing their children | §6 |

**Recommended disposition:** adopt R15 once M1–M7 and the coverage model are agreed. Do not yet add the alternative labels in bulk or re-parent anything: each of those waits for its own decision.

## 1. The question

The folk corpus names **278** values. The BFO folk module has **137** classes. They meet in only **92** places:

- **186** corpus values have no class — among them *frugality*, the search that failed in the demonstration.
- **45** module classes name no corpus value.
- **37** trigger lexicons have no class in the corpus at all.

## 2. What the research found

**The corpus has no membership rule to inherit.** De Giorgis and Gangemi's paper gives the method as: "Scrape the web to gather all the main lists of so-called 'values' … collecting more than 350 potential Folk Values, mainly from 7 different URLs", then "Manually analyse the list, in order to filter the granularity of detail, dedupe entities pointing at the very same semantic space (e.g. folk:Winning and folk:Victory) and determine a taxnomy among them" ([arXiv:2303.00632](https://arxiv.org/abs/2303.00632), §5). Apart from that deduplication, it states no inclusion test.

Three further facts about the corpus:

- **Its clusters copy one list author's page headings.** Scott Jeffrey's 2021 page files *family*, *fairness* and *teamwork* under "Spirituality", so a cluster is no evidence of a parent class.
- **Its `inner:InnerValue` typing records provenance, not meaning.**
- **`folk:Religion` is a ValueNet addition**, not an upstream value. D-012 has been corrected, and `ReligionDisposition`'s class comment will be corrected on implementation.

**ValueNet's own Phase 1 term lists.** `docs/bfo/guides/Phase1_RawTerms.md` was "extracted from sources representative of those in `ThatsAllFolks/URLs.txt`". It names no source, and it is where several module-only classes come from (§7). Its successor, `Phase1_NormalizedTerms.md`, already separated "core value concepts from related concepts like goals, capabilities, or states". That is the distinction M2 and M5 make explicit here.

**What a value is.** Schwartz: "trans-situational goals, varying in importance, that serve as guiding principles in the life of a person or group" ([Schwartz et al. 2012](https://library.scottbarrykaufman.com/uploads/2017/09/Schwartz-2012-19-values-JPSP.pdf)). He separates values from traits: "people who exhibit a trait may not value the corresponding goal and those lacking a trait may value the corresponding goal highly" ([overview](https://whatdowevalue.com.au/wp-content/uploads/2021/06/An-Overview-of-the-Schwartz-Theory-of-Basic-Values.pdf)). He excludes happiness, "because people achieve it through attaining whatever outcomes they value". In this ontology the corresponding entity is a value disposition or value role: a realizable entity borne by an Agent. It is neither the principle nor any information content representing the principle.

**Survey items are indicators.** Schwartz's survey lists items that express each value, for example *wealth* under Power, *devout* under Tradition and *capable* under Achievement. An item is evidence of a broader motivational construct: someone may value wealth for security, independence or family, not only for power. So an item's placement shows the construct it indicates, not that it is a taxonomic subclass or a synonym.

**Specific terms.**

- *Frugality*: not a survey item in Schwartz, Rokeach or VIA, and a consumer trait in [Lastovicka et al. 1999](https://academic.oup.com/jcr/article-abstract/26/1/85/1916418). It is, however, a dictionary synonym of *thrift*, and `ThriftDisposition` exists without that label; the missing label, not a missing class, is why the search failed.
- *Openness*: three constructs — the Big Five trait, the VIA strength once called open-mindedness, and Schwartz's openness to change. It is polysemous, so it should not be an unqualified label anywhere.
- *Belief in God*: from a sentence naming a topic, "a belief, or lack thereof, in God".

## 3. Proposed membership criteria

**M1. Membership.** A member is a class whose instances are value-related realizable entities borne by an Agent, of any kind CCO admits:
- a **value disposition**, concerning what the bearer treats as important or normatively significant; or
- a **value role**, whose external grounding is value- or norm-relevant.

A role is not defined by its bearer's own valuation: BFO and CCO roles can be grounded in organizational, social or institutional circumstances whatever the bearer values. Excluded:

- beliefs about how the world is;
- structural dimensions of a theory;
- category headings;
- misspellings;
- population- or culture-level analytical constructs, such as Schwartz's cultural value orientations. The reason is that they are theoretical characterizations of a population's value emphases, outside the module's bearer-level pattern — not that their bearer is a culture rather than a person.

A word whose surface sense is an act, practice, state or property is not excluded on that reading alone: the sense the source intended is checked first.

**M2. Three kinds of correspondence, three mechanisms.**
- *Lexical synonym*: another name for the same concept → `skos:altLabel` on the class. **Substitution test:** a candidate is an alternative label only if substituting it for the preferred label leaves the referent class unchanged — "Frugality Disposition" picks out the same class as "Thrift Disposition". That dictionaries call the ordinary-language nouns synonyms is not enough, and the test catches shifts of category between state, trait and disposition (*serenity* is a state; *calmness disposition* is not). The label added is the corpus term itself.
- *Correspondence*: the word evokes, indicates or operationalizes the value without naming it → the mapping and trigger layer (§5), never a label.
- *Narrower value*: a genuinely more specific value → a subclass candidate, decided under M4.

**M3. Survey items and Schwartz copies.** A corpus word that is a value-survey item is a correspondence to the construct it indicates, never a synonym or subclass on that ground alone. A folk class that repeats a Schwartz class with no differentia is removed. Each of its subclasses moves to the Schwartz class only if its own definition satisfies that class's differentia; otherwise it moves to the general parent, and any correspondence to the Schwartz value is recorded in the mapping layer.

**M4. New classes.** A class is added only if it:
1. passes M1;
2. has a differentia that no existing class covers; and
3. has paradigmatic examples that distinguish it from its siblings.

Value surveys, research and source lists are evidence for a class that passes. The number of lists naming a word is provenance, not a criterion, and one authoritative source can outweigh several popular lists.

**M5. States and traits.** Emotional states and trait terms listed as values — *happiness*, *contentment*, *smart*, *vitality* — are correspondences, not labels of dispositions. The exception is a decision that deliberately introduces a disposition to value that state or trait, made under M4.

**M6. Module classes with no corpus value.** Retained only if at least one holds:
- a named source or value research attests it as a value;
- it is a value role within the module's scope;
- a recorded competency question requires it.

Being a ValueNet addition is not enough. A class that fails all three is removed, once its dependencies are resolved.

**M7. Curation.** Everything retained is curated under D-013: the parent as genus, and a comment and an example for each class.

**Roles and coverage.** The module's membership is value dispositions *and* value roles. The corpus contains no roles, so corpus coverage (§4) is measured over corpus values only, and the four role classes are reported separately (Table B).

## 4. Coverage, reported by kind

Over the 278 corpus values, if this revision's proposals are adopted:

| kind | count | meaning |
|---|---:|---|
| exact class | 96 | a class that is the value — 92 today, plus the 4 new classes |
| lexical synonym | 9 | passes the substitution test; the corpus term becomes an alternative label |
| correspondence | 135 | linked through the mapping and trigger layer; 13 to Schwartz classes and 10 to the proposed new classes. Not ontological coverage |
| excluded | 22 | not a value-related realizable entity under M1 |
| pending | 16 | 14 owner judgements (including Management, Risk-management and Experience) and 2 narrower-value candidates |

The first two rows together, **105**, are the honest measure of how many corpus values the ontology names. Correspondences show what the annotation pipeline can reach, which is a different claim. A tool that reports one blended figure would overstate ontological coverage, so the coverage tool should report these rows separately. Confidence across the 186 decisions: 83 high, 75 medium, 28 low.

## 5. Two layers: labels and correspondences

- **Labels** (`rdfs:label`, `skos:altLabel`) name the class's own concept. Only lexical synonyms go here.
- **Correspondences** say that a corpus value evokes or indicates a class without naming it. The repository already has the vocabulary for this: D-003's annotation-only mapping properties, recorded in `valuenet-mappings.ttl` from the ValueNet class to the corpus value's IRI.
  - `vn-core:historicallyCorrespondsTo`, where the class was refactored from that corpus value;
  - `vn-core:hasRelatedConceptualMatch`, otherwise.
- **Triggers.** The corpus's trigger lexicons stay attached to the corpus value IRIs, so annotation reaches the class through the correspondence. A trigger only has to evoke a value; it does not have to denote the same universal. "Belief in God" can trigger religion-related annotation without becoming a name of `ReligionDisposition`, and "capable" can trigger Achievement without becoming another name for it.

Implementing the correspondences adds mapping assertions, so the site's published mapping counts move with them.

## 6. Folk Power, Security and Tradition

The three folk classes repeat the Schwartz classes of the same name without differentia. Security and Tradition have no subclasses and nothing refers to them, so they can be removed as they stand. Power has five subclasses. Each is checked against the Schwartz definition, "a personal value disposition to seek social status and prestige, and control or dominance over people and resources":

| subclass | its definition | satisfies Schwartz Power? | proposal |
|---|---|---|---|
| `StatusDisposition` | "to seek a high relative social or professional standing" | yes — social status | under `schwartz-values:PowerDisposition` |
| `ControlDisposition` | "to seek the power to influence or direct people's behavior or the course of events" | only in part: "or the course of events" is not control over people or resources | general parent; correspondence to Power. The definition is not narrowed to fit a parent: the hierarchy follows the concept's meaning, unless independent evidence shows ValueNet intends social or resource control |
| `LeadershipDisposition` | "to guide, direct, or command a group, organization, or country" | no — guiding a group need not seek dominance or status | general parent; correspondence to Power |
| `InfluenceDisposition` | "to seek the capacity to have an effect on the character, development, or behavior of someone or something" | no — an effect on development is not dominance | general parent |
| `RecognitionDisposition` | "to seek acknowledgment, appreciation, or validation from others for one's achievements or status" | no — recognition does not entail control | general parent; correspondence to Power and Achievement, since *social recognition* is a secondary survey item for both |

## 7. Module classes that need a decision

**Openness.** Recommendation: retire `OpennessDisposition`. It stands on no corpus value and no value item, and its experience sense is a trait whose value side is already carried by Variety, Adventure and Curiosity. The word *openness* goes to the correspondence layer only; it does not become a label of `OpenMindednessDisposition`, because it is polysemous. This reopens D-012 item 3.

**Impact.** It has a definition of its own:
- Impact: "to seek to have a strong and marked effect on someone or something";
- its parent, Influence: "to seek the capacity to have an effect on the character, development, or behavior of someone or something".

Impact values the effect and its size; Influence values a capacity over agents' character or conduct. That is a differentia, so no merge is proposed. Its provenance is ValueNet's Phase 1 term list, which names no source. Under M6 it is removed unless a competency question requires it.

**Discretion, Equity, Resourcefulness.** Like Impact, these come from the Phase 1 term list, with no named source and no value item found. Under M6 each needs a competency question, or it is removed. Removing any of them has knock-on effects:

| class | depends on it | removal needs |
|---|---|---|
| `DiscretionDisposition` | `moral-epistemics:PrudenceDisposition` maps to it (`hasRelatedConceptualMatch`) and names it in its comment | the mapping and comment revised |
| `EquityDisposition` | `tests/bfo/test_bfo_core_definitions.py` uses it as the leaf for the Justice & Fairness cluster | another leaf chosen |
| `ResourcefulnessDisposition` | nothing | nothing |

Equity is the strongest candidate to keep with a competency question: distribution by need rather than equally is a distinction fairness questions can depend on.

**Decisiveness, Mindfulness, Calmness, Duty and Intuition.** No corpus value *names* any of these classes; corpus words only correspond to them. The other module classes in that position were checked directly against the source lists and value research, and are attested (Table B). These five are not:

| class | corresponding corpus words | direct attestation |
|---|---|---|
| `DecisivenessDisposition` | Decision making | none found |
| `MindfulnessDisposition` | Presence, Alertness, Concentration, Consciousness, Self-awareness | none; Scott Jeffrey lists "Present", "Awareness" and "Attentive", related words rather than the concept |
| `CalmnessDisposition` | Composure, Serenity, Tranquility, Poise | none found; not on Scott Jeffrey's current list |
| `DutyDisposition` | Dutiful | none found |
| `IntuitionDisposition` | Intuitive, Intuitiveness, TrustYourGuts | none found |

Each stays pending under M6 until one of three things is supplied: concept-level evidence that a source instantiates the same value, a recorded competency question, or a decision to remove it. Related words alone do not satisfy M6.

## 8. Decisions the owner needs to make

1. Adopt **M1–M7** and the **coverage model** (§4).
2. The **two-layer rule** (§5): lexical synonyms as labels, correspondences in `valuenet-mappings.ttl`.
3. **Folk Power's subclasses** (§6), as proposed there: Status under Schwartz Power, the other four under the general parent. Security and Tradition can be removed now.
4. **Openness** retired, and **Impact**, **Discretion**, **Equity**, **Resourcefulness**, **Decisiveness**, **Mindfulness**, **Calmness**, **Duty** and **Intuition**: concept-level attestation, a competency question, or removal (§7).
5. The **four new classes**, with their draft definitions (Table A3), and the **two narrower-value candidates**, Patriotism and Work-Life Balance (Table A3).
6. The **14 judgement calls** (Table A4), including the unchecked senses of Management, Risk-management and Experience.

Nothing is implemented until these are settled; the alternative labels and any re-parenting then land one decision at a time.


## Table A — the 186 corpus values with no class

*Source* is the corpus's own attribution. *Confidence*: H high, M medium, L low.


### A1. Lexical synonyms — pass the substitution test (9)

| corpus value | class | label added | conf. | source | why it names the same concept |
|---|---|---|---|---|---|
| Independence | `AutonomyDisposition` | Independence | M | Scott Jeffrey, DevelopGoodHabits, Mind Fool | 'Independence Disposition' picks out the class defined as being 'self-directing and independent in thought and action' |
| Bravery | `CourageDisposition` | Bravery | H | Georgetown | 'Bravery Disposition' picks out the class defined as facing 'danger, difficulty, or pain without being overcome by fear' |
| Politeness | `CourtesyDisposition` | Politeness | H | Schwartz 1992 | the class is defined as showing 'politeness in one's attitude and behavior', so 'Politeness Disposition' picks out the same class |
| Reliability | `DependabilityDisposition` | Reliability | H | — | the class is defined as being 'consistently reliable and trustworthy', so 'Reliability Disposition' picks out the same class |
| Self-discipline | `DisciplineDisposition` | Self-discipline | H | Schwartz 1992 | the class is defined as training oneself or controlling one's impulses, so 'Self-discipline Disposition' picks out the same class |
| Adaptability | `FlexibilityDisposition` | Adaptability | H | Georgetown | the class's own definition glosses it as 'adaptability' |
| Thankfulness | `GratitudeDisposition` | Thankfulness | H | Georgetown | gratitude and thankfulness are ambiguous between state and disposition in the same way, so substituting one for the other keeps the class |
| Respect for self | `SelfRespectDisposition` | Respect for self | H | Spall | 'Respect for self Disposition' picks out the same class as its label |
| Frugality | `ThriftDisposition` | Frugality | H | DevelopGoodHabits | 'Frugality Disposition' picks out the class defined as using 'money and other resources carefully and not wastefully' — the failed demo search |

### A2. Correspondences — mapping and trigger layer (135)

| corpus value | corresponds to | conf. | source | note |
|---|---|---|---|---|
| Daring | `AdventureDisposition` | H | Schwartz 1992 | Schwartz Stimulation item; evokes adventure, does not name it |
| Doing good | `AltruismDisposition` | L | YourDictionary |  |
| Drive | `AmbitionDisposition` | H | Georgetown |  |
| Assertion | `AssertivenessDisposition` | H | Scott Jeffrey, DevelopGoodHabits | names an act; the class names the value of being assertive |
| Congruence | `AuthenticityDisposition` | H | DevelopGoodHabits | corpus comment: true to one's authentic self |
| Rest | `BalanceDisposition` | L | DevelopGoodHabits |  |
| Association | `BelongingDisposition` | L | Mind Fool |  |
| Risk | `BoldnessDisposition` | H | Scott Jeffrey, DevelopGoodHabits | Boldness: 'willing to take risks' |
| Composure | `CalmnessDisposition` | M | DevelopGoodHabits | a state or manner; 'Composure Disposition' would not pick out the calmness class |
| Poise | `CalmnessDisposition` | M | Georgetown |  |
| Serenity | `CalmnessDisposition` | M | Georgetown | a state; fails the substitution test for a disposition class |
| Tranquility | `CalmnessDisposition` | M | Georgetown | a state; fails the substitution test for a disposition class |
| Philanthropy | `CharityDisposition` | H | Mind Fool |  |
| Partnership | `CollaborationDisposition` | H | DevelopGoodHabits |  |
| Building communities | `CommunityDisposition` | H | — |  |
| Involvement | `CommunityDisposition` | M | ValueNet | Community: 'actively participate' |
| Healthy competition | `CompetitionDisposition` | H | Mind Fool |  |
| Victory | `CompetitionDisposition` | H | Scott Jeffrey | ThatsAllFolks README names Victory/Winning as a duplicate pair |
| Healthy relationships | `ConnectionDisposition` | M | Mind Fool |  |
| Trusting relationships | `ConnectionDisposition` | M | DevelopGoodHabits |  |
| Service | `ContributionDisposition` | H | Georgetown | Contribution: 'provide service' |
| Fearless | `CourageDisposition` | H | Georgetown | a trait adjective; fearlessness is not courage, which acts despite fear |
| Valor | `CourageDisposition` | M | Georgetown | courage in battle or great danger — narrower, so not another name for the class |
| Improvisation | `CreativityDisposition` | M | Mind Fool |  |
| Originality | `CreativityDisposition` | H | Georgetown |  |
| Inquisitive | `CuriosityDisposition` | M | Georgetown | an adjective; the label would be a different word, so the corpus term does not name the class |
| Wonder | `CuriosityDisposition` | M | Georgetown |  |
| Decision making | `DecisivenessDisposition` | H | DevelopGoodHabits |  |
| Perseverance | `DeterminationDisposition` | M | DevelopGoodHabits, Spall | persisting is not the same concept as determination, though the class's definition describes it |
| Accuracy | `DiligenceDisposition` | M | Scott Jeffrey, DevelopGoodHabits |  |
| Rigor | `DiligenceDisposition` | M | Scott Jeffrey |  |
| Thoroughfulness | `DiligenceDisposition` | H | Scott Jeffrey |  |
| Self-control | `DisciplineDisposition` | H | Mind Fool | Discipline: 'control impulses' |
| Dutiful | `DutyDisposition` | M | Mind Fool | an adjective; the corpus term does not name the duty class |
| Fun | `EnjoymentDisposition` | H | Scott Jeffrey | Enjoyment: 'pleasure, fun' |
| Lively | `EnthusiasmDisposition` | L | Mind Fool | a trait term |
| Zeal | `EnthusiasmDisposition` | H | Mind Fool |  |
| Goodness | `EthicsDisposition` | L | Georgetown |  |
| Morality | `EthicsDisposition` | M | Spall | a system or quality of right conduct, not the disposition to adhere to one |
| Greatness | `ExcellenceDisposition` | M | Scott Jeffrey |  |
| Performance | `ExcellenceDisposition` | H | Scott Jeffrey | definition names performance |
| Quality | `ExcellenceDisposition` | M | Scott Jeffrey, Mind Fool | a property of work that excellence aims at |
| Workmanship | `ExcellenceDisposition` | M | Mind Fool |  |
| Exciting life | `ExcitementDisposition` | H | Schwartz 1992 | SVS Stimulation item 'an exciting life' |
| Communication | `ExpressivenessDisposition` | M | Georgetown |  |
| Impartial | `FairnessDisposition` | M | Mind Fool | fairness does not require impartial treatment in every case — Equity is need-based |
| Objectivity | `FairnessDisposition` | M | DevelopGoodHabits |  |
| Versatility | `FlexibilityDisposition` | M | DevelopGoodHabits |  |
| Forgiving | `ForgivenessDisposition` | H | Schwartz 1992 | an adjective; no label would be added, so the corpus term does not name the class |
| Giving | `GenerosityDisposition` | H | Scott Jeffrey |  |
| Development | `GrowthDisposition` | H | Scott Jeffrey |  |
| Evolution | `GrowthDisposition` | M | Mind Fool | cluster heading for Improvement |
| Improvement | `GrowthDisposition` | H | Scott Jeffrey |  |
| Potential | `GrowthDisposition` | L | Scott Jeffrey | realizing one's potential |
| Energy | `HealthDisposition` | L | Georgetown | a state or trait |
| Fitness | `HealthDisposition` | M | DevelopGoodHabits, Mind Fool | a condition health values aim at |
| Longevity | `HealthDisposition` | M | DevelopGoodHabits | an outcome of health |
| Vitality | `HealthDisposition` | M | Georgetown | a state or trait of health |
| Sincerity | `HonestyDisposition` | H | Georgetown | Honesty: 'truthful, sincere' |
| Truth | `HonestyDisposition` | H | Georgetown |  |
| Modesty | `HumilityDisposition` | H | Schwartz 1992 | SVS Tradition item 'humble' |
| Amusement | `HumorDisposition` | H | Scott Jeffrey | Humor: 'what is amusing' |
| Playfulness | `HumorDisposition` | M | Georgetown |  |
| Conviction | `IntegrityDisposition` | M | Georgetown |  |
| Brilliance | `IntelligenceDisposition` | M | Scott Jeffrey | a trait term |
| Cleverness | `IntelligenceDisposition` | M | Georgetown | a trait term |
| Genius | `IntelligenceDisposition` | M | Scott Jeffrey | a trait term |
| Reflection | `IntelligenceDisposition` | M | Georgetown | an activity; Rokeach glosses 'intellectual' with 'reflective' |
| Smart | `IntelligenceDisposition` | M | Scott Jeffrey | a trait term |
| Intuitive | `IntuitionDisposition` | M | ValueNet | an adjective; does not name the intuition class |
| Intuitiveness | `IntuitionDisposition` | M | Scott Jeffrey | a quality of a person or a thought; fails the substitution test |
| TrustYourGuts | `IntuitionDisposition` | M | — | a maxim for the same value |
| Contentment | `JoyDisposition` | L | Georgetown | an emotional state; see Happiness |
| Happiness | `JoyDisposition` | M | Georgetown | an emotional state (Schwartz excludes it as a value); correspondence only, unless a disposition to value happiness is introduced |
| Satisfaction | `JoyDisposition` | L | Scott Jeffrey | an emotional state; see Happiness |
| Approachability | `KindnessDisposition` | M | DevelopGoodHabits, Mind Fool |  |
| Consideration | `KindnessDisposition` | H | DevelopGoodHabits | Kindness: 'considerate' |
| Welcoming | `KindnessDisposition` | M | Scott Jeffrey |  |
| Continuous learning | `LearningDisposition` | H | DevelopGoodHabits |  |
| Education | `LearningDisposition` | H | DevelopGoodHabits, Mind Fool | a means or institution of learning |
| Knowledge | `LearningDisposition` | M | Scott Jeffrey, Mind Fool, Spall | an object of learning, not a name for it |
| Recreation | `LeisureDisposition` | H | Scott Jeffrey |  |
| Relaxation | `LeisureDisposition` | M | Mind Fool |  |
| Analysis | `LogicDisposition` | M | Mind Fool |  |
| Reason | `LogicDisposition` | H | Georgetown |  |
| Alertness | `MindfulnessDisposition` | L | Scott Jeffrey |  |
| Concentration | `MindfulnessDisposition` | L | Scott Jeffrey |  |
| Consciousness | `MindfulnessDisposition` | M | Scott Jeffrey |  |
| Presence | `MindfulnessDisposition` | M | Scott Jeffrey, Mind Fool |  |
| Self-awareness | `MindfulnessDisposition` | M | DevelopGoodHabits, Mind Fool |  |
| Receptiveness | `OpenMindednessDisposition` | H | Mind Fool |  |
| Positivity | `OptimismDisposition` | H | Mind Fool, Spall |  |
| Organization | `OrderDisposition` | H | Georgetown | Order: 'organization' |
| Structure | `OrderDisposition` | H | Scott Jeffrey, DevelopGoodHabits |  |
| Intensity | `PassionDisposition` | L | Scott Jeffrey |  |
| Inner peace | `PeaceDisposition` | M | DevelopGoodHabits, Mind Fool | a state; fails the substitution test for a disposition class |
| Silence | `PeaceDisposition` | L | Scott Jeffrey |  |
| Isolation | `PrivacyDisposition` | L | Mind Fool |  |
| Solitude | `PrivacyDisposition` | M | Scott Jeffrey |  |
| Timeliness | `PunctualityDisposition` | H | Georgetown | a property of acts; fails the substitution test |
| Meaningful work | `PurposeDisposition` | M | Mind Fool |  |
| Famous | `RecognitionDisposition` | M | Scott Jeffrey |  |
| Belief in God | `ReligionDisposition` | M | YourDictionary | a YourDictionary sentence about belief 'or lack thereof' in God; a topic that can trigger religion-related annotation |
| Devotion | `ReligionDisposition` | M | Georgetown, Schwartz 1992 | Schwartz Tradition item 'devout'; evokes religion without naming it |
| Self-love | `SelfRespectDisposition` | M | Mind Fool |  |
| Spirit | `SpiritualityDisposition` | H | Scott Jeffrey |  |
| Certainty | `StabilityDisposition` | M | Scott Jeffrey |  |
| Helpfulness | `SupportDisposition` | H | Schwartz 1992 | SVS Benevolence item 'helpful' |
| Helping | `SupportDisposition` | H | YourDictionary |  |
| Stewardship | `SustainabilityDisposition` | M | Georgetown |  |
| Economy | `ThriftDisposition` | H | Scott Jeffrey | polysemous ('the economy'); as a label it would mislead search |
| Acceptance | `ToleranceDisposition` | H | Georgetown | corpus comment: accepting people |
| Diversity | `ToleranceDisposition` | M | DevelopGoodHabits | Schwartz universalism-tolerance: acceptance and understanding of those who are different |
| Inclusiveness | `ToleranceDisposition` | M | DevelopGoodHabits |  |
| Earning trust | `TrustworthinessDisposition` | H | YourDictionary |  |
| Insightful | `UnderstandingDisposition` | H | Georgetown | Understanding: 'with empathy and insight' |
| Distinctiveness | `UniquenessDisposition` | H | Mind Fool |  |
| Novelty | `VarietyDisposition` | H | DevelopGoodHabits | Variety: 'novelty' |
| Surprise | `VarietyDisposition` | L | Scott Jeffrey |  |
| Foresight | `VisionDisposition` | H | Georgetown |  |
| Prosperity | `WealthDisposition` | M | Scott Jeffrey, Mind Fool | Rokeach 'a comfortable life (a prosperous life)' — an end-state, not a name for valuing wealth |
| Common sense | `WisdomDisposition` | M | Georgetown |  |
| Accomplishment | `schwartz:AchievementDisposition` | M | Scott Jeffrey | Rokeach terminal value 'a sense of accomplishment' |
| Capable | `schwartz:AchievementDisposition` | M | Scott Jeffrey | Schwartz Achievement item 'capable' — an indicator of the value |
| Effectiveness | `schwartz:AchievementDisposition` | M | Scott Jeffrey | SVS 'capable' gloss |
| Efficiency | `schwartz:AchievementDisposition` | M | Scott Jeffrey, DevelopGoodHabits | SVS 'capable' gloss |
| Compliance | `schwartz:ConformityDisposition` | M | DevelopGoodHabits |  |
| Lawfulness | `schwartz:ConformityDisposition` | M | Georgetown | Schwartz 2012 conformity-rules |
| Comfort | `schwartz:HedonismDisposition` | L | Scott Jeffrey |  |
| Pleasure | `schwartz:HedonismDisposition` | H | Schwartz 1992 | SVS Hedonism item 'pleasure' |
| Self-indulgence | `schwartz:HedonismDisposition` | H | Schwartz 1992 | SVS Hedonism item 'self-indulgent' |
| Family security | `schwartz:SecurityDisposition` | H | Schwartz 1992 | SVS Security item 'family security' |
| Financial stability | `schwartz:SecurityDisposition` | M | Mind Fool |  |
| Social order | `schwartz:SecurityDisposition` | H | Schwartz 1992 | SVS Security item 'social order' |
| World of Peace | `schwartz:UniversalismDisposition` | H | Schwartz 1992 | Schwartz Universalism item 'a world at peace' — an indicator of the value |

### A3. New classes and narrower values (6)

| corpus value | proposal | parent | conf. | source | draft definition or reason |
|---|---|---|---|---|---|
| Patriotism | narrower value | `LoyaltyDisposition` | M | DevelopGoodHabits, Mind Fool | loyalty to one's country; a subclass candidate under M4, not a synonym |
| Work-Life Balance | narrower value | `BalanceDisposition` | M | Mind Fool | the paradigm case of balance, and narrower than it; a subclass candidate under M4 |
| Health | new `HealthDisposition` | `core:PersonalValueDisposition` | M | Scott Jeffrey, Mind Fool, Spall | draft: a personal value disposition to protect and maintain bodily and mental health. Schwartz 2012: 'health is another value' whose meaning varies across cultures; survey item 'healthy' is secondary |
| Intelligence | new `IntelligenceDisposition` | `core:PersonalValueDisposition` | M | Scott Jeffrey, DevelopGoodHabits | draft: a personal value disposition to seek the development, possession, or exercise of intellectual ability. Rokeach 'intellectual'; README names folk:Intelligence |
| Moderation | new `ModerationDisposition` | `core:PersonalValueDisposition` | M | Georgetown | draft: a personal value disposition to avoid excess and extremes in consumption, feeling and action. Differentia from Discipline, which trains conduct to a code or restrains impulses: moderation aims at a measure, with or without a code. Its examples must show moderation without an externally imposed rule |
| Wealth | new `WealthDisposition` | `core:PersonalValueDisposition` | H | Schwartz 1992 | draft: a personal value disposition to seek the acquisition or retention of financial and material wealth. Under the general parent, since wealth may be valued for security, independence or family as well as power; the Schwartz Power item 'wealth' is recorded as a correspondence |

### A4. Owner judgement (14)

| corpus value | candidate | conf. | source | note |
|---|---|---|---|---|
| Willingness | `CooperationDisposition` | L | ValueNet |  |
| Responsiveness | `DependabilityDisposition` | L | DevelopGoodHabits |  |
| Grace | `GratitudeDisposition` | L | Scott Jeffrey, DevelopGoodHabits | corpus comment: unconditional love and gratitude |
| Irreverent | `HumorDisposition` | L | Scott Jeffrey | playful disregard of convention |
| Inspiration | `PassionDisposition` | L | Georgetown |  |
| Reverence | `ReligionDisposition` | L | Georgetown | deep respect for the sacred |
| Consent | `RespectDisposition` | L | Mind Fool | the noun names an act, but 'valuing consent' is a normative orientation; the source's sense decides |
| Empowerment | `SupportDisposition` | L | Scott Jeffrey, Mind Fool | empowering others or oneself |
| Clarity | `UnderstandingDisposition` | L | Scott Jeffrey, Mind Fool |  |
| Experience | `VarietyDisposition, AdventureDisposition or EnjoymentDisposition` | L | Scott Jeffrey | listed under Scott Jeffrey's Enjoyment Values; its sense decides the target, which cannot be OpennessDisposition |
| Preparedness | `VisionDisposition` | L | DevelopGoodHabits |  |
| Realism | `WisdomDisposition` | L | Georgetown |  |
| Management | `—` | M | Mind Fool | M1 requires the source's intended sense to be checked before exclusion; not yet done |
| Risk-management | `—` | M | Mind Fool | M1 requires the source's intended sense to be checked before exclusion; not yet done |

### A5. Excluded (22)

| corpus value | reason | conf. | source | note |
|---|---|---|---|---|
| BadHealth | a belief, not a value | H | ValueNet | negative world belief or situation (mft:NegativeValue) |
| LifeIsMeaningless | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| OtherPeopleCannotBeTrusted | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| PeopleCannotChangeTheirSituation | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| SelfDoesntDeserveGood | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| StrongSurviveInBrutalWorld | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| Affective autonomy | culture-level construct | H | Schwartz 2006 | a culture-level analytical construct, outside the module's bearer-level pattern |
| Egalitarianism | culture-level construct | H | Schwartz 2006 | a culture-level analytical construct, outside the module's bearer-level pattern |
| Embeddedness | culture-level construct | H | Schwartz 2006 | a culture-level analytical construct, outside the module's bearer-level pattern |
| Hierarchy | culture-level construct | H | Schwartz 2006 | a culture-level analytical construct, outside the module's bearer-level pattern |
| Intellectual autonomy | culture-level construct | H | Schwartz 2006 | a culture-level analytical construct, outside the module's bearer-level pattern |
| Anticipation | category or heading | H | Mind Fool | category or cluster heading |
| Beliefs | category or heading | H | Mind Fool | category or cluster heading |
| Feelings | category or heading | H | Scott Jeffrey | category or cluster heading |
| FolkValue | category or heading | H | — | category or cluster heading |
| Feasibility | not a value orientation | H | Mind Fool | a property of plans |
| Ferocious | not a value orientation | M | Scott Jeffrey | a manner, not an orientation |
| Temperament | not a value orientation | H | Mind Fool | a trait noun with no evaluative direction |
| Personal focus | structural dimension of a theory | H | — | Schwartz structural dimension |
| Self-protection | structural dimension of a theory | H | Schwartz 1992 | Schwartz structural dimension |
| Social focus | structural dimension of a theory | H | — | Schwartz structural dimension |
| Happyness | misspelling | H | trigger lexicon only | misspelling of Happiness; its trigger lexicon joins Happiness's in the correspondence layer |

## Table B — the 45 module classes with no corpus value

*Names* lists corpus values that become alternative labels; *corresponds* lists corpus values linked in the mapping layer. *Scott Jeffrey list* is his current page, checked 2026-09-16.

| class | names | corresponds | proposal |
|---|---|---|---|
| `AssertivenessDisposition` | — | Assertion | keep — Scott Jeffrey list |
| `AutonomyDisposition` | Independence | — | keep — named by a corpus value |
| `BelongingDisposition` | — | Association | keep — Schwartz survey item *sense of belonging* |
| `BoldnessDisposition` | — | Risk | keep — Scott Jeffrey list |
| `CalmnessDisposition` | — | Composure, Poise, Serenity, Tranquility | pending under M6 (§7): no attestation found |
| `CareDisposition` | — | — | keep — Schwartz benevolence–caring; Scott Jeffrey list |
| `ChastityDisposition` | — | — | keep — Scott Jeffrey list |
| `DecisivenessDisposition` | — | Decision making | pending under M6 (§7): no attestation found |
| `DependabilityDisposition` | Reliability | Responsiveness (judgement) | keep — named by a corpus value |
| `DeterminationDisposition` | — | Perseverance | keep — Scott Jeffrey list |
| `DiligenceDisposition` | — | Accuracy, Rigor, Thoroughfulness | keep — Scott Jeffrey list |
| `DisciplineDisposition` | Self-discipline | Self-control | keep — named by a corpus value |
| `DiscretionDisposition` | — | — | decide under M6 (§7); a moral-epistemics mapping depends on it |
| `DutyDisposition` | — | Dutiful | pending under M6 (§7): no attestation found |
| `EncouragementDisposition` | — | — | keep — Scott Jeffrey list |
| `EquityDisposition` | — | — | decide under M6 (§7); a test fixture depends on it |
| `ExcitementDisposition` | — | Exciting life | keep — Schwartz and Rokeach item *an exciting life* |
| `FairnessDisposition` | — | Impartial, Objectivity | keep — Scott Jeffrey list |
| `FlexibilityDisposition` | Adaptability | Versatility | keep — named by a corpus value |
| `ForgivenessDisposition` | — | Forgiving | keep — Schwartz survey item *forgiving*; Scott Jeffrey list |
| `GoodCitizenRole` | — | — | keep — value role |
| `GrowthDisposition` | — | Development, Evolution, Improvement, Potential | keep — Scott Jeffrey list |
| `HumilityDisposition` | — | Modesty | keep — a value in Schwartz's refined theory; Scott Jeffrey list |
| `ImpactDisposition` | — | — | decide under M6: competency question or removal (§7) |
| `InfluenceDisposition` | — | — | keep — survey item *influential*; Scott Jeffrey list; moves to the general parent (§6) |
| `IntimacyDisposition` | — | — | keep — survey item *mature love* attests the value |
| `IntuitionDisposition` | — | Intuitive, Intuitiveness, TrustYourGuts | pending under M6 (§7): no attestation found |
| `LeaderRole` | — | — | keep — value role |
| `LeisureDisposition` | — | Recreation, Relaxation | keep — Rokeach *pleasure (an enjoyable leisurely life)* |
| `LoyaltyDisposition` | — | Patriotism (narrower) | keep — survey item *loyal*; Scott Jeffrey list |
| `MasteryDisposition` | — | — | keep — Scott Jeffrey list |
| `MindfulnessDisposition` | — | Alertness, Concentration, Consciousness, Presence, Self-awareness | pending under M6 (§7): related words only |
| `OpennessDisposition` | — | — | retire (§7); *openness* goes to the correspondence layer |
| `PowerDisposition` | — | — | remove after its subclasses are placed (§6) |
| `PrivacyDisposition` | — | Isolation, Solitude | keep — Schwartz survey item *privacy*; Scott Jeffrey list |
| `ProfessionalismRole` | — | — | keep — value role |
| `PunctualPersonRole` | — | — | keep — value role |
| `ResourcefulnessDisposition` | — | — | decide under M6 (§7) |
| `SecurityDisposition` | — | — | remove — repeats `schwartz-values:SecurityDisposition` |
| `SimplicityDisposition` | — | — | keep — Scott Jeffrey list |
| `ThriftDisposition` | Frugality | Economy | keep — named by a corpus value |
| `ToleranceDisposition` | — | Acceptance, Diversity, Inclusiveness | keep — Schwartz universalism–tolerance; Scott Jeffrey list |
| `TraditionDisposition` | — | — | remove — repeats `schwartz-values:TraditionDisposition` |
| `TrustworthinessDisposition` | — | Earning trust | keep — Schwartz benevolence–dependability; Scott Jeffrey list (*trustworthy*) |
| `VarietyDisposition` | — | Novelty, Surprise | keep — Schwartz survey item *a varied life* |

## Sources

- De Giorgis, S. & Gangemi, A. "That's All Folks: a KG of Values as Commonsense Social Norms and Behaviors." [arXiv:2303.00632](https://arxiv.org/abs/2303.00632); VALE 2023, Springer LNCS, [doi:10.1007/978-3-031-58202-8_2](https://link.springer.com/chapter/10.1007/978-3-031-58202-8_2).
- ThatsAllFolks README and data, [StenDoipanni/ValueNet](https://github.com/StenDoipanni/ValueNet/blob/main/ThatsAllFolks/README.md).
- Schwartz, S. H. et al. (2012). "Refining the theory of basic individual values." *JPSP* 103(4). [PDF](https://library.scottbarrykaufman.com/uploads/2017/09/Schwartz-2012-19-values-JPSP.pdf).
- Schwartz, S. H. (2012). "An Overview of the Schwartz Theory of Basic Values." *Online Readings in Psychology and Culture* 2(1). [Mirror](https://whatdowevalue.com.au/wp-content/uploads/2021/06/An-Overview-of-the-Schwartz-Theory-of-Basic-Values.pdf).
- Rokeach Value Survey: [terminal and instrumental values with descriptors](https://mio-ecsde.org/protarea/Annex_4_3_values_lists.pdf).
- VIA Classification of Character Strengths: [viacharacter.org](https://www.viacharacter.org/character-strengths).
- Lastovicka, J. L. et al. (1999). "Lifestyle of the Tight and Frugal." *Journal of Consumer Research* 26(1). [Abstract](https://academic.oup.com/jcr/article-abstract/26/1/85/1916418).
- Source lists: [Scott Jeffrey](https://scottjeffrey.com/core-values-list/), [DevelopGoodHabits](https://www.developgoodhabits.com/core-values/), [The Mind Fool](https://themindfool.com/list-of-core-values-for-a-balanced-life/), [Benjamin Spall](https://benjaminspall.com/core-values/), [YourDictionary](https://www.yourdictionary.com/articles/examples-core-values); Georgetown Psychology "inner values", [Wayback capture](https://web.archive.org/web/20200814054550/https://georgetownpsychology.com/inner-values/).
- ValueNet Phase 1 term lists: `docs/bfo/guides/Phase1_RawTerms.md`, `docs/bfo/guides/Phase1_NormalizedTerms.md`.

**Not verified:** Rokeach's own chapter on values versus attitudes, the original Roccas et al. (2002), and the word-selection rules of the lexical value studies could not be read. Dictionary senses were seen only in search summaries. The source lists were checked for the module-only classes against Scott Jeffrey's current page only.
