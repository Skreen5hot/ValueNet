<!--
Provenance (added on receipt; not part of the reply)

  received     2026-09-16, forwarded by the project owner
  replying to  the analysis of where a text value can live: three levels
               (content, form, bearer) and the HermiT experiment now pinned as
               tests/bfo/test_text_value_placement.py
  effect       withdraws the review's recommendation to replace
               vn-core:hasTextValue with CCO has text value; see D-005 in
               docs/bfo/remediation/DECISION_RECORDS.md
  note         the definition wording proposed below ("concretized by one or
               more information bearing entities") was not adopted: BFO restricts
               the concretizer of a GDC to a process or specifically dependent
               continuant, which D-004 item 5 already records and scenario 11 of
               the test demonstrates. D-005 uses "generically depends on".

Recorded verbatim. Nothing below this comment has been edited.
-->

Yes. Your correction is well founded, and I would revise my formal review accordingly.

The decisive point is that BFO's own elucidation of **generically dependent continuant** explicitly covers both **content and pattern**, and gives a sequence as an example: the entity is “the content or the pattern that multiple copies would share,” with protein sequences among the examples.  That makes a copy-independent Unicode sequence a legitimate candidate for a BFO GDC without forcing it to be an ICE.

Your HermiT result also follows directly from the supplied axioms. CCO's `has text value` has `Information Bearing Entity` as its domain,  while an IBE is an **Object**.  BFO makes Independent Continuant, Specifically Dependent Continuant, and Generically Dependent Continuant pairwise disjoint.  So applying `cco:has text value` to a form-level GDC does not “reuse the existing property”; it changes the subject's ontological category and makes that individual inconsistent. My earlier recommendation to replace `vn-core:hasTextValue` with the CCO property was therefore too strong and should be withdrawn.

The distinction I would now endorse is:

**content → ICE; form → non-ICE GDC; bearer → IBE.**

This also explains exactly why the present model is *consistent but misclassified*: CCO's ICE is itself a GDC, but adds an aboutness condition, and its scope note explicitly says ICE subtyping is based on what the content is about rather than characteristics such as format or language.  A `TextualRepresentation` individuated by exact Unicode sequence is consequently better placed at the broader BFO GDC level.

I want **all three changes**, in this order:

1. **Move the HermiT experiment into `tests/bfo/`.** This is the most important action because it converts the architectural argument into a permanent regression test. Keep all eight cases, especially both controls. I would also add one ninth case if convenient: `TextualRepresentation ⊑ GDC`, `generically depends on some IBE`, local `hasTextValue`, two distinct IBEs carrying the same representation → consistent.

2. **Draft the decision record in `DECISION_RECORDS.md`.** Record this explicitly as an intentional, narrowly scoped departure from CCO's bearer-level literal convention. The justification should say that CCO has no form-level subclass of GDC, BFO expressly admits shared patterns/sequences as GDCs, and `cco:has text value` cannot type-safely be reused for such an entity because its domain is IBE. That makes the local property an **extension filling an uncovered semantic level**, not a duplicate CCO relation.

3. **Update R9.** I would change the finding from “MAJOR CCO conflict / replace `vn-core:hasTextValue`” to something like **“Current ICE classification requires correction; form-level GDC extension justified.”** Present the bearer-level CCO pattern as the alternative for applications that do not need copy-independent form identity, but make the form-level solution the recommended ValueNet design because offsets and exact-sequence identity are competency requirements.

I would make one addition to your implementation recommendation: don't rely on SHACL alone for the existence of a bearer. BFO already provides `generically depends on`, inverse to `is carrier of`; its domain is GDC.  I would therefore give `TextualRepresentation` an OWL existential along the lines of:

```ttl
vn-core:TextualRepresentation
    rdfs:subClassOf
        obo:BFO_0000031 ,
        [
            a owl:Restriction ;
            owl:onProperty obo:BFO_0000084 ; # generically depends on
            owl:someValuesFrom cco:ont00000253 # Information Bearing Entity
        ] .
```

Then retain SHACL to require an **explicitly represented** carrier in instance data. The OWL axiom states the ontological commitment; SHACL enforces data completeness. That division of labor is cleaner than using SHACL to supply an existential commitment missing from the ontology.

For the definition, under the required genus–differentia format, I suggest:

> **A Textual Representation is a generically dependent continuant that is an exact sequence of Unicode code points and is concretized by one or more information bearing entities.**

I would avoid saying “shared by every information bearing entity that carries it,” because a GDC need not actually have multiple simultaneous copies; BFO says there is **at least one of what may be multiple copies**. 

Likewise, keeping `TextSpanSelector` under **Designative ICE** is now even cleaner: the selector belongs at the content/aboutness level, while the selected offsets are calculated against the form-level sequence. That preserves precisely the separation your table identifies.

So: **please do all three—test, decision record, then R9—and incorporate the OWL existential carrier restriction as part of the ontology change.** The HermiT experiment has materially changed my disposition of this issue from a ValueNet defect to a justified BFO-level extension over a gap in CCO's information model.
