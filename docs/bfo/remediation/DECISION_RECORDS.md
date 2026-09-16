# BFO Alignment Decision Records

## Status

The four prerequisite decisions were provisionally adopted on 2026-08-24 to authorize baseline, test, and source-inventory work. D-001 was adopted on 2026-08-25 when Phase 2 encoded the agent-borne realization contract. D-002 was adopted and implemented during Phase 1 on 2026-08-24. D-004 was adopted on 2026-08-25 when Phase 3 implemented the exact-representation and selector pattern. D-003 was adopted and implemented on 2026-08-25 when Phase 5 adjudicated all 71 mapping assertions.

The user's instruction to start the remediation plan authorizes these recommended defaults as working assumptions. Any later instruction that changes scope or metaphysical commitments supersedes the corresponding record.

D-005 was provisionally adopted on 2026-09-16, on the project owner's instruction following the formal review of that date, to authorize the ontology change it describes. It amends D-004 item 4 and is adopted when that change is implemented.

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
**Amended:** item 4 by D-005, 2026-09-16

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

## D-005 — Form-Level Textual Representation Outside ICE

**Status:** Provisionally adopted 2026-09-16; ontology implementation pending  
**Finding coverage:** ALN-005; formal review 2026-09-16, finding 4  
**Amends:** D-004 item 4  
**Evidence:** `tests/bfo/test_text_value_placement.py`; `docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_REVIEWER_REPLY.md`; `docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_REVIEWER_REPLY_2.md`

### Decision

An intentional and narrowly scoped departure from CCO's convention of placing literal values on information bearing entities, made because CCO has no class for the level at which ValueNet's text identity lives.

1. Three levels are distinguished:
   - **content** — an Information Content Entity, individuated by aboutness;
   - **form** — a generically dependent continuant that is not an ICE, individuated by its exact sequence;
   - **bearer** — an Information Bearing Entity, a particular carrier.
2. `vn-core:TextualRepresentation` is a subclass of BFO generically dependent continuant (`BFO_0000031`), not of CCO Information Content Entity, and carries the existential restriction `generically depends on` (`BFO_0000084`) some Information Bearing Entity (`cco:ont00000253`).
3. Its definition is: *a generically dependent continuant that is one exact sequence of Unicode code points and that generically depends on at least one information bearing entity.* It does not say "concretized by": BFO restricts the concretizer of a GDC to a process or specifically dependent continuant, as item 5 of D-004 already records. It does not say "shared by every carrier", which implies multiple copies where BFO requires only one of what may be several.
4. `vn-core:TextSpan` is likewise a generically dependent continuant and not an ICE. Its definition is: *a generically dependent continuant that is a continuant part of exactly one textual representation and is individuated by a contiguous interval of code-point positions in that representation.* It is **not** a subclass of `TextualRepresentation`, and it is not individuated by its own string: `"abc"` at code points 2–4 and `"abc"` at 20–22 of one representation are two spans. Parthood remains `isTextSpanOf`, a specialization of BFO `continuant part of` (D-004 item 6, unchanged), and the *exactly one* is enforced by the existing SHACL shape. The definition says *continuant part*, not *proper* continuant part: BFO 2020 core supplies no proper-part relation, so properness would be a local constraint; and the shapes admit a span covering its whole representation, which is how a whole utterance is cited as evidence, since evidence must be a span. Restricting spans to proper parts would make that evidence unexpressible.
5. The local text property is retained as an extension filling a level CCO leaves uncovered, not as a duplicate of CCO `has text value`, and is renamed from `vn-core:hasTextValue` to `vn-core:hasTextualSequenceValue`. The old name read as a variant of the CCO property, and that resemblance is what made it look like a duplicate in the first place. Its domain is the union of `TextualRepresentation` and `TextSpan`: not the ICE, which would readmit the misclassification, and not `TextualRepresentation` alone, which by domain entailment would classify every span as a representation — spans carry their own value, which SHACL requires and checks against the substring at their offsets. No deprecated alias is kept for `vn-core:hasTextValue`: the text layer is new (D-004, 2026-08-25) and has no consumers to migrate. Should an alias ever be added, it must not carry a domain that entails ICE: an `owl:equivalentProperty` to a property with an ICE domain would re-classify every form-level entity as ICE and undo this decision.

   ```turtle
   @prefix owl:     <http://www.w3.org/2002/07/owl#> .
   @prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
   @prefix skos:    <http://www.w3.org/2004/02/skos/core#> .
   @prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
   @prefix vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#> .

   vn-core:hasTextualSequenceValue
       a owl:DatatypeProperty ;
       rdfs:label "has textual sequence value"@en ;
       rdfs:domain [ a owl:Class ;
                     owl:unionOf ( vn-core:TextualRepresentation vn-core:TextSpan ) ] ;
       rdfs:range xsd:string ;
       skos:definition "Relates a textual representation or a text span to the string that expresses its exact sequence of Unicode code points."@en .
   ```

6. CCO `has text value` is not asserted on either class; doing so makes the subject an Information Bearing Entity, which is disjoint from a generically dependent continuant. If a consumer requires CCO's bearer-level strings, they are derived by query from `is carrier of` and `hasTextualSequenceValue`, never authored separately.
7. The OWL existential states that a carrier exists. SHACL continues to require an explicitly represented carrier in instance data, because under the open-world assumption a representation with no recorded carrier remains consistent.
8. `vn-core:TextSpanSelector` is a CCO Designative Information Content Entity: it is about the span it picks out. Its offsets are computed against the form-level sequence exactly as D-004 item 7 specifies. Whether CCO `designates` replaces `vn-core:selectsTextSpan` is tested against the competency questions during implementation and is not decided here.
9. The departure is confined to text. The other seven CCO literal-value properties, all with domain Information Bearing Entity, are unaffected: only text is addressed below the level of its whole value.

### Rationale

- **CCO has no form level.** Information Content Entity is CCO's only subclass of generically dependent continuant, and its scope note subtypes ICEs by what they are about "rather than characteristics such as format, language, measurement scale, or media". A textual representation is individuated by exact sequence — its own record says a changed string is a different representation — so under ICE it was consistent but misclassified.
- **BFO has one.** BFO elucidates a generically dependent continuant as "the content or the pattern that multiple copies would share", and gives "the sequence of this protein molecule; the sequence that is a copy thereof" as an example. An exact code-point sequence is that kind of entity.
- **The CCO property cannot be used here.** `has text value` has domain Information Bearing Entity; an IBE is a BFO object; BFO declares independent, specifically dependent and generically dependent continuants pairwise disjoint. Applied to a form-level representation it is inconsistent, so the local property does not duplicate it.
- **Form identity is a requirement, not a preference.** Evidence offsets are meaningless without one fixed sequence (D-004 items 2 and 7), and one sequence may be carried by many files.
- **Both parties to the review concur.** The reviewer withdrew the recommendation to replace `hasTextValue` ("too strong and should be withdrawn") and revised the finding to a justified BFO-level extension over a gap in CCO's information model.

### Evidence

`tests/bfo/test_text_value_placement.py` runs fourteen scenarios through HermiT, with two controls. Among them: the model before this decision is consistent (03); CCO `has text value` on the same individual is inconsistent (04); the reviewer's form-level case with two distinct carriers is consistent (09); the existential does not demand carrier data (10); requiring an IBE concretizer is inconsistent (11); the design exactly as recorded here, spans and the union domain included, is consistent (12); two spans with the same string at different positions are consistent as distinct spans (13); and identifying spans by their string instead — an `owl:hasKey` on the text property — collapses them into one, which contradicts their being different (14). Scenario 13 differs from 14 only by that key, and 14 becomes consistent once the spans are no longer asserted different, so the merge is what fails. On 2026-09-16 the test was falsified twice, each mutation first verified to have changed its input: removing the stated CCO domain axiom turned 04 consistent, and removing BFO's disjointness groups turned control 02 consistent. The CCO axioms relied on were compared across CCO 2.0 and 2.2 and are identical.

### Dependency

Item 4 cannot be implemented while `TextSpan` is a subclass of `vn-core:EvidenceSource`, which is itself an ICE: the span would be classified back under ICE. Removing that subclass axiom is recommendation R10 of the review response, and must land in the same change.

### Reopen when

- CCO introduces a form-level generically dependent continuant, or a text-value property whose domain admits one;
- a competency question requires one content across different sequences, such as a translation or a revision — answered by adding a content-level ICE related to the representations, not by moving the representation back under ICE; or
- BFO removes or weakens the disjointness of the continuant categories, which the test's control 02 would detect first.

## Decision Gate Result

| Decision | Working status | Semantic ontology edits authorized? |
| --- | --- | --- |
| D-001 | Adopted | Yes; Phase 2 realization and bearer-participant constraints implemented |
| D-002 | Adopted and implemented | Yes; pinned extracts and import closure established in Phase 1 |
| D-003 | Adopted and implemented | Yes; Phase 5 mapping vocabulary, CCO subclass promotions, and profile controls implemented |
| D-004 | Adopted and implemented; item 4 amended by D-005 | Yes; Phase 3 carrier/content/representation/selector pattern implemented |
| D-005 | Provisionally adopted | Yes; authorizes moving `TextualRepresentation` and `TextSpan` to a form-level GDC with the carrier existential, renaming and re-scoping `hasTextValue` as `hasTextualSequenceValue`, and removing `TextSpan ⊑ EvidenceSource`; not yet implemented |
