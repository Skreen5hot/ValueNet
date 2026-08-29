# valuenet-run3 — findings

Rendered from `RUN3_STATE.yaml` by `ValueNet_code/report_run.py`. The state file is the record; this is a view of it.

**Two kinds of statement appear below and are never merged.** Finding titles, severities and evidence are exactly what the run concluded from the substrate it was given, reproduced unedited. Anything inside a `⚠ RECONCILIATION` block was established *after* the run, sometimes contradicting it, and is never folded back into the finding. The state file itself is not modified by reconciliation.

- **phase** complete, **version** 144
- **substrate** `sha256:8bda30687a250a0aebc…`
- **findings** 27 — 22 confirmed, 3 unresolved, 2 archived
- **tokens declared** 425,000
- **evidence** 228/228 verified against the substrate
- **reconciled** against the tree at `42e8126` — 6 finding(s) superseded or resolved; the state file itself is unmodified

## confirmed (22)

### ALIGN-002 — One undefined predicate carries the trigger claims of three mutually independent value theories over overlappi [clipped]

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **PREMISE FALSE - the conclusion stands, a supporting claim does not**
>
> Rests on a false premise I supplied. The Run 3 Alignment brief said vcvf:triggers has no domain, no range and no definition. It declares rdfs:domain owl:Thing and rdfs:range vcvf:Value at ValueCore.ttl:97; only the definition was missing. The finding's own conclusion - that one undefined predicate carries the trigger claims of three groups - survives, because "undefined" is the true part. Its supporting sentences about domain and range do not.
> - The predicate declares both, verified directly against the merged graph.
> - The grounding gate marked the claim verified because the citation resolved. It now returns resolves_only for exactly this shape.

_Everything below this line is what the run itself concluded, unedited._

*high · proposed by Alignment*
 · confirmed by Lexicon, Alignment, Skeptic

- mf-triggers holds 12,338 vcvf:triggers statements; the predicate declares no domain, no range and no definition; babelnet.org supplies 2,940 subjects and dbpedia.org 183
  <br/>`metric:trigger_statements:mf-triggers` — verified
- thats-all-folks holds 38,714 vcvf:triggers statements over the same host families, babelnet.org 8,250
  <br/>`metric:trigger_statements:thats-all-folks` — verified
- repository-root holds a further 6,530 vcvf:triggers statements, babelnet.org 1,646
  <br/>`metric:trigger_statements:repository-root` — verified
- mf-triggers uses exactly one non-builtin predicate across its 13 files, i.e. the entire moral-foundations trigger set is expressed through vcvf:triggers alone with no subtypes
  <br/>`metric:predicates_used_but_not_declared:mf-triggers` — verified
- repository-root's trigger content is carried by bhvtriggers.ttl, a 6,532-triple file bound to the bhv vocabulary rather than to folk values or moral foundations
  <br/>`document:bhvtriggers.ttl` — verified
- babelnet.org supplies trigger subjects in all three groups (8,250 in thats-all-folks, 2,940 in mf-triggers, 1,646 in repository-root), but no metric records whether the same babelnet resources are triggered under more than one theory, so host overlap is measured and resource-level collision is not
  <br/>`metric:trigger_statements:thats-all-folks` — verified
- The babelnet figures are per-group statement counts (2,940 in mf-triggers), not distinct resources, so no magnitude of resource-level overlap between the three theories can be derived from them
  <br/>`metric:trigger_statements:mf-triggers` — verified

### ASSURANCE-001 — Every clean result in the corpus comes from one ~2% slice, so the green signals corroborate nothing beyond each other

*high · proposed by Skeptic*
 · confirmed by Validation, Skeptic

- The definitional all-clear covers 179 classes of 2,866 declared corpus-wide, with 2,687 classes outside the check's scope
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- classes_missing_definition is 0 only for bfo-suite-merged, a 179-class population
  <br/>`metric:classes_missing_definition:bfo-suite-merged` — verified
- SHACL validated 6 of 165 ontology files, data graph = BFO layer plus scenario, nothing else
  <br/>`metric:shacl_files_validated:corpus` — verified
- The shapes targeted 14 focus nodes in total
  <br/>`metric:shacl_focus_nodes:corpus` — verified
- Every competency query ran over the same 10-file, 2,610-triple graph
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ1` — verified
- No file in any group fails to parse, refuting the parse-failure explanation for validator coverage
  <br/>`metric:files_not_parsing:thats-all-folks` — verified
- Run 1 note asserts the definitional result covers 23% of the corpus
  <br/>`note:run1:DEF-002` — verified
- Run 1 note attributes zero violations to 127 files being invisible to the validator
  <br/>`note:run1:VALIDATION-001` — verified
- valuenet-core-shapes.ttl carries 68 triples and declares no classes; with valuenet-moral-epistemics-shapes.ttl's 50 triples it is the entire shapes stock for a 165-file repository
  <br/>`document:BFO/valuenet-core-shapes.ttl` — verified
- The only recorded non-zero validator output anywhere is a single warning from valuenet-moral-epistemics-shapes
  <br/>`metric:shacl_warnings:valuenet-moral-epistemics-shapes` — verified
- The grounding check was computed over 179 classes of the 2,866 declared corpus-wide, 6.2 percent, so run 1's 23 percent coverage figure overstates the clean result's reach by nearly fourfold
  <br/>`metric:classes_measured_for_grounding:corpus` — verified

### IRI-001 — The corpus mints class declarations in four namespaces it does not control, without importing the upstream tha [clipped]

*high · proposed by Identity*
 · confirmed by Identity, Skeptic

- Six namespaces receive class declarations, four of them external to the project: www.ontologydesignpatterns.org 1039, purl.obolibrary.org 36, www.commoncoreontologies.org 1, dbpedia.org 1
  <br/>`metric:namespaces_minting_classes:corpus` — verified
- ThatsAllFolks/folk.ttl declares 378 classes and 5828 triples with 0 imports
  <br/>`document:ThatsAllFolks/folk.ttl` — verified
- 376 of the thats-all-folks group's classes are rooted in DUL despite the group's declaring files carrying no resolvable import of DUL
  <br/>`metric:classes_rooted_in_dul:thats-all-folks` — verified
- DUL-namespace terms Description and Situation appear among the group's own declared classes lacking necessary conditions, i.e. they are declared locally
  <br/>`metric:classes_without_necessary_conditions:thats-all-folks` — verified
- purl.obolibrary.org's 36 minted class declarations correspond exactly to the 36 classes declared by bfo-vendored, i.e. BFO terms are re-declared in a local file
  <br/>`metric:classes_declared:bfo-vendored` — verified
- BFO/bfo-core.ttl carries 1,014 triples and 0 imports, so the obolibrary-namespace declarations are a vendored copy rather than an import of the upstream artefact
  <br/>`document:BFO/bfo-core.ttl` — verified
- repository-root repeats the pattern with 384 classes rooted in DUL, so foreign-namespace declaration is a corpus-wide habit and not one group's shortcut
  <br/>`metric:classes_rooted_in_dul:repository-root` — verified
- The six minting namespaces sum to 5,363 declarations (4,107+1,039+179+36+1+1), exactly the total of classes_sum_over_files across the seven groups (180+36+0+26+817+378+3,926), so every foreign-namespace declaration is made by a file in this corpus
  <br/>`metric:namespaces_minting_classes:corpus` — verified

### IRI-002 — 378 folk value IRIs are declared in full by two files in different groups, with no statement of which is authoritative

*high · proposed by Identity*
 · confirmed by Identity, Skeptic

- 378 class IRIs are declared in files belonging to different groups, samples being folk value names such as Accomplishment, Acceptance, Accountability
  <br/>`metric:class_iris_declared_across_groups:corpus` — verified
- ThatsAllFolks/folk.ttl parses as 5828 triples, 378 classes, 0 imports
  <br/>`document:ThatsAllFolks/folk.ttl` — verified
- folk_aligned.ttl parses as 5828 triples, 378 classes, 0 imports - identical counts, different group
  <br/>`document:folk_aligned.ttl` — verified
- The thats-all-folks group declares exactly 378 distinct class IRIs, i.e. the entire group vocabulary is the duplicated set
  <br/>`metric:classes_declared:thats-all-folks` — verified
- Artefact names in this family encode a process history or transformation the artefacts do not exhibit
  <br/>`note:run1:NAME-003` — verified
- duplicate_triple_ratio is computed within a group (repository-root: 185 of 16,115), so folk_aligned.ttl's 5,828 triples are never compared against ThatsAllFolks/folk.ttl and divergence between the two declaration sites would go unmeasured
  <br/>`metric:duplicate_triple_ratio:repository-root` — verified
- repository-root sums 817 class declarations over 763 distinct IRIs, so re-declaration without a stated owning file also occurs inside a single group
  <br/>`metric:classes_sum_over_files:repository-root` — verified
- thats-all-folks' 38,563 duplicate triples are accounted for within the group by taf.ttl's 38,558, so the duplicate measurement never reaches across the group boundary to compare folk.ttl with folk_aligned.ttl
  <br/>`metric:duplicate_triple_ratio:thats-all-folks` — verified

### LEXICON-001 — vale2024 is a 3,700-term vocabulary in which every term's meaning is its label, and the label is not a stable key

*high · proposed by Lexicon*
 · confirmed by Lexicon, Skeptic

- All 1,861 vale2024 classes lack any definition text (rdfs:comment, skos:definition, scopeNote, isDefinedBy), so meaning rests on the name
  <br/>`metric:classes_without_definition_text:vale2024` — verified
- All 1,861 vale2024 classes also lack an rdfs:label, so not even a human-readable form of the name is asserted
  <br/>`metric:classes_without_a_label:vale2024` — verified
- 26 of 1,835 distinct normalised local names in vale2024 collide, e.g. TraditionRole/Traditionrole and BenevolenceRole/Benevolencerole
  <br/>`metric:local_names_colliding_on_normalisation:vale2024` — verified
- All 1,840 vale2024 properties lack domain, range and any characteristic, so predicate meaning also rests entirely on the name
  <br/>`metric:properties_without_domain:vale2024` — verified
- 2,687 of 2,866 corpus classes lie outside the scope in which definitional coverage was measured
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- The zero-missing-definition result covers only the 179-class merged BFO suite
  <br/>`metric:classes_missing_definition:bfo-suite-merged` — verified
- All 1,861 vale2024 classes reach no known upper ontology by rdfs:subClassOf, so superclass placement supplies no sense either
  <br/>`metric:classes_with_no_upper_root:vale2024` — verified
- 1,854 of 1,861 vale2024 classes carry no restriction or equivalence, so no axiom substitutes for the missing gloss
  <br/>`metric:classes_without_necessary_conditions:vale2024` — verified

### LEXICON-002 — 798 owl:equivalentClass assertions identify terms that carry no definition on either side, making the alignmen [clipped]

*high · proposed by Lexicon*
 · confirmed by Lexicon, Identity
 · contested by Alignment, Skeptic

- thats-all-folks asserts 375 owl:equivalentClass mappings
  <br/>`metric:mapping_statements:thats-all-folks` — verified
- repository-root asserts 391 owl:equivalentClass mappings
  <br/>`metric:mapping_statements:repository-root` — verified
- moral-molecules asserts 32 owl:equivalentClass mappings while all 26 of its classes carry no definition text
  <br/>`metric:classes_without_definition_text:moral-molecules` — verified
- All 26 moral-molecules classes also carry no label
  <br/>`metric:classes_without_a_label:moral-molecules` — verified
- 629 of 763 repository-root classes carry no definition text
  <br/>`metric:classes_without_definition_text:repository-root` — verified
- The bfo-layer, with full definition coverage, prefers graded mapping: 60 skos:broadMatch and one owl:equivalentClass
  <br/>`metric:mapping_statements:bfo-layer` — verified
- Label-driven alignment already misfires: DBpedia targets include works of fiction and strictly broader concepts
  <br/>`note:run1:MAPPING-002` — verified
- All 26 moral-molecules classes also reach no upper root, so with no definition, no label and no superclass the 32 owl:equivalentClass statements are the entire semantics of those terms
  <br/>`metric:classes_with_no_upper_root:moral-molecules` — verified
- No metric records the object of any mapping statement — neither its host nor whether it carries definition text — in any group, so the 'either side' half of the claim is unmeasured for all 798 assertions
  <br/>`metric:mapping_statements:repository-root` — verified
- 134 of 763 repository-root classes do carry definition text, and no measurement says whether the 391 owl:equivalentClass assertions originate from the defined or the undefined subset
  <br/>`metric:classes_without_definition_text:repository-root` — verified
- Run 1's DBpedia-fiction finding did not distinguish which predicate carried the alignment, so it cannot be cited as evidence about the behaviour of the owl:equivalentClass layer specifically
  <br/>`note:run1:MAPPING-002` — verified
- moral-molecules is the only group where the mapping count and a total absence of definition text on the subject side are jointly measured, covering 32 of the 798 assertions
  <br/>`metric:mapping_statements:moral-molecules` — verified
- 100 of 378 thats-all-folks classes do carry definition text, so for the 375 owl:equivalentClass assertions in that group the 'no definition on either side' claim is false for an unmeasured share even on the subject side
  <br/>`metric:classes_without_definition_text:thats-all-folks` — verified

### SHACL-001 — Shapes must be re-targeted from classes to predicates, because three of seven groups declare no individuals at all

*high · proposed by Validation*
 · confirmed by Validation, Skeptic

- mf-triggers declares 0 individuals and 0 classes, so no class-targeted or ABox class shape can bind in that group
  <br/>`metric:individuals_declared:mf-triggers` — verified
- mf-triggers nonetheless carries 12,338 vcvf:triggers statements
  <br/>`metric:trigger_statements:mf-triggers` — verified
- vale2024 declares 1,861 classes and 0 individuals
  <br/>`metric:individuals_declared:vale2024` — verified
- thats-all-folks carries 38,714 vcvf:triggers statements, the largest single instantiated construct in the corpus
  <br/>`metric:trigger_statements:thats-all-folks` — verified
- The shapes currently reach 14 focus nodes over 6 of 165 files
  <br/>`metric:shacl_focus_nodes:corpus` — verified
- bfo-vendored also declares zero individuals, so four of seven groups, not three, offer no ABox for a class-targeted shape to bind to
  <br/>`metric:individuals_declared:bfo-vendored` — verified
- mf-triggers declares 0 distinct class IRIs, so in that group there is no sh:targetClass to point at even before the question of instances arises
  <br/>`metric:classes_declared:mf-triggers` — verified

### SHACL-002 — The vcvf:triggers direction convention is the one unstated commitment with tens of thousands of nodes able to violate it

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **PREMISE FALSE - the conclusion stands, a supporting claim does not**
>
> Same false premise, and the conclusion is strengthened rather than weakened by the correction. The finding says the direction convention is the one unstated commitment with tens of thousands of nodes able to violate it, and cites "no domain, no range" as the reason OWL cannot constrain direction. The real reason is better: the range is declared, and it entails rather than validates - an object of the wrong kind is inferred to be a Value instead of being rejected. OWL cannot catch a direction error here not because the predicate is unconstrained but because the constraint it has runs the wrong way for the job. Still a SHACL obligation, for a sharper reason.
> - folk:BadHealth is entailed to be a vcvf:Value from a single trigger statement under RDFS closure, verified directly.
> - 18,668 thats-all-folks trigger statements place the external resource in subject position and zero place one in object position.

_Everything below this line is what the run itself concluded, unedited._

*high · proposed by Validation*
 · confirmed by Alignment, Validation, Skeptic

- vcvf:triggers declares no domain, no range and no definition, so OWL cannot constrain its direction
  <br/>`metric:trigger_statements:thats-all-folks` — verified
- 18,668 thats-all-folks trigger statements put the external resource in subject position
  <br/>`metric:triggers_with_foreign_subject:thats-all-folks` — verified
- Zero thats-all-folks trigger statements put an external resource in object position
  <br/>`metric:triggers_with_foreign_object:thats-all-folks` — verified
- Zero mf-triggers trigger statements put an external resource in object position, so the convention holds across groups
  <br/>`metric:triggers_with_foreign_object:mf-triggers` — verified
- External alignment targets include works of fiction and strictly broader concepts, so direction carries real semantic weight
  <br/>`note:run1:MAPPING-002` — verified
- w3id.org supplies 20,043 of thats-all-folks' 38,714 trigger subjects and 9,207 of mf-triggers' 12,338, so a direction shape must forbid foreign objects rather than require foreign subjects, and 'foreign' must be spelled out as a host list the corpus does not declare
  <br/>`metric:trigger_statements:thats-all-folks` — verified
- repository-root also records zero triggers with an external resource in object position, so the convention is unbroken in all three trigger-bearing groups
  <br/>`metric:triggers_with_foreign_object:repository-root` — verified
- The three trigger groups carry 57,582 vcvf:triggers statements between them, against the 14 focus nodes the shapes currently reach across the whole corpus
  <br/>`metric:shacl_focus_nodes:corpus` — verified
- No metric records object hosts for the 377 thats-all-folks mapping statements or any other mapping layer, so run 1's fiction-target observation cannot be attributed to a predicate and cannot bear weight on the direction argument
  <br/>`metric:mapping_statements:thats-all-folks` — verified

### ALIGN-003 — Subject position under vcvf:triggers mixes lexical senses, web documents, encyclopedic entities, frame models, [clipped]

*medium · proposed by Alignment*
 · confirmed by Alignment, Skeptic

- thats-all-folks draws trigger subjects from 12 distinct hosts spanning lexicons, wiktionary editions, DBpedia/YAGO, premon, umbel and the corpus's own w3id and ODP namespaces
  <br/>`metric:trigger_source_hosts:thats-all-folks` — verified
- repository-root draws from 11 hosts of the same mixed kinds
  <br/>`metric:trigger_source_hosts:repository-root` — verified
- w3id.org supplies 20,043 of thats-all-folks' 38,714 trigger subjects, i.e. the majority of the layer is internal-to-internal
  <br/>`metric:trigger_statements:thats-all-folks` — verified
- Only 18,668 of thats-all-folks' 38,714 trigger statements have an external subject at all
  <br/>`metric:triggers_with_foreign_subject:thats-all-folks` — verified
- mf-triggers records 7 trigger statements whose subject sits in the www.w3.org namespace and 1 in ontologydesignpatterns.org
  <br/>`metric:trigger_statements:mf-triggers` — verified
- vcvf:triggers appears in mf-triggers' host list alongside w3id.org 9,207, confirming the internal-subject pattern is not confined to one group
  <br/>`metric:trigger_source_hosts:mf-triggers` — verified
- The wiktionary subjects are HTML page URLs rather than lexical-entry or sense IRIs, so at least one host contributes document identities into the same subject position as babelnet senses and DBpedia entities
  <br/>`note:run1:IRI-002` — verified

### ALIGN-004 — The single competency question that exercises the trigger layer touches only its smallest group and returns one row

*medium · proposed by Alignment*
 · confirmed by Alignment, Validation, Skeptic

- CQ6 'What value does a span of text reach through the existing trigger data?' returns 1 row over 23 files and 14,974 triples, while every other CQ runs over 10 files and 2,610 triples
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ6` — verified
- The mf-triggers group contributes 12,364 distinct triples, consistent with CQ6's widened graph being the BFO layer plus mf-triggers only
  <br/>`metric:triples_distinct_in_group:mf-triggers` — verified
- The largest trigger set, 38,714 statements in thats-all-folks, is not within any CQ's file scope
  <br/>`metric:trigger_statements:thats-all-folks` — verified
- All 6 CQs are recorded as passing, which for CQ6 means only that a non-empty answer was returned
  <br/>`metric:queries_passing:valuenet-moral-epistemics-CQ` — verified
- mf-triggers, the only trigger group inside CQ6's widened scope, declares 0 classes and 0 individuals, so its 12,338 vcvf:triggers edges are the whole of what CQ6 could traverse in that group and they yield a single row
  <br/>`metric:individuals_declared:mf-triggers` — verified
- SHACL touched 6 of 165 files and the widest CQ scope is 23 files, so the 130 files of thats-all-folks are outside both the validator and every query
  <br/>`metric:shacl_files_validated:corpus` — verified
- Those 130 files resolve to 44,934 distinct triples, the largest unexercised body of content in the corpus
  <br/>`metric:triples_distinct_in_group:thats-all-folks` — verified
- 2,610 (the standard CQ scope) plus mf-triggers' 12,364 distinct triples equals 14,974 exactly, confirming CQ6's widened graph is the standard scope plus the entire mf-triggers group and nothing else
  <br/>`metric:triples_distinct_in_group:mf-triggers` — verified

### IRI-003 — Two project-controlled minting hosts, with the best-defined layer on the less persistent one

*medium · proposed by Identity*
 · confirmed by Identity
 · contested by Skeptic

- Class declarations are split across two project hosts: w3id.org 4107 and fandaws.com 179
  <br/>`metric:namespaces_minting_classes:corpus` — verified
- The bfo-layer declares 180 distinct class IRIs, one more than the fandaws.com count
  <br/>`metric:classes_declared:bfo-layer` — verified
- All 180 bfo-layer classes carry definition text - it is the corpus's best-defined layer
  <br/>`metric:classes_without_definition_text:bfo-layer` — verified
- All 180 bfo-layer classes carry a label
  <br/>`metric:classes_without_a_label:bfo-layer` — verified
- bfo-layer declares 180 distinct class IRIs while fandaws.com mints 179, so the best-defined layer is itself split across minting namespaces
  <br/>`metric:classes_declared:bfo-layer` — verified
- namespaces_minting_classes records declaration counts per host only; no substrate record reports resolution, ownership or persistence policy for w3id.org or fandaws.com
  <br/>`metric:namespaces_minting_classes:corpus` — verified
- bfo-layer sums 180 class declarations over files against fandaws.com's 179 mints, so one bfo-layer class is minted elsewhere and the layer-to-host assignment is inferred from a near-match
  <br/>`metric:classes_sum_over_files:bfo-layer` — verified

### IRI-004 — The trigger layer's direction-only discipline over 43,616 foreign resources is correct, unstated, and unenforceable

*medium · proposed by Identity*
 · confirmed by Identity, Alignment, Skeptic

- The corpus asserts about 43,616 resources in namespaces it does not control: babelnet.org 22,864, yago-knowledge.org 11,299, en.wiktionary.org 5,630, fr.wiktionary.org 1,684, dbpedia.org 846
  <br/>`metric:foreign_iris_used_as_subjects:corpus` — verified
- Zero triggers place an external resource in object position in thats-all-folks
  <br/>`metric:triggers_with_foreign_object:thats-all-folks` — verified
- Zero triggers place an external resource in object position in mf-triggers
  <br/>`metric:triggers_with_foreign_object:mf-triggers` — verified
- vcvf:triggers declares no domain, no range and no definition, across 38,714 statements in thats-all-folks alone
  <br/>`metric:trigger_statements:thats-all-folks` — verified
- Identity-strength predicates are already in use in the same group: 375 owl:equivalentClass and 2 owl:sameAs
  <br/>`metric:mapping_statements:thats-all-folks` — verified
- DBpedia alignment targets include works of fiction and strictly broader concepts
  <br/>`note:run1:MAPPING-002` — verified
- repository-root also records zero triggers with an external resource in object position, so the subject-only discipline holds in every trigger-bearing group measured
  <br/>`metric:triggers_with_foreign_object:repository-root` — verified
- The 392 mapping statements at the repository root (391 owl:equivalentClass, 1 owl:sameAs) have no recorded object-host breakdown, so whether identity-strength predicates already point at foreign IRIs is unmeasured
  <br/>`metric:mapping_statements:repository-root` — verified
- Foreign-subject trigger statements total 24,869 across the three trigger-bearing groups (18,668 + 3,078 + 3,123), fewer than the 43,616 foreign-namespace subjects the corpus asserts about, so the direction result does not cover every foreign-resource assertion in the headline figure
  <br/>`metric:foreign_iris_used_as_subjects:corpus` — verified
- thats-all-folks uses 26 non-builtin predicates, 21 of them declared nowhere in the corpus, and no metric records object hosts for any of them, so the zero-foreign-object result establishes direction for vcvf:triggers alone
  <br/>`metric:predicates_used_but_not_declared:thats-all-folks` — verified
- babelnet.org alone accounts for 22,864 of the 43,616 foreign subject IRIs, against 12,836 babelnet-subject trigger statements across the three groups (8,250 + 2,940 + 1,646), so most of the headline figure sits outside the layer whose direction was measured
  <br/>`metric:foreign_iris_used_as_subjects:corpus` — verified

### IRI-005 — The 378 cross-group IRI collisions are almost certainly one duplicated file, not 378 ownership disputes

*medium · proposed by Skeptic*
 · confirmed by Lexicon, Identity, Skeptic

- 378 IRIs are declared across group boundaries, of 2,240 multi-file IRIs
  <br/>`metric:class_iris_declared_across_groups:corpus` — verified
- thats-all-folks declares exactly 378 distinct classes
  <br/>`metric:classes_declared:thats-all-folks` — verified
- ThatsAllFolks/folk.ttl: 5,828 triples, 378 classes
  <br/>`document:ThatsAllFolks/folk.ttl` — verified
- folk_aligned.ttl at repository root: 5,828 triples, 378 classes — identical counts
  <br/>`document:folk_aligned.ttl` — verified
- repository-root sums 817 class declarations over files against 763 distinct, the source of IRI-001's 54
  <br/>`metric:classes_sum_over_files:repository-root` — verified
- The substrate states multi-file declaration is mostly parameter variants within a group and not contested ownership
  <br/>`metric:class_iris_declared_in_multiple_files:corpus` — verified
- Run 1 note concludes contested IRI ownership from the 54 figure
  <br/>`note:run1:IRI-001` — verified
- duplicate_triple_ratio is within-group (repository-root records 185 of 16,115 duplicates, not folk_aligned.ttl's 5,828), so cross-group content identity between the two 378-class files is inferred from counts alone and not measured
  <br/>`metric:duplicate_triple_ratio:repository-root` — verified
- thats-all-folks sums 378 class declarations over 130 files against 378 distinct IRIs, so the group declares each IRI once and the duplicate declaration site is entirely outside the group — reducing the ownership question to a single file pair
  <br/>`metric:classes_sum_over_files:thats-all-folks` — verified

### LANG-001 — Which lexicon governs a term's sense is recoverable only by reading a hostname out of an IRI

*medium · proposed by Identity*
 · confirmed by Lexicon, Identity, Alignment, Skeptic

- 3,658 wiktionary triggers in thats-all-folks split across two language editions, en=2,769 and fr=889, with the edition choice recorded nowhere
  <br/>`metric:wiktionary_language_editions:thats-all-folks` — verified
- 889 of 3,658 wiktionary triggers are non-English; the language edition is a commitment about which lexicon defines the term and nothing in the corpus records it
  <br/>`metric:wiktionary_non_english_triggers:thats-all-folks` — verified
- Wiktionary HTML page URLs are used as mapping objects, with uncontrolled language-edition drift
  <br/>`note:run1:IRI-002` — verified
- All 38,714 trigger statements in thats-all-folks use vcvf:triggers, which declares no domain, no range and no definition
  <br/>`metric:trigger_statements:thats-all-folks` — verified
- Value terms taking their lexical gloss from a French dictionary while the rest use English was confirmed in run 1
  <br/>`note:run1:LANG-001` — verified
- repository-root independently splits its 624 wiktionary triggers across the same two editions, en=477 and fr=147, so the unrecorded edition choice is a corpus-wide pattern rather than a single file's drift
  <br/>`metric:wiktionary_language_editions:repository-root` — verified
- en.wiktionary.org and fr.wiktionary.org are listed among the 12 SUBJECT-position trigger hosts for thats-all-folks, so the unrecorded edition choice attaches to the trigger source and the finding does not depend on run 1's 'mapping object' framing
  <br/>`metric:trigger_source_hosts:thats-all-folks` — verified
- en.wiktionary.org and fr.wiktionary.org appear in repository-root's SUBJECT-position host list too, and no metric places any Wiktionary IRI in object position, so the finding stands on trigger-source evidence and not on run 1's gloss framing
  <br/>`metric:trigger_source_hosts:repository-root` — verified

### LEXICON-003 — Near-synonym value families are separated by nothing statable and nothing checkable

*medium · proposed by Lexicon*
 · confirmed by Lexicon, Validation, Skeptic

- Dense near-synonym families in the folk vocabulary have no audited definitions to separate them (confirmed run 1)
  <br/>`note:run1:DEF-003` — verified
- 278 of 378 thats-all-folks classes carry no definition text, so their meaning rests on the name
  <br/>`metric:classes_without_definition_text:thats-all-folks` — verified
- 96 of 378 thats-all-folks classes carry no label at all
  <br/>`metric:classes_without_a_label:thats-all-folks` — verified
- All 49 sibling sets in thats-all-folks lack disjointness, so no sibling distinction is asserted
  <br/>`metric:sibling_sets_without_disjointness:thats-all-folks` — verified
- thats-all-folks has zero axioms by which a reasoner could find a conflation inconsistent
  <br/>`metric:contradiction_capacity:thats-all-folks` — verified
- Brilliance is carried by 19 triples, an extension too thin to serve as the differentia against its near-synonyms
  <br/>`document:ThatsAllFolks/folk_Brilliance.ttl` — verified
- Trigger extensions are drawn from 12 distinct external hosts with no stated assignment rule
  <br/>`metric:trigger_source_hosts:thats-all-folks` — verified
- Where thats-all-folks classes do carry definition text, run 1 found glosses written against the proper-name sense of the term rather than the value sense, so the 100 defined classes are not automatically sense-fixed
  <br/>`note:run1:SENSE-001` — verified
- All 21 populated thats-all-folks classes lack a shape, so the near-synonym families are unseparated by SHACL as well as by OWL
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- The SHACL data graph is the BFO layer plus the scenario across 6 of 165 files, so no folk value class is in validator scope at all
  <br/>`metric:shacl_files_validated:corpus` — verified

### LOGIC-001 — The consistency and satisfiability verdicts are close to unfalsifiable and should not be cited as evidence of [clipped]

*medium · proposed by Skeptic*
 · confirmed by Validation, Skeptic

- vale2024, the largest group by class count, has zero axioms by which a reasoner could find it inconsistent
  <br/>`metric:contradiction_capacity:vale2024` — verified
- thats-all-folks likewise has zero contradiction capacity, so a consistency verdict over it is guaranteed
  <br/>`metric:contradiction_capacity:thats-all-folks` — verified
- The single consistent verdict rests on only 32 axioms that could have produced a failure, with no ABox checked
  <br/>`metric:reasoner_consistent:bfo-layer` — verified
- 0 unsatisfiable of 267 classes, where only 32 axioms could have made one fail
  <br/>`metric:unsatisfiable_classes:bfo-layer` — verified
- 1,854 of 1,861 vale2024 classes carry no restriction or equivalence at all
  <br/>`metric:classes_without_necessary_conditions:vale2024` — verified
- moral-molecules also has zero contradiction capacity, so a fourth group's consistency would be guaranteed in advance
  <br/>`metric:contradiction_capacity:moral-molecules` — verified
- The reasoner ran over 0 individuals while repository-root alone declares 694, so no declared instance has been in reasoner scope any more than in shape scope
  <br/>`metric:reasoner_individuals:bfo-layer` — verified
- contradiction_capacity for bfo-layer is 2 while the reasoner run counted 32 failure-capable axioms over 7 files, so 30 of them come from the vendored BFO copy and the authored layer contributes two
  <br/>`metric:contradiction_capacity:bfo-layer` — verified

### MAPPING-001 — Trigger statements are being read as external alignments; the measurements say they are not, and the predicate [clipped]

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **PREMISE FALSE - the conclusion stands, a supporting claim does not**
>
> The central claim - that trigger statements are being read as external alignments when the measurements say they are not - is unaffected and was independently corroborated by ALIGN-001 and ALIGN-005. Only its characterisation of the predicate as wholly unconstrained inherits the false premise.
> - Direction is a total convention in the data with zero counterexamples.
> - The predicate's declared range is what makes a misread trigger statement silently acceptable rather than detectably wrong.

_Everything below this line is what the run itself concluded, unedited._

*medium · proposed by Alignment*
 · confirmed by Alignment, Skeptic

- No vcvf:triggers statement in thats-all-folks places an external resource in object position (0), while 18,668 place one in subject position
  <br/>`metric:triggers_with_foreign_object:thats-all-folks` — verified
- The same zero-foreign-object, foreign-subject pattern holds in repository-root (0 objects, 3,078 subjects)
  <br/>`metric:triggers_with_foreign_subject:repository-root` — verified
- And in mf-triggers (0 foreign objects, 3,123 foreign subjects)
  <br/>`metric:triggers_with_foreign_object:mf-triggers` — verified
- A separate, much smaller equivalence layer exists in the same group: 377 mapping statements, of which 375 are owl:equivalentClass and 2 owl:sameAs
  <br/>`metric:mapping_statements:thats-all-folks` — verified
- repository-root carries a further 391 owl:equivalentClass plus 1 owl:sameAs
  <br/>`metric:mapping_statements:repository-root` — verified
- Run 1 recorded MAPPING-002 as confirmed on the basis that 'folk_Education.ttl aligns the Education...' to a work of fiction, without distinguishing the predicate used
  <br/>`note:run1:MAPPING-002` — verified
- Run 1 note characterises Wiktionary URLs as mapping objects
  <br/>`note:run1:IRI-002` — verified
- The zero-foreign-object result covers vcvf:triggers only; the 801 mapping statements corpus-wide (377 in thats-all-folks, 392 at the repository root, 32 in moral-molecules) have no recorded object hosts, so run 1's fiction target cannot yet be attributed to either layer
  <br/>`metric:mapping_statements:thats-all-folks` — verified

### SHACL-003 — A lexicon-edition shape on trigger subjects is the only proposed shape that fails on the corpus as it stands

*medium · proposed by Validation*
 · confirmed by Alignment, Validation, Skeptic

- 889 of 3,658 thats-all-folks wiktionary triggers are non-English and nothing in the corpus records the language commitment
  <br/>`metric:wiktionary_non_english_triggers:thats-all-folks` — verified
- 147 of 624 repository-root wiktionary triggers are non-English
  <br/>`metric:wiktionary_non_english_triggers:repository-root` — verified
- Two language editions are mixed with no recorded rationale
  <br/>`metric:wiktionary_language_editions:thats-all-folks` — verified
- Three value terms take their lexical gloss from a French dictionary while the rest use English
  <br/>`note:run1:LANG-001` — verified
- Both editions appear in SUBJECT position, i.e. as the resource claimed to trigger the value, so the shape governs source-lexicon policy rather than gloss language and should require the edition be recorded rather than fixed to en
  <br/>`metric:trigger_source_hosts:thats-all-folks` — verified
- The shape would bind 4,282 Wiktionary trigger subjects across two groups (3,658 plus 624), none of which records an edition anywhere but in the hostname
  <br/>`metric:wiktionary_language_editions:thats-all-folks` — verified
- The claim to be the 'only' failing shape is untested against SHACL-005: no measurement reports what a shape over repository-root's 26 populated unshaped classes would return
  <br/>`metric:populated_classes_without_a_shape:repository-root` — verified

### SHACL-005 — The 1,080 declared individuals worth shaping sit behind five undeclared-domain properties and 21 undeclared predicates

*medium · proposed by Validation*
 · confirmed by Validation, Skeptic

- All 26 populated repository-root classes lack a shape; largest are WVSVariable (323), IndividualValue (171), FolkValue (160), InnerValue (130)
  <br/>`metric:populated_classes_without_a_shape:repository-root` — verified
- All 21 populated thats-all-folks classes lack a shape
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- The largest unshaped population in the validated BFO layer is three individuals
  <br/>`metric:populated_classes_without_a_shape:bfo-layer` — verified
- thats-all-folks uses 21 of 26 non-builtin predicates that are declared nowhere in the corpus
  <br/>`metric:predicates_used_but_not_declared:thats-all-folks` — verified
- Five of nine thats-all-folks properties declare no domain, so OWL cannot constrain their subjects
  <br/>`metric:properties_without_domain:thats-all-folks` — verified
- The same five declare no range
  <br/>`metric:properties_without_range:thats-all-folks` — verified
- repository-root declares 694 individuals available to an ABox check
  <br/>`metric:individuals_declared:repository-root` — verified
- thats-all-folks and repository-root report identical unshaped populations for IndividualValue (171), FolkValue (160) and InnerValue (130), so the 1,080 total is unlikely to be 1,080 distinct focus nodes
  <br/>`metric:populated_classes_without_a_shape:thats-all-folks` — verified
- folk_aligned.ttl parses as 5,828 triples and 378 classes, matching ThatsAllFolks/folk.ttl, which is the likely source of that overlap
  <br/>`document:folk_aligned.ttl` — verified
- WVSVariable (323) appears only in repository-root's population list and is therefore the largest non-duplicated shape target in the corpus
  <br/>`metric:populated_classes_without_a_shape:repository-root` — verified
- thats-all-folks declares 386 individuals, but its four largest unshaped populated classes alone sum to 468 instances (171+160+130+7), so population figures count multi-typed individuals repeatedly and 1,080 cannot be read as a focus-node count
  <br/>`metric:individuals_declared:thats-all-folks` — verified

### TEST-001 — The query suite passes against author-declared expectations at the minimum possible threshold, including three [clipped]

*medium · proposed by Skeptic*
 · confirmed by Validation, Skeptic

- A query passes by matching its own '# expect:' declaration, which differs between documents
  <br/>`metric:queries_passing:TestingFramework` — verified
- Query1 passes by returning zero rows, with no positive control distinguishing 'defect absent' from 'pattern never instantiated'
  <br/>`metric:query_rows:TestingFramework:Query1` — verified
- CQ3 is satisfied by a single row
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ3` — verified
- CQ6 returns one row over 23 files and 14,974 triples
  <br/>`metric:query_rows:valuenet-moral-epistemics-CQ:CQ6` — verified
- The scenario the CQs exercise is a 75-triple file
  <br/>`document:BFO/valuenet-moral-epistemics-scenario.ttl` — verified
- Query1 is a Disjoint Parentage Check, yet all 26 bfo-layer sibling sets lack disjointness, so the pattern it searches for is not instantiated in its scope and its zero-row pass carries no information
  <br/>`metric:sibling_sets_without_disjointness:bfo-layer` — verified
- Query3's redundant-broadMatch check is not vacuous in the same way: the bfo-layer holds 60 skos:broadMatch statements for it to range over
  <br/>`metric:mapping_statements:bfo-layer` — verified
- bfo-vendored has disjointness on 10 of its 11 sibling sets and its 1,014 triples plus bfo-layer's 1,597 distinct triples account for the queries' 10-file, 2,610-triple scope, so the Disjoint Parentage Check does not run over a disjointness-free graph and EV-006's vacuity argument does not hold
  <br/>`metric:sibling_sets_without_disjointness:bfo-vendored` — verified

### ALIGN-005 — French Wiktionary subjects are trigger sources, not glosses — the corrected reading changes the remedy Run 1 implies

*low · proposed by Alignment*
 · confirmed by Lexicon, Identity, Alignment, Skeptic

- 889 of 3,658 wiktionary triggers in thats-all-folks are non-English, and nothing in the corpus records the language edition as a commitment
  <br/>`metric:wiktionary_non_english_triggers:thats-all-folks` — verified
- 147 of 624 wiktionary triggers in repository-root are French
  <br/>`metric:wiktionary_non_english_triggers:repository-root` — verified
- en.wiktionary.org and fr.wiktionary.org appear in the SUBJECT-position host list, i.e. as the resource that triggers the value
  <br/>`metric:trigger_source_hosts:thats-all-folks` — verified
- Run 1 IRI-002 characterises the wiktionary URLs as 'mapping objects'
  <br/>`note:run1:IRI-002` — verified
- Run 1 LANG-001 characterises the French pages as supplying a 'lexical gloss' to the value term
  <br/>`note:run1:LANG-001` — verified
- The 377 mapping statements in thats-all-folks (375 owl:equivalentClass, 2 owl:sameAs) have no recorded host breakdown for their objects, so the zero-foreign-object result for vcvf:triggers does not cover them
  <br/>`metric:mapping_statements:thats-all-folks` — verified
- 278 of 378 thats-all-folks classes carry no definition text of any kind, so the Wiktionary URLs cannot be the source of a gloss on those value terms — consistent with reading them as trigger sources
  <br/>`metric:classes_without_definition_text:thats-all-folks` — verified
- 100 of 378 thats-all-folks classes do carry definition text, so the trigger-subject reading does not exclude run 1's sampled French-glossed terms and the correction should be stated as a scope correction rather than a refutation of the sample
  <br/>`metric:classes_without_definition_text:thats-all-folks` — verified

### DUP-001 — The ~50% duplicate-triple ratios are aggregate build products, not divergent copies, and carry no integrity ri [clipped]

*low · proposed by Skeptic*
 · confirmed by Identity, Skeptic

- mf-triggers: 12,320 of 24,684 triples are restatements from another file
  <br/>`metric:duplicate_triple_ratio:mf-triggers` — verified
- ClosureHaidtValueFrames.ttl alone holds 12,342 triples, matching the group's duplicate count
  <br/>`document:MFTriggers/ClosureHaidtValueFrames.ttl` — verified
- thats-all-folks: 38,563 of 83,497 triples are duplicates
  <br/>`metric:duplicate_triple_ratio:thats-all-folks` — verified
- taf.ttl alone holds 38,558 triples, matching the group's duplicate count
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- thats-all-folks still resolves to 44,934 distinct triples, so the duplication is additive, not conflicting
  <br/>`metric:triples_distinct_in_group:thats-all-folks` — verified
- No duplicate-triple measurement spans groups (repository-root reports 185 of 16,115), so the folk.ttl / folk_aligned.ttl pair at 5,828 triples each falls outside this finding's scope
  <br/>`metric:duplicate_triple_ratio:repository-root` — verified
- taf.ttl's 38,558 triples fall entirely within the group's 38,563 duplicated triples, and 83,497 minus 38,563 equals the recorded 44,934 distinct, so the aggregate adds no unique statement
  <br/>`metric:duplicate_triple_ratio:thats-all-folks` — verified

## unresolved (3)

### LANG-002 — LANG-001 understates the French-source pattern by roughly three orders of magnitude, and a systematic bilingua [clipped]

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **REWRITTEN - the subject held, the proposition did not**
>
> Rewritten on like-for-like units, and the result refutes LANG-001 rather than understating it. The original proposition claimed LANG-001 understates the French pattern "by roughly three orders of magnitude", comparing value terms against trigger statements - different units whose ratio is not a magnitude of anything, which is why every voting agent declined to confirm it. Measured in one unit, value classes: 133 of the 147 value classes that carry any trigger have at least one French Wiktionary trigger, 90 percent of them, rising to 123 of 125 among folk values. And the number that matters most: ZERO value classes have a French trigger without also having an English one. Every one of the 133 is bilingual. So French is not an exception applied to a few terms. It is a systematic en+fr pairing applied to almost the whole vocabulary. LANG-001's framing - "three value terms take their lexical gloss from a French dictionary while the rest use English" - is wrong about the count, wrong about the kind of thing (ALIGN-005: these are trigger sources, not glosses), and wrong that the rest differ.
>
> **Restated as:** The trigger layer is systematically bilingual: 133 of 147 value classes carry both English and French Wiktionary triggers, and none carries French alone
> **Consequence:** There is no lexicon cleanup to do here. The open question is only whether the corpus should state that it is en+fr by design, since nothing records it. Implementation plan section 3 is narrowed accordingly, and SHACL-003's proposed lexicon-edition shape would flag 133 values - that is, it would flag the design rather than a defect.

_Everything below this line is what the run itself concluded, unedited._

*medium · proposed by Skeptic*
 · contested by Lexicon, Identity, Alignment, Skeptic

- 889 of 3,658 Wiktionary triggers in thats-all-folks are non-English, and nothing in the corpus records the language commitment
  <br/>`metric:wiktionary_non_english_triggers:thats-all-folks` — verified
- 147 of 624 at the repository root, the same ~24% proportion, indicating a systematic split rather than isolated drift
  <br/>`metric:wiktionary_non_english_triggers:repository-root` — verified
- Exactly two Wiktionary language editions are in use, en=2,769 and fr=889
  <br/>`metric:wiktionary_language_editions:thats-all-folks` — verified
- 1,684 fr.wiktionary IRIs are used as subjects corpus-wide
  <br/>`metric:foreign_iris_used_as_subjects:corpus` — verified
- Run 1 note asserts the pattern is confined to three value terms
  <br/>`note:run1:LANG-001` — verified
- The substrate reports fr.wiktionary counts only as trigger statements and subject-position IRIs; no metric counts the distinct value classes those triggers attach to, so no term-level comparison with run 1's figure is available
  <br/>`metric:wiktionary_non_english_triggers:thats-all-folks` — verified
- Run 1 LANG-001's figure concerns value terms taking a lexical gloss, a different construct from the trigger statements the metrics count
  <br/>`note:run1:LANG-001` — verified
- repository-root independently splits its 624 wiktionary triggers en=477 / fr=147, supporting the systematic-split claim while saying nothing about how many value terms are affected
  <br/>`metric:wiktionary_language_editions:repository-root` — verified
- The fr.wiktionary figures are counts of trigger statements, not of value terms, so comparing 889 against run 1's three glossed terms compares different constructs in different units
  <br/>`metric:wiktionary_non_english_triggers:thats-all-folks` — verified
- The substrate records wiktionary usage only as edition splits of trigger statements (en=477 / fr=147 at the repository root), with no count of distinct value classes reached, so no term-level comparison with run 1 is available
  <br/>`metric:wiktionary_language_editions:repository-root` — verified
- Both groups split at close to the same ratio (2,769 en / 889 fr and 477 en / 147 fr), a regularity more consistent with deliberate bilingual sourcing than with uncontrolled drift
  <br/>`metric:wiktionary_language_editions:repository-root` — verified
- fr.wiktionary.org is recorded only as a subject-position trigger host; no measurement evaluates the correctness of any French-sourced trigger, so no defect magnitude can be attributed to the French share
  <br/>`metric:trigger_source_hosts:thats-all-folks` — verified

### LEXICON-004 — 378 class names are declared in more than one module with no gloss in either to settle whether they name the s [clipped]

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **SUPERSEDED - a better finding covers this**
>
> Superseded by IRI-005, and the agents who objected were right. The finding read 378 cross-group class IRIs as 378 semantic naming collisions. Checked directly: all 378 are the same file pair, ThatsAllFolks/folk.ttl against folk_aligned.ttl, and 325 of them are that pair and nothing else - the remainder add a third file but always include both. There is one governance question here, not 378: which of two near-copies of a module is canonical. The two files hold 5,828 triples each and are not isomorphic, so it is a real question, and a single one.
> - Group pairing is repository-root + thats-all-folks for all 378, with no other pair contributing any.
> - 325 of 378 are exactly folk.ttl + folk_aligned.ttl.
> - The instrument has been corrected. cross_group_file_pairings now ships beside the IRI count and reports 4, which is the number of ownership decisions actually pending.

_Everything below this line is what the run itself concluded, unedited._

*medium · proposed by Lexicon*
 · contested by Lexicon, Identity, Skeptic

- 378 of 2,240 multi-file class IRIs are declared in files in different groups, including Accomplishment, Acceptance, Accountability, Accuracy, Achievement
  <br/>`metric:class_iris_declared_across_groups:corpus` — verified
- 629 of 763 repository-root classes carry no definition text, so no gloss exists to adjudicate a shared name
  <br/>`metric:classes_without_definition_text:repository-root` — verified
- 278 of 378 thats-all-folks classes carry no definition text
  <br/>`metric:classes_without_definition_text:thats-all-folks` — verified
- repository-root contains two names that collide on normalisation, SocialFocus/Social_focus and PersonalFocus/Personal_focus
  <br/>`metric:local_names_colliding_on_normalisation:repository-root` — verified
- Folk value terms mix adjectival and nominal forms and three multiword conventions, so string form does not track concept identity
  <br/>`note:run1:NAME-002` — verified
- thats-all-folks declares exactly 378 distinct class IRIs, equal to the cross-group collision count, consistent with the whole group vocabulary being one duplicated file rather than 378 separate naming events
  <br/>`metric:classes_declared:thats-all-folks` — verified
- folk_aligned.ttl parses as 5,828 triples and 378 classes, identical to ThatsAllFolks/folk.ttl
  <br/>`document:folk_aligned.ttl` — verified
- repository-root records only 185 duplicate triples of 16,115, so folk_aligned.ttl's 5,828 triples are not compared against the other group's copy; no measurement of divergence between the two declaration sites exists
  <br/>`metric:duplicate_triple_ratio:repository-root` — verified
- thats-all-folks sums 378 class declarations over files against 378 distinct IRIs, so no IRI is declared twice inside the group and the whole of the cross-group collision set comes from one external copy
  <br/>`metric:classes_sum_over_files:thats-all-folks` — verified
- folk_aligned.ttl parses as 5,828 triples and 378 classes, matching ThatsAllFolks/folk.ttl exactly
  <br/>`document:folk_aligned.ttl` — verified
- The corpus metric on multi-file declaration states the pattern is mostly parameter variants of one ontology within a single group and explicitly not contested ownership
  <br/>`metric:class_iris_declared_in_multiple_files:corpus` — verified
- folk_aligned.ttl parses as 5,828 triples and 378 classes with 0 imports, the same figures as ThatsAllFolks/folk.ttl, which is consistent with one copy rather than two independent naming events
  <br/>`document:folk_aligned.ttl` — verified

### SHACL-004 — Do not write shapes for the vale2024, moral-molecules or mf-triggers class layers: no instance can violate them

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **MIS-SHAPED - a recommendation in a finding's place; split into fact and action**
>
> Not a status problem but a lifecycle one, and it does not want a new status. The proposition is literally a recommendation - "do not write shapes for the vale2024, moral-molecules or mf-triggers class layers" - and agents cannot confirm a recommendation on evidence, so they abstained and it fell through to unresolved. Findings state what is true; actions state what should be done. The factual core is confirmable as it stands: class-targeted instance shapes over these three graphs have no focus nodes, because the groups declare no individuals. The recommendation belongs in the actions phase, which the protocol already has, rather than smuggled into a finding title.
> - individuals_declared is 0 for vale2024, moral-molecules and mf-triggers.
> - mf-triggers declares 0 classes and 0 individuals while carrying 12,338 vcvf:triggers statements, so the construct worth validating there is a predicate, not a class.
> - SHACL-001, which states the predicate-retargeting fact rather than a recommendation, was confirmed with 7 of 7 evidence items verified.
>
> **Restated as:** Class-targeted instance shapes over the vale2024, moral-molecules and mf-triggers graphs bind zero focus nodes, because those groups declare no individuals
> **Then Action:** Do not invest in class-targeted shapes for those three layers until they carry instances; retarget to predicates per SHACL-001.

_Everything below this line is what the run itself concluded, unedited._

*medium · proposed by Validation*
 · contested by Skeptic

- vale2024 declares 1,861 classes and zero individuals, so class-targeted instance shapes have no focus nodes
  <br/>`metric:classes_declared:vale2024` — verified
- moral-molecules declares 26 classes and zero individuals
  <br/>`metric:individuals_declared:moral-molecules` — verified
- All 1,861 vale2024 classes lack definition text, a TBox deficit invisible to instance-level SHACL
  <br/>`metric:classes_without_definition_text:vale2024` — verified
- 26 vale2024 local names collide on normalisation, e.g. TraditionRole/Traditionrole
  <br/>`metric:local_names_colliding_on_normalisation:vale2024` — verified
- Zero violations should not be read as categorial correctness
  <br/>`note:run1:SHACL-001` — verified
- All 1,861 vale2024 classes lack a label, so a shape targeting owl:Class instances in that group would bind 1,861 focus nodes and flag all of them, contradicting the claim that nothing in the layer can be validated
  <br/>`metric:classes_without_a_label:vale2024` — verified
- The corpus's shapes currently reach 14 focus nodes in total, so declining the vale2024 and moral-molecules TBox as a shape target forgoes the largest validatable population available
  <br/>`metric:shacl_focus_nodes:corpus` — verified

## archived (2)

### ALIGN-001 — The trigger layer states evocation, not identity — Run 1's MAPPING-002 verdict conflates it with the separate [clipped]

*medium · proposed by Alignment*

- No vcvf:triggers statement in thats-all-folks places an external resource in object position (0), while 18,668 place one in subject position
  <br/>`metric:triggers_with_foreign_object:thats-all-folks` — verified
- The same zero-foreign-object, foreign-subject pattern holds in repository-root (0 objects, 3,078 subjects)
  <br/>`metric:triggers_with_foreign_subject:repository-root` — verified
- And in mf-triggers (0 foreign objects, 3,123 foreign subjects)
  <br/>`metric:triggers_with_foreign_object:mf-triggers` — verified
- A separate, much smaller equivalence layer exists in the same group: 377 mapping statements, of which 375 are owl:equivalentClass and 2 owl:sameAs
  <br/>`metric:mapping_statements:thats-all-folks` — verified
- repository-root carries a further 391 owl:equivalentClass plus 1 owl:sameAs
  <br/>`metric:mapping_statements:repository-root` — verified
- Run 1 recorded MAPPING-002 as confirmed on the basis that 'folk_Education.ttl aligns the Education...' to a work of fiction, without distinguishing the predicate used
  <br/>`note:run1:MAPPING-002` — verified

### DEF-001 — Definitional authority for 4,282 lexical triggers is delegated to two different Wiktionary editions, with no r [clipped]

*low · proposed by Identity*

- 3,658 wiktionary triggers in thats-all-folks split across two language editions, en=2,769 and fr=889, with the edition choice recorded nowhere
  <br/>`metric:wiktionary_language_editions:thats-all-folks` — verified
- 889 of 3,658 wiktionary triggers are non-English; the language edition is a commitment about which lexicon defines the term and nothing in the corpus records it
  <br/>`metric:wiktionary_non_english_triggers:thats-all-folks` — verified
- Wiktionary HTML page URLs are used as mapping objects, with uncontrolled language-edition drift
  <br/>`note:run1:IRI-002` — verified

## contest rationales (5)

Why an agent disputed a finding. Kept because the reasoning is often worth more than the verdict: three agents contested INV-001 on the ground that its premise was falsified by its own evidence, and they were right.

**LEXICON-004**

> **Skeptic** — The finding counts 378 declarations across modules as 378 unresolved naming questions, but its own EV-006 to EV-010 show a single duplicated file: thats-all-folks sums 378 declarations over 130 files against 378 distinct IRIs, so no IRI is declared twice inside the group, and the second si [clipped]
>

**LANG-002**

> **Skeptic** — The comparison at the heart of the finding is invalid on its own admission: 889 is a count of trigger statements and run 1's three is a count of value terms glossed, and EV-006, EV-009 and EV-010 all state that no metric counts the distinct value classes the French triggers attach to. 'Thr [clipped]
>

**LEXICON-002**

> **Skeptic** — The headline asserts of all 798 assertions that neither side carries a definition, and the finding's own EV-009 and EV-010 concede that the object side is unmeasured everywhere and that the subject side is unattributed for the 391 repository-root cases. Worse, the subject-side claim is mea [clipped]
>

**IRI-003**

> **Skeptic** — The measured content is that class declarations split across two project hosts, 4,107 and 179, and that the 180-class bfo-layer is the corpus's only fully defined and fully labelled layer. The operative claim in the title, that one host is 'less persistent' than the other, is supported by [clipped]
>

**SHACL-004**

> **Skeptic** — The premise is true and the recommendation does not follow from it. 'No instance can violate them' holds for instance-level, class-targeted shapes, which is what EV-001 and EV-003 measure. But SHACL is not confined to that: a node shape targeting instances of owl:Class binds the 1,861 vale [clipped]
>

## decisions (28)

- **DEC-001** merged on `ISSUE:DEF-001` — merged into LANG-001 (adjudicator)
- **DEC-002** merged on `ISSUE:ALIGN-001` — merged into MAPPING-001 (adjudicator)
- **DEC-003** consensus_outcome on `ISSUE:LEXICON-004:status:confirmed` — unresolved (adjudicator)
- **DEC-004** consensus_outcome on `ISSUE:SHACL-004:status:confirmed` — unresolved (adjudicator)
- **DEC-005** consensus_outcome on `ISSUE:LANG-002:status:confirmed` — unresolved (adjudicator)
- **DEC-006** no_action_required on `ISSUE:LEXICON-001` — no action this cycle (adjudicator)
- **DEC-007** no_action_required on `ISSUE:LEXICON-002` — no action this cycle (adjudicator)
- **DEC-008** no_action_required on `ISSUE:LANG-001` — no action this cycle (adjudicator)
- **DEC-009** no_action_required on `ISSUE:LEXICON-003` — no action this cycle (adjudicator)
- **DEC-010** no_action_required on `ISSUE:IRI-001` — no action this cycle (adjudicator)
- **DEC-011** no_action_required on `ISSUE:IRI-002` — no action this cycle (adjudicator)
- **DEC-012** no_action_required on `ISSUE:IRI-003` — no action this cycle (adjudicator)
- **DEC-013** no_action_required on `ISSUE:IRI-004` — no action this cycle (adjudicator)
- **DEC-014** no_action_required on `ISSUE:ALIGN-002` — no action this cycle (adjudicator)
- **DEC-015** no_action_required on `ISSUE:ALIGN-003` — no action this cycle (adjudicator)
- **DEC-016** no_action_required on `ISSUE:ALIGN-004` — no action this cycle (adjudicator)
- **DEC-017** no_action_required on `ISSUE:ALIGN-005` — no action this cycle (adjudicator)
- **DEC-018** no_action_required on `ISSUE:SHACL-001` — no action this cycle (adjudicator)
- **DEC-019** no_action_required on `ISSUE:SHACL-002` — no action this cycle (adjudicator)
- **DEC-020** no_action_required on `ISSUE:SHACL-003` — no action this cycle (adjudicator)
- **DEC-021** no_action_required on `ISSUE:SHACL-005` — no action this cycle (adjudicator)
- **DEC-022** no_action_required on `ISSUE:ASSURANCE-001` — no action this cycle (adjudicator)
- **DEC-023** no_action_required on `ISSUE:LOGIC-001` — no action this cycle (adjudicator)
- **DEC-024** no_action_required on `ISSUE:TEST-001` — no action this cycle (adjudicator)
- **DEC-025** no_action_required on `ISSUE:IRI-005` — no action this cycle (adjudicator)
- **DEC-026** no_action_required on `ISSUE:DUP-001` — no action this cycle (adjudicator)
- **DEC-027** no_action_required on `ISSUE:MAPPING-001` — no action this cycle (adjudicator)
- **DEC-028** compression on `RETROSPECTIVE` — history archived (adjudicator)

