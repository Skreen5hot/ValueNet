# BFO Alignment Decision Records

## Status

The four prerequisite decisions were provisionally adopted on 2026-08-24 to authorize baseline, test, and source-inventory work. D-001 was adopted on 2026-08-25 when Phase 2 encoded the agent-borne realization contract. D-002 was adopted and implemented during Phase 1 on 2026-08-24. D-004 was adopted on 2026-08-25 when Phase 3 implemented the exact-representation and selector pattern. D-003 was adopted and implemented on 2026-08-25 when Phase 5 adjudicated all 71 mapping assertions.

The user's instruction to start the remediation plan authorizes these recommended defaults as working assumptions. Any later instruction that changes scope or metaphysical commitments supersedes the corresponding record.

## D-001 — Extension of the Realist Value Model

**Status:** Adopted 2026-08-25  
**Finding coverage:** ALN-004, ALN-007

### Decision

1. Agent-borne values are modeled as realizable entities:
   - internally grounded values as dispositions;
   - externally grounded normative expectations as roles.
2. Beliefs, goals, plans, norms, value labels, and value concepts are not automatically values. Their informational content is modeled separately from the realizable entities it may describe, prescribe, or be about.
3. Group- and organization-level value bearing remains out of scope until the appropriate CCO group model is supplied and reviewed.
4. Artificial-agent value bearing remains out of scope until the intended bearer class and material realization assumptions are explicitly approved.

### Rationale

This preserves the existing ValueNet architecture while preventing information content, goals, roles, dispositions, and processes from being collapsed by lexical similarity.

### Reopen when

- organizational values become a required competency question;
- artificial agents must bear values;
- the intended domain includes value concepts that are not about agent-borne realizable entities; or
- definition review shows that the disposition/role partition excludes paradigmatic intended cases.

## D-002 — External Ontology Dependency Strategy

**Status:** Adopted and implemented 2026-08-24  
**Finding coverage:** ALN-001

### Decision

Use version-pinned MIREOT extracts under `BFO/imports/` for the limited CCO, RO/Extended Relation Ontology, and IAO vocabulary needed by the suite.

Each extract must include:

- ontology and version IRIs;
- retrieval or extraction provenance;
- label and authoritative definition;
- superclass path required for BFO grounding;
- domain and range for properties;
- inverse and superproperty axioms;
- logical characteristics;
- restrictions required to interpret the imported term; and
- a manifest identifying the exact source artifact and selected terms.

### Rationale

This preserves a small dependency closure without reducing imported terms to unversioned labels or guessed semantics.

### Reopen when

- a full source module is small and stable enough to import directly;
- the selected term's meaning depends on axioms that cannot be reproduced safely in a small extract; or
- redistribution or licensing terms prevent committing the extract.

## D-003 — Mapping Semantics

**Status:** Adopted and implemented 2026-08-25  
**Finding coverage:** ALN-006

### Decision

1. Lexical, historical, and provenance correspondences are annotation-only by default.
2. Canonical SKOS mapping properties will be used only if the suite introduces separate `skos:Concept` individuals in an explicit concept scheme.
3. `rdfs:subClassOf` will be used only for reviewed universal-to-universal extension inclusion.
4. `owl:equivalentClass` will be used only after necessary-and-sufficient comparison.
5. The 71 mapping assertions preserved during Phase 0 were adjudicated in Phase 5: 67 are annotation-only conceptual or historical correspondences and four are reviewed CCO superclass axioms.

### Implementation

- Canonical SKOS mapping properties are no longer asserted in the BFO modules.
- `vn-core:hasBroaderConceptualMatch`, `vn-core:hasRelatedConceptualMatch`, and `vn-core:historicallyCorrespondsTo` are explicitly declared annotation properties.
- No SKOS concept scheme or `skos:Concept` individuals were introduced.
- Four narrower ValueNet universals now use verified CCO parents; no mapping was promoted to equivalence.
- The complete assertion-by-assertion disposition is recorded in `PHASE5_MAPPING_AUDIT.md`.

### Rationale

This prevents accidental class/individual punning and prevents lexical similarity from being interpreted as ontological equivalence.

### Reopen when

- a downstream consumer explicitly requires canonical SKOS concept mappings; or
- a source ontology supplies formal class semantics that justify OWL alignment.

## D-004 — Text Span Identity and Offsets

**Status:** Adopted and implemented 2026-08-25  
**Finding coverage:** ALN-003, ALN-005

### Decision

1. Abstract information content and its physical or digital carrier are distinct individuals.
2. A span is identified relative to one exact textual representation or version.
3. Character offsets belong to a selector or annotation entity whose source is that exact representation; they are not treated as invariant features of an abstract document across all concretizations.
4. Exact textual representations, spans, selectors, and evidence annotations are information content entities; information-bearing carriers are separate independent continuants.
5. A carrier is linked to its representation with BFO `is carrier of` (`BFO_0000101`). A direct carrier-to-content `concretizes` assertion is prohibited because BFO restricts the concretizer to a process or specifically dependent continuant.
6. `isTextSpanOf` specializes BFO `continuant part of` (`BFO_0000176`) and ranges over the exact textual representation.
7. Offsets are zero-based Unicode code-point indexes into the exact representation's canonical string, with the end excluded. Both offsets are required on a selector; no implicit normalization or line-ending conversion is permitted.

### Rationale

Offsets cannot be interpreted without a fixed source string and indexing convention, while a generically dependent information entity may have multiple concretizations and versions.

### Reopen when

- the project formally defines a document identity policy under which one canonical string is part of the document's identity; or
- an adopted external annotation ontology supplies a different verified selector pattern.

## Decision Gate Result

| Decision | Working status | Semantic ontology edits authorized? |
| --- | --- | --- |
| D-001 | Adopted | Yes; Phase 2 realization and bearer-participant constraints implemented |
| D-002 | Adopted and implemented | Yes; pinned extracts and import closure established in Phase 1 |
| D-003 | Adopted and implemented | Yes; Phase 5 mapping vocabulary, CCO subclass promotions, and profile controls implemented |
| D-004 | Adopted and implemented | Yes; Phase 3 carrier/content/representation/selector pattern implemented |
