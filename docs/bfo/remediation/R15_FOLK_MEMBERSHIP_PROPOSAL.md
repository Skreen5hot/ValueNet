# R15 — Folk Value Membership: Proposal

**Status:** Proposal, 2026-09-16. It decides nothing. The owner decides; what is adopted becomes D-014 in `DECISION_RECORDS.md`.
**Question (R15 of the formal review response):** which folk values belong in `valuenet-folk.ttl`, before its 84 genus corrections and its comments and examples are written (D-013).
**Evidence:** web research carried out 2026-09-16, with every quotation used below checked against the source; the repository's own folk corpus (`ThatsAllFolks/folk.ttl` and its trigger lexicons); and `tools/bfo/folk_coverage.py`.

## 1. What the question is

The folk corpus names **278** values. The BFO folk module has **137** classes. They meet in only **92** places:

- **186** corpus values have no class — among them *frugality*, the search that failed in the demonstration.
- **45** module classes name no corpus value.
- **37** trigger lexicons have no class in the corpus at all, so the annotation pipeline can evoke values the ontology cannot express.

Nothing records why the two lists differ, and the corpus itself turns out to have no membership rule to inherit.

## 2. What the research found

**The corpus has no inclusion criterion.** De Giorgis and Gangemi's paper describes the method as: "Scrape the web to gather all the main lists of so-called 'values' … collecting more than 350 potential Folk Values, mainly from 7 different URLs", then "Manually analyse the list, in order to filter the granularity of detail, dedupe entities pointing at the very same semantic space (e.g. folk:Winning and folk:Victory) and determine a taxnomy among them" ([arXiv:2303.00632](https://arxiv.org/abs/2303.00632), §5; published in VALE 2023, LNCS). Apart from that deduplication, it states no test of what counts. The README says the module "does not bear any domain expert authority", and the upstream data file calls itself "a quick and dirty collection of values … from the Web". Two consequences follow:

- **The corpus clusters are one list author's page headings, not a taxonomy.** Scott Jeffrey's 2021 core-values page groups *family*, *fairness*, *community* and *teamwork* under "Spirituality", and the corpus copies that grouping. A cluster is therefore no evidence of a parent class.
- **`inner:InnerValue` records where a term came from, not what it means.** It is the typing given to the Georgetown Psychology "inner values" list, a bare alphabetical page with no definitions that is now offline (Wayback capture, 14 Aug 2020).

**`folk:Religion` is a ValueNet addition, not a corpus value.** Upstream has no such entry. This repository declared it (commit d9ee3f1) to hold a 480-trigger religion lexicon. D-012 described it as the corpus's value; that record is corrected alongside this proposal, and `ReligionDisposition`'s class comment, which repeats the claim, is corrected when this proposal is implemented.

**What a value is.** Schwartz defines basic values as "trans-situational goals, varying in importance, that serve as guiding principles in the life of a person or group" ([Schwartz et al. 2012](https://library.scottbarrykaufman.com/uploads/2017/09/Schwartz-2012-19-values-JPSP.pdf)). He separates them from traits: "the same term can refer to both a value and a trait (e.g., wisdom, obedience). However, people who exhibit a trait may not value the corresponding goal and those lacking a trait may value the corresponding goal highly" ([Schwartz 2012 overview](https://whatdowevalue.com.au/wp-content/uploads/2021/06/An-Overview-of-the-Schwartz-Theory-of-Basic-Values.pdf)). He also distinguishes values from beliefs, attitudes and norms. That is the line this module already draws: a value disposition is what an agent treats as important, not what the agent is like.

**Emotional states listed as values.** Schwartz excludes happiness: "Although happiness is an important value, it is not included because people achieve it through attaining whatever outcomes they value" (overview, footnote 2). Later work criticises Rokeach's survey on the same ground, since items such as "happiness" and "inner harmony" "are emotional states … while values are defined as broad goals" ([Sagiv & Schwartz, via PMC12342246](https://pmc.ncbi.nlm.nih.gov/articles/PMC12342246/)).

**Specific terms.**

- *Frugality* is not an item in Schwartz's survey, Rokeach's or the VIA classification. Consumer research treats it as a trait ([Lastovicka et al. 1999](https://academic.oup.com/jcr/article-abstract/26/1/85/1916418)). It is, however, listed by the corpus's own sources, and the module already has **ThriftDisposition** — which carries no "frugal" or "frugality" label. That, not a missing value, is why the search failed.
- *Openness* names three different constructs: the Big Five trait openness to experience; the VIA strength formerly called open-mindedness (judgment); and Schwartz's higher-order group openness to change. As a value, the closest items are the survey item "broadminded" (Universalism) and Rokeach's "broadminded (open-minded)". The corpus authors themselves merged the words: `folk:Open-mindedness` is labelled "open-mindedness, openness".
- *Belief in God* comes from a YourDictionary sentence that frames it as a topic — "a belief, or lack thereof, in God". The value item is Schwartz's "devout (holding to religious faith and belief)", under Tradition.
- *Spirituality* was proposed as an eleventh basic value and "dropped from the theory despite its potential importance in many societies", because it "did not demonstrate a consistent meaning across cultures" (overview). That is no reason to drop it from a folk module, which does not claim cross-cultural universality.
- Schwartz lists the survey items that express each value (overview). Several corpus words are among them, and the tables below cite the item wherever a mapping rests on it:
  - *capable*, *influential*: Achievement;
  - *daring*, *an exciting life*: Stimulation;
  - *pleasure*, *self-indulgent*: Hedonism;
  - *wealth*: Power;
  - *social order*, *family security*, *clean*: Security;
  - *self-discipline*, *politeness*: Conformity;
  - *humble*, *devout*: Tradition;
  - *broadminded*, *a world at peace*: Universalism;
  - secondary items [*healthy*, *moderate*, *sense of belonging*, *privacy*].

## 3. Proposed membership criteria

M1. **A member is a value an agent can hold as a guiding principle.** A word that fails this test is excluded:

- a belief about how the world is, such as "other people cannot be trusted";
- an orientation of a culture rather than a person (Schwartz's cultural value orientations);
- a structural dimension of the theory ("personal focus", "self-protection");
- a category heading ("Feelings", "Beliefs", "FolkValue");
- a practice or act ("risk management", "consent");
- a property of a thing ("feasibility");
- a misspelling.

M2. **One class per value, not one per word.** Synonyms, inflections and near-glosses become `skos:altLabel` on the class that already carries the sense. This is the corpus authors' own deduplication step (Victory/Winning), applied to the words they left in.

M3. **No folk copies of Schwartz classes.** A corpus word that is a survey item for a Schwartz basic value attaches to the Schwartz class, when no folk class carries a narrower sense. A folk class that repeats a Schwartz class with no differentia is removed.

M4. **A new class needs evidence beyond one list, and no existing class covering its sense.** The evidence is a value-survey item (Schwartz, Rokeach, VIA), a naming in the corpus README, or appearance on at least two source lists.

M5. **Emotional states listed as values attach to the nearest existing class** rather than founding one, following Schwartz's exclusion of happiness.

M6. **ValueNet's additions — module classes with no corpus value — are kept when attested** in value research or a source list, or when they are value roles (D-001). They are recorded as additions, not left to look like corpus coverage.

M7. **Everything this admits is then curated under D-013**: parent as genus, and a comment and an example for each class.

## 4. The proposal in numbers

For the 186 corpus values with no class:

| proposal | count |
|---|---:|
| synonym of an existing folk class | 124 |
| synonym of a Schwartz class (M3) | 13 |
| new class | 4 (Health, Intelligence, Moderation, Wealth) |
| synonym of a proposed new class | 10 |
| exclude (M1) | 25 |
| owner judgement | 10 |

Confidence: 97 high, 62 medium, 27 low.

If adopted, the folk module covers **230 of 278** corpus values, up from 92, or **243** once the coverage tool also counts synonyms placed on Schwartz classes. Of the 37 trigger lexicons with no class, 7 already have a BFO class, 25 gain one, 3 wait on the judgement calls, and 2 are excluded (one is the misspelling *Happyness*, whose lexicon follows *Happiness*).

For the 45 module classes with no corpus value, see Table B:

- 25 pair with a corpus value through a synonym above;
- 8 are attested and kept — Loyalty also gains Patriotism as a synonym;
- 4 are value roles and are kept;
- 3 duplicate Schwartz classes and are removed;
- 2 are proposed for merging: Openness (which would otherwise pair with Experience) and Impact;
- 3 are unattested and need a decision.

## 5. Decisions the owner needs to make

1. **Adopt M1–M7.**
2. **Openness.** Recommendation: merge `OpennessDisposition` into `OpenMindednessDisposition`, with "Openness" as an alternative label, and retire the IRI. The reasons:
   - the corpus authors made that merge;
   - Scott Jeffrey files openness under Creativity and Intelligence;
   - in the values literature, the experience sense is a trait (Big Five), and its value analogue — seeking novelty and experience — is already carried by `VarietyDisposition`, `AdventureDisposition` and `CuriosityDisposition`.

   This reopens D-012 item 3, which narrowed Openness to openness to experience only this morning. Keeping it distinct is defensible, but then the class stands on no corpus value and no value item.
3. **The duplicates.** Remove folk `PowerDisposition`, `SecurityDisposition` and `TraditionDisposition`. Folk Power has five subclasses — Leadership, Influence, Recognition, Control and Status — which move to `schwartz-values:PowerDisposition`.
4. **The 10 judgement calls** in Table A (*owner judgement*), each with a suggested home.
5. **The unattested additions.** Discretion, Equity and Resourcefulness appear in no source list checked and no value survey. Recommendation: keep them as recorded ValueNet additions, and merge Impact into Influence, its parent, whose meaning it repeats.
6. **Whether the coverage tool should count Schwartz classes** (M3). Recommendation: yes, so that a corpus value attached under M3 counts as covered instead of looking like a gap.

## 6. What adoption would change

- Most changes are `skos:altLabel` additions on existing classes. The coverage tool's altLabel rule already pairs them, and the site's search already indexes alternative labels, so "frugal" would find Thrift.
- Four new classes, each written to D-013, with RULES 2.0's CCO search and three checks recorded:
  - `HealthDisposition` and `IntelligenceDisposition`, under personal value disposition;
  - `ModerationDisposition`, under personal value disposition, because its survey item is only secondary for Security and Tradition and the 2012 theory set it aside;
  - `WealthDisposition`, under `schwartz-values:PowerDisposition`, where the survey item *wealth* belongs.
- Three classes removed (four with the Openness merge, five with Impact), with their labels moved to the class that absorbs them.
- The folk genus record in `test_definition_discipline.py` loses the removed classes, and gains nothing, since new classes must be written aligned.
- Every pinned count moves in the commit that moves it: the site's content pin, the evidence baseline and ledger, and the coverage figures in `test_folk_coverage.py`.
- Then the folk curation pass: genus corrections, comments and examples for every folk class that remains.


## Table A — the 186 corpus values with no class

*Source* is the corpus's own attribution. *Confidence*: H high, M medium, L low.


### A1. Synonyms of existing classes (137)

| corpus value | proposed home | conf. | source | evidence or reason |
|---|---|---|---|---|
| Daring | `AdventureDisposition` | H | Schwartz 1992 | SVS Stimulation item 'daring'; Adventure: 'daring experiences' |
| Doing good | `AltruismDisposition` | L | YourDictionary |  |
| Drive | `AmbitionDisposition` | H | Georgetown |  |
| Assertion | `AssertivenessDisposition` | H | Scott Jeffrey, DevelopGoodHabits |  |
| Congruence | `AuthenticityDisposition` | H | DevelopGoodHabits | corpus comment: true to one's authentic self |
| Independence | `AutonomyDisposition` | H | Scott Jeffrey, DevelopGoodHabits, MindFool |  |
| Rest | `BalanceDisposition` | L | DevelopGoodHabits |  |
| Work-Life Balance | `BalanceDisposition` | H | MindFool | Balance: 'work, family, and self' |
| Association | `BelongingDisposition` | L | MindFool |  |
| Risk | `BoldnessDisposition` | H | Scott Jeffrey, DevelopGoodHabits | Boldness: 'willing to take risks' |
| Composure | `CalmnessDisposition` | H | DevelopGoodHabits |  |
| Poise | `CalmnessDisposition` | M | Georgetown |  |
| Serenity | `CalmnessDisposition` | H | Georgetown | Calmness: 'tranquil, serene' |
| Tranquility | `CalmnessDisposition` | H | Georgetown |  |
| Philanthropy | `CharityDisposition` | H | MindFool |  |
| Partnership | `CollaborationDisposition` | H | DevelopGoodHabits |  |
| Building communities | `CommunityDisposition` | H | — |  |
| Involvement | `CommunityDisposition` | M | ValueNet | Community: 'actively participate' |
| Healthy competition | `CompetitionDisposition` | H | MindFool |  |
| Victory | `CompetitionDisposition` | H | Scott Jeffrey | ThatsAllFolks README names Victory/Winning as a duplicate pair |
| Healthy relationships | `ConnectionDisposition` | M | MindFool |  |
| Trusting relationships | `ConnectionDisposition` | M | DevelopGoodHabits |  |
| Service | `ContributionDisposition` | H | Georgetown | Contribution: 'provide service' |
| Bravery | `CourageDisposition` | H | Georgetown |  |
| Fearless | `CourageDisposition` | H | Georgetown |  |
| Valor | `CourageDisposition` | H | Georgetown |  |
| Politeness | `CourtesyDisposition` | H | Schwartz 1992 | SVS Conformity item 'politeness' |
| Improvisation | `CreativityDisposition` | M | MindFool |  |
| Originality | `CreativityDisposition` | H | Georgetown |  |
| Inquisitive | `CuriosityDisposition` | H | Georgetown |  |
| Wonder | `CuriosityDisposition` | M | Georgetown |  |
| Decision making | `DecisivenessDisposition` | H | DevelopGoodHabits |  |
| Reliability | `DependabilityDisposition` | H | — |  |
| Perseverance | `DeterminationDisposition` | H | DevelopGoodHabits, Spall |  |
| Accuracy | `DiligenceDisposition` | M | Scott Jeffrey, DevelopGoodHabits |  |
| Rigor | `DiligenceDisposition` | M | Scott Jeffrey |  |
| Thoroughfulness | `DiligenceDisposition` | H | Scott Jeffrey |  |
| Self-control | `DisciplineDisposition` | H | MindFool | Discipline: 'control impulses' |
| Self-discipline | `DisciplineDisposition` | H | Schwartz 1992 | SVS Conformity item 'self-discipline' |
| Dutiful | `DutyDisposition` | H | MindFool |  |
| Fun | `EnjoymentDisposition` | H | Scott Jeffrey | Enjoyment: 'pleasure, fun' |
| Lively | `EnthusiasmDisposition` | L | MindFool |  |
| Zeal | `EnthusiasmDisposition` | H | MindFool |  |
| Goodness | `EthicsDisposition` | L | Georgetown |  |
| Morality | `EthicsDisposition` | H | Spall |  |
| Greatness | `ExcellenceDisposition` | M | Scott Jeffrey |  |
| Performance | `ExcellenceDisposition` | H | Scott Jeffrey | definition names performance |
| Quality | `ExcellenceDisposition` | M | Scott Jeffrey, MindFool |  |
| Workmanship | `ExcellenceDisposition` | M | MindFool |  |
| Exciting life | `ExcitementDisposition` | H | Schwartz 1992 | SVS Stimulation item 'an exciting life' |
| Communication | `ExpressivenessDisposition` | M | Georgetown |  |
| Impartial | `FairnessDisposition` | H | MindFool | folk Fairness: 'treat people impartially' |
| Objectivity | `FairnessDisposition` | M | DevelopGoodHabits |  |
| Adaptability | `FlexibilityDisposition` | H | Georgetown | Flexibility: 'adaptability' |
| Versatility | `FlexibilityDisposition` | M | DevelopGoodHabits |  |
| Forgiving | `ForgivenessDisposition` | H | Schwartz 1992 | SVS Benevolence item 'forgiving' |
| Giving | `GenerosityDisposition` | H | Scott Jeffrey |  |
| Thankfulness | `GratitudeDisposition` | H | Georgetown |  |
| Development | `GrowthDisposition` | H | Scott Jeffrey |  |
| Evolution | `GrowthDisposition` | M | MindFool | cluster heading for Improvement |
| Improvement | `GrowthDisposition` | H | Scott Jeffrey |  |
| Potential | `GrowthDisposition` | L | Scott Jeffrey | realizing one's potential |
| Sincerity | `HonestyDisposition` | H | Georgetown | Honesty: 'truthful, sincere' |
| Truth | `HonestyDisposition` | H | Georgetown |  |
| Modesty | `HumilityDisposition` | H | Schwartz 1992 | SVS Tradition item 'humble' |
| Amusement | `HumorDisposition` | H | Scott Jeffrey | Humor: 'what is amusing' |
| Playfulness | `HumorDisposition` | M | Georgetown |  |
| Conviction | `IntegrityDisposition` | M | Georgetown |  |
| Intuitive | `IntuitionDisposition` | H | ValueNet |  |
| Intuitiveness | `IntuitionDisposition` | H | Scott Jeffrey |  |
| TrustYourGuts | `IntuitionDisposition` | M | — | a maxim for the same value |
| Contentment | `JoyDisposition` | L | Georgetown | an emotional state; see Happiness |
| Happiness | `JoyDisposition` | M | Georgetown | Schwartz excludes happiness as a basic value: it is attained through whatever else one values |
| Satisfaction | `JoyDisposition` | L | Scott Jeffrey | an emotional state; see Happiness |
| Approachability | `KindnessDisposition` | M | DevelopGoodHabits, MindFool |  |
| Consideration | `KindnessDisposition` | H | DevelopGoodHabits | Kindness: 'considerate' |
| Welcoming | `KindnessDisposition` | M | Scott Jeffrey |  |
| Continuous learning | `LearningDisposition` | H | DevelopGoodHabits |  |
| Education | `LearningDisposition` | H | DevelopGoodHabits, MindFool |  |
| Knowledge | `LearningDisposition` | M | Scott Jeffrey, MindFool, Spall |  |
| Recreation | `LeisureDisposition` | H | Scott Jeffrey |  |
| Relaxation | `LeisureDisposition` | M | MindFool |  |
| Analysis | `LogicDisposition` | M | MindFool |  |
| Reason | `LogicDisposition` | H | Georgetown |  |
| Patriotism | `LoyaltyDisposition` | M | DevelopGoodHabits, MindFool | folk Loyalty: 'to a ... nation' |
| Alertness | `MindfulnessDisposition` | L | Scott Jeffrey |  |
| Concentration | `MindfulnessDisposition` | L | Scott Jeffrey |  |
| Consciousness | `MindfulnessDisposition` | M | Scott Jeffrey |  |
| Presence | `MindfulnessDisposition` | M | Scott Jeffrey, MindFool |  |
| Self-awareness | `MindfulnessDisposition` | M | DevelopGoodHabits, MindFool |  |
| Receptiveness | `OpenMindednessDisposition` | H | MindFool |  |
| Experience | `OpennessDisposition` | L | Scott Jeffrey | moves with Openness if Openness merges into OpenMindedness |
| Positivity | `OptimismDisposition` | H | MindFool, Spall |  |
| Organization | `OrderDisposition` | H | Georgetown | Order: 'organization' |
| Structure | `OrderDisposition` | H | Scott Jeffrey, DevelopGoodHabits |  |
| Intensity | `PassionDisposition` | L | Scott Jeffrey |  |
| Inner peace | `PeaceDisposition` | H | DevelopGoodHabits, MindFool | Rokeach 'inner harmony' |
| Silence | `PeaceDisposition` | L | Scott Jeffrey |  |
| Isolation | `PrivacyDisposition` | L | MindFool |  |
| Solitude | `PrivacyDisposition` | M | Scott Jeffrey |  |
| Timeliness | `PunctualityDisposition` | H | Georgetown |  |
| Meaningful work | `PurposeDisposition` | M | MindFool |  |
| Famous | `RecognitionDisposition` | M | Scott Jeffrey |  |
| Belief in God | `ReligionDisposition` | M | YourDictionary | source is a YourDictionary sentence about belief in God 'or lack thereof': a topic, taken here in its religious sense |
| Devotion | `ReligionDisposition` | M | Georgetown, Schwartz 1992 | SVS Tradition item 'devout' |
| Respect for self | `SelfRespectDisposition` | H | Spall | Rokeach terminal 'self-respect' |
| Self-love | `SelfRespectDisposition` | M | MindFool |  |
| Spirit | `SpiritualityDisposition` | H | Scott Jeffrey |  |
| Certainty | `StabilityDisposition` | M | Scott Jeffrey |  |
| Helpfulness | `SupportDisposition` | H | Schwartz 1992 | SVS Benevolence item 'helpful' |
| Helping | `SupportDisposition` | H | YourDictionary |  |
| Stewardship | `SustainabilityDisposition` | M | Georgetown |  |
| Economy | `ThriftDisposition` | H | Scott Jeffrey |  |
| Frugality | `ThriftDisposition` | H | DevelopGoodHabits | not an item in SVS, RVS or VIA, and a consumer trait in Lastovicka et al. 1999; but listed by developgoodhabits and Scott Jeffrey, and Thrift already has the class. The demo search failed because Thrift has no such label |
| Acceptance | `ToleranceDisposition` | H | Georgetown | corpus comment: accepting people |
| Diversity | `ToleranceDisposition` | M | DevelopGoodHabits | Schwartz universalism-tolerance: acceptance and understanding of those who are different |
| Inclusiveness | `ToleranceDisposition` | M | DevelopGoodHabits |  |
| Earning trust | `TrustworthinessDisposition` | H | YourDictionary |  |
| Insightful | `UnderstandingDisposition` | H | Georgetown | Understanding: 'with empathy and insight' |
| Distinctiveness | `UniquenessDisposition` | H | MindFool |  |
| Novelty | `VarietyDisposition` | H | DevelopGoodHabits | Variety: 'novelty' |
| Surprise | `VarietyDisposition` | L | Scott Jeffrey |  |
| Foresight | `VisionDisposition` | H | Georgetown |  |
| Common sense | `WisdomDisposition` | M | Georgetown |  |
| Accomplishment | `schwartz:AchievementDisposition` | M | Scott Jeffrey | Rokeach terminal value 'a sense of accomplishment' |
| Capable | `schwartz:AchievementDisposition` | M | Scott Jeffrey | SVS Achievement item 'capable (competent, effective, efficient)' |
| Effectiveness | `schwartz:AchievementDisposition` | M | Scott Jeffrey | SVS 'capable' gloss |
| Efficiency | `schwartz:AchievementDisposition` | M | Scott Jeffrey, DevelopGoodHabits | SVS 'capable' gloss |
| Compliance | `schwartz:ConformityDisposition` | M | DevelopGoodHabits |  |
| Lawfulness | `schwartz:ConformityDisposition` | M | Georgetown | Schwartz 2012 conformity-rules |
| Comfort | `schwartz:HedonismDisposition` | L | Scott Jeffrey |  |
| Pleasure | `schwartz:HedonismDisposition` | H | Schwartz 1992 | SVS Hedonism item 'pleasure' |
| Self-indulgence | `schwartz:HedonismDisposition` | H | Schwartz 1992 | SVS Hedonism item 'self-indulgent' |
| Family security | `schwartz:SecurityDisposition` | H | Schwartz 1992 | SVS Security item 'family security' |
| Financial stability | `schwartz:SecurityDisposition` | M | MindFool |  |
| Social order | `schwartz:SecurityDisposition` | H | Schwartz 1992 | SVS Security item 'social order' |
| World of Peace | `schwartz:UniversalismDisposition` | H | Schwartz 1992 | SVS Universalism item 'a world at peace' |

### A2. Synonyms of proposed new classes (10)

| corpus value | proposed home | conf. | source | evidence or reason |
|---|---|---|---|---|
| Energy | `HealthDisposition` | L | Georgetown |  |
| Fitness | `HealthDisposition` | M | DevelopGoodHabits, MindFool |  |
| Longevity | `HealthDisposition` | M | DevelopGoodHabits |  |
| Vitality | `HealthDisposition` | M | Georgetown |  |
| Brilliance | `IntelligenceDisposition` | M | Scott Jeffrey |  |
| Cleverness | `IntelligenceDisposition` | M | Georgetown |  |
| Genius | `IntelligenceDisposition` | M | Scott Jeffrey |  |
| Reflection | `IntelligenceDisposition` | M | Georgetown | Rokeach 'intellectual (intelligent, reflective)' |
| Smart | `IntelligenceDisposition` | M | Scott Jeffrey |  |
| Prosperity | `WealthDisposition` | M | Scott Jeffrey, MindFool | Rokeach 'a comfortable life (a prosperous life)' |

### A3. New classes (4)

| corpus value | proposed home | conf. | source | evidence or reason |
|---|---|---|---|---|
| Health | `HealthDisposition` | M | Scott Jeffrey, MindFool, Spall | Schwartz 2012: health is another value whose meaning varies across cultures; SVS secondary item 'healthy'; README names folk:Fitness |
| Intelligence | `IntelligenceDisposition` | M | Scott Jeffrey, DevelopGoodHabits | README names folk:Intelligence |
| Moderation | `ModerationDisposition` | M | Georgetown | SVS secondary item 'moderate' (Security, Tradition), set aside in the 2012 theory; VIA virtue temperance |
| Wealth | `WealthDisposition` | H | Schwartz 1992 | SVS Power item 'wealth', so under schwartz:PowerDisposition; README names wealthiness |

### A4. Owner judgement (10)

| corpus value | proposed home | conf. | source | evidence or reason |
|---|---|---|---|---|
| Willingness | `CooperationDisposition` | L | ValueNet |  |
| Responsiveness | `DependabilityDisposition` | L | DevelopGoodHabits |  |
| Grace | `GratitudeDisposition` | L | Scott Jeffrey, DevelopGoodHabits | corpus comment: unconditional love and gratitude |
| Irreverent | `HumorDisposition` | L | Scott Jeffrey | playful disregard of convention |
| Inspiration | `PassionDisposition` | L | Georgetown |  |
| Reverence | `ReligionDisposition` | L | Georgetown | deep respect for the sacred |
| Empowerment | `SupportDisposition` | L | Scott Jeffrey, MindFool | empowering others or oneself |
| Clarity | `UnderstandingDisposition` | L | Scott Jeffrey, MindFool |  |
| Preparedness | `VisionDisposition` | L | DevelopGoodHabits |  |
| Realism | `WisdomDisposition` | L | Georgetown |  |

### A5. Excluded (25)

| corpus value | reason code | conf. | source | evidence or reason |
|---|---|---|---|---|
| BadHealth | a belief, not a value | H | ValueNet | negative world belief or situation (mft:NegativeValue) |
| LifeIsMeaningless | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| OtherPeopleCannotBeTrusted | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| PeopleCannotChangeTheirSituation | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| SelfDoesntDeserveGood | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| StrongSurviveInBrutalWorld | a belief, not a value | H | YourDictionary | negative world belief or situation (mft:NegativeValue) |
| Affective autonomy | culture-level orientation | H | Schwartz 2006 | Schwartz cultural value orientation |
| Egalitarianism | culture-level orientation | H | Schwartz 2006 | Schwartz cultural value orientation |
| Embeddedness | culture-level orientation | H | Schwartz 2006 | Schwartz cultural value orientation |
| Hierarchy | culture-level orientation | H | Schwartz 2006 | Schwartz cultural value orientation |
| Intellectual autonomy | culture-level orientation | H | Schwartz 2006 | Schwartz cultural value orientation |
| Anticipation | category or heading | H | MindFool | category or cluster heading |
| Beliefs | category or heading | H | MindFool | category or cluster heading |
| Feelings | category or heading | H | Scott Jeffrey | category or cluster heading |
| FolkValue | category or heading | H | — | category or cluster heading |
| Management | category or heading | M | MindFool | cluster heading; an activity |
| Consent | not an orientation | M | MindFool | an act, not a standing orientation |
| Feasibility | not an orientation | H | MindFool | a property of plans |
| Ferocious | not an orientation | M | Scott Jeffrey | a manner, not an orientation |
| Risk-management | not an orientation | M | MindFool | a practice |
| Temperament | not an orientation | H | MindFool | a trait noun with no evaluative direction |
| Personal focus | Schwartz structural dimension | H | — | Schwartz structural dimension |
| Self-protection | Schwartz structural dimension | H | Schwartz 1992 | Schwartz structural dimension |
| Social focus | Schwartz structural dimension | H | — | Schwartz structural dimension |
| Happyness | misspelling | H | trigger lexicon only | misspelling of Happiness; its trigger fragment follows Happiness to JoyDisposition |

## Table B — the 45 module classes with no corpus value

*Scott Jeffrey list* means his current core-values page, checked 2026-09-16.

| class | proposal | through or because |
|---|---|---|
| `AssertivenessDisposition` | pairs | Assertion |
| `AutonomyDisposition` | pairs | Independence |
| `BelongingDisposition` | pairs | Association |
| `BoldnessDisposition` | pairs | Risk |
| `CalmnessDisposition` | pairs | Composure, Poise, Serenity, Tranquility |
| `CareDisposition` | keep | Schwartz benevolence–caring; Scott Jeffrey list |
| `ChastityDisposition` | keep | Scott Jeffrey list |
| `DecisivenessDisposition` | pairs | Decision making |
| `DependabilityDisposition` | pairs | Reliability, Responsiveness |
| `DeterminationDisposition` | pairs | Perseverance |
| `DiligenceDisposition` | pairs | Accuracy, Rigor, Thoroughfulness |
| `DisciplineDisposition` | pairs | Self-control, Self-discipline |
| `DiscretionDisposition` | owner | no source list or value item found; recommend keeping as a recorded ValueNet addition |
| `DutyDisposition` | pairs | Dutiful |
| `EncouragementDisposition` | keep | Scott Jeffrey list |
| `EquityDisposition` | owner | no source list or value item found; recommend keeping as a recorded ValueNet addition — equity, need-based, is not equality |
| `ExcitementDisposition` | pairs | Exciting life |
| `FairnessDisposition` | pairs | Impartial, Objectivity |
| `FlexibilityDisposition` | pairs | Adaptability, Versatility |
| `ForgivenessDisposition` | pairs | Forgiving |
| `GoodCitizenRole` | keep | value role (D-001); ValueNet addition |
| `GrowthDisposition` | pairs | Development, Evolution, Improvement, Potential |
| `HumilityDisposition` | pairs | Modesty |
| `ImpactDisposition` | merge (owner) | into its parent `InfluenceDisposition`; no source list or value item names it |
| `InfluenceDisposition` | keep | survey item *influential* (Achievement); Scott Jeffrey list |
| `IntimacyDisposition` | keep | survey item *mature love* (Benevolence) |
| `IntuitionDisposition` | pairs | Intuitive, Intuitiveness, TrustYourGuts |
| `LeaderRole` | keep | value role (D-001); ValueNet addition |
| `LeisureDisposition` | pairs | Recreation, Relaxation |
| `LoyaltyDisposition` | keep | survey item *loyal* (Benevolence); Scott Jeffrey list; paired with Patriotism |
| `MasteryDisposition` | keep | Scott Jeffrey list |
| `MindfulnessDisposition` | pairs | Alertness, Concentration, Consciousness, Presence, Self-awareness |
| `OpennessDisposition` | merge (owner) | into `OpenMindednessDisposition`; see §5.2 |
| `PowerDisposition` | remove | duplicates `schwartz-values:PowerDisposition` with no differentia; its 5 subclasses move to the Schwartz class |
| `PrivacyDisposition` | pairs | Isolation, Solitude |
| `ProfessionalismRole` | keep | value role (D-001); ValueNet addition |
| `PunctualPersonRole` | keep | value role (D-001); ValueNet addition |
| `ResourcefulnessDisposition` | owner | no source list or value item found; recommend keeping as a recorded ValueNet addition |
| `SecurityDisposition` | remove | duplicates `schwartz-values:SecurityDisposition` |
| `SimplicityDisposition` | keep | Scott Jeffrey list |
| `ThriftDisposition` | pairs | Economy, Frugality |
| `ToleranceDisposition` | pairs | Acceptance, Diversity, Inclusiveness |
| `TraditionDisposition` | remove | duplicates `schwartz-values:TraditionDisposition` |
| `TrustworthinessDisposition` | pairs | Earning trust |
| `VarietyDisposition` | pairs | Novelty, Surprise |

## Sources

- De Giorgis, S. & Gangemi, A. "That's All Folks: a KG of Values as Commonsense Social Norms and Behaviors." [arXiv:2303.00632](https://arxiv.org/abs/2303.00632); VALE 2023, Springer LNCS, [doi:10.1007/978-3-031-58202-8_2](https://link.springer.com/chapter/10.1007/978-3-031-58202-8_2).
- ThatsAllFolks README and data, [StenDoipanni/ValueNet](https://github.com/StenDoipanni/ValueNet/blob/main/ThatsAllFolks/README.md).
- Schwartz, S. H. et al. (2012). "Refining the theory of basic individual values." *JPSP* 103(4). [PDF](https://library.scottbarrykaufman.com/uploads/2017/09/Schwartz-2012-19-values-JPSP.pdf).
- Schwartz, S. H. (2012). "An Overview of the Schwartz Theory of Basic Values." *Online Readings in Psychology and Culture* 2(1), doi:10.9707/2307-0919.1116. [Mirror](https://whatdowevalue.com.au/wp-content/uploads/2021/06/An-Overview-of-the-Schwartz-Theory-of-Basic-Values.pdf).
- Rokeach Value Survey, 18 terminal and 18 instrumental values: [list with descriptors](https://mio-ecsde.org/protarea/Annex_4_3_values_lists.pdf).
- VIA Classification of Character Strengths: [viacharacter.org](https://www.viacharacter.org/character-strengths); Seligman et al. 2005, [PDF](https://greatergood.berkeley.edu/images/uploads/Seligman-PosPsychProgress.pdf).
- Lastovicka, J. L. et al. (1999). "Lifestyle of the Tight and Frugal." *Journal of Consumer Research* 26(1). [Abstract](https://academic.oup.com/jcr/article-abstract/26/1/85/1916418).
- Source lists: [Scott Jeffrey](https://scottjeffrey.com/core-values-list/), [DevelopGoodHabits](https://www.developgoodhabits.com/core-values/), [The Mind Fool](https://themindfool.com/list-of-core-values-for-a-balanced-life/), [Benjamin Spall](https://benjaminspall.com/core-values/), [YourDictionary](https://www.yourdictionary.com/articles/examples-core-values); Georgetown Psychology "inner values", offline, [Wayback capture](https://web.archive.org/web/20200814054550/https://georgetownpsychology.com/inner-values/).

**Not verified:** the research could not read Rokeach's own chapter on values versus attitudes, the original Roccas et al. (2002), or the lexical studies' word-selection criteria. Dictionary senses were seen only in search summaries. Which source lists carry Discretion, Equity, Impact, Intimacy and Resourcefulness was checked against Scott Jeffrey's current page only.
