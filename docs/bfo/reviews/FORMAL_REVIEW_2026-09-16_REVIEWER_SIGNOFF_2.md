<!--
Provenance (added on receipt; not part of the sign-off)

  received     2026-09-17, forwarded by the project owner
  replying to  FORMAL_REVIEW_2026-09-16_POST_SIGNOFF_UPDATE.md
  effect       confirms the sign-off; accepts D-011 and D-014 as breaking and
               justified; accepts D-014's membership criteria M1-M7 and
               D-013's three readings of RULES 2.0; names the complete
               breaking set as six items; suggests one non-blocking test,
               direct disjointness cases for D-011, which was added to
               tests/bfo/test_text_layer_follows_d005.py
               (test_form_typed_as_information_content_is_inconsistent)

Recorded verbatim. Nothing below this comment has been edited.
-->

I reviewed the Dev update. **Sign-off remains granted.** The new D-011 and D-014 changes are breaking, but they are justified and consistent with the criteria already used in the review. I see no new ontology blocker. 

### 1. D-011 — accepted as a breaking change

Yes. Adding:

```ttl
TextualRepresentation owl:disjointWith InformationContentEntity .
TextSpan              owl:disjointWith InformationContentEntity .
```

is a breaking semantic change because previously consistent data can now become inconsistent. That is exactly the same test I applied to `MoralCulpabilityRole`: a new OWL condition affecting satisfiability/class membership is breaking. 

The modeling decision itself is sound. D-005 established these as **form-level GDCs**, specifically to keep them distinct from content-level ICEs. D-011 makes that distinction machine-enforceable instead of documentary.

The four HermiT cases are sufficient for sign-off. I would add **one non-blocking regression test** if convenient:

```text
x rdf:type TextualRepresentation .
x rdf:type InformationContentEntity .
→ inconsistent
```

and the analogous case for `TextSpan`.

That directly pins the `owl:disjointWith` contract rather than only exercising it indirectly through `is about` / `designates`. But this is a test-hardening suggestion, **not a release blocker**.

### 2. D-014 removals and re-parenting — accepted

Yes. Removing the seven folk IRIs without deprecated aliases is acceptable on the same footing as the earlier removals, given that the project has deliberately chosen a breaking remediation release rather than preserving known-bad ontology API surface. 

I also approve the Power restructuring:

* `StatusDisposition ⊑ schwartz:PowerDisposition`
* `ControlDisposition ⊑ PersonalValueDisposition`
* `LeadershipDisposition ⊑ PersonalValueDisposition`
* `InfluenceDisposition ⊑ PersonalValueDisposition`
* `RecognitionDisposition ⊑ PersonalValueDisposition`

The loss of the four former Schwartz-Power entailments is a **real logical break**, and the update correctly identifies it as such. More importantly, the new hierarchy follows the class definitions rather than forcing definitions to fit an inherited parent. That is the correct direction of ontology engineering. 

The removals of `PowerDisposition`, `SecurityDisposition`, and `TraditionDisposition` as undifferentiated duplicates are particularly appropriate. Removing `OpennessDisposition`, `ImpactDisposition`, `DiscretionDisposition`, and `ResourcefulnessDisposition` is also consistent with the adopted M6 policy.

### 3. D-014 M1–M7 — accepted

Yes. **M1–M7 are now an acceptable membership policy for the Folk module.**

The key strengths are:

* membership is about **value-related realizable entities**, not words;
* labels require concept identity;
* weaker relations use annotation-only mappings;
* survey items are evidence/indicators rather than automatic taxonomic assertions;
* state/trait vocabulary is not confused with dispositions;
* unsupported project-local classes need attestation, a role justification, or a competency question;
* curation happens only after membership is settled.

That architecture fixes the central problem in the original Folk modeling: lexical association no longer drives ontology identity.

The reported split between **98 exact classes, 9 alternative labels, 146 related matches, and 25 exclusions** is also much more semantically meaningful than a single “coverage” percentage. 

I sign off on D-014.

### 4. D-013 readings of RULES 2.0 — accepted

All three readings are reasonable and faithful to the substance of the supplied rules.

**Reading 1 — definition form:** accepted. The important constraint is genus–differentia structure with the asserted immediate parent as genus. Requiring the literal word **“that”** would be grammatical formalism without ontological benefit. A definition such as:

> “A Moral Value Disposition to protect others from harm”

still has the required genus and differentia structure.

**Reading 2 — process:** accepted. RULES 2.0 says external web search is used **“if necessary”**, so treating it as optional rather than mandatory is correct. CCO-first searching and clarity/inclusiveness/exclusiveness checks remain mandatory.

**Reading 3 — scope:** accepted. Section 6 is an example workflow and section 7 is deployment guidance; neither creates a new annotation requirement beyond the explicit rules. And section 4 explicitly frames equivalence handling as **“upon request.”** 

One subtle point: by recording these three readings in D-013, ValueNet is adopting a **project interpretation of RULES 2.0**, not claiming these interpretations are themselves BFO or CCO requirements. That is exactly the right way to handle it.

## Final disposition

**Approved. No further breaking changes are required from this review.**

The complete breaking set I now recognize is:

1. D-005 — text-layer category/property redesign.
2. EvidenceSource retirement.
3. `hasInformationalInput` / `hasInformationalOutput` retirement.
4. `MoralAssessmentAct` re-parenting.
5. **D-011 — form-level classes made disjoint with ICE.**
6. **D-014 — seven Folk IRIs removed and four classes lose Schwartz-Power subsumption.**

D-009, D-010, D-012, D-013, and the definition/comment/example curation are non-breaking in OWL/API terms as described.

**You can treat the formal-review remediation as signed off.**
