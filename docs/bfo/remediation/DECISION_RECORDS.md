# BFO Alignment Decision Records

## Status

The four prerequisite decisions were provisionally adopted on 2026-08-24 to authorize baseline, test, and source-inventory work. D-001 was adopted on 2026-08-25 when Phase 2 encoded the agent-borne realization contract. D-002 was adopted and implemented during Phase 1 on 2026-08-24. D-004 was adopted on 2026-08-25 when Phase 3 implemented the exact-representation and selector pattern. D-003 was adopted and implemented on 2026-08-25 when Phase 5 adjudicated all 71 mapping assertions.

The user's instruction to start the remediation plan authorizes these recommended defaults as working assumptions. Any later instruction that changes scope or metaphysical commitments supersedes the corresponding record.

D-005 was provisionally adopted on 2026-09-16, on the project owner's instruction following the formal review of that date, to authorize the ontology change it describes. It amends D-004 item 4. It was adopted and implemented the same day, together with R10 of the review response and D-007.

D-006 and D-007 were adopted on 2026-09-16, after the reviewer signed off on the review response and the owner instructed that the remediation proceed. Both were implemented with D-005: D-006's source digest is corrected in the regenerated extract manifest, and D-007's properties are retired.

D-013 was adopted on 2026-09-16 on the owner's instruction, following the recommendation that answered R2: RULES 2.0 becomes the standard, with the readings the record states. Its non-folk half was implemented the same day, and its folk half on 2026-09-17, after D-014.

D-011 and D-012 were adopted and implemented on 2026-09-16 on the owner's instruction after phase E: the disjointness D-005 had left undecided, and the two splits R17 had left to the owner.

D-008, D-009 and D-010 were adopted and implemented on 2026-09-16 under the same instruction. They record R12, R13 and R14 of the review response, following the recommendations the reviewer accepted: `RashJudgmentAct` as the negative fixture for the first two, and conditional acceptance of `contravenes` for the third.

D-014 was adopted on 2026-09-16 on the owner's instruction, closing R15: the folk module's membership criteria, its coverage reported by kind, and a decision on every item the proposal's revision 3 had left pending. It supersedes D-012 item 3. It was implemented on 2026-09-17 on the owner's instruction to finish the remediation.

D-015 was adopted and implemented on 2026-09-17, after the remediation, on the owner's assessment of the open-items backlog: two folk classes sat under a Schwartz value that neither their definitions nor, in one case, the corpus supported.

On 2026-09-17 the reviewer reviewed the decisions taken after their sign-off, D-011 to D-014 and the folk curation, and confirmed the sign-off (`docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF_2.md`). They accepted D-011 and D-014 as justified breaking changes, D-014's membership criteria M1–M7, and D-013's three readings of RULES 2.0. The breaking set they recognize is six items: D-005's text layer, the retirement of `EvidenceSource`, the retirement of the informational input and output properties, the re-parenting of `MoralAssessmentAct`, D-011, and D-014.

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

**Status:** Adopted and implemented 2026-09-16  
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

### Implementation, 2026-09-16

- `valuenet-core.ttl` states items 2 to 5 and 8. The definitions and the property declaration are the ones recorded above, and `tests/bfo/test_text_layer_follows_d005.py` reads them out of this record and compares them with the module. The same test runs HermiT over the suite with the worked scenario: consistent, neither class nor any scenario text individual classified as information content, and, as the control in the same run, the selector and the annotation are.
- **Item 8 decided: `selectsTextSpan` specializes CCO `designates` rather than being replaced by it.** Replacing it would lose the `TextSpan` range, which the selector shapes rely on to find the span whose text the offsets must delimit. As a subproperty, a CCO consumer asking what a selector designates still reaches the span. No competency question needs `designates` itself.
- **A boundary the implementation surfaced.** CCO 2.2 defines Information Content Entity as *equivalent to* a generically dependent continuant that is about some entity. A representation or span therefore stays out of ICE only while nothing asserts it is about something, directly or through a subproperty of `is about` such as `designates` or `describes`; if something does, the reasoner re-classifies it without any inconsistency to report. The rule is written into the class comments and the annotation guide, and the test pins the behaviour both ways. A disjointness axiom between the form classes and ICE would make such an assertion an error rather than a silent re-classification. This record did not decide one; D-011 does, and asserts it.
- **A shape item 4 implies.** A span individuated by its position has one position, so every selector of a span must give the same offsets. Nothing enforced that: two selectors at different offsets could select one span whenever both positions held the same string, and each would pass the substring check. `valuenet-core-shapes.ttl` now rejects it; the fixture with the same substring twice, as two spans, conforms.
- `vn-core:isEvidenceFor`'s documentary domain is removed rather than re-pointed (R10). The two approved subjects share no named parent short of generically dependent continuant, and OWL 2 DL permits only a named class as an annotation property's domain. SHACL, which already named both classes, is unchanged.
- The CCO extract was regenerated with Designative ICE and `designates` as roots, under version IRI `.../2.2-2026-09-16-d005`, from the release artifact whose digest D-006 pins. Before changing the roots, the unmodified generator was run on that artifact and reproduced the previous extract byte for byte.

### Dependency

Item 4 cannot be implemented while `TextSpan` is a subclass of `vn-core:EvidenceSource`, which is itself an ICE: the span would be classified back under ICE. Removing that subclass axiom is recommendation R10 of the review response, and must land in the same change.

### Reopen when

- CCO introduces a form-level generically dependent continuant, or a text-value property whose domain admits one;
- a competency question requires one content across different sequences, such as a translation or a revision — answered by adding a content-level ICE related to the representations, not by moving the representation back under ICE; or
- BFO removes or weakens the disjointness of the continuant categories, which the test's control 02 would detect first.

## D-006 — CCO 2.2 as the Normative Conformance Baseline

**Status:** Adopted and implemented 2026-09-16
**Finding coverage:** formal review 2026-09-16, overall determination and R1 of the response
**Amends:** the source provenance recorded in `ontology/bfo/vendor/cco/cco-valuenet-extract.manifest.json`

### Decision

1. CCO release **v2.2** is ValueNet's normative conformance baseline: tag `v2.2`, commit `0bc7d33e1bc09fd4693366119ab4e03cb0340042`, merged artifact `CommonCoreOntologiesMerged-2.2.ttl`.
2. The audit record distinguishes the project's baseline from the reviewer's, in the reviewer's words: *the original external review was conducted against supplied CCO 2.0; ValueNet subsequently verified each implicated term against its normative CCO 2.2 baseline and found no disposition-changing difference.* It is not a certification of the ontology against 2.2 by the reviewer.
3. The pinned source digest is the release artifact's own: `a9453382b25b40781c181d6ba44981f228abb76d90d548846713adba9baadb42`, as listed in the release's published `SHA256SUMS`.

### Rationale

- ValueNet already pins, extracts, reasons over and tests against 2.2. Declaring 2.0 would describe a target the repository does not have.
- Every CCO term the review cites was compared across 2.0 (tag `v2.0-2024-11-06`) and 2.2, and no finding's disposition changes; see §4 of the review response. The reviewer accepted that comparison as evidence about the repository.
- **The previously recorded source digest was not the release's.** The extract manifest recorded `f6d1f7008fb0589b…`. That is the digest of the same file with every line ending converted to CRLF: the release artifact uses LF, digests to `a9453382…`, and converting it to CRLF reproduces the recorded value exactly. The content was right and the recorded provenance could not be checked against the published release. The manifest was corrected when the extract was regenerated for D-005 on 2026-09-16. Before the roots were changed, the unmodified generator was run on the LF release artifact and reproduced the previous extract byte for byte, so the release artifact is shown to be the extract's source, not only a file with the same content.

### Reopen when

- a later CCO release is adopted; or
- a certification the project needs is only available against a different CCO version.

## D-007 — Informational Input and Output Use CCO Directly

**Status:** Adopted and implemented 2026-09-16, with D-005
**Finding coverage:** formal review 2026-09-16, finding 3; R3 and R11 of the response
**Supersedes:** the "Retain; the local subproperty narrows the range to ICE" disposition for `hasInformationalInput` and `hasInformationalOutput` in `EXTERNAL_TERM_INVENTORY.md`

### Decision

1. `vn-me:hasInformationalInput` and `vn-me:hasInformationalOutput` are retired.
2. Class restrictions, SHACL paths, competency queries and instance data use CCO `has input` (`ont00001921`) and `has output` (`ont00001986`) directly, with the information-content filler stated in the restriction.
3. This is an IRI break with the intended semantics preserved.

### Rationale

- Every use of either property is an existential restriction whose filler is already an information content entity subclass, so the narrowed range supplies no inference the restriction does not.
- The two local properties duplicated a CCO relation to restate a filler type, which the reuse policy exists to prevent. The reviewer concurred that the earlier "Retain" should be superseded.
- The CCO parents admit generically dependent continuants in range under both 2.0 (`continuant`) and 2.2 (a union including generically dependent continuant), so no use is lost.

### Reopen when

- a competency question needs to quantify over informational inputs or outputs as such, independently of any filler class.

## D-008 — Moral Assessment Is Not Necessarily Planned

**Status:** Adopted and implemented 2026-09-16
**Finding coverage:** formal review 2026-09-16, finding 10; R12 of the response
**Evidence:** `tests/bfo/test_moral_assessment_commitments.py`

### Decision

1. `vn-me:MoralAssessmentAct` is a subclass of CCO Act (`ont00000005`), not of Act of Appraisal (`ont00000636`). Its definition opens "An act in which an agent evaluates…".
2. `vn-me:MoralDiscernmentAct` is additionally asserted a subclass of Act of Appraisal. Its definition already said so.
3. `vn-me:RashJudgmentAct` inherits no plannedness. No local "planned moral assessment" class is introduced: discernment is the only deliberate subclass the module needs, and it takes the CCO class directly.

### Rationale

- Act of Appraisal is a subclass of Act of Measuring, which CCO defines as a Planned Act, and a Planned Act is "prescribed by some Directive Information Content Entity held by at least one of the Agents". Under the old parent every moral assessment was entailed to be planned in that sense, which the definition never said.
- Spontaneous moral judgment is in scope, and the module's own `RashJudgmentAct` is the case: an unwarranted ascription produced without deliberation is the paradigm, and nothing prescribes it.
- CCO Act, "a process in which at least one agent plays a causative role", is exactly what the class needs, and the existing `has participant some Agent` restriction already states the agent.
- Discernment assesses observed behaviour against a norm it takes as input, deliberately; Act of Appraisal fits it and keeps CCO's appraisal classification where it is true.
- `MixedMoralAssessmentAct`, a subclass of both, remains satisfiable, because nothing makes plannedness and its absence disjoint: an act that is not entailed to be planned may still be planned.

### Reopen when

- a competency question needs to distinguish planned from unplanned moral assessment in general, rather than discernment from rash judgment; or
- CCO introduces an appraisal class that is not a Planned Act.

## D-009 — Moral Culpability Is Grounded in Conduct, Not in Appraisal

**Status:** Adopted and implemented 2026-09-16
**Finding coverage:** formal review 2026-09-16, finding 12; R13 of the response
**Evidence:** `tests/bfo/test_moral_assessment_commitments.py`

### Decision

1. `vn-me:MoralCulpabilityRole` is defined as *a role that inheres in an agent in virtue of that agent's having participated, as a responsible agent, in conduct that violates a moral norm applying to that agent, and that can be realized in processes of censure, correction, restitution, forgiveness, or sanction.*
2. The OWL conditions are unchanged: a BFO role, inhering in some Agent. `CulpabilityAscriptionICE` continues not to require the role of what it describes.
3. The role is asserted in data independently of any ascription, and only on the ground the definition names.

### Rationale

- The previous definition grounded the role in "a norm-governed moral appraisal [that] treats that agent as accountable". An unwarranted appraisal treats an agent as accountable too, so by definition a rash judgment would have conferred the culpability it wrongly ascribes. The class comment already denied that; the definition contradicted it.
- What makes an agent culpable is what the agent did under a norm that applies to it. Whether anyone appraises it, and whether the appraisal is warranted, is a separate fact, carried by the moral assessment ICEs and their warrant.
- The change is to the definition only, so it is not an OWL-breaking change. The test holds the OWL side where it was: over the suite with the worked scenario, neither the agent a rash judgment describes nor the agent who judges is inferred to bear the role, while an agent asserted to bear it is recognised in the same run.
- "Responsible agent" is not further analysed here. Capacity, excuse and diminished responsibility are real distinctions, and a module that needs them should model them rather than have this definition pretend to.

### Reopen when

- a competency question needs the grounds of culpability as entities — the norm, the conduct, the capacity — rather than the status; or
- a tradition-specific module needs a notion of culpability that this definition excludes.

## D-010 — `vn-core:contravenes` Is a Justified Local Relation

**Status:** Adopted and implemented 2026-09-16
**Finding coverage:** formal review 2026-09-16, findings 2 and 8; R14 of the response
**Evidence:** competency questions CQ1 and CQ5 in `valuenet-moral-epistemics-CQ.md`

### Decision

1. `vn-core:contravenes` (process → value-related realizable entity) is retained as a project-local extension. This record is the justification the reviewer's conditional acceptance required.
2. **Reading.** Its object is a particular realizable entity borne by some agent: a process contravenes *that agent's* disposition or role. It is not violation of a norm. This is the first of the two readings finding 8 distinguishes, and it is the one the axioms already commit to, since the range is `ValueRelatedRealizableEntity`, every instance of which inheres in an agent.
3. **Norm-centred questions** — which acts violate a rule, independently of whether anyone bears a corresponding value — are asked of `vn-me:MoralNormICE`, the prescriptive information content the module already has, not of `contravenes`.
4. The justification is recorded on the property itself as a comment, and CQ1 and CQ5 are named in the competency-question notes as the questions that require it.

### The alternatives, and why each fails the competency questions

CQ1 asks *which acts run against a value that the acting agent themselves bears*; its query joins the act to the value, and the agent to the same value by `bearer of`. CQ5 asks *which processes realize one value while contravening another*.

| alternative | signature and meaning (CCO 2.2) | why it does not answer CQ1 or CQ5 |
|---|---|---|
| `disrupts` (`ont00001888`) | process → process; one process disrupts another "from occurring as it would have" | Its object is a process. A contravened value need not be realized at all — Agent B's justice disposition is not being realized when B judges rashly — so there is no process to disrupt, and CQ1's `bearer of` join has nothing to reach. Using it would mean inventing counterfactual realizations. |
| `inhibits` (`ont00001959`), defined through `inhibited by` (`ont00001970`) | process → process; the inhibiting process causes a decrease of a realizable entity that is realized in the inhibited process | Also process-valued, and causal: it asserts that the disposition decreased. One rash judgment does not diminish its agent's justice disposition, and CQ1 does not ask whether it did. |
| realization, BFO `realizes` (`BFO_0000055`) | process → realizable entity; the process is the entity's realization | The opposite relation. CQ5 needs both on one process, to different values; the protective action in the scenario realizes a care disposition and contravenes a trust disposition. A process cannot realize the value it violates, so realization cannot record the violation. |
| norm-centred, `MoralNormICE` with CCO `has input` or `prescribes` | an information content entity that prescribes | A norm is information content; no agent bears it. CQ1's join from the agent through `bearer of` cannot reach a norm, so the question the relation exists for cannot be asked. Norm violation is a different question, and item 3 routes it there. |

### Reopen when

- CCO or BFO introduces a relation from a process to a realizable entity that is not realization; or
- the competency questions change so that CQ1 and CQ5 no longer need a process-to-value relation.

## D-011 — Form-Level Text Is Disjoint With Information Content

**Status:** Adopted and implemented 2026-09-16
**Finding coverage:** D-005 implementation note on aboutness
**Amends:** D-005, which left the question open
**Evidence:** `tests/bfo/test_text_layer_follows_d005.py`, which reaches the disjointness through aboutness and, since the reviewer's suggestion of 2026-09-17, also asserts it directly (`test_form_typed_as_information_content_is_inconsistent`)
**Reviewed:** accepted by the reviewer as a breaking change, 2026-09-17

### Decision

1. `vn-core:TextualRepresentation` and `vn-core:TextSpan` are each `owl:disjointWith` CCO Information Content Entity (`ont00000958`).
2. No disjointness is asserted between `TextualRepresentation` and `TextSpan`. D-005 distinguishes them by how they are individuated and does not decide whether a span covering its whole representation is a different entity; this record does not either.

### Rationale

- CCO 2.2 defines Information Content Entity as *equivalent to* a generically dependent continuant that is about some entity. Both form classes are generically dependent continuants, so any aboutness asserted of one — through `is about`, or a subproperty such as `designates` or `describes` — entailed that it was information content. Nothing was inconsistent, so nothing reported it, and D-005 was undone for that individual without trace.
- With the disjointness the same assertion is an inconsistency a reasoner reports. The test holds both routes there: a representation asserted to be about a process, and a span asserted to designate one.
- It costs nothing D-005 permits. A selector designating a span is aboutness *of* the span, not *by* it, and stays consistent; that case is in the same test. HermiT finds the suite with the worked scenario consistent with the axioms asserted.

### Reopen when

- a competency question needs text that is at once form and content — which D-005's own reopen condition already answers with a content-level ICE related to the representation, not by relaxing this.

## D-012 — Faith and Openness Each Define One Disposition

**Status:** Adopted and implemented 2026-09-16
**Finding coverage:** formal review 2026-09-16, finding 13; R17 of the response
**Evidence:** `tests/bfo/test_folk_sense_splits.py`; `tests/bfo/test_definition_discipline.py`
**Method:** RULES 2.0, the reviewer's rules (`docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_RULES_2.0.md`), applied to the classes touched

### Decision

1. `folk:FaithDisposition` keeps its IRI and one sense: *a personal value disposition to place complete trust or confidence in someone or something without requiring proof.*
2. `folk:ReligionDisposition` is added for the other: *a personal value disposition to hold a system of religious belief and practice as a guide to living.* Its parent is `core:PersonalValueDisposition`, like Faith's and Spirituality's, and it follows the module's naming pattern, which pairs it with `folk:Religion` in this repository's copy of the folk corpus.
3. `folk:OpennessDisposition` keeps its IRI and one sense: *a personal value disposition to be receptive to new experiences, including unfamiliar activities, sensations, and ways of living.*
4. No class is added for Openness's other sense. Being candid and transparent is what the existing `CandorDisposition` and `TransparencyDisposition` define, under `HonestyDisposition`; a third class would duplicate them.
5. The three classes carry every annotation RULES 2.0 section 5 requires: subclass assertion, label, definition, comment and example. No mapping assertion is added.

### How the rules were applied

- **Search CCO first.** CCO 2.2 has no value or character dispositions to serve as a parent. It has `Religion` (`ont00000616`), but that is an Information Content Entity — the collection of claims a religion consists of — and a disposition cannot be its subclass. ReligionDisposition's comment names it as what the disposition is directed at. The parents are therefore the ValueNet dispositions the classes already specialized.
- **Sources.** The folk corpus, not a web search: `folk:Faith`'s own comment describes believing things will work out and letting beliefs guide decisions, with no doctrine in it, and this repository's copy of the corpus records `folk:Religion` as a separate value — "holding a system of religious belief and practice as a guide to living" — which had no class. The two senses were already two values there. *Correction, 2026-09-16:* `folk:Religion` is not in the upstream ThatsAllFolks corpus or any of its source lists; this repository added it (commit d9ee3f1) to hold a 480-trigger religion lexicon. The split stands on the two senses, not on the entry's provenance (see `R15_FOLK_MEMBERSHIP_PROPOSAL.md` §2).

| class | clarity | inclusiveness | exclusiveness |
|---|---|---|---|
| Faith | one disposition, stated without "or" | trust in a person, in an outcome, in providence | trust that rests on evidence of reliability (TrustDisposition); holding a religious system (ReligionDisposition) |
| Religion | one disposition; the religion itself is named as content | any tradition's belief and practice held as a guide | spiritual concern without a system of belief and practice (SpiritualityDisposition); the belief system itself (CCO Religion) |
| Openness | one disposition, receptive rather than seeking | unfamiliar activities, sensations, ways of living | seeking change or daring experience (Variety, Adventure); receptiveness to ideas (OpenMindedness); candour (Candor, Transparency) |

### Why the IRIs stay with these senses

- **Faith** keeps the sense the corpus's own `folk:Faith` has, and the religious sense goes to `folk:Religion`, the entry this repository added to its copy of the corpus.
- **Openness** keeps the sense its existing broader conceptual matches already described: Schwartz Stimulation and Self-Direction are openness to change, not candour.

### Consequences

- Folk coverage rises from 91 to 92 of 278 corpus values: `folk:Religion` now has a class.
- The disjunction check in `test_definition_discipline.py` fires on no definition.
- Authored classes rise from 186 to 187.

### Reopen when

- R15 decides folk membership. The corpus gives "openness" as an alternative label of `folk:Open-mindedness` and has no `folk:Openness`, so membership may merge OpennessDisposition into OpenMindednessDisposition rather than keep both; and `folk:Belief_in_God`, narrower than Religion, has no class.

## D-013 — RULES 2.0 Is ValueNet's Definition and Annotation Standard

**Status:** Adopted 2026-09-16; implemented for the non-folk modules 2026-09-16, and for folk 2026-09-17 after D-014
**Finding coverage:** formal review 2026-09-16, finding 13; R2 and R18 of the response
**Standard:** `docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_RULES_2.0.md`
**Evidence:** `tests/bfo/test_definition_discipline.py`

### Decision

1. RULES 2.0, the rules the formal review applied, is adopted as ValueNet's standard for the definitions and annotations of every authored term — class and property — in the five published modules.
2. **Definition form.** "b is a c that d's" is met when the definition opens with an asserted immediate parent as genus, the measure R16 gates. A disposition's differentia may be phrased "to …" ("a moral value disposition to protect others from harm"), which is how BFO itself phrases dispositions; the 148 definitions phrased that way are conforming and are not rewritten to "that".
3. **Annotations.** Every term carries `rdfs:label`, `skos:definition`, `rdfs:comment` and `skos:example`, and every class its `rdfs:subClassOf`. From adoption this is required of every term added, and of every term whose definition is changed. The gap that existed at adoption is recorded by name and gated by equality, so it can only shrink, and it is paid down in this order:
   1. the non-folk modules — 32 comments and 60 examples, missing from 62 of their 67 classes and properties;
   2. the folk module's 134 comments and 134 examples, after R15 decides folk membership, in the same pass as its 84 genus corrections, so that nothing is written for a class that is then removed.
4. **Process.** Section 3, step 1 — search CCO before choosing a parent, and record what the search found — is required, as D-012 did. Step 2, web search with citations, is optional: the sources ValueNet uses are the folk corpus, CCO and BFO, and the theories its modules are named for. Step 3's clarity, inclusiveness and exclusiveness checks are required, and are recorded for any class a decision adds or splits.
5. Sections 6 and 7 describe the reviewing tool itself, and section 4's equivalence handling applies only on request; neither adds a requirement here.

### Rationale

- It is the standard the reviewer measured ValueNet against. Adopting it means the next review measures something the project agreed to, rather than something only the reviewer holds.
- The definition-form rule already had its substantive part enforced: genus alignment is gated. Rewriting "to" as "that" would change the wording of 148 definitions and the meaning of none.
- The annotation gap is a writing programme, not a defect with a single fix. A gate that records it and admits no new debt lets it be paid down in reviewable steps.
- Folk curation waits on membership, for the same reason its genus corrections do.

### Folk implementation, 2026-09-17

After D-014 settled membership, the folk module was curated in one pass: the 75 remaining misaligned definitions now open with their asserted parent, and the 128 terms lacking a comment and an example have both. Every module is at zero on both gates, and the records in `test_definition_discipline.py` are empty. The examples use the form the other modules use for a disposition, "a person's standing inclination to …"; the three folk examples written earlier (Faith, Religion, and D-014's six classes) were brought to the same form.

Most genus corrections change only the opening words. Eight definitions changed more, each for a reason under RULES 2.0 or D-014, and the owner may want to read them:

| class | now | why |
|---|---|---|
| `IntuitionDisposition` | "a personal value disposition to favor intuitive judgment, understanding reached immediately without conscious reasoning, as a guide to belief and action" | D-014: valuing or favoring intuitive judgment, not having the faculty |
| `EquityDisposition` | "a justice disposition to distribute resources and opportunities according to individuals' needs and other materially relevant differences, so that the outcome is fair rather than identical" | D-014: the definition carries the competency reason; it had named need only and ended in "a fair and equal outcome" |
| `StrengthDisposition` | "a resilience disposition to value and cultivate the capacity to withstand great force, pressure, or adversity" | was "to possess and value": a value disposition is valuing, not having (M1) |
| `ExcellenceDisposition` | "an achievement disposition to strive for qualities of a very high degree and for superiority in performance or outcome" | was "to possess qualities to a very high degree", for the same reason |
| `PeaceDisposition` | "a calmness disposition to seek freedom from disturbance, within oneself and in one's surroundings" | dropped "; a state of tranquility or quiet": the state corresponds, it is not the disposition (M5) |
| `BoldnessDisposition` | "a courage disposition to take risks and act with confidence and forwardness" | dropped "; a form of courage", which the new genus states |
| `LeisureDisposition` | "an enjoyment disposition to value time free from work or other occupation" | dropped the gloss "; free time" |
| `ForgivenessDisposition` | "… toward a person or group who has harmed one" | was "who has harmed you" |

### Reopen when

- RULES is revised; or
- a term category outside classes and properties — individuals, or shapes — is published and needs a standard.

## D-014 — Folk Membership Is Decided by Criteria, and Coverage Is Reported by Kind

**Status:** Adopted 2026-09-16; implemented 2026-09-17
**Reviewed:** accepted by the reviewer 2026-09-17: the removals and re-parenting as a breaking change, and M1–M7 as the folk membership policy
**Finding coverage:** formal review 2026-09-16, finding 13; N6 and R15 of the response
**Record:** `docs/bfo/remediation/R15_FOLK_MEMBERSHIP_PROPOSAL.md`, revision 4 — the research, and a disposition for each of the 186 corpus values with no class (Table A) and each of the 45 module classes with no corpus value (Table B)
**Supersedes:** D-012 item 3

### Decision

1. **Membership.** A folk class is a member if its instances are value-related realizable entities borne by an Agent:
   - a *value disposition*, concerning what the bearer treats as important or normatively significant; or
   - a *value role*, whose external grounding is value- or norm-relevant, whatever the bearer's own valuation.

   Beliefs, structural dimensions of a theory, category headings, misspellings and culture-level analytical constructs are not members. A word whose surface sense is an act, practice, state or property is excluded only after the source's intended sense has been checked (M1).
2. **Three relations, three mechanisms** (M2):
   - a *lexical synonym* becomes `skos:altLabel`, and only if it passes the substitution test — substituting it for the preferred label leaves the referent class unchanged;
   - a *correspondence* — a word that evokes, indicates or operationalizes a value without naming it — goes in `valuenet-mappings.ttl`, from the class to the corpus value's IRI, never into a label;
   - a *narrower value* becomes a subclass if it passes M4.
3. **Evidence is not taxonomy.** A value-survey item is a correspondence to the construct it indicates, not a synonym or subclass on that ground (M3). A source's grouping is evidence for a weak mapping, not for a parent. Emotional states and trait terms are correspondences (M5).
4. **New classes** need M1, a differentia no existing class covers, and paradigmatic examples that separate them from their siblings. The number of lists naming a word is provenance, not a criterion (M4).
5. **Classes with no corpus value** are kept only if a named source or value research attests the value, the class is a value role, or a recorded competency question requires it. A differentia alone, or being a ValueNet addition, is not enough (M6). Everything kept is curated under D-013 (M7).
6. **Coverage is reported by kind.** Over the 278 corpus values:

   | kind | count |
   |---|---:|
   | exact class | 98 |
   | lexical synonym | 9 |
   | correspondence | 146 |
   | excluded | 25 |
   | pending | 0 |

   The ontology names 107 of them. Correspondences are what annotation can reach, and are not reported as ontological coverage.
7. **Removed:** folk `PowerDisposition`, `SecurityDisposition` and `TraditionDisposition`, which repeat the Schwartz classes without differentia; `OpennessDisposition`, whose word is polysemous and stays in the correspondence layer only; and `ImpactDisposition`, `DiscretionDisposition` and `ResourcefulnessDisposition`, which have no attestation M6 accepts and no recorded competency question. Removal is an IRI break, as D-007's retirements were.
8. **Re-parented:** `StatusDisposition` under `schwartz-values:PowerDisposition`. `ControlDisposition`, `LeadershipDisposition`, `InfluenceDisposition` and `RecognitionDisposition` go under `core:PersonalValueDisposition`, with correspondences to Schwartz Power (and, for Recognition, Achievement). Control's definition is not narrowed to fit a parent.
9. **Kept under M6:**

   | class | ground |
   |---|---|
   | `CalmnessDisposition` | Scott Jeffrey, "Calm"; DevelopGoodHabits, "Calmness" |
   | `DecisivenessDisposition` | Scott Jeffrey, "Decisive"; The Mind Fool, "Decisiveness" |
   | `DutyDisposition` | The Mind Fool, "Dutiful" |
   | `IntuitionDisposition` | Scott Jeffrey, "Intuitive" |
   | `MindfulnessDisposition` | Scott Jeffrey: "Presence values emphasize mindfulness, awareness, and inner stillness" |
   | `EquityDisposition` | Favero, Jensen, Kim and Piatak (2025) measure equity as a core public value; and a competency reason: queries may need to distinguish **equal treatment** from **fair treatment sensitive to materially relevant differences** — the line between Equity and `EqualityDisposition` |

10. **Added:**

    | class | parent | definition |
    |---|---|---|
    | `HealthDisposition` | `core:PersonalValueDisposition` | a personal value disposition to protect and maintain bodily and mental health |
    | `IntelligenceDisposition` | `core:PersonalValueDisposition` | a personal value disposition to seek the development, possession, or exercise of intellectual ability |
    | `ModerationDisposition` | `core:PersonalValueDisposition` | a personal value disposition to avoid excess and extremes in consumption, feeling and action |
    | `WealthDisposition` | `core:PersonalValueDisposition` | a personal value disposition to seek the acquisition or retention of financial and material wealth |
    | `PatriotismDisposition` | `folk:LoyaltyDisposition` | "A Patriotism Disposition is a Loyalty Disposition that concerns commitment to and special concern for the bearer's country or political community." |
    | `WorkLifeBalanceDisposition` | `folk:BalanceDisposition` | "A Work-Life Balance Disposition is a Balance Disposition that concerns maintaining an appropriate allocation of time, attention, or effort between occupational and non-occupational domains." |

    The last two are the owner's wording. Like every module definition, their `skos:definition` states the definiens: "a loyalty disposition that concerns …", "a balance disposition that concerns …".
11. **The sixteen corpus values revision 3 left pending:**

    | corpus value | disposition |
    |---|---|
    | Responsiveness | correspondence: `RespectDisposition` |
    | Grace | correspondence: `GratitudeDisposition`, `ForgivenessDisposition` |
    | Irreverent | correspondence, deliberately weak: `HumorDisposition` |
    | Inspiration | correspondence: `PassionDisposition` |
    | Reverence | correspondence: `SpiritualityDisposition`, `RespectDisposition` |
    | Consent | correspondence: `RespectDisposition`; no `ConsentDisposition` without a competency question |
    | Empowerment | correspondence: `AutonomyDisposition`, `SupportDisposition` |
    | Clarity | correspondence: `UnderstandingDisposition` |
    | Preparedness | correspondence: `VisionDisposition`, `schwartz-values:SecurityDisposition` |
    | Realism | correspondence: `WisdomDisposition` |
    | Experience | correspondence: `EnjoymentDisposition` |
    | Willingness, Management, Risk-management | excluded |
    | Patriotism, Work-Life Balance | subclasses (item 10) |

### How RULES 2.0 was applied to the six added classes

D-013 requires, for any class a decision adds, a CCO search before its parent is chosen and a record of the clarity, inclusiveness and exclusiveness checks.

**CCO search.** Searched on 2026-09-17: CCO 2.2, the merged release file, whose SHA-256 is `a9453382…` as recorded in the extract manifest. The search covered every class under BFO disposition, role and realizable entity, and the labels and definitions of all 1,400 CCO classes for each new class's concept. CCO 2.2 has no value disposition of any kind, so no CCO class can be a parent, and each class keeps the ValueNet parent in item 10. What the search found is recorded because several CCO classes sit next to these concepts and mark what they exclude:

| class | nearest CCO classes | why none is a parent |
|---|---|---|
| `HealthDisposition` | Disease (`ont00000318`), "a disposition to undergo pathological processes"; Healthcare and Healing Artifact Functions | Disease is a disposition of the organism, not a valuing of health; the functions belong to artifacts |
| `IntelligenceDisposition` | Skill (`ont00000089`) and Agent Capability (`ont00001379`); Act of Intelligence Gathering | Skill and Agent Capability are the ability, which this class values rather than is; intelligence gathering is another sense of the word |
| `ModerationDisposition` | none | no CCO class concerns excess or measure |
| `WealthDisposition` | Financial Instrument, Financial Value of Property, Act of Ownership | these are the wealth, its value and its holding, not a valuing of them |
| `PatriotismDisposition` | Citizen Role (`ont00000987`), Allegiance Role (`ont00000392`) | Citizen Role is legal membership of a state, whatever the bearer values; Allegiance Role is support committed to another agent in a conflict. Both are roles, not dispositions |
| `WorkLifeBalanceDisposition` | Occupation Role (`ont00000984`), Act of Employment | Occupation Role is the responsibilities of employment, the domain this class weighs against the rest of life, not a disposition |

**Web search** (optional under D-013) was done in R15's research. Its sources are cited in the R15 record: Schwartz (2012) for health, Rokeach's "intellectual" for intelligence, Primoratz on patriotism, and the source lists for the others.

**Checks.**

| class | clarity | inclusiveness | exclusiveness |
|---|---|---|---|
| Health | one disposition, valuing health rather than being healthy | protecting and maintaining health, bodily and mental | being in good or bad health (CCO Disease is a disposition of the organism); concern for others' welfare (CareDisposition); pleasure (HedonismDisposition); vitality and fitness, which only correspond |
| Intelligence | one disposition, valuing intellectual ability | developing, having, or exercising that ability | the ability itself (CCO Skill, Agent Capability); acquiring knowledge (LearningDisposition); being drawn to what is new (CuriosityDisposition); applying judgment and experience (WisdomDisposition) |
| Moderation | one disposition, avoiding excess and extremes | in consumption, feeling and action, with or without a rule | following a code or restraining impulses (DisciplineDisposition); careful use of resources (ThriftDisposition); weighing parts of a life against each other (BalanceDisposition) |
| Wealth | one disposition, the acquisition or retention of wealth | financial and material wealth, earned, saved or held | status and control, which wealth can serve (Schwartz Power, a related match only); careful use of resources (ThriftDisposition); safety and stability (Schwartz Security); the wealth itself (CCO Financial Instrument) |
| Patriotism | one disposition, loyalty whose object is the bearer's country or political community | commitment to and special concern for a country, or a political community that is not a state | a claim of national superiority, which is not part of the differentia; legal membership (CCO Citizen Role; GoodCitizenRole); commitment to support in a conflict (CCO Allegiance Role); loyalty to a person, group or cause (the parent) |
| Work-Life Balance | one disposition, the division between occupational and non-occupational life | time, attention and effort | balance among other parts of a life (the parent); free time valued for itself (LeisureDisposition); the responsibilities of a job (CCO Occupation Role); avoiding excess in anything (ModerationDisposition) |

Each class's `skos:example` is a paradigm case that separates it from these neighbours, as M4 requires.

### Rationale

- **The corpus has no membership rule to inherit.** Its authors scraped lists of so-called values, deduplicated them and built a taxonomy by hand ([arXiv:2303.00632](https://arxiv.org/abs/2303.00632), §5), and its clusters copy one list author's page headings.
- **An alternative label asserts identity.** Using one for every word that points roughly at a class would make search return classes the word does not name. Correspondences keep what annotation needs without that claim.
- **A differentia is necessary, not sufficient.** Impact is distinct from Influence, so merging them would be wrong, but distinctness does not show that anyone holds the value.
- **The evidence is the corpus's own sources and value research.** Every list attestation in item 9 comes from a list the corpus itself cites: its values carry `prov:wasAttributedTo` Scott Jeffrey, The Mind Fool and DevelopGoodHabits. A class is not rescued by searching further lists once the policy is set.
- **A dependant is not a reason to keep a class.** Discretion's only support was a related match from `moral-epistemics:PrudenceDisposition`; the match goes, with no replacement forced.
- **Equity earns its place by the distinction it lets queries draw,** not by the list that names it.
- **Re-checking corrected the record.** Revision 3 said no attestation had been found for Calmness, Decisiveness, Duty and Intuition. The owner's check found them, and the pages were read again on 2026-09-16 before this record was written.

### Carried into implementation

- `IntuitionDisposition`'s definition must concern valuing or favoring intuitive judgment, not possessing an intuitive faculty; today's is checked against that.
- `EquityDisposition`'s definition is checked against its competency reason: today it names need, one kind of relevant difference, and ends in "a fair and equal outcome".
- "Dutiful" attests Duty but stays a correspondence; it fails the substitution test.
- `PatriotismDisposition`'s differentia makes no claim of national superiority.
- `ModerationDisposition`'s examples show moderation without an externally imposed rule, which is what separates it from `DisciplineDisposition`.
- `ReligionDisposition`'s comment, which calls `folk:Religion` a corpus value, is corrected (D-012's provenance correction).

### Consequences, on implementation

- The folk module goes from 137 classes to 136, and authored classes from 187 to 186.
- Folk coverage is reported as four figures, with 98 exact classes against 92 today.
- The recorded genus misalignments fall from 84 to 75: five of the removed classes are among them, and Control, Leadership, Influence and Recognition align under the general parent. Status stays misaligned under Schwartz Power until curation.
- The recorded annotation gap falls from 134 comments and 134 examples to 128 each, since six of the removed classes are in it; the six new classes carry every annotation from the start.
- These figures come from applying items 7, 8 and 10 to a copy of the folk module and running `test_definition_discipline.py`'s own measures over it, which also found the six new definitions aligned with their parents and none disjunctive. The records in that test change when the implementation lands, not before.
- Table A2 adds 150 mapping assertions, four corpus values having two targets; §6 of the record adds the Power correspondences; `PrudenceDisposition` loses one. The site's mapping counts and the evidence ledger move with them.
- The implementation order is §8 of the record, each step with its tests, site pins and evidence.

### Implementation notes

- **Measured, not asserted.** `tools/bfo/folk_coverage.py` now reports the four kinds from the ontology itself — `rdfs:seeAlso` for exact classes, `skos:altLabel` for synonyms, the mapping assertions for correspondences — and reads exclusions from `config/folk-membership.json`, the only kind no triple can carry. It measures 98, 9, 146 and 25, with none pending and no value of two kinds. Before, it stopped at a class's first matching name, so an alternative label could never count.
- **The record is the test's input.** `tests/bfo/test_folk_membership.py` reads items 7 to 10 of this record and Tables A1 to A4 of the R15 record, and checks the ontology against them: the removed IRIs are used nowhere, the placements and definitions are as recorded, and the 150 correspondences are exactly Table A2's.
- **Correspondence IRIs.** Each correspondence points at the IRI the corpus's trigger lexicon uses, so annotation reaches the class. They differ from folk.ttl's declared IRI for one value only: the lexicon uses `folk:Accomplishment`, and folk.ttl declares `FolkValues.owl#:Accomplishment`.
- **Mapping counts.** Phase 5's 45 broader, 5 related and 17 historical become 42, 159 and 17: Openness and Resourcefulness took three broader matches with them; Prudence lost its match to Discretion, and 150 corpus correspondences and five class-level related matches arrived — Control, Leadership and Wealth to Schwartz Power, Recognition to Power and Achievement. The site's diagram description says 218 mapping assertions overall.
- **Annotations.** The six new classes carry every RULES 2.0 annotation. The records in `test_definition_discipline.py` fall to 75 misaligned genera and 128 missing comments and examples, as simulated.

### Reopen when

- a competency question is recorded that needs a removed class, or a distinction a correspondence does not carry — `ConsentDisposition` is the named case;
- the reviewer, on seeing M1–M7, disputes a criterion; or
- the folk corpus is re-imported and its values change.

## D-015 — Creativity and Respect Are Placed by Their Definitions

**Status:** Adopted and implemented 2026-09-17
**Finding coverage:** OI-8 in `docs/bfo/OPEN_ITEMS.md`
**Applies:** D-014's M3, that a corpus grouping or a survey item is evidence for a mapping and not for a parent
**Evidence:** `tests/bfo/test_open_items.py` re-derives the comparison; the genus gate in `tests/bfo/test_definition_discipline.py`; the mapping inventory in `tests/bfo/test_bfo_mapping_semantics.py`

### Decision

1. `folk:CreativityDisposition` moves from `schwartz-values:StimulationDisposition` to `schwartz-values:SelfDirectionDisposition`, with an annotation-only related match to Stimulation.
2. `folk:RespectDisposition` moves from `schwartz-values:UniversalismDisposition` to `core:PersonalValueDisposition`, with annotation-only related matches to Universalism, Conformity and Tradition.
3. Neither definition changes except its opening genus, which D-013 requires to name the asserted parent. No definition is narrowed to fit a parent.
4. This is an IRI-preserving but logically breaking change: `CreativityDisposition` is no longer entailed to be a Stimulation disposition, and `RespectDisposition` and its subclass `CourtesyDisposition` are no longer entailed to be Universalism dispositions. ValueNet is new and nothing consumes its IRIs.

### Rationale

- **Creativity belongs to Self-Direction.** Schwartz's Self-Direction has the defining goal of independent thought and action — choosing, creating, exploring — and its survey items include creativity. Stimulation's items are a varied life, an exciting life and daring: novelty and arousal, not origination. The folk corpus places `folk:Creativity` under Self-Direction as well, which is evidence pointing the same way rather than the reason.
- **Respect belongs to no one Schwartz value.** Its extension is due regard for others' feelings, wishes, rights *or* traditions. Universalism covers others' welfare and rights, Conformity the restraint from upsetting people, and Tradition respect for custom — Schwartz's own item "respect for tradition" sits under Tradition, not under a general respect value. A class whose extension crosses three values has no single Schwartz parent, so it takes the general one, and the overlap is recorded where overlap belongs, in annotation-only matches.
- **The alternative was worse.** Either narrow the definition until it fits one Schwartz value, which would change what the class means to preserve a hierarchy, or leave the corpus's grouping to decide, which D-014's M3 rejects for mappings and which the corpus itself contradicts in one of the two cases.

### Consequences

- The project's related matches go from 159 to 163.
- Both definitions open with their new parent, so the genus gate stays at zero in every module.
- OI-8 closes, and the placement comparison it rested on is now a test: if any folk class comes to sit under a Schwartz value the corpus does not place it under, that test fails rather than the register quietly going stale.

### Reopen when

- a competency question needs `RespectDisposition` subsumed by a Schwartz value, which would mean narrowing it or splitting it; or
- Schwartz's own theory is re-mapped in this repository, which would revisit every folk class with a Schwartz parent rather than these two.

## Decision Gate Result

| Decision | Working status | Semantic ontology edits authorized? |
| --- | --- | --- |
| D-001 | Adopted | Yes; Phase 2 realization and bearer-participant constraints implemented |
| D-002 | Adopted and implemented | Yes; pinned extracts and import closure established in Phase 1 |
| D-003 | Adopted and implemented | Yes; Phase 5 mapping vocabulary, CCO subclass promotions, and profile controls implemented |
| D-004 | Adopted and implemented; item 4 amended by D-005 | Yes; Phase 3 carrier/content/representation/selector pattern implemented |
| D-005 | Adopted and implemented | Yes; `TextualRepresentation` and `TextSpan` are form-level GDCs with the carrier existential on the representation, `hasTextValue` is renamed and re-scoped as `hasTextualSequenceValue`, `EvidenceSource` is retired, and `TextSpanSelector` is a Designative ICE |
| D-006 | Adopted and implemented | Yes; pins CCO v2.2 at its release digest, now recorded in the extract manifest |
| D-007 | Adopted and implemented | Yes; `hasInformationalInput` and `hasInformationalOutput` are retired in favour of CCO `has input` and `has output` |
| D-008 | Adopted and implemented | Yes; `MoralAssessmentAct` is a CCO Act and `MoralDiscernmentAct` an Act of Appraisal |
| D-009 | Adopted and implemented | Yes; `MoralCulpabilityRole` is defined by the agent's conduct; no OWL condition changes |
| D-010 | Adopted and implemented | Documentation only; `contravenes` is retained with its justification recorded |
| D-011 | Adopted and implemented | Yes; `TextualRepresentation` and `TextSpan` are disjoint with CCO Information Content Entity |
| D-012 | Adopted and implemented; item 3 superseded by D-014 | Yes; `FaithDisposition` and `OpennessDisposition` narrowed to one sense each; `ReligionDisposition` added |
| D-013 | Adopted and implemented | Annotations and definitions; every module has every term's comment and example, and every definition opens with its asserted parent. Both gates are at zero |
| D-014 | Adopted and implemented | Yes; seven folk classes removed and five re-parented, six added, 9 alternative labels, 150 corpus correspondences, coverage reported by kind; folk curation under D-013 done |
| D-015 | Adopted and implemented | Yes; `CreativityDisposition` moves to Schwartz Self-Direction and `RespectDisposition` to the general parent, with the overlaps recorded as annotation-only matches |
