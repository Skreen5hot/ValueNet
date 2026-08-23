# Plan for Integrating Folk Values into BFO-Aligned ValueNet

This document outlines the strategic plan for systematically expanding the BFO-aligned ValueNet ontology to include a comprehensive collection of "folk values"—the everyday terms people use to describe what is important to them.

## 1. Objective

The primary goal is to create a comprehensive, BFO-aligned ontology of human values by systematically identifying, analyzing, and modeling folk values. The final product should be:

*   **Rigorous:** Adhering strictly to the realist principles of BFO and the established `valuenet-core` model (e.g., the Disposition vs. Role distinction).
*   **Comprehensive:** Covering the breadth of common value terms found in everyday language and popular psychology.
*   **Organized:** Intelligently structuring the "messiness" of language by using a combination of `rdfs:subClassOf` for formal hierarchy and `skos` for conceptual mapping, avoiding a flat, unmanageable list of terms.
*   **Maintainable:** Developed in a modular, iterative fashion that allows for review, refinement, and future expansion.

## 2. Core Strategy: Thematic Iteration

A "bulk import" of hundreds of value terms would be unreliable and lead to an inconsistent ontology. Instead, we will follow a **thematic, iterative approach**.

1.  **Consolidate & Cluster:** We will first create a master list of candidate value terms from the source URLs. These terms will then be grouped into thematic clusters (e.g., "Achievement & Growth," "Community & Social Connection").
2.  **Process by Cluster:** We will tackle one thematic cluster at a time. This allows for focused analysis of related terms, enabling consistent decisions about synonymy, hierarchy, and definitions.
3.  **Model with Precision:** For each term within a cluster, we will perform a careful ontological analysis to determine if it represents:
    *   A `ValueDisposition` (an internal tendency).
    *   A `ValueRole` (an external expectation).
    *   A synonym or specific type of an existing disposition/role.
    *   Something else entirely (e.g., a goal, a virtue, a capability) that should be modeled differently or excluded.
4.  **Integrate & Document:** Approved classes will be added to `valuenet-folk.owl` with clear, OBO-style definitions and appropriate axioms (`rdfs:subClassOf`, `skos:broadMatch`) linking them to the core and Schwartz modules.

## 3. Execution Plan & Progress Tracker

This section will serve as our living progress tracker.

### Phase 1: Term Consolidation & Clustering

*   [x] **Task 1.1:** Extract all unique value terms from the source URLs in `ThatsAllFolks/URLs.txt`.
*   [x] **Task 1.2:** Normalize and de-duplicate the master list of terms.
*   [x] **Task 1.3:** Group the master list of terms into the thematic clusters defined below.

### Phase 2: Thematic Modeling Sprints

We will process the following clusters iteratively.

**Cluster Modeling Checklist:**

*   [x] **Foundational Concepts** (Kindness, Punctuality, Responsibility, Authenticity) - *Completed*
*   [x] **Achievement & Growth** (Ambition, Excellence, Learning, Creativity) - *Completed*
*   [x] **Community & Social Connection:** Values related to interaction, relationships, and social bonds. - *Completed*
    > Terms: `Altruism`, `Belonging`, `Care`, `Charity`, `Citizenship`, `Collaboration`, `Community`, `Compassion`, `Connection`, `Contribution`, `Cooperation`, `Empathy`, `Encouragement`, `Family`, `Friendship`, `Generosity`, `Intimacy`, `Love`, `Selflessness`, `Sharing`, `Support`, `Teamwork`, `Unity`

*   [x] **Integrity & Principle:** Values related to moral character, ethical conduct, and adherence to principles. - *Completed*
    > Terms: `Candor`, `Dependability`, `Dignity`, `Ethics`, `Faith`, `Fidelity`, `Honesty`, `Honor`, `Integrity`, `Responsibility`, `Self-respect`, `Transparency`, `Trust`

*   [x] **Security & Stability:** Values related to order, safety, and predictability. - *Completed*
    > Terms: `Cleanliness`, `Consistency`, `Order`, `Punctuality`, `Security`, `Stability`, `Tradition`

*   [x] **Freedom & Autonomy:** Values related to independence, self-direction, and personal liberty. - *Completed*
    > Terms: `Autonomy`, `Freedom`, `Privacy`

*   [x] **Well-being & Harmony:** Values related to inner peace, contentment, and a balanced life. - *Completed*
    > Terms: `Balance`, `Calmness`, `Harmony`, `Hope`, `Joy`, `Leisure`, `Meaning`, `Mindfulness`, `Optimism`, `Peace`, `Purpose`, `Simplicity`, `Spirituality`

*   [x] **Justice & Fairness:** Values related to equity, rights, and respectful treatment. - *Completed*
    > Terms: `Accountability`, `Courtesy`, `Diversity`, `Duty`, `Equality`, `Equity`, `Fairness`, `Forgiveness`, `Justice`, `Respect`, `Tolerance`

*   [x] **Power & Influence:** Values related to status, control, and impact on the world. - *Completed*
    > Terms: `Assertiveness`, `Boldness`, `Control`, `Influence`, `Leadership`, `Power`, `Recognition`, `Status`, `Vision`

*   [x] **Achievement & Growth:** Values related to competence, self-improvement, and accomplishment. - *Completed*
    > Terms: `Achievement`, `Ambition`, `Creativity`, `Determination`, `Diligence`, `Excellence`, `Growth`, `Impact`, `Learning`, `Mastery`, `Professionalism`, `Resilience`, `Resourcefulness`, `Strength`, `Wisdom`

*   [x] **Experiential & Stimulation:** Values related to novelty, excitement, and aesthetic appreciation. - *Completed*
    > Terms: `Adventure`, `Beauty`, `Challenge`, `Curiosity`, `Discovery`, `Enjoyment`, `Enthusiasm`, `Excitement`, `Exploration`, `Expressiveness`, `Flexibility`, `Humor`, `Imagination`, `Innovation`, `Intuition`, `Passion`, `Spontaneity`, `Uniqueness`, `Variety`

*   [x] **Discipline & Restraint:** Values related to self-control, prudence, and moderation. - *Completed*
    > Terms: `Chastity`, `Decisiveness`, `Discipline`, `Discretion`, `Endurance`, `Maturity`, `Patience`, `Thrift`

*   [x] **Intellectual:** Values related to reason, logic, and understanding. - *Completed*
    > Terms: `Logic`, `Open-mindedness`, `Openness`, `Understanding`

*(This list of clusters will be refined and expanded as part of Task 1.3)*

### Phase 2.1: Gap-Filling Sprints

Following the coverage analysis in Phase 3, this phase will address the remaining high-priority concepts from the normalized list.

**Gap-Filling Cluster Checklist:**

*   [x] **Core Social Bonds:** `Belonging`, `Community`, `Connection`, `Family`, `Intimacy`, `Love`, `Unity` - *Completed*

*   [x] **Prosocial Actions:** `Care`, `Charity`, `Collaboration`, `Empathy`, `Encouragement`, `Selflessness`, `Sharing`, `Support`, `Teamwork` - *Completed*

*   [x] **Core Moral Principles:** `Candor`, `Dignity`, `Ethics`, `Faith`, `Honor`, `Transparency`, `Trust` - *Completed*

*   [x] **Personal Fortitude:** `Boldness`, `Courage`, `Diligence`, `Impact`, `Strength` - *Completed*

*   [x] **Experiential Openness:** `Enthusiasm`, `Excitement`, `Exploration`, `Expressiveness`, `Flexibility`, `Imagination`, `Intuition`, `Uniqueness` - *Completed*

*   [x] **Personal Conduct & Demeanor:** `Chastity`, `Commitment`, `Competition`, `Control`, `Courtesy`, `Discretion`, `Duty`, `Gratitude`, `Hope`, `Humility`, `Maturity`, `Professionalism`, `Status` - *Completed*

*   [x] **Life Philosophy & State:** `Discovery`, `Leisure`, `Meaning`, `Mindfulness`, `Peace`, `Sensitivity`, `Simplicity`, `Sustainability` - *Completed*


### Phase 3: Review and Refinement

This phase involves a rigorous testing and validation process to ensure the quality and consistency of the ontology. The full methodology is detailed in the `TestingFramework.md` document.

*   [x] **Task 3.1: Execute Testing Framework:** Systematically perform all checks outlined in `TestingFramework.md`, including reasoner validation and all SPARQL sanity checks. Document and fix any issues found. - *Completed*

### Phase 4: Linguistic Grounding (Future Work)

With the folk value module now mature, we can address the gap left by the removal of `vcvf:triggers`.

*   [x] **Task 4.1:** Define a formal annotation property (e.g., `vn-core:isEvidenceFor`) to link linguistic units (text spans, frames) to `ValueRealizationProcess` instances. - *Completed*
*   [x] **Task 4.2:** Develop a schema or guide for annotating data using the new BFO-aligned model, providing a clear and powerful replacement for the old method. - *Completed*
**Phase 4 artefacts.** `vn-core:isEvidenceFor` and `vn-core:TextSpan` are now declared in `valuenet-core`, together with the properties a span needs to be usable: `hasTextValue`, `isTextSpanOf`, `hasStartOffset`, `hasEndOffset`, and `evokesFrame`. `evokesFrame` is the bridge back to the 12,338 `vcvf:triggers` statements in `MFTriggers/`, so the trigger corpus is reused as a lexical layer rather than discarded. Annotation well-formedness is checked by `valuenet-core-shapes.ttl`, since annotation-property domains and ranges are not enforced by any reasoner.

### Phase 5: Suite Repair

Defects found while adding the moral epistemics module. All fixed and verified; see the validation summary at the end of this document.

*   [x] **Task 5.1: Repair `valuenet-schwartz-values.ttl`.** The file was a copy-paste of an EasyRdf converter web page — HTML navigation, the input pasted once, converter UI text, the output pasted again, and the page footer. It did not parse. Rebuilt from the converted block (56 triples, isomorphic to the `.owl`). - *Completed*
*   [x] **Task 5.2: Fix dangling parent IRIs.** `valuenet-folk` and `valuenet-schwartz-values` referenced their parents as `…/valuenet-core.owl#X` and `…/valuenet-schwartz-values.owl#X`, but those modules declare `…/valuenet-core#X` and `…/valuenet-schwartz-values#X`. 160 occurrences of 12 distinct IRIs resolved to nothing, leaving 146 of 158 classes with no path to a BFO root. The reasoner run recorded under Task 3.1 was therefore checking a hierarchy that was not connected. - *Completed*
*   [x] **Task 5.3: Correct nonexistent BFO identifiers in the documentation.** `Phase4_LinguisticGrounding.md` and `annotationGuide.md` used `bfo:0000041` for *person*, `bfo:0000086` for *has_disposition*, and `bfo:0000133` for *realizes*. None of the three exist in BFO 2020. Replaced with `BFO_0000040` (material entity, with a note that BFO has no *person* class), `BFO_0000196` (bearer of), and `BFO_0000055` (realizes). - *Completed*
*   [x] **Task 5.4: Correct the annotation pattern.** Both documents taught `:someProcess bfo:0000055 folk:CourageDisposition`, which points a relation at a class. That is OWL 2 punning, falls outside OWL 2 DL, and produces data no reasoner or SHACL shape can check. Examples now mint disposition individuals first. - *Completed*
*   [x] **Task 5.5: Point imports at ontology IRIs.** `valuenet-moral-foundations` and `valuenet-mappings` imported version IRIs (`…/1.0/…`) while the other modules imported ontology IRIs. - *Completed*
*   [x] **Task 5.6: Settle the namespace question.** `https://fandaws.com/ontology/bfo/valuenet-<module>#` is canonical and resolvable; the `w3id.org/valuenet` IRIs are reserved aliases used only in `rdfs:seeAlso`. Recorded as an `rdfs:comment` on the `valuenet-core` ontology header. - *Completed*

### Phase 6: Moral Epistemics Module

*   [x] **Task 6.1:** Add `vn-core:ValueViolationProcess` and `vn-core:contravenes`, restoring the violation and dyadic-opposition structure of the original MFT module (`mft:Violation`, `mft:violates`, `mft:opposedTo`), which the BFO refactor did not carry over. Deliberately not disjoint from `ValueRealizationProcess`: one act can realize one value while contravening another. - *Completed*
*   [x] **Task 6.2:** Model moral assessment in `valuenet-moral-epistemics.owl` — `PrudenceDisposition`, `ProtectorRole`, `AgentBehaviorProcess`, `ActOfBehavioralObservation`, `MoralDiscernmentAct`, `RashJudgmentAct`, `ProtectiveAction`, and the information content entities they consume and produce. - *Completed*
*   [x] **Task 6.3:** Supply competency questions and a worked scenario, following the pattern used for the BHV and MFT modules. - *Completed*

### Phase 7: Corpus Consolidation and the Agent Class

*   [x] **Task 7.1: Remove the duplicate trigger directory.** `haidt_frames/` (added 2022-02-14) and `MFTriggers/` (added 2022-06-23) held byte-identical copies of the same 13 `.ttl` files, verified with `cmp` immediately before deletion. `MFTriggers/` is the later, curated copy, has its own `README.md`, and is the name the repository README and the published module IRI use, so `haidt_frames/` was removed. It remains recoverable from git history at `3d87930`. - *Completed*
*   [x] **Task 7.2: Consolidate the `vcvf` namespace.** `vcvf:triggers` was two distinct predicates: 12 files in `MFTriggers/` bound `vcvf` to `http://www.semanticweb.org/sdg/ontologies/2022/0/valuecore_with_value_frames.owl#`, a Protégé-generated default, while `harm_frame.ttl` used `http://www.ontologydesignpatterns.org/ont/values/valuecore_with_value_frames.owl#`. The latter is what `ValueCore.ttl` declares, what the README documents, and what the published module IRI is, so it was adopted throughout. `bhvtriggers.ttl` and `ThatsAllFolks/taf.ttl` each carried one `owl:imports` of the same stale IRI and were corrected too — 28 occurrences across 14 files. Verified by parsing before and after: the trigger count is unchanged, and is now 12,338 under the canonical namespace and 0 under the stale one. - *Completed*
    > A note on counts. Earlier drafts of this document quoted 33,243 trigger statements, then 24,656. Both were artefacts of how the corpus was counted. 33,243 counts textual occurrences of `vcvf:triggers`. 24,656 sums distinct triples file by file. Loaded as a single merged graph the corpus holds **12,338** distinct trigger statements — which is exactly the "more than 12000 triples" the repository README has claimed all along. The gap is `ClosureHaidtValueFrames.ttl`, which is a superset of the 12 individual frame files: every trigger statement in them also appears in it, and it carries 20 that they do not.
*   [x] **Task 7.3: Adopt CCO `Agent`.** The suite had no class for the bearer of a value. `cco:ont00001017` is now declared in `valuenet-core` as a MIREOT stub — adopted by its canonical IRI, with `rdfs:isDefinedBy` pointing at CCO's AgentOntology, rather than duplicated as a local class. `vn-core:ValueRelatedRealizableEntity` now asserts `inheres in some cco:Agent`, which states the realist commitment of the whole refactor formally for the first time: a value is a property of an agent. The moral epistemics acts assert `has participant some cco:Agent`, and `valuenet-core-shapes.ttl` gained a shape checking that recorded bearers are actually typed as agents. - *Completed*
    > Why a stub and not an import. CCO's AgentOntology transitively imports the CCO Event and Information Entity ontologies, roughly 490KB, which would change the dependency profile of the whole suite for one class. The stub carries the asserted parent only; in CCO proper `Agent` is a *defined* class, equivalent to a material entity bearing some Agent Capability, and that equivalence is what lets a reasoner recognise agents. Swapping the stub for `owl:imports <https://www.commoncoreontologies.org/AgentOntology>` restores it and is a one-line change.
    > Groups. CCO places neither `Person` nor `Organization` under `Agent`: a person is an animal, and an organization is a `Group of Agents` (`cco:ont00000300`), an object aggregate. Value bearing is asserted over `Agent` alone, which fits the current content — loyalty to an in-group is a disposition inhering in an individual and directed at a group, not one borne by the group. Group-level value bearing would need `cco:ont00000300` added to the range.

#### Open items

*   [x] **Task 7.4: Reasoner validation.** — *Completed.* HermiT (via owlready2, Java 23) was run over the merged import closure of `bfo-core`, `valuenet-core`, `valuenet-schwartz-values`, `valuenet-moral-foundations`, `valuenet-folk`, `valuenet-moral-epistemics` and `valuenet-mappings` — 2,318 triples, 210 classes, 48 object properties — and again with the scenario individuals loaded (2,391 triples). Both runs report the ontology **consistent with 0 unsatisfiable classes**. This exercises the suite's first `owl:complementOf` and `owl:disjointWith` (moral epistemics) and its first `owl:equivalentClass` and universal existential on value classes (core), and it re-runs Task 3.1 against a hierarchy that is, for the first time, actually connected.

    Two design decisions were confirmed by entailment rather than by inspection:

    * `:protectiveActionByA`, asserted only as a `ProtectiveAction`, was **inferred** to be a `vn-core:ValueViolationProcess` from its `contravenes :trustOfA` axiom via the defined-class definition. Automatic classification of violations works as intended.
    * The same individual holds both `ValueRealizationProcess` and `ValueViolationProcess`, while `:rashJudgmentByB` holds only the latter. The deliberate non-disjointness of the two classes (§Task 6.1) is what permits a moral trade-off to be represented, and it does not collapse.
*   [ ] **`ClosureHaidtValueFrames.ttl` duplicates the individual frame files.** Measured with `rdflib`: the 12 individual frames contribute 12,318 trigger statements and every one of them also appears in `ClosureHaidtValueFrames.ttl`, which holds 12,338 — a strict superset, with 20 statements of its own. Nothing is lost by loading only the Closure file, and nothing but those 20 is lost by loading only the individual frames. Harmless to a triplestore, which deduplicates, but it doubles the on-disk corpus and makes per-file counts misleading. Deciding whether the Closure file is a build artefact that should be generated rather than committed is a maintenance question, not an ontology one.

## Validation Summary

Run over the whole `BFO/` suite after Phases 5 and 6. Reproduce with `rdflib` and `pyshacl`.

| Check | Result |
| --- | --- |
| Files parse as Turtle (`.ttl` and `.owl`) | 15 / 15 |
| `.ttl` / `.owl` pairs isomorphic | 6 / 6 |
| Merged suite triples | 1,394 (was 1,006) |
| Declared ValueNet entities | 205 (was 158) |
| Dangling ValueNet IRIs | 0 (was 160 occurrences of 12 distinct IRIs) |
| ValueNet classes reaching a BFO root | 173 / 173 (was 12 / 158) |
| Classes without `rdfs:label` | 0 |
| Classes without `skos:definition` | 0 |
| Entities declared under `w3id.org/valuenet` | 0 |
| `TestingFramework.md` Query 1, disjoint parentage | 0 hits |
| `TestingFramework.md` Query 3, redundant `skos:broadMatch` | 0 hits |
| SHACL `valuenet-core-shapes.ttl` over the scenario | 0 results |
| SHACL `valuenet-moral-epistemics-shapes.ttl` over the scenario | 1 result, the intended rash-judgment warning |
| SHACL agent shape, negative control (a rock bearing a value) | fires as expected |
| Competency questions returning expected rows | 6 / 6 |
| HermiT: ontology consistency | consistent |
| HermiT: unsatisfiable classes | 0 of 210 |
| HermiT: consistency with scenario individuals | consistent, 0 unsatisfiable |
| `MFTriggers/` trigger statements under the canonical namespace | 12,338 |
| `MFTriggers/` trigger statements under the stale namespace | 0 (was 19,872 per-file) |
| Stale `semanticweb.org/sdg` IRIs anywhere in the repository | 0 (was 28 across 14 files) |

Reasoner classification completed under Task 7.4; see the open items above for what remains.
