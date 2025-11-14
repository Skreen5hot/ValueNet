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