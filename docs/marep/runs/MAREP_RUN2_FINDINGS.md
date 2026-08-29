# valuenet-run2 — findings

Rendered from `RUN2_STATE.yaml` by `ValueNet_code/report_run.py`. The state file is the record; this is a view of it.

**Two kinds of statement appear below and are never merged.** Finding titles, severities and evidence are exactly what the run concluded from the substrate it was given, reproduced unedited. Anything inside a `⚠ RECONCILIATION` block was established *after* the run, sometimes contradicting it, and is never folded back into the finding. The state file itself is not modified by reconciliation.

- **phase** complete, **version** 145
- **substrate** `sha256:bb60e518f2861fda02c…`
- **findings** 28 — 22 confirmed, 4 unresolved, 2 archived
- **tokens declared** 412,000
- **evidence** 221/221 verified against the substrate

## confirmed (22)

### DECL-001 — vale2024's 1,840 properties are name declarations, not relations: nothing in that module can carry a constrain [clipped]

*high · proposed by Grounding*
 · confirmed by Formalist, Restraint

- vale2024 declares 1,840 object properties and all 1,840 lack a domain
  <br/>`metric:properties_without_domain:vale2024` — verified
- all 1,840 lack a range
  <br/>`metric:properties_without_range:vale2024` — verified
- all 1,840 lack functionality, transitivity, symmetry or inverse
  <br/>`metric:properties_without_characteristics:vale2024` — verified
- all 1,861 vale2024 classes reach no known upper ontology by rdfs:subClassOf
  <br/>`metric:classes_with_no_upper_root:vale2024` — verified
- 1,854 of 1,861 vale2024 classes carry no restriction or equivalence
  <br/>`metric:classes_without_necessary_conditions:vale2024` — verified
- vale2024 has zero axioms by which a reasoner could find it inconsistent
  <br/>`metric:contradiction_capacity:vale2024` — verified
- vale2024 declares no individuals, so no ABox or SHACL check has anything to target there
  <br/>`metric:individuals_declared:vale2024` — verified
- vale2024's 1,861 classes are 65% of the 2,866 distinct class IRIs in the corpus
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- All 1,861 vale2024 classes reach no known upper ontology, so the module shares no subsumption path with the BFO-rooted or DUL-rooted groups and cannot alter their entailments under merge
  <br/>`metric:classes_with_no_upper_root:vale2024` — verified
- By contrast the authored BFO layer's 180 classes are all BFO-rooted, so the two populations are formally unconnected
  <br/>`metric:classes_rooted_in_bfo:bfo-layer` — verified
- vale2024 has 0 contradiction capacity and 0 individuals, so the module cannot make a merged graph inconsistent nor produce a violation, which bounds the consequence of its inertness to 'no inference gained' rather than 'harm done'
  <br/>`metric:contradiction_capacity:vale2024` — verified

### DEF-001 — The one layer that gets reasoned over has no defined classes, so the CQ answers can never become entailments

*high · proposed by Formalist*
 · confirmed by Formalist, Validator, Restraint

- CQ5 returns 2 rows for processes that realize one value while contravening another, over 10 files / 2610 triples
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ5` — verified
- 164 of 180 bfo-layer classes are placed in a hierarchy but carry no restriction or equivalence
  <br/>`metric:classes_without_necessary_conditions:bfo-layer` — verified
- bfo-layer has contradiction capacity 2 — only two axioms by which a reasoner could find it inconsistent
  <br/>`metric:contradiction_capacity:bfo-layer` — verified
- 'contravenes' is a declared bfo-layer property carrying no characteristics
  <br/>`metric:properties_without_characteristics:bfo-layer` — verified
- The 32 contradiction axioms in the reasoner run decompose as 30 from the vendored BFO file plus 2 from the authored layer, so no failure mode currently available to the reasoner was authored by this project
  <br/>`metric:reasoner_contradiction_axioms:bfo-layer` — verified
- bfo-vendored supplies 30 of those axioms on its own
  <br/>`metric:contradiction_capacity:bfo-vendored` — verified
- CQ5's two rows are processes that realize one value while contravening another (distinct values), so a property-disjointness axiom between realization and 'contravenes' would not falsify the present fixture while making same-value pairs detectable
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ5` — verified
- The reasoner run carried 0 individuals while the layer declares 32, so the same clash rule stated as a shape would have 32 focus-node candidates that the entailment route currently has none of
  <br/>`metric:reasoner_individuals:bfo-layer` — verified
- bfo-layer declares 32 individuals available to a SHACL shape
  <br/>`metric:individuals_declared:bfo-layer` — verified
- No authored bfo-layer class carries any restriction or equivalence (164 of 180, including ValueDisposition itself), so nothing in the corpus currently states that realization and contravention are mutually exclusive; a disjointness axiom would be new domain content rather than a formalizat [clipped]
  <br/>`metric:classes_without_necessary_conditions:bfo-layer` — verified
- The reasoner run carried 0 individuals, so any new disjointness axiom would enter the layer without ever having been tested against the 32 individuals it would govern
  <br/>`metric:reasoner_individuals:bfo-layer` — verified

### DISJOINTNESS-001 — Sibling disjointness in the folk value hierarchy would contradict measured multi-typing

*high · proposed by Restraint*
 · confirmed by Formalist, Validator, Restraint

- thats-all-folks declares 386 individuals in total
  <br/>`metric:individuals_declared:thats-all-folks` — verified
- The four largest populated classes in the group carry 171, 160, 130 and 7 instances respectively, summing to 468
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- All 49 sibling sets in the group lack disjointness, and the measurement records this as a domain question rather than a shortfall
  <br/>`metric:sibling_sets_without_disjointness:thats-all-folks` — verified
- 386 declared individuals against 468 memberships in the four largest populated classes forces at least 82 individuals to hold two or more of those types
  <br/>`metric:individuals_declared:thats-all-folks` — verified
- The four largest populated classes carry 171, 160, 130 and 7 instances, summing to 468 memberships
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- All 21 populated thats-all-folks classes are unshaped, so the multi-typing measured here has never been put in front of a validator and the overlap is currently invisible to any check
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- repository-root reports the same three instance counts (IndividualValue 171, FolkValue 160, InnerValue 130) as thats-all-folks, so the overlapping typing of folk values is a corpus-wide convention rather than an artefact of one group
  <br/>`metric:populated_classes_without_a_shape:repository-root` — verified
- thats-all-folks has 24 of 378 classes without necessary conditions, including FolkValue, InnerValue and CulturalValue themselves, so there is no definitional content anywhere from which sibling exclusivity could be derived
  <br/>`metric:classes_without_necessary_conditions:thats-all-folks` — verified

### FIXTURE-001 — The moral-epistemics scenario's gaps are the test, not defects to be filled

*high · proposed by Restraint*
 · confirmed by Validator, Restraint

- CQ3 returns 1 row for culpability ascriptions lacking evidential warrant and expects a non-empty answer
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ3` — verified
- CQ4 returns 4 rows for values an agent bears that no recorded process realizes, and expects a non-empty answer
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ4` — verified
- The moral-epistemics shapes produce 1 warning and 0 violations over the same 14 focus nodes
  <br/>`metric:shacl_warnings:valuenet-moral-epistemics-shapes` — verified
- The scenario file is a small dedicated graph of 75 triples with one import, consistent with a hand-built fixture
  <br/>`document:BFO/valuenet-moral-epistemics-scenario.ttl` — verified
- The shape run over the same 14 focus nodes reports 0 violations, so the deliberate scenario gaps are indistinguishable from clean data in the validation artefacts
  <br/>`metric:shacl_violations:valuenet-moral-epistemics-shapes` — verified
- All 6 CQs pass by matching their own '# expect:' declarations, two of which require the scenario's gaps to be present, so filling those gaps would convert passing queries into failures
  <br/>`metric:queries_passing:valuenet-moral-epistemics-CQ` — verified

### PREREQ-001 — The largest instance graph is asserted through 21 predicates that no file in the corpus declares, so no constr [clipped]

*high · proposed by Grounding*
 · confirmed by Formalist, Validator, Restraint

- 21 of 26 non-builtin predicates used by thats-all-folks are declared nowhere in the corpus, including hasModality, involves, associatedWith, hasDataValue and hasQuality
  <br/>`metric:predicates_used_but_not_declared:thats-all-folks` — verified
- thats-all-folks declares only 9 object properties in total
  <br/>`metric:properties_declared:thats-all-folks` — verified
- the group holds 44,934 distinct triples
  <br/>`metric:triples_distinct_in_group:thats-all-folks` — verified
- it declares 386 individuals available to a SHACL or ABox check
  <br/>`metric:individuals_declared:thats-all-folks` — verified
- all 21 of its populated classes have no shape targeting them
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- taf.ttl alone carries 38,558 triples of this instance content
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- thats-all-folks has zero axioms by which a reasoner could find it inconsistent, so no verdict over its 44,934 triples can currently be anything but consistent
  <br/>`metric:contradiction_capacity:thats-all-folks` — verified
- The group declares only 9 object properties against 26 non-builtin predicates in use, so 21 predicates carry no type declaration that a domain, range or property shape could attach to
  <br/>`metric:properties_declared:thats-all-folks` — verified

### SCOPE-001 — Every clean result in this repository is a property of a 179-class island; 2,687 of 2,866 classes are outside [clipped]

*high · proposed by Skeptic*
 · confirmed by Validator, Restraint

- 2,687 corpus classes are declared but outside the grounding check's scope; only 179 were measured
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- SHACL validated 6 of 165 ontology files, data graph limited to the BFO layer plus the scenario
  <br/>`metric:shacl_files_validated:corpus` — verified
- Shapes targeted 14 focus nodes; the metric states zero violations over zero focus nodes says nothing
  <br/>`metric:shacl_focus_nodes:corpus` — verified
- The reasoner ran over 7 files and 2,403 triples with 0 individuals, a TBox satisfiability check only
  <br/>`metric:reasoner_individuals:bfo-layer` — verified
- All TestingFramework and CQ queries ran over 10 files / 2,610 triples
  <br/>`metric:query_rows:TestingFramework:Query1` — verified
- the reasoner run covered 7 files and 2,403 triples with no ABox
  <br/>`metric:reasoner_triples:bfo-layer` — verified
- all 179 measured classes reach a BFO root and none lack a label or definition
  <br/>`metric:classes_reaching_bfo_root:bfo-suite-merged` — verified

### SHACL-001 — Shapes reach 14 of ~1,100 declared individuals; every populated class outside the scenario is unvalidated

*high · proposed by Validator*
 · confirmed by Validator, Restraint

- Shapes were validated over 6 of 165 ontology files, targeting 14 focus nodes
  <br/>`metric:shacl_focus_nodes:corpus` — verified
- Only 6 of 165 files formed the data graph: the BFO layer plus the scenario, nothing else
  <br/>`metric:shacl_files_validated:corpus` — verified
- All 26 populated classes in repository-root lack a shape; largest are WVSVariable (323), IndividualValue (171), FolkValue (160), InnerValue (130)
  <br/>`metric:populated_classes_without_a_shape:repository-root` — verified
- All 21 populated classes in thats-all-folks lack a shape, including CulturalValue (7)
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- 13 of 18 populated bfo-layer classes lack a shape: ont00001017 (3), CareDisposition (2), TrustDisposition (1), RashJudgmentAct (1)
  <br/>`metric:populated_classes_without_a_shape:bfo-layer` — verified
- repository-root declares 694 individuals available to a SHACL shape
  <br/>`metric:individuals_declared:repository-root` — verified
- thats-all-folks declares 386 individuals available to a SHACL shape
  <br/>`metric:individuals_declared:thats-all-folks` — verified
- thats-all-folks has no axioms by which a reasoner could find it inconsistent, so OWL cannot substitute for shapes there
  <br/>`metric:contradiction_capacity:thats-all-folks` — verified
- 46% of thats-all-folks triples are the same statement made in another file, so instance counts across groups likely double-count
  <br/>`metric:duplicate_triple_ratio:thats-all-folks` — verified
- Both groups report the same three instance counts (IndividualValue 171, FolkValue 160, InnerValue 130), so summing 694 and 386 counts at least 461 memberships twice and the '~1,100' figure is an upper bound
  <br/>`metric:populated_classes_without_a_shape:repository-root` — verified
- thats-all-folks reports the identical trio of counts, confirming the overlap
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- WVSVariable at 323 appears only in repository-root's populated-class list, so a shape there reaches instances no thats-all-folks shape would
  <br/>`metric:populated_classes_without_a_shape:repository-root` — verified

### SHACL-002 — Missing evidential warrant is currently a query answer, not a validation failure

*high · proposed by Validator*
 · confirmed by Formalist, Validator, Restraint

- CQ3 ('Which ascriptions of culpability have no recorded evidential warrant') returns 1 row and expects a non-empty answer
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ3` — verified
- CQ4 ('Which values does an agent bear that no recorded process realizes?') returns 4 rows
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ4` — verified
- All 6 CQs pass by matching their own '# expect:' declaration, so a row indicating absent warrant is recorded as a pass
  <br/>`metric:queries_passing:valuenet-moral-epistemics-CQ` — verified
- The scenario file the CQs run against contributes 75 triples and declares no classes, so these are instance-level facts
  <br/>`document:BFO/valuenet-moral-epistemics-scenario.ttl` — verified
- The layer offers 2 axioms by which a reasoner could find it inconsistent, none of which concern the presence of warrant assertions, so no OWL axiom currently converts a missing warrant into a detectable fault
  <br/>`metric:contradiction_capacity:bfo-layer` — verified
- The reasoner run carried no individuals, so even a cardinality restriction would have had no ABox to apply to
  <br/>`metric:reasoner_individuals:bfo-layer` — verified
- The moral-epistemics shapes report 0 violations over the same 14 focus nodes that CQ3's warrant-less ascription is drawn from, so the identical fact registers as a query row and as a clean validation
  <br/>`metric:shacl_violations:valuenet-moral-epistemics-shapes` — verified
- CQ3 returns 1 row for a culpability ascription with no recorded evidential warrant
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ3` — verified
- All 6 CQs currently pass, and CQ3 and CQ4 pass by returning non-empty results over the same graph the shapes validate, so a shape making warrant-absence a violation would permanently red-flag the fixture that the CQ suite requires to stay as it is
  <br/>`metric:queries_passing:valuenet-moral-epistemics-CQ` — verified

### SHACL-003 — 12,364 trigger triples carry no shape, no class, and nothing a reasoner can fail on

*high · proposed by Validator*
 · confirmed by Formalist, Validator, Restraint

- mf-triggers spans 13 parsing files with 12,364 distinct triples and 0 declared classes
  <br/>`metric:triples_distinct_in_group:mf-triggers` — verified
- mf-triggers uses exactly 1 non-builtin predicate across the whole group
  <br/>`metric:predicates_used_but_not_declared:mf-triggers` — verified
- mf-triggers has zero axioms by which a reasoner could find it inconsistent, so a consistency verdict over it is guaranteed
  <br/>`metric:contradiction_capacity:mf-triggers` — verified
- CQ6 reaches a value from a span of text across 23 files and 14,974 triples, showing trigger data is loadable alongside the BFO layer
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ6` — verified
- care_frame.ttl alone contributes 5,379 triples with no classes declared
  <br/>`document:MFTriggers/care_frame.ttl` — verified
- degradation_frame.ttl contributes only 20 triples, so frame files vary by two orders of magnitude in size
  <br/>`document:MFTriggers/degradation_frame.ttl` — verified
- The bfo-layer declares the offset datatype properties (hasEndOffset among them) with no functionality, transitivity, symmetry or inverse
  <br/>`metric:properties_without_characteristics:bfo-layer` — verified
- mf-triggers uses exactly one non-builtin predicate, so the offset properties cited by the issue are not used in that group and functionality on them would not change its failure surface
  <br/>`metric:predicates_used_but_not_declared:mf-triggers` — verified
- TextSpan is declared in the BFO layer with no restriction or equivalence, so functional offset properties would be the first constraint attaching to it and would raise that layer's contradiction capacity above its current 2
  <br/>`metric:classes_without_necessary_conditions:bfo-layer` — verified
- mf-triggers declares 0 classes, so no sh:targetClass can bind anywhere in the group and the single predicate is the only usable shape target
  <br/>`metric:classes_declared:mf-triggers` — verified
- mf-triggers declares 0 individuals, confirming there is no rdf:type-based focus node in the group
  <br/>`metric:individuals_declared:mf-triggers` — verified
- mf-triggers declares 0 individuals, so there is no rdf:type-based focus node anywhere in the group and any shape must key on the single predicate rather than on invented class memberships
  <br/>`metric:individuals_declared:mf-triggers` — verified
- Frame files span two orders of magnitude (care_frame.ttl 5,379 triples against degradation_frame.ttl 20), so any shape asserting a minimum coverage per frame would fail legitimately sparse frames
  <br/>`document:MFTriggers/degradation_frame.ttl` — verified

### AXIOMS-001 — vale2024 is a generated role lexicon; adding domains, ranges or characteristics would assert what the extracti [clipped]

*medium · proposed by Restraint*
 · confirmed by Formalist, Restraint

- All 1,840 declared properties in vale2024 lack domain, and the same 1,840 lack range
  <br/>`metric:properties_without_domain:vale2024` — verified
- All 1,840 properties lack functionality, transitivity, symmetry or inverse
  <br/>`metric:properties_without_characteristics:vale2024` — verified
- 1,854 of 1,861 vale2024 classes carry no restriction or equivalence, and the sampled names (Ability, Accompany, Accusation, Accused) are role labels rather than defined universals
  <br/>`metric:classes_without_necessary_conditions:vale2024` — verified
- vale2024 has zero contradiction capacity, so a consistency verdict over it is guaranteed and it cannot break a merge
  <br/>`metric:contradiction_capacity:vale2024` — verified
- vale2024 declares no individuals, so no domain or range assertion could be validated against instance data
  <br/>`metric:individuals_declared:vale2024` — verified
- vale2024 declares no individuals, so a domain or range assertion there could produce no type inference and no violation
  <br/>`metric:individuals_declared:vale2024` — verified
- vale2024 has zero axioms by which a reasoner could find it inconsistent, so a new range could not conflict with anything already stated
  <br/>`metric:contradiction_capacity:vale2024` — verified
- vale2024 spans 5 files with class counts of 1,842 / 1,849 / 81 / 81 / 73 and a 0.1237 duplicate ratio, the shape of a generated artefact emitted at several thresholds rather than of hand-authored modules
  <br/>`metric:duplicate_triple_ratio:vale2024` — verified
- All 22 vale2024 sibling sets lack disjointness as well, completing the pattern of uniform axiomatic silence across every dimension measured
  <br/>`metric:sibling_sets_without_disjointness:vale2024` — verified

### CQ-001 — The competency questions pass by returning rows, which does not establish that the returned rows are correct

*medium · proposed by Skeptic*
 · confirmed by Validator, Restraint

- All 6 CQs pass, where passing means matching the document's own '# expect:' declaration
  <br/>`metric:queries_passing:valuenet-moral-epistemics-CQ` — verified
- CQ2 returns 1 row and its expectation is only 'expected a non-empty answer'
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ2` — verified
- CQ3 returns 1 row under the same non-empty expectation
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ3` — verified
- The scenario supplying these answers is a 75-triple file
  <br/>`document:BFO/valuenet-moral-epistemics-scenario.ttl` — verified
- Both shape files report 0 violations over the same 14 focus nodes the CQs draw their rows from, so no independent check bears on the row contents
  <br/>`metric:shacl_violations:valuenet-core-shapes` — verified
- The three TestingFramework queries declare 'expected no results' and return 0 rows, showing the harness supports exact expectations and that the non-empty form used by the CQs is a per-document choice rather than a limitation
  <br/>`metric:query_rows:TestingFramework:Query1` — verified

### DISJ-001 — Disposition siblings in the BFO layer are undeclared-disjoint, so the 32 individuals cannot be falsified by type

*medium · proposed by Formalist*
 · confirmed by Formalist, Validator
 · contested by Restraint

- 26 of 26 bfo-layer sibling sets have no disjointness, including ValueDisposition, MoralValueDisposition and PersonalValueDisposition
  <br/>`metric:sibling_sets_without_disjointness:bfo-layer` — verified
- bfo-layer declares 32 individuals across 18 populated classes
  <br/>`metric:individuals_declared:bfo-layer` — verified
- 13 of 18 populated bfo-layer classes have no SHACL shape, largest CareDisposition (2), TrustDisposition (1), RashJudgmentAct (1)
  <br/>`metric:populated_classes_without_a_shape:bfo-layer` — verified
- The reasoner run over bfo-layer had 0 individuals in scope — TBox satisfiability only
  <br/>`metric:reasoner_individuals:bfo-layer` — verified
- The vendored upper layer already declares disjointness in 10 of its 11 sibling sets, so cross-branch type conflicts are detectable and the undeclared-disjointness gap is confined to locally authored siblings
  <br/>`metric:sibling_sets_without_disjointness:bfo-vendored` — verified
- bfo-vendored carries 30 contradiction axioms against the authored layer's 2, locating the entire existing failure surface upstream
  <br/>`metric:contradiction_capacity:bfo-vendored` — verified
- The same corpus's folk layer has 386 declared individuals against 468 memberships in its four largest populated classes, forcing at least 82 individuals to hold two or more of those types — evidence that overlapping value categories are the authors' intent, not an oversight
  <br/>`metric:individuals_declared:thats-all-folks` — verified
- bfo-layer's populated classes are thinly filled — largest unshaped ones are ont00001017 (3), CareDisposition (2), TrustDisposition (1) — so there is no measured multi-typing in this layer that a disjointness axiom would catch
  <br/>`metric:populated_classes_without_a_shape:bfo-layer` — verified
- The reasoner run over bfo-layer carried no ABox, so disjointness axioms added to this layer would be unexercised against its 32 individuals
  <br/>`metric:reasoner_individuals:bfo-layer` — verified

### DOMRANGE-001 — RO_0002233/RO_0002234 and evokesFrame are used without domain or range, forfeiting type inference over the trigger data

*medium · proposed by Formalist*
 · confirmed by Formalist, Validator
 · contested by Restraint

- RO_0002233 and RO_0002234 are the two bfo-layer properties with no domain
  <br/>`metric:properties_without_domain:bfo-layer` — verified
- RO_0002233, RO_0002234 and evokesFrame are declared with no range
  <br/>`metric:properties_without_range:bfo-layer` — verified
- mf-triggers is 12,364 distinct triples using 1 non-builtin predicate
  <br/>`metric:predicates_used_but_not_declared:mf-triggers` — verified
- CQ6 reaches a value from a text span across 23 files and 14,974 triples
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ6` — verified
- mf-triggers uses exactly one non-builtin predicate and zero of its predicates are undeclared, so the property carrying all 12,364 assertions is declared elsewhere in the corpus — but the substrate does not name it, leaving the identification with evokesFrame inferential
  <br/>`metric:predicates_used_but_not_declared:mf-triggers` — verified
- evokesFrame carries neither a range nor any characteristic, so it constrains nothing on either side of its assertions
  <br/>`metric:properties_without_characteristics:bfo-layer` — verified
- RO_0002233, RO_0002234 and evokesFrame are the three declared bfo-layer properties with no range, leaving the object position of every assertion they carry unconstrained on the OWL side
  <br/>`metric:properties_without_range:bfo-layer` — verified
- bfo-vendored declares 40 object properties with 0 lacking a domain and 0 lacking a range, so the upstream axiomatization of borrowed relations is already complete where it is vendored — the pattern in this corpus is to take such axioms from upstream, not to author them locally
  <br/>`metric:properties_without_domain:bfo-vendored` — verified
- mf-triggers declares 0 classes and 0 individuals, so a range asserted on the predicate carrying its 12,364 triples would manufacture type memberships for objects that no author ever typed and no shape currently checks
  <br/>`metric:classes_declared:mf-triggers` — verified

### DUPLICATION-001 — The high duplicate ratios are materialized aggregates and parameter variants, not drift

*medium · proposed by Skeptic*
 · confirmed by Restraint

- duplicate_triple_ratio for thats-all-folks is 0.4618, 38,563 of 83,497 triples
  <br/>`metric:duplicate_triple_ratio:thats-all-folks` — verified
- ThatsAllFolks/taf.ttl alone contains 38,558 triples
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- duplicate_triple_ratio for mf-triggers is 0.4991, 12,320 of 24,684 triples
  <br/>`metric:duplicate_triple_ratio:mf-triggers` — verified
- MFTriggers/ClosureHaidtValueFrames.ttl contains 12,342 triples
  <br/>`document:MFTriggers/ClosureHaidtValueFrames.ttl` — verified
- folk_aligned.ttl parses to 5,828 triples and 378 classes, identical in size to ThatsAllFolks/folk.ttl
  <br/>`document:folk_aligned.ttl` — verified
- folk_aligned.ttl reports 5,828 triples and 378 classes, matching folk.ttl, but sits in a different measurement group so no content comparison exists
  <br/>`document:folk_aligned.ttl` — verified
- folk_aligned.ttl and ThatsAllFolks/folk.ttl match only on triple count (5,828) and class count (378); no content comparison exists in the substrate, so an aligned variant and an un-synced copy are indistinguishable on the present evidence
  <br/>`document:folk_aligned.ttl` — verified
- vale2024's 0.1237 duplicate ratio across 5 files is an order of magnitude below the two aggregate cases, consistent with parameter variants rather than materialized restatement
  <br/>`metric:duplicate_triple_ratio:vale2024` — verified

### GROUNDING-001 — Do not extend the BFO-rooting requirement past the 179 classes it was scoped to

*medium · proposed by Restraint*
 · confirmed by Restraint

- 179 classes were measured for BFO grounding and 2,687 are explicitly outside the check's scope
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- All 179 classes in the merged BFO suite reach the BFO root
  <br/>`metric:classes_reaching_bfo_root:bfo-suite-merged` — verified
- 384 repository-root classes already reach a DUL root, an alternative and complete upper grounding
  <br/>`metric:classes_rooted_in_dul:repository-root` — verified
- The BFO suite has zero dangling IRIs, indicating the scoped layer is internally closed
  <br/>`metric:dangling_iris:bfo-suite-merged` — verified
- All 1,861 vale2024 classes reach no known upper ontology and the module declares 0 individuals, so extending the BFO-rooting requirement there would demand 1,861 subsumption assertions that could neither be derived from existing content nor validated against instance data
  <br/>`metric:classes_with_no_upper_root:vale2024` — verified
- All 26 moral-molecules classes also reach no upper ontology, in a 288-triple single-file class sketch, so the unrooted population is dominated by lexicons and sketches rather than by modules that were meant to be grounded
  <br/>`metric:classes_with_no_upper_root:moral-molecules` — verified

### IMPORTS-001 — The 21 undeclared predicates in thats-all-folks are DUL terms; declaring them locally would fork DUL

*medium · proposed by Restraint*
 · confirmed by Formalist, Validator, Restraint

- 21 of 26 non-builtin predicates used in thats-all-folks have no declaration anywhere in the corpus, including hasQuality, involves, associatedWith and hasDataValue
  <br/>`metric:predicates_used_but_not_declared:thats-all-folks` — verified
- 376 of 378 classes in the group reach a DUL root, so the group is authored against DUL
  <br/>`metric:classes_rooted_in_dul:thats-all-folks` — verified
- Every other group reports zero undeclared predicates, so the gap is specific to the DUL-based layer
  <br/>`metric:predicates_used_but_not_declared:repository-root` — verified
- The group holds 44,934 distinct triples asserted through predicates whose domain and range live upstream in DUL, so resolving the import is the only way any type inference over that volume becomes available
  <br/>`metric:triples_distinct_in_group:thats-all-folks` — verified
- The 21 undeclared predicates include hasQuality, involves, associatedWith and hasDataValue, all of which carry axioms in DUL that a local redeclaration would not inherit
  <br/>`metric:predicates_used_but_not_declared:thats-all-folks` — verified
- thats-all-folks has 21 of 21 populated classes unshaped and 386 individuals, a validation gap that does not depend on the DUL import being resolved
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- thats-all-folks declares only 9 object properties in total, none of them the 21 DUL terms in use, indicating the module never intended to own those relations
  <br/>`metric:properties_declared:thats-all-folks` — verified

### IRI-001 — The 21 undeclared predicates in thats-all-folks are the one absence count here that is unambiguously a defect, [clipped]

*medium · proposed by Skeptic*
 · confirmed by Validator, Restraint

- thats-all-folks uses 21 of 26 non-builtin predicates that are undeclared anywhere in the corpus
  <br/>`metric:predicates_used_but_not_declared:thats-all-folks` — verified
- repository-root uses 14 non-builtin predicates with 0 undeclared, showing the check is not systematically failing
  <br/>`metric:predicates_used_but_not_declared:repository-root` — verified
- thats-all-folks contains 44,934 distinct triples
  <br/>`metric:triples_distinct_in_group:thats-all-folks` — verified
- thats-all-folks declares only 9 object properties in total
  <br/>`metric:properties_declared:thats-all-folks` — verified

### REASONER-001 — The consistency result is close to unfalsifiable outside the BFO layer, so it should not be cited as evidence [clipped]

*medium · proposed by Skeptic*
 · confirmed by Formalist, Validator, Restraint

- reasoner_consistent for bfo-layer is 1, annotated 'only 32 axioms could have produced a failure; no individuals in scope'
  <br/>`metric:reasoner_consistent:bfo-layer` — verified
- contradiction_capacity for thats-all-folks is 0, with the note that a consistency verdict over it is guaranteed
  <br/>`metric:contradiction_capacity:thats-all-folks` — verified
- contradiction_capacity for vale2024 is 0, same annotation
  <br/>`metric:contradiction_capacity:vale2024` — verified
- unsatisfiable_classes for bfo-layer is 0 of 267 classes, with 32 axioms that could have made one fail
  <br/>`metric:unsatisfiable_classes:bfo-layer` — verified
- repository-root carries 30 contradiction axioms which no reasoner run in this substrate covered, so the corpus's largest authored failure surface has never been exercised
  <br/>`metric:contradiction_capacity:repository-root` — verified
- The reasoner's 32 available failure modes are 30 vendored plus 2 authored, so the verdict tests the imported upper ontology rather than the project's own axioms
  <br/>`metric:reasoner_contradiction_axioms:bfo-layer` — verified
- thats-all-folks combines zero contradiction capacity with 386 declared individuals, so its entire instance population is beyond both the reasoner's and the validator's reach
  <br/>`metric:individuals_declared:thats-all-folks` — verified
- All 21 of its populated classes are unshaped, confirming no shape covers the population the reasoner cannot fault
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified

### ROOT-001 — Two live anchoring regimes and one 19-triple bridge: cross-module constraints have no substrate to be stated over

*medium · proposed by Grounding*
 · confirmed by Formalist, Restraint

- 180 classes in the bfo-layer are rooted in BFO
  <br/>`metric:classes_rooted_in_bfo:bfo-layer` — verified
- 376 thats-all-folks classes are rooted in DUL
  <br/>`metric:classes_rooted_in_dul:thats-all-folks` — verified
- 384 repository-root classes are rooted in DUL
  <br/>`metric:classes_rooted_in_dul:repository-root` — verified
- 379 repository-root classes reach no upper ontology
  <br/>`metric:classes_with_no_upper_root:repository-root` — verified
- all 26 moral-molecules classes reach no upper ontology
  <br/>`metric:classes_with_no_upper_root:moral-molecules` — verified
- the mappings file contains 19 triples and declares no classes
  <br/>`document:BFO/valuenet-mappings.ttl` — verified
- The mappings file is 19 triples and declares no classes, which is too little to carry equivalence axioms across two upper-ontology regimes
  <br/>`document:BFO/valuenet-mappings.ttl` — verified
- 164 of 180 BFO-layer classes carry no restriction or equivalence, so even where the two regimes name the same notion there is no definitional content for a bridge axiom to transfer
  <br/>`metric:classes_without_necessary_conditions:bfo-layer` — verified
- A third population sits outside both regimes — all 26 moral-molecules classes reach no upper ontology — so a two-regime bridge would still leave part of the corpus unconnected and should not be presented as a completeness fix
  <br/>`metric:classes_with_no_upper_root:moral-molecules` — verified

### VENDORED-001 — The gaps in bfo-core.ttl are upstream and must not be patched locally

*medium · proposed by Restraint*
 · confirmed by Formalist, Restraint

- bfo-vendored has exactly 1 class reaching no known upper ontology, out of 36
  <br/>`metric:classes_with_no_upper_root:bfo-vendored` — verified
- 10 of 11 sibling sets in bfo-vendored already declare disjointness; only BFO_0000040 does not
  <br/>`metric:sibling_sets_without_disjointness:bfo-vendored` — verified
- 17 of 36 vendored classes carry no restriction or equivalence, including the BFO top-level classes BFO_0000001 and BFO_0000003
  <br/>`metric:classes_without_necessary_conditions:bfo-vendored` — verified
- bfo-core.ttl is a self-contained 1014-triple file with no imports and no duplicated statements
  <br/>`metric:duplicate_triple_ratio:bfo-vendored` — verified
- bfo-vendored contributes 30 of the 32 contradiction axioms available to the reasoner run, making the vendored file the corpus's existing failure surface rather than a gap in it
  <br/>`metric:reasoner_contradiction_axioms:bfo-layer` — verified
- All 40 bfo-vendored object properties carry a domain and a range (0 without either), so the vendored file is the one fully constrained property set in the corpus and needs no local supplementation
  <br/>`metric:properties_without_domain:bfo-vendored` — verified
- bfo-vendored is a single file with 0 duplicate triples of 1,014, so it is an unmodified vendored drop that local edits would make un-refreshable
  <br/>`metric:duplicate_triple_ratio:bfo-vendored` — verified

### SHACL-005 — The only signal the shape run produces is a non-blocking warning

*low · proposed by Validator*
 · confirmed by Validator, Restraint

- valuenet-moral-epistemics-shapes emits 1 warning
  <br/>`metric:shacl_warnings:valuenet-moral-epistemics-shapes` — verified
- valuenet-moral-epistemics-shapes reports 0 violations over 14 focus nodes in 6 of 165 files
  <br/>`metric:shacl_violations:valuenet-moral-epistemics-shapes` — verified
- valuenet-core-shapes emits 0 warnings and 0 violations
  <br/>`metric:shacl_warnings:valuenet-core-shapes` — verified
- The core shapes file is 68 triples
  <br/>`document:BFO/valuenet-core-shapes.ttl` — verified
- The moral-epistemics shapes file is 50 triples
  <br/>`document:BFO/valuenet-moral-epistemics-shapes.ttl` — verified

### SHAPES-001 — populated_classes_without_a_shape is a coverage gap only where instances exist, and that is 1,080 instances in [clipped]

*low · proposed by Skeptic*
 · confirmed by Validator, Restraint

- repository-root has 26 of 26 populated classes without a shape; largest are WVSVariable (323), IndividualValue (171), FolkValue (160), InnerValue (130)
  <br/>`metric:populated_classes_without_a_shape:repository-root` — verified
- vale2024 declares 0 individuals, so no instance-level shape check applies to it
  <br/>`metric:individuals_declared:vale2024` — verified
- repository-root declares 694 individuals available to a SHACL or ABox check
  <br/>`metric:individuals_declared:repository-root` — verified
- thats-all-folks declares 386 individuals and has 21 of 21 populated classes unshaped
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- repository-root's largest populated classes include IndividualValue (171), FolkValue (160) and InnerValue (130)
  <br/>`metric:populated_classes_without_a_shape:repository-root` — verified
- thats-all-folks reports the same three counts, so the 694 and 386 individual totals overlap by at least 461 memberships and cannot simply be added
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- mf-triggers and moral-molecules also declare 0 individuals, so together with vale2024 three of the seven groups have no instance-level shape obligation whatsoever and the coverage gap is confined to bfo-layer, repository-root and thats-all-folks
  <br/>`metric:individuals_declared:moral-molecules` — verified

## unresolved (4)

### METHOD-001 — Absence counts in this corpus are not defect counts, and three of them are explicitly self-annotated as such

*high · proposed by Skeptic*
 · contested by Formalist

- sibling_sets_without_disjointness for thats-all-folks is 49 of 49, annotated 'whether siblings should be disjoint is a domain question, not a shortfall'
  <br/>`metric:sibling_sets_without_disjointness:thats-all-folks` — verified
- sibling_sets_without_disjointness for vale2024 is 22 of 22, carrying the same annotation
  <br/>`metric:sibling_sets_without_disjointness:vale2024` — verified
- vale2024 declares 1,840 object properties, of which 1,840 lack domain
  <br/>`metric:properties_without_domain:vale2024` — verified
- vale2024 declares 1,861 classes, of which 1,854 carry no restriction or equivalence
  <br/>`metric:classes_without_necessary_conditions:vale2024` — verified
- The 'domain question, not a shortfall' annotation appears verbatim on bfo-vendored's disjointness metric, where 10 of 11 sibling sets do declare disjointness, showing the note is metric-level boilerplate rather than a case-specific judgement
  <br/>`metric:sibling_sets_without_disjointness:bfo-vendored` — verified
- In thats-all-folks the disjointness question is settled empirically rather than by domain taste: 386 individuals against 468 memberships in four classes forces overlap
  <br/>`metric:individuals_declared:thats-all-folks` — verified

### INV-001 — hasPositiveCounterpart/hasNegativeCounterpart are an unlinked inverse pair in a module with zero contradiction capacity

*medium · proposed by Formalist*
 · contested by Formalist, Validator, Restraint

- hasPositiveCounterpart and hasNegativeCounterpart are declared with no domain
  <br/>`metric:properties_without_domain:moral-molecules` — verified
- 6 of 10 moral-molecules properties carry no functionality, transitivity, symmetry or inverse
  <br/>`metric:properties_without_characteristics:moral-molecules` — verified
- MoralElement and NegativeMoralElement are among the 3 of 3 sibling sets without disjointness
  <br/>`metric:sibling_sets_without_disjointness:moral-molecules` — verified
- moral-molecules contradiction capacity is 0 — a consistency verdict over it is guaranteed
  <br/>`metric:contradiction_capacity:moral-molecules` — verified
- The six moral-molecules properties lacking characteristics are listed alphabetically and the list skips both hasNegativeCounterpart and hasPositiveCounterpart while including the later-sorting hasSocialComponent, indicating both counterpart properties do carry a characteristic
  <br/>`metric:properties_without_characteristics:moral-molecules` — verified
- The alphabetical listing convention is confirmed by the domain metric, which enumerates fulfilledBy, hasMoralComponent, hasNegativeCounterpart, hasPositiveCounterpart, includesRole in order
  <br/>`metric:properties_without_domain:moral-molecules` — verified
- moral-molecules declares 0 individuals, so no SHACL shape in that module would have a focus node and no ABox consequence of an inverse declaration could be observed
  <br/>`metric:individuals_declared:moral-molecules` — verified
- moral-molecules declares 0 individuals, so no inverse declaration or shape in that module could produce an observable ABox consequence or a violation
  <br/>`metric:individuals_declared:moral-molecules` — verified
- moral-molecules is a single 288-triple file with 26 classes and no imports, i.e. a class sketch rather than an axiomatized module, so its uniform absence of domains and ranges (5 of 10 properties) is the module's character rather than a lapse on one pair
  <br/>`document:MoralMolecules/curry_no_combinations_updated.ttl` — verified

### SHACL-004 — Datatype conformance is unenforceable anywhere outside the BFO layer: 3 datatype properties in the entire corpus

*medium · proposed by Validator*
 · contested by Validator, Restraint

- thats-all-folks uses 21 undeclared predicates of 26 in use, including hasDataValue, hasQuality and hasModality
  <br/>`metric:predicates_used_but_not_declared:thats-all-folks` — verified
- thats-all-folks declares 9 properties, all object properties and none datatype
  <br/>`metric:properties_declared:thats-all-folks` — verified
- bfo-layer is the only group declaring datatype properties: 3 of 11
  <br/>`metric:properties_declared:bfo-layer` — verified
- repository-root declares 43 properties, all object, none datatype
  <br/>`metric:properties_declared:repository-root` — verified
- vale2024 declares 1,840 object properties, all without domain or range
  <br/>`metric:properties_without_range:vale2024` — verified
- taf.ttl carries 38,558 triples of instance data under this unconstrained predicate set
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- thats-all-folks declares 386 individuals, which are available as focus nodes for a sh:datatype constraint irrespective of whether hasDataValue is declared
  <br/>`metric:individuals_declared:thats-all-folks` — verified
- hasDataValue is among the 21 predicates in use without a declaration, i.e. it is in use and therefore reachable by sh:path regardless of declaration status
  <br/>`metric:predicates_used_but_not_declared:thats-all-folks` — verified
- thats-all-folks declares 386 individuals, which are available as focus nodes for a sh:datatype constraint regardless of whether the predicate carries an owl:DatatypeProperty declaration
  <br/>`metric:individuals_declared:thats-all-folks` — verified
- The 21 undeclared predicates including hasDataValue and hasQuality are DUL terms in a group where 376 of 378 classes reach a DUL root, so redeclaring them locally as datatype properties would fork the upstream vocabulary
  <br/>`metric:classes_rooted_in_dul:thats-all-folks` — verified

### RANGE-001 — vale2024's 1,840 properties mirror its class names one-for-one but assert no range, so its 30,889 triples entail nothing

*low · proposed by Formalist*
 · contested by Restraint

- All 1,840 vale2024 properties lack a range; the first listed are hasAbility, hasAccompany, hasAccusation, hasAccused, hasAchievedobject
  <br/>`metric:properties_without_range:vale2024` — verified
- 1,854 of 1,861 vale2024 classes carry no restriction or equivalence; the first listed are Ability, Accompany, Accusation, Accused, Achievedobject
  <br/>`metric:classes_without_necessary_conditions:vale2024` — verified
- vale2024 contradiction capacity is 0
  <br/>`metric:contradiction_capacity:vale2024` — verified
- vale2024 holds 30,889 distinct triples
  <br/>`metric:triples_distinct_in_group:vale2024` — verified
- vale2024 spans 5 files with a 0.1237 duplicate ratio (4,359 of 35,248 triples), consistent with parameter variants of one generated artefact rather than independently authored modules
  <br/>`metric:duplicate_triple_ratio:vale2024` — verified
- vale2024 declares 0 individuals, so a range assertion there could be neither exercised nor falsified
  <br/>`metric:individuals_declared:vale2024` — verified
- All 1,840 vale2024 properties also lack functionality, transitivity, symmetry or inverse — the same complete uniformity as the domain and range absences, indicating mechanical generation
  <br/>`metric:properties_without_characteristics:vale2024` — verified

## archived (2)

### SCOPE-002 — Every green verdict in this substrate was produced over 1 to 6 percent of the corpus, so no group-level qualit [clipped]

*high · proposed by Skeptic*

- 2,687 corpus classes are declared but outside the grounding check's scope; only 179 were measured
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- SHACL validated 6 of 165 ontology files, data graph limited to the BFO layer plus the scenario
  <br/>`metric:shacl_files_validated:corpus` — verified
- Shapes targeted 14 focus nodes; the metric states zero violations over zero focus nodes says nothing
  <br/>`metric:shacl_focus_nodes:corpus` — verified
- The reasoner ran over 7 files and 2,403 triples with 0 individuals, a TBox satisfiability check only
  <br/>`metric:reasoner_individuals:bfo-layer` — verified
- All TestingFramework and CQ queries ran over 10 files / 2,610 triples
  <br/>`metric:query_rows:TestingFramework:Query1` — verified

### DUPLICATION-002 — The ~46-50 percent duplicate ratios are an artefact of stored aggregates and must not be read as redundant authoring

*medium · proposed by Skeptic*

- duplicate_triple_ratio for thats-all-folks is 0.4618, 38,563 of 83,497 triples
  <br/>`metric:duplicate_triple_ratio:thats-all-folks` — verified
- ThatsAllFolks/taf.ttl alone contains 38,558 triples
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- duplicate_triple_ratio for mf-triggers is 0.4991, 12,320 of 24,684 triples
  <br/>`metric:duplicate_triple_ratio:mf-triggers` — verified
- MFTriggers/ClosureHaidtValueFrames.ttl contains 12,342 triples
  <br/>`document:MFTriggers/ClosureHaidtValueFrames.ttl` — verified
- folk_aligned.ttl parses to 5,828 triples and 378 classes, identical in size to ThatsAllFolks/folk.ttl
  <br/>`document:folk_aligned.ttl` — verified

## contest rationales (6)

Why an agent disputed a finding. Kept because the reasoning is often worth more than the verdict: three agents contested INV-001 on the ground that its premise was falsified by its own evidence, and they were right.

**INV-001**

> **Restraint** — The title's premise is falsified by the issue's own evidence. The properties_without_characteristics listing for moral-molecules is alphabetical and skips both hasNegativeCounterpart and hasPositiveCounterpart while including the later-sorting hasSocialComponent, so both counterpart proper [clipped]
>

**METHOD-001**

> **Formalist** — The observation is right that absence counts are not automatically defect counts; the evidence offered for it is not. The 'whether siblings should be disjoint is a domain question, not a shortfall' note is not a per-case adjudication that the substrate reached about thats-all-folks and val [clipped]
>

**SHACL-004**

> **Restraint** — The title's claim — that datatype conformance is 'unenforceable' outside the BFO layer — does not follow from the property-declaration counts, and the issue's own EV-007 and EV-008 say so: sh:datatype applies over a sh:path and a focus node, neither of which requires the predicate to be de [clipped]
>

**DISJ-001**

> **Restraint** — This reads an undeclared disjointness as a falsifiability shortfall across 26 of 26 sibling sets, including the value-disposition sets. Nothing measured supports exclusivity there, and the corpus's own practice points the other way: in the folk layer, 386 declared individuals against 468 m [clipped]
>

**DOMRANGE-001**

> **Restraint** — Two objections, both narrow. First, two of the three properties named are OBO Relation Ontology identifiers (RO_0002233, RO_0002234) reused in the authored layer; asserting local domains and ranges on borrowed upstream IRIs is the same move that VENDORED-001 and IMPORTS-001 — both confirme [clipped]
>

**RANGE-001**

> **Restraint** — This restates three measurements and then invites remediation that AXIOMS-001 — confirmed — establishes would be wrong. The uniformity is itself the evidence of deliberateness: 1,840 of 1,840 properties lack a domain, the same 1,840 lack a range, and the same 1,840 lack any characteristic, [clipped]
>

## decisions (29)

- **DEC-001** merged on `ISSUE:SCOPE-002` — merged into SCOPE-001 (adjudicator)
- **DEC-002** merged on `ISSUE:DUPLICATION-002` — merged into DUPLICATION-001 (adjudicator)
- **DEC-003** no_action_required on `ISSUE:DEF-001` — no action this cycle (adjudicator)
- **DEC-004** no_action_required on `ISSUE:DISJ-001` — no action this cycle (adjudicator)
- **DEC-005** no_action_required on `ISSUE:DOMRANGE-001` — no action this cycle (adjudicator)
- **DEC-006** no_action_required on `ISSUE:SHACL-001` — no action this cycle (adjudicator)
- **DEC-007** no_action_required on `ISSUE:SHACL-002` — no action this cycle (adjudicator)
- **DEC-008** no_action_required on `ISSUE:SHACL-003` — no action this cycle (adjudicator)
- **DEC-009** no_action_required on `ISSUE:SHACL-005` — no action this cycle (adjudicator)
- **DEC-010** no_action_required on `ISSUE:DISJOINTNESS-001` — no action this cycle (adjudicator)
- **DEC-011** no_action_required on `ISSUE:FIXTURE-001` — no action this cycle (adjudicator)
- **DEC-012** no_action_required on `ISSUE:VENDORED-001` — no action this cycle (adjudicator)
- **DEC-013** no_action_required on `ISSUE:IMPORTS-001` — no action this cycle (adjudicator)
- **DEC-014** no_action_required on `ISSUE:GROUNDING-001` — no action this cycle (adjudicator)
- **DEC-015** no_action_required on `ISSUE:DUPLICATION-001` — no action this cycle (adjudicator)
- **DEC-016** no_action_required on `ISSUE:AXIOMS-001` — no action this cycle (adjudicator)
- **DEC-017** no_action_required on `ISSUE:DECL-001` — no action this cycle (adjudicator)
- **DEC-018** no_action_required on `ISSUE:PREREQ-001` — no action this cycle (adjudicator)
- **DEC-019** no_action_required on `ISSUE:SCOPE-001` — no action this cycle (adjudicator)
- **DEC-020** no_action_required on `ISSUE:ROOT-001` — no action this cycle (adjudicator)
- **DEC-021** no_action_required on `ISSUE:REASONER-001` — no action this cycle (adjudicator)
- **DEC-022** no_action_required on `ISSUE:CQ-001` — no action this cycle (adjudicator)
- **DEC-023** no_action_required on `ISSUE:SHAPES-001` — no action this cycle (adjudicator)
- **DEC-024** no_action_required on `ISSUE:IRI-001` — no action this cycle (adjudicator)
- **DEC-025** consensus_outcome on `ISSUE:INV-001:status:confirmed` — unresolved (adjudicator)
- **DEC-026** consensus_outcome on `ISSUE:RANGE-001:status:confirmed` — unresolved (adjudicator)
- **DEC-027** consensus_outcome on `ISSUE:SHACL-004:status:confirmed` — unresolved (adjudicator)
- **DEC-028** consensus_outcome on `ISSUE:METHOD-001:status:confirmed` — unresolved (adjudicator)
- **DEC-029** compression on `RETROSPECTIVE` — history archived (adjudicator)

