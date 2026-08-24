# valuenet-run1 — findings

Rendered from `RUN1_STATE.yaml` by `ValueNet_code/report_run.py`. The state file is the record; this is a view of it.

**Two kinds of statement appear below and are never merged.** Finding titles, severities and evidence are exactly what the run concluded from the substrate it was given, reproduced unedited. Anything inside a `⚠ RECONCILIATION` block was established *after* the run, sometimes contradicting it, and is never folded back into the finding. The state file itself is not modified by reconciliation.

- **phase** complete, **version** 155
- **substrate** `sha256:77b0fdabc1068b456e1…`
- **findings** 27 — 21 confirmed, 4 unresolved, 2 archived
- **tokens declared** 407,000
- **evidence** 220/220 verified against the substrate
- **reconciled** against the tree at `d3b87ef` — 5 finding(s) superseded or resolved; the state file itself is unmodified

## confirmed (21)

### BFO-002 — Class-bearing ontology files import no upper ontology, so no category error in them is even expressible

*high · proposed by Realist*
 · confirmed by Realist, Interoperability, Corpus
 · contested by Skeptic

- ValueCore.ttl declares 22 classes and has 0 imports
  <br/>`document:ValueCore.ttl` — verified
- bhv.ttl declares 36 classes and has 0 imports
  <br/>`document:bhv.ttl` — verified
- mft.ttl declares 25 classes and has 0 imports
  <br/>`document:mft.ttl` — verified
- folk_aligned.ttl declares 378 classes and has 0 imports
  <br/>`document:folk_aligned.ttl` — verified
- the Curry moral-molecules file declares 26 classes and has 0 imports
  <br/>`document:MoralMolecules/curry_no_combinations_updated.ttl` — verified
- wvs.owl declares 356 classes and 3 imports — the only class-bearing file in the corpus with any imports — and the substrate records no target for those imports, so 'imports no upper ontology' is unverified rather than confirmed for this file
  <br/>`document:wvs.owl` — verified
- ThatsAllFolks/folk.owl declares 378 classes with 0 imports, extending the no-imports class-bearing set to 865 of the 1221 class declarations in the corpus
  <br/>`document:ThatsAllFolks/folk.owl` — verified
- taf.ttl's single import is recorded as a bare count with no target IRI, as are bhvtriggers.ttl's one and wvs.owl's three, so no import edge anywhere in the corpus is resolvable from the substrate and 'imports no upper ontology' is only decidable for the 0-import files
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- Exactly three files in the whole corpus declare any import — taf.ttl (1), bhvtriggers.ttl (1), wvs.owl (3) — and two of the three declare zero classes, so apart from wvs.owl the importing set and the class-declaring set are disjoint at file level
  <br/>`document:bhvtriggers.ttl` — verified
- wvs.owl is a class-bearing file (356 classes) with 3 imports, so the class-bearing set and the zero-import set are not coextensive and the universal as titled is false at file level
  <br/>`document:wvs.owl` — verified
- The zero-import class-bearing files sum to 865 declarations (ValueCore 22 + bhv 36 + mft 25 + folk_aligned 378 + curry 26 + folk.owl 378), which is the defensible scope for the finding
  <br/>`document:folk_aligned.ttl` — verified
- The ValueCore.ttl record contains only triple, class and import counts; no axiom or hierarchy content is recorded for any corpus file, so claims about what is expressible inside these files are inference rather than measurement
  <br/>`document:ValueCore.ttl` — verified

### HEALTH-001 — Every file-level quality metric is computed over a population disjoint from the corpus

*high · proposed by Skeptic*
 · confirmed by Interoperability
 · contested by Corpus, Skeptic

- Grounding, definition, label and dangling-IRI checks are all scoped to bfo-suite-merged, which totals 179 classes
  <br/>`metric:classes_total:bfo-suite-merged` — verified
- 179 classes reach a BFO root, and the population the check was computed over is 179
  <br/>`metric:classes_measured_for_grounding:corpus` — verified
- 789 distinct class IRIs exist across every parsing file in the corpus
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- 789 classes are recorded as declared in the corpus but outside the grounding check's scope
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- bfo-suite-merged reports 0 classes missing a definition, a perfect score over the same narrow population
  <br/>`metric:classes_missing_definition:bfo-suite-merged` — verified
- The scope gap was already identified as something agents misread
  <br/>`commit:e2ac15e5868a1bd283af187ff371a4bc387114c6` — verified
- dangling_iris exists only for bfo-suite-merged (0); no equivalent metric is recorded for any corpus scope, so no cross-file reference among the 789 distinct class IRIs has been checked for resolvability
  <br/>`metric:dangling_iris:bfo-suite-merged` — verified
- 127 of 130 thats-all-folks files yield no triples, so even a corpus-wide reference check would not see their outbound IRIs — the unmeasured region and the unloadable region coincide
  <br/>`metric:files_not_parsing:thats-all-folks` — verified
- files_not_parsing (127), files_with_undeclared_prefixes (128), files_parsing (3) and triples_sum (44548) are all computed over thats-all-folks itself — corpus scopes, not bfo-suite-merged — so the disjointness holds for the class-level semantic checks only
  <br/>`metric:files_not_parsing:thats-all-folks` — verified
- files_with_undeclared_prefixes is recorded for thats-all-folks (128), repository-root (0) and moral-molecules (0) — corpus scopes, not bfo-suite-merged — so file-level quality metrics over the corpus do exist and the universal in the title is false
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified
- files_not_parsing and files_parsing are likewise computed per corpus scope, so the disjointness the finding describes holds for the class-level semantic checks only
  <br/>`metric:files_parsing:thats-all-folks` — verified

### MAPPING-001 — The corpus's entire external alignment layer contributes zero triples to the loadable graph

*high · proposed by Interoperability*
 · confirmed by Corpus, Skeptic

- triples_sum for thats-all-folks is 44548, exactly equal to the three parsing files (357_GRAPH.ttl 162 + folk.owl 5828 + taf.ttl 38558), leaving zero triples from the 127 failing fragments
  <br/>`metric:triples_sum_over_files:thats-all-folks` — verified
- 127 of 130 files in thats-all-folks fail to parse
  <br/>`metric:files_not_parsing:thats-all-folks` — verified
- The unparsed content is alignment content: folk_BadHealth.ttl's failing line links to <https://w3id.org/framester/data/framestercore/MedicalConditions>
  <br/>`document:ThatsAllFolks/folk_BadHealth.ttl` — verified
- folk_Knowledge.ttl's failing line links to <http://dbpedia.org/resource/Knowledge> under a section header '# DBpedia Entities'
  <br/>`document:ThatsAllFolks/folk_Knowledge.ttl` — verified
- Only 10 of the corpus's 137 inventoried files parse (6 repository-root, 3 thats-all-folks, 1 moral-molecules), and every one of the 127 unloadable files is a single-term folk fragment, so the loss is confined to exactly one artefact class
  <br/>`metric:files_parsing:repository-root` — verified
- taf.ttl's 38558 triples are recorded as a count with no content breakdown, so whether alignment assertions also exist inside the loadable files is unmeasured; 'entire external alignment layer' should be read as the fragment layer
  <br/>`document:ThatsAllFolks/taf.ttl` — verified

### NAMESPACE-001 — ThatsAllFolks fragment files are not self-contained RDF documents, and the missing bindings are not one prefix [clipped]

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **RESOLVED - fixed since this run**
>
> Fixed. Every one of the 130 ThatsAllFolks files now parses standalone as Turtle, and files_with_undeclared_prefixes for the scope is 0. The finding was correct and has been acted on.
> - Each fragment carries its own six prefix declarations.
> - The corpus went from 0 loadable triples to 38,949.
> - tests/test_ontology_artifacts.py::test_every_fragment_is_self_contained and ::test_every_fragment_parses_standalone hold the invariant, so the defect cannot return silently.

_Everything below this line is what the run itself concluded, unedited._

*high · proposed by Interoperability*
 · confirmed by Interoperability, Corpus, Skeptic

- folk_Courage.ttl fails with 'Prefix "vcvf:" not bound', the same cause reported for the overwhelming majority of the 127 failures
  <br/>`document:ThatsAllFolks/folk_Courage.ttl` — verified
- folk_Happyness.ttl fails on a different unbound prefix, folk:, showing the binding gap is not confined to one namespace
  <br/>`document:ThatsAllFolks/folk_Happyness.ttl` — verified
- 128 files in thats-all-folks carry undeclared prefixes, enumerated as Justice, Schwartz, be, cohabitation, folk, goal — a set disjoint from the vcvf: prefix that appears in the parse errors
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified
- folk_Consciousness.ttl, folk_Understanding.ttl and folk_Victory.ttl fail with 'expected directive or statement' rather than an unbound prefix, so at least three files have structural damage a prefix header would not repair
  <br/>`document:ThatsAllFolks/folk_Consciousness.ttl` — verified
- 128 thats-all-folks files carry undeclared prefixes while only 127 fail to parse, so at least one file that does load also carries an unbound namespace: the binding gap is not wholly contained in the unparseable set
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified
- The prefix reported unbound in the fragment parse errors is vcvf:, e.g. in folk_Zeal.ttl, and vcvf is absent from the undeclared-prefix metric's named list, confirming the two measurements cover different missing bindings rather than the same one
  <br/>`document:ThatsAllFolks/folk_Zeal.ttl` — verified
- files_with_undeclared_prefixes is 0 for repository-root and 0 for moral-molecules, so all 128 affected files lie inside a single directory: the binding gap is directory-local rather than a corpus-wide convention failure
  <br/>`metric:files_with_undeclared_prefixes:repository-root` — verified
- 128 of the scope's 130 files carry an undeclared prefix, so at most two ThatsAllFolks files are free of the binding defect — the gap is near-total within the directory and absent outside it
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified

### VALIDATION-001 — Zero SHACL violations is largely an artifact of 127 files being invisible to the validator

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **CAUSE REFUTED - the conclusion stands, the stated cause does not**
>
> The most useful reconciliation result, because the finding's prediction was testable and failed. It claimed zero SHACL violations was "largely an artifact of 127 files being invisible to the validator". All 127 are now visible and contribute 44,934 triples, and shacl_violations is still 0 on both shape sets. Fragment invisibility was not the cause. The conclusion survives - zero violations is still not a clean bill of health - but for a different and larger reason: the SHACL data graph loads 6 of 165 files and reaches 14 focus nodes, and the shapes target BFO-layer classes the folk corpus never instantiates. Repairing the fragments could not have changed the result. The finding said so itself. Its last evidence item reads "nothing in the substrate states which data graph was validated, so the attribution of the clean result to fragment invisibility is inference and not a measured causal link". The agent flagged its own causal claim as unsupported, and that flag was right.
> - shacl_violations is 0 on both shape sets before and after the repair.
> - shacl_files_validated:corpus is 6 of 165; shacl_focus_nodes:corpus is 14.
> - Run 2's SHACL-001 states the same fact with the correct cause and is confirmed with 12 of 12 evidence items verified.

_Everything below this line is what the run itself concluded, unedited._

*high · proposed by Skeptic*
 · confirmed by Corpus, Skeptic

- valuenet-core-shapes reports 0 SHACL violations
  <br/>`metric:shacl_violations:valuenet-core-shapes` — verified
- valuenet-moral-epistemics-shapes reports 0 violations and 1 warning
  <br/>`metric:shacl_warnings:valuenet-moral-epistemics-shapes` — verified
- 127 of 130 ThatsAllFolks files do not parse and so yield no triples to validate
  <br/>`metric:files_not_parsing:thats-all-folks` — verified
- Only 3 ThatsAllFolks files parse, and they account for the whole module's triple count
  <br/>`metric:files_parsing:thats-all-folks` — verified
- The unvalidated portion is 127 of 130 files but 0 of the 44548 triples in that scope, all of which come from the three parsing files, so the shortfall is in artefact coverage and alignment content rather than in triple volume
  <br/>`metric:triples_sum_over_files:thats-all-folks` — verified
- The shacl records name shape sets only; nothing in the substrate states which data graph was validated, so the attribution of the clean result to fragment invisibility is inference and not a measured causal link
  <br/>`metric:shacl_violations:valuenet-core-shapes` — verified

### COUNTING-001 — Corpus size and class-count figures double-count a duplicated file and must not be summed

*medium · proposed by Skeptic*
 · confirmed by Corpus, Skeptic

- folk.owl reports 5828 triples and 378 classes
  <br/>`document:ThatsAllFolks/folk.owl` — verified
- folk_aligned.ttl reports the identical 5828 triples and 378 classes in a different scope
  <br/>`document:folk_aligned.ttl` — verified
- The class sum metric explicitly notes that .ttl/.owl pairs are counted twice
  <br/>`metric:classes_sum_over_files:repository-root` — verified
- Distinct class IRIs across the corpus are 789, well below the 1,221 obtained by summing scopes
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- The thats-all-folks class sum of 378 is entirely folk.owl, duplicated in the root scope
  <br/>`metric:classes_sum_over_files:thats-all-folks` — verified
- Summing the three scope triple totals gives 60951, of which the folk.owl/folk_aligned duplicate contributes 5828 twice — 9.6% of the apparent corpus size is one file counted a second time
  <br/>`metric:triples_sum_over_files:thats-all-folks` — verified

### DEF-003 — Dense near-synonym families in the folk vocabulary have no audited definitions to separate them

*medium · proposed by Lexicographer*
 · confirmed by Lexicographer, Corpus, Skeptic

- Smart declared as a distinct term
  <br/>`document:ThatsAllFolks/folk_Smart.ttl` — verified
- Intelligence declared as a distinct term
  <br/>`document:ThatsAllFolks/folk_Intelligence.ttl` — verified
- Genius declared as a distinct term
  <br/>`document:ThatsAllFolks/folk_Genius.ttl` — verified
- Brilliance declared as a distinct term
  <br/>`document:ThatsAllFolks/folk_Brilliance.ttl` — verified
- Rest, Relaxation, Silence and Solitude declared separately alongside Inner_peace
  <br/>`document:ThatsAllFolks/folk_Solitude.ttl` — verified
- none of these classes fall within the 179 measured for definition completeness
  <br/>`metric:classes_measured_for_grounding:corpus` — verified
- folk_Rest.ttl, folk_Relaxation.ttl and folk_Silence.ttl exist as separate artefacts alongside folk_Solitude.ttl and folk_Inner_peace.ttl, confirming the second near-synonym family at five members
  <br/>`document:ThatsAllFolks/folk_Rest.ttl` — verified
- The only differentiating content in the intelligence family is a single external link each — folk_Intelligence.ttl to <http://dbpedia.org/resource/Intelligence>, folk_Genius.ttl to <http://dbpedia.org/resource/Genius>, folk_Brilliance.ttl to <http://en.wiktionary.org/wiki/brilliance> — wit [clipped]
  <br/>`document:ThatsAllFolks/folk_Intelligence.ttl` — verified
- The family also mixes lexical form: Smart is glossed at <http://en.wiktionary.org/wiki/smart> as an adjectival term while its three near-synonyms are nominal, so the terms differ in grammatical category as well as being undifferentiated in sense
  <br/>`document:ThatsAllFolks/folk_Smart.ttl` — verified
- Each fragment record reports one error at one line (e.g. folk_Genius.ttl at line 16), so the unquoted remainder of every fragment is unmeasured and no claim about the totality of a file's differentiating content can be made from the substrate
  <br/>`document:ThatsAllFolks/folk_Genius.ttl` — verified

### DUP-001 — folk.owl and folk_aligned.ttl are an undeclared duplicate pair, and the class counts double-count it

*medium · proposed by Interoperability*
 · confirmed by Corpus, Skeptic

- ThatsAllFolks/folk.owl parses to 5828 triples and 378 classes
  <br/>`document:ThatsAllFolks/folk.owl` — verified
- folk_aligned.ttl parses to exactly the same 5828 triples and 378 classes, containing no additional alignment content
  <br/>`document:folk_aligned.ttl` — verified
- Distinct class IRIs across the corpus number 789 while the per-scope file sums total 1221 (817 + 378 + 26), a gap of 432 duplicate declarations
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- classes_sum_over_files for repository-root is 817 and for thats-all-folks 378, both explicitly counting .ttl/.owl pairs twice
  <br/>`metric:classes_sum_over_files:repository-root` — verified
- Distinct count across the corpus is 789, far below the 1221 file-wise sum
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- A prior consolidation already dropped one duplicate directory, so duplicate copies are a recurring pattern here
  <br/>`commit:f29c22dfe8e853c602fd15f623b1f0f0336cc565` — verified
- The folk.owl/folk_aligned.ttl pair accounts for 378 of the corpus's 432 redundant class declarations (1221 summed minus 789 distinct), i.e. 87% of all class-level duplication in the collection
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- Commit f29c22df is characterised in this issue as a duplicate-directory consolidation and in PARSE-001 EV-007 as a corpus-wide namespace consolidation onto vcvf:; the two readings of one ref should be reconciled before either supports a conclusion
  <br/>`commit:f29c22dfe8e853c602fd15f623b1f0f0336cc565` — verified

### HEALTH-002 — Repair effort has tracked the measured suite rather than the broken mass

*medium · proposed by Corpus*
 · confirmed by Corpus, Skeptic

- A repair pass fixed an unparseable file, dangling parents and version imports in the BFO suite
  <br/>`commit:27b6b3e9eab8903e348c392d43ba9b27938a7e99` — verified
- The repaired suite now reports zero missing labels
  <br/>`metric:classes_missing_label:bfo-suite-merged` — verified
- All 179 of its classes reach the BFO root
  <br/>`metric:classes_reaching_bfo_root:bfo-suite-merged` — verified
- 127 files remain unparseable in the largest directory
  <br/>`metric:files_not_parsing:thats-all-folks` — verified
- Only 3 of 130 ThatsAllFolks files currently parse
  <br/>`metric:files_parsing:thats-all-folks` — verified
- 127 of the corpus's 137 inventoried files (93%) remain unparseable and all sit in one directory, while files_not_parsing is 0 for repository-root and 0 for moral-molecules — the failing set is untouched and unchanged
  <br/>`metric:files_not_parsing:repository-root` — verified
- The substrate records one current parse state for the 127 fragments and no prior state, so 'untouched and unchanged' is inference from a single snapshot; what is measured is only that they are unparseable now
  <br/>`metric:files_not_parsing:thats-all-folks` — verified

### INVENTORY-001 — A directory named MFRC_1k_graphs contributes exactly one file to the measured inventory

*medium · proposed by Corpus*
 · confirmed by Corpus, Skeptic

- Exactly one file from MFRC_1k_graphs appears in the inventory, numbered 357
  <br/>`document:ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl` — verified
- The whole ThatsAllFolks tree is recorded as 130 files
  <br/>`metric:files_total:thats-all-folks` — verified
- A survey count has previously disagreed with a hand count in this repository
  <br/>`commit:f82f871f4866459b9b54fdcdd7f908d88dbdc884` — verified
- The 130-file scope total is exhausted by 127 non-parsing fragments plus 3 parsing files, so exactly one MFRC_1k_graphs artefact is inside the measurement and its numbered siblings (the file is 357_GRAPH.ttl) are absent from the inventory rather than unparsed
  <br/>`metric:files_parsing:thats-all-folks` — verified

### IRI-001 — At least 54 class IRIs receive class axioms in two or more separate files

*medium · proposed by Realist*
 · confirmed by Realist, Corpus
 · contested by Skeptic

- repository-root sums 817 class declarations across its files
  <br/>`metric:classes_sum_over_files:repository-root` — verified
- thats-all-folks sums 378 class declarations
  <br/>`metric:classes_sum_over_files:thats-all-folks` — verified
- moral-molecules sums 26 class declarations
  <br/>`metric:classes_sum_over_files:moral-molecules` — verified
- only 789 distinct class IRIs exist across every parsing file, versus 1221 declarations
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- The 817 repository-root class sum decomposes as ValueCore 22 + bhv 36 + mft 25 + folk_aligned 378 + wvs.owl 356 (bhvtriggers 0), fixing the number of class-declaring files in the corpus at seven and raising the duplicated-IRI lower bound from 54 to 72
  <br/>`document:wvs.owl` — verified
- Corpus-wide redundancy is exactly 432 declarations (1221 summed minus 789 distinct); the folk.owl/folk_aligned pair accounts for 378 of them, leaving 54 redundant declarations spread over the other five class-declaring files
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- Corpus surplus is 432 declarations (1221 − 789); with seven class-declaring files a single IRI can contribute at most six surplus declarations, so a residual of 54 surplus declarations implies between 9 and 54 additional multiply-declared IRIs, not 'at least 54'
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- folk_aligned.ttl and folk.owl each declare 378 classes with identical triple counts, so on the finding's own reading at least 378 IRIs are declared in two files — the true lower bound, which the title's 54 contradicts rather than supports
  <br/>`document:folk_aligned.ttl` — verified

### MAPPING-002 — DBpedia alignment targets include works of fiction and strictly broader concepts

*medium · proposed by Interoperability*
 · confirmed by Realist, Interoperability, Skeptic

- folk_Education.ttl aligns the Education value to <http://dbpedia.org/resource/An_Education>, a film title rather than the concept education
  <br/>`document:ThatsAllFolks/folk_Education.ttl` — verified
- folk_Helping.ttl aligns Helping to <http://dbpedia.org/resource/The_Help>, a work title rather than the act of helping
  <br/>`document:ThatsAllFolks/folk_Helping.ttl` — verified
- folk_Belief.ttl aligns Belief to <http://dbpedia.org/resource/Religion>, a narrower and categorially different resource
  <br/>`document:ThatsAllFolks/folk_Belief.ttl` — verified
- folk_Financial_stability.ttl aligns Financial stability to <http://dbpedia.org/resource/Wealth>
  <br/>`document:ThatsAllFolks/folk_Financial_stability.ttl` — verified
- folk_Inner_peace.ttl aligns Inner peace to <http://dbpedia.org/resource/Peace>
  <br/>`document:ThatsAllFolks/folk_Inner_peace.ttl` — verified
- The predicate carrying every one of these alignments is an unbound vcvf: term, so whether the mapping asserts equivalence or mere relatedness is unmeasured — the broader-concept cases are contingent on this, the individual-vs-universal cases are not
  <br/>`document:ThatsAllFolks/folk_Belief.ttl` — verified
- The same unresolvable vcvf: predicate carries the Framester alignment in folk_BadHealth.ttl as carries the DBpedia and Wiktionary links, so no mapping in the fragment layer has a measurable predicate semantics
  <br/>`document:ThatsAllFolks/folk_BadHealth.ttl` — verified
- The other-category target pattern extends beyond the five cited DBpedia cases: folk_Workmanship.ttl targets <http://en.wiktionary.org/wiki/DIY> and folk_Doing_good.ttl targets <http://en.wiktionary.org/wiki/benefactor>, a role-bearer rather than the act
  <br/>`document:ThatsAllFolks/folk_Workmanship.ttl` — verified
- folk_Belief.ttl targets <http://dbpedia.org/resource/Religion>, which is narrower than Belief; the 'strictly broader' half of the title is carried by the Wealth and Peace cases only
  <br/>`document:ThatsAllFolks/folk_Belief.ttl` — verified

### NAME-001 — Two misspelled value terms are carried in artefact names, one of them contradicting the class name inside the same file

*medium · proposed by Lexicographer*
 · confirmed by Lexicographer, Corpus, Skeptic

- file is named folk_Happyness.ttl while its content declares '## folk:Happiness'
  <br/>`document:ThatsAllFolks/folk_Happyness.ttl` — verified
- file is named folk_Strenght.ttl while its content references the term 'strength'
  <br/>`document:ThatsAllFolks/folk_Strenght.ttl` — verified
- folk_Happyness.ttl fails at line 10 with the correct spelling appearing only inside a '## folk:Happiness' comment header; the file yields no parsed classes, so the corrected spelling exists nowhere machine-readable and the misspelling survives as the artefact's only stable identifier
  <br/>`document:ThatsAllFolks/folk_Happyness.ttl` — verified
- In folk_Strenght.ttl the correct spelling occurs only as the lexical gloss target <http://en.wiktionary.org/wiki/strength>, i.e. in the object of the mapping rather than in any term or filename
  <br/>`document:ThatsAllFolks/folk_Strenght.ttl` — verified
- folk_Happyness.ttl and folk_Strenght.ttl are both among the 127 non-parsing files, so neither contributes any IRI to the 789 distinct class set and the misspelling cannot be corrected by any graph-level operation
  <br/>`metric:files_not_parsing:thats-all-folks` — verified

### NAME-002 — Folk value terms mix adjectival and nominal forms and mix three multiword conventions

*medium · proposed by Lexicographer*
 · confirmed by Realist
 · contested by Lexicographer, Corpus, Skeptic

- adjectival term name
  <br/>`document:ThatsAllFolks/folk_Capable.ttl` — verified
- adjectival term name
  <br/>`document:ThatsAllFolks/folk_Irreverent.ttl` — verified
- propositional term name in a value vocabulary
  <br/>`document:ThatsAllFolks/folk_LifeIsMeaningless.ttl` — verified
- propositional term name in a value vocabulary
  <br/>`document:ThatsAllFolks/folk_OtherPeopleCannotBeTrusted.ttl` — verified
- snake_case multiword term
  <br/>`document:ThatsAllFolks/folk_Inner_peace.ttl` — verified
- CamelCase multiword term in the same directory
  <br/>`document:ThatsAllFolks/folk_BadHealth.ttl` — verified
- second snake_case multiword term
  <br/>`document:ThatsAllFolks/folk_Decision_making.ttl` — verified
- folk_LifeIsMeaningless.ttl points at <http://dbpedia.org/resource/Nihilism>, a doctrine, from a term named as a proposition
  <br/>`document:ThatsAllFolks/folk_LifeIsMeaningless.ttl` — verified
- folk_Capable.ttl points at <http://en.wiktionary.org/wiki/capable>, an adjectival quality of a bearer, so the two entries sit in different BFO categories inside one hierarchy
  <br/>`document:ThatsAllFolks/folk_Capable.ttl` — verified
- Underscore-with-lowercase-continuation is attested at least five times across the fragment files — Doing_good, Earning_trust, Financial_stability, Inner_peace, Decision_making — establishing it as a settled convention rather than a one-off
  <br/>`document:ThatsAllFolks/folk_Financial_stability.ttl` — verified
- Every other multiword folk term in the substrate's file records is CamelCase (BadHealth, LifeIsMeaningless, OtherPeopleCannotBeTrusted); no third multiword convention is attested anywhere in the 130-file listing
  <br/>`document:ThatsAllFolks/folk_Doing_good.ttl` — verified
- The adjectival/nominal split is broader than the two cited cases: Dutiful, Impartial, Intuitive, Famous, Ferocious, Lively, Smart and Welcoming are all adjectival names sitting alongside nominal terms such as Courage and Knowledge
  <br/>`document:ThatsAllFolks/folk_Dutiful.ttl` — verified
- The complete 130-file thats-all-folks listing contains exactly eight multiword terms — BadHealth, Decision_making, Doing_good, Earning_trust, Financial_stability, Inner_peace, LifeIsMeaningless, OtherPeopleCannotBeTrusted — which fall into two conventions (CamelCase and underscore-with-low [clipped]
  <br/>`document:ThatsAllFolks/folk_Earning_trust.ttl` — verified
- The eight multiword names in the listing (BadHealth, Decision_making, Doing_good, Earning_trust, Financial_stability, Inner_peace, LifeIsMeaningless, OtherPeopleCannotBeTrusted) fall into exactly two forms; no third form is attested in the 130-file scope
  <br/>`document:ThatsAllFolks/folk_Inner_peace.ttl` — verified
- All eight multiword artefacts lie in the 127 non-parsing set and yield no classes, so the conventions observed are filename conventions and no corresponding term IRI is recorded anywhere in the substrate
  <br/>`metric:files_not_parsing:thats-all-folks` — verified

### PARSE-002 — The parse failures are not one missing prefix, and the reported errors are first-failure-only, so remediation [clipped]

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **SUPERSEDED - was right, no longer applies**
>
> Right, and now obsolete. The claim was that the failures were not one missing prefix and that the reported errors were first-failure-only, so remediation could not be costed from the error set. The diagnosis run confirmed exactly that: three files failed structurally rather than on a binding, one failed on folk: rather than vcvf:, and the per-file error showed only the first fault. All 130 now parse.
> - folk_Consciousness.ttl, folk_Victory.ttl and folk_Understanding.ttl needed content repair, not a prefix binding, exactly as claimed.
> - All three now parse (1,049, 399 and 79 triples).

_Everything below this line is what the run itself concluded, unedited._

*medium · proposed by Skeptic*
 · confirmed by Interoperability, Corpus, Skeptic

- folk_Consciousness.ttl fails with 'expected directive or statement', not a prefix error
  <br/>`document:ThatsAllFolks/folk_Consciousness.ttl` — verified
- folk_Victory.ttl fails with a structural 'expected directive or statement' error at line 13
  <br/>`document:ThatsAllFolks/folk_Victory.ttl` — verified
- folk_Happyness.ttl fails on an unbound 'folk:' prefix, a different binding from vcvf:
  <br/>`document:ThatsAllFolks/folk_Happyness.ttl` — verified
- The undeclared-prefix metric counts 128 files and names Justice, Schwartz, be, cohabitation, folk, goal — not vcvf
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified
- 127 files fail to parse, one fewer than the 128 with undeclared prefixes
  <br/>`metric:files_not_parsing:thats-all-folks` — verified
- The three structural failures all occur at the '## folk:X' header block (folk_Understanding.ttl at line 13, folk_Consciousness.ttl at line 12, folk_Victory.ttl at line 13) rather than at an alignment line, so they are a distinct co-located defect and not prefix damage
  <br/>`document:ThatsAllFolks/folk_Understanding.ttl` — verified
- 128 files carry undeclared prefixes against 127 that fail to parse, so at least one currently-loading file also carries an unbound namespace and the defect reaches into the loadable graph
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified
- 128 files carry one of the six named undeclared prefixes and 123 fail on the separate vcvf: binding (127 failures less three structural and one folk:), so across 130 files at least 121 carry two independent binding defects and per-file repair cost cannot be read off the single reported error
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified
- The three structural failures and folk_Happyness.ttl's folk: failure all occur at the '## folk:X' header block rather than at an alignment line, so the residual class is header damage and is distinguishable from the vcvf: failures by location as well as by message
  <br/>`document:ThatsAllFolks/folk_Happyness.ttl` — verified

### SENSE-001 — Several value classes are glossed against the proper-name sense of their term rather than the value sense

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **UPHELD - and extended by cases found since**
>
> Upheld, and four further cases observed since. The finding is that value classes are targeted at the capitalised Wiktionary entry - the proper-name sense - where the house convention is the lowercase common noun. Measured across all 127 fragments: nine target the capitalised form of their own value term. Run 1 named seven cases, five of which are in that nine (Grace, Faith, Excellence, Independence, Lively); the other two, Education and Helping, are the distinct work-title pattern (An_Education, The_Help) rather than a capitalised term. Newly observed and not named in Run 1: Knowledge, Religion, Rest and Victory. folk_Rest targets REST, which is an acronym rather than a proper noun but the same defect - a technical sense standing in for the value sense. One qualification that narrows the remedy: all nine also carry the lowercase entry. The capitalised IRI is an ADDITIONAL target, not a substituted one, so the fix is to drop a target rather than to correct one, and no trigger statement is lost by doing so. A separate count, deliberately kept apart: 44 of 127 fragments target some capitalised entry, but most are acronyms or proper nouns serving legitimately as trigger sources - LASER under Accuracy, DevOps under Development, SEAT under Comfort. Those are not SENSE-001 cases and folding them in would inflate the finding roughly fivefold.
> - Nine fragments target the capitalised form of their own value term, measured over all 127.
> - All nine also carry the lowercase form of the same word.
> - folk:Religion is among them, from the fragment renamed during this round's trigger-target work.

_Everything below this line is what the run itself concluded, unedited._

*medium · proposed by Lexicographer*
 · confirmed by Lexicographer, Interoperability, Skeptic

- Education is glossed against the title 'An_Education'
  <br/>`document:ThatsAllFolks/folk_Education.ttl` — verified
- Helping is glossed against the title 'The_Help'
  <br/>`document:ThatsAllFolks/folk_Helping.ttl` — verified
- Grace is glossed against the capitalised form 'Grace'
  <br/>`document:ThatsAllFolks/folk_Grace.ttl` — verified
- Faith is glossed against the capitalised form 'Faith'
  <br/>`document:ThatsAllFolks/folk_Faith.ttl` — verified
- Excellence is glossed against the capitalised form 'Excellence'
  <br/>`document:ThatsAllFolks/folk_Excellence.ttl` — verified
- folk_Independence.ttl targets the capitalised entry <http://en.wiktionary.org/wiki/Independence>, a sixth instance of the same capitalised-entry pattern
  <br/>`document:ThatsAllFolks/folk_Independence.ttl` — verified
- folk_Lively.ttl targets the capitalised entry <http://en.wiktionary.org/wiki/Lively>, whose capitalised Wiktionary entry is a surname rather than the adjectival quality the term names
  <br/>`document:ThatsAllFolks/folk_Lively.ttl` — verified
- The prevailing convention elsewhere is the lowercase common-noun entry, e.g. folk_Accuracy.ttl targets <http://en.wiktionary.org/wiki/accuracy>, so the capitalised cases are departures rather than house style
  <br/>`document:ThatsAllFolks/folk_Accuracy.ttl` — verified
- The lowercase target form is the attested house convention across the fragment records, e.g. folk_Zeal.ttl targets <http://en.wiktionary.org/wiki/zeal>, making the capitalised targets divergent IRIs rather than a stylistic variant of the same resource
  <br/>`document:ThatsAllFolks/folk_Zeal.ttl` — verified
- What the substrate establishes for folk_Faith.ttl is that the target is <http://en.wiktionary.org/wiki/Faith>, a distinct case-sensitive page IRI from the lowercase form used elsewhere; the sense that page carries is not recorded
  <br/>`document:ThatsAllFolks/folk_Faith.ttl` — verified
- Fragment records contain a single parse-error line and no sense, gloss or definition content for any target page, so the proper-name reading is measurable only where the IRI string itself names a work (An_Education, The_Help)
  <br/>`document:ThatsAllFolks/folk_Education.ttl` — verified

### SHACL-001 — Zero SHACL violations is not evidence of categorial correctness and should not be read as such

*medium · proposed by Realist*
 · confirmed by Realist, Corpus, Skeptic

- valuenet-core-shapes reports 0 violations
  <br/>`metric:shacl_violations:valuenet-core-shapes` — verified
- valuenet-moral-epistemics-shapes reports 0 violations and 1 warning
  <br/>`metric:shacl_warnings:valuenet-moral-epistemics-shapes` — verified
- the 789 corpus classes are all outside the grounding check, so no categorial check backs the clean SHACL result
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- dangling_iris for bfo-suite-merged is 0 — the substrate's only structural-integrity check is likewise confined to the 179-class suite, so nothing measured inspects the categorial placement of any corpus class
  <br/>`metric:dangling_iris:bfo-suite-merged` — verified
- shacl_violations and shacl_warnings are recorded against shape-set names (valuenet-core-shapes, valuenet-moral-epistemics-shapes); no substrate record states which data graph either was evaluated over, so the coverage of the clean result is unmeasured in both directions
  <br/>`metric:shacl_violations:valuenet-moral-epistemics-shapes` — verified

### IRI-002 — Wiktionary HTML page URLs used as mapping objects, with uncontrolled language-edition drift

*low · proposed by Interoperability*
 · confirmed by Interoperability, Corpus, Skeptic

- folk_Amusement.ttl targets <http://fr.wiktionary.org/wiki/amusement> rather than the English edition
  <br/>`document:ThatsAllFolks/folk_Amusement.ttl` — verified
- folk_Fitness.ttl targets <http://fr.wiktionary.org/wiki/fitness>
  <br/>`document:ThatsAllFolks/folk_Fitness.ttl` — verified
- folk_Fun.ttl targets <http://fr.wiktionary.org/wiki/fun>
  <br/>`document:ThatsAllFolks/folk_Fun.ttl` — verified
- folk_Excellence.ttl uses capitalised <http://en.wiktionary.org/wiki/Excellence> while folk_Accuracy.ttl uses lowercase <http://en.wiktionary.org/wiki/accuracy>, an inconsistent casing convention for case-sensitive page IRIs
  <br/>`document:ThatsAllFolks/folk_Excellence.ttl` — verified
- Capitalised Wiktionary page targets are attested at least five times — Excellence, Faith, Grace, Independence, Lively — against a lowercase majority, so casing drift is systematic rather than a single slip
  <br/>`document:ThatsAllFolks/folk_Grace.ttl` — verified
- Mapping objects also vary by URI scheme: the Wiktionary and DBpedia targets use http: while folk_BadHealth.ttl's Framester target uses https:, a further axis on which the same resource can be named two ways
  <br/>`document:ThatsAllFolks/folk_BadHealth.ttl` — verified
- A sixth casing form is attested: folk_Workmanship.ttl targets <http://en.wiktionary.org/wiki/DIY>, an all-caps entry, so the collection uses lowercase, Capitalised and ALLCAPS page IRIs against a case-sensitive resource
  <br/>`document:ThatsAllFolks/folk_Workmanship.ttl` — verified

### LANG-001 — Three value terms take their lexical gloss from a French dictionary while the rest use English

*low · proposed by Lexicographer*
 · confirmed by Lexicographer, Interoperability, Corpus, Skeptic

- Amusement glossed from fr.wiktionary
  <br/>`document:ThatsAllFolks/folk_Amusement.ttl` — verified
- Fun glossed from fr.wiktionary
  <br/>`document:ThatsAllFolks/folk_Fun.ttl` — verified
- Fitness glossed from fr.wiktionary
  <br/>`document:ThatsAllFolks/folk_Fitness.ttl` — verified
- surrounding terms are glossed from en.wiktionary
  <br/>`document:ThatsAllFolks/folk_Humor.ttl` — verified
- Exactly three folk fragment files reference fr.wiktionary (Amusement, Fitness, Fun); every other lexical gloss in the substrate's fragment records uses en.wiktionary, e.g. folk_Zeal.ttl targets <http://en.wiktionary.org/wiki/zeal>
  <br/>`document:ThatsAllFolks/folk_Zeal.ttl` — verified
- All three French-glossed terms are English borrowings into French, so the fr.wiktionary entry documents a loanword sense rather than the source-language value concept the class names
  <br/>`document:ThatsAllFolks/folk_Fitness.ttl` — verified
- fr.wiktionary appears in exactly three of the 127 recorded parse-error lines (Amusement, Fitness, Fun); since each record shows only the first failing line of a file, three is a floor rather than a census
  <br/>`document:ThatsAllFolks/folk_Fitness.ttl` — verified
- All three French-glossed files are among the 127 non-parsing artefacts, so the language divergence is visible only by file inspection and never reaches a loaded graph where a query could detect it
  <br/>`metric:files_not_parsing:thats-all-folks` — verified
- The folk_Fitness.ttl record consists solely of a parse-failure line quoting the fr.wiktionary target; it carries no lexical, etymological or sense information, so the 'English borrowings into French' characterisation is not grounded in the substrate
  <br/>`document:ThatsAllFolks/folk_Fitness.ttl` — verified

### NAME-003 — Artefact names encode process history or a transformation the artefacts do not exhibit

*low · proposed by Lexicographer*
 · confirmed by Lexicographer, Corpus

- folk.owl carries 5828 triples and 378 classes
  <br/>`document:ThatsAllFolks/folk.owl` — verified
- folk_aligned.ttl carries the identical 5828 triples and 378 classes despite the differentiating name
  <br/>`document:folk_aligned.ttl` — verified
- artefact name encodes a negation and a revision marker
  <br/>`document:MoralMolecules/curry_no_combinations_updated.ttl` — verified
- The directory name MFRC_1k_graphs encodes a cardinality of one thousand graphs while exactly one file from that directory, 357_GRAPH.ttl, appears in the measured inventory — a third artefact name asserting a property the artefact set does not exhibit
  <br/>`document:ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl` — verified
- curry_no_combinations_updated.ttl composes three separate process markers — source attribution, a content exclusion, and a revision state — none of which is recoverable from the file's 288 triples and 26 classes
  <br/>`document:MoralMolecules/curry_no_combinations_updated.ttl` — verified
- folk_aligned.ttl's 5828 triples are 36% of repository-root's entire 16115-triple mass, so the redundantly named copy dominates the scope it sits in
  <br/>`metric:triples_sum_over_files:repository-root` — verified

### BFO-001 — The 179/179 grounding result certifies a BFO suite that shares no classes with the value corpus

*critical · proposed by Realist*
 · confirmed by Realist, Corpus, Skeptic

- classes_reaching_bfo_root for bfo-suite-merged is 179, over a measured population of 179
  <br/>`metric:classes_reaching_bfo_root:bfo-suite-merged` — verified
- the population the grounding check is computed over is 179 classes
  <br/>`metric:classes_measured_for_grounding:corpus` — verified
- 789 classes are declared in the corpus but outside the grounding check's scope
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- 789 distinct class IRIs exist across every parsing file, i.e. the unmeasured set is the whole corpus
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- wvs.owl alone declares 356 classes — twice the entire 179-class population the grounding check was computed over — so no reading of the scopes lets the measured suite contain the corpus's classes
  <br/>`document:wvs.owl` — verified
- The measured file inventory is 137 artefacts across exactly three scopes (repository-root 6, thats-all-folks 130, moral-molecules 1), and no files_total or files_parsing metric exists for bfo-suite-merged, so the certified suite is not one of the corpus's inventoried files
  <br/>`metric:files_total:repository-root` — verified
- classes_total:bfo-suite-merged (179) equals classes_measured_for_grounding:corpus (179), so the measured population is exactly the suite and nothing else, which is what licenses the disjointness inference rather than a coincidence of two 789s
  <br/>`metric:classes_total:bfo-suite-merged` — verified

## unresolved (4)

### DEF-002 — The "zero missing definitions" result covers 23% of the corpus and cannot be read as corpus-wide definitional health

*high · proposed by Lexicographer*
 · contested by Lexicographer, Corpus

- classes_missing_definition and classes_missing_label are both 0, but only for the bfo-suite-merged scope
  <br/>`metric:classes_missing_definition:bfo-suite-merged` — verified
- the population the check is computed over is 179 classes
  <br/>`metric:classes_measured_for_grounding:corpus` — verified
- the corpus declares 789 distinct class IRIs across every parsing file
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- 789 classes are recorded as declared but outside the grounding check's scope
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- folk.owl alone contributes 378 classes, none of them in the measured population
  <br/>`document:ThatsAllFolks/folk.owl` — verified
- classes_unmeasured_for_grounding equals classes_distinct_in_corpus exactly (789 = 789), which is only consistent with the 179-class measured population lying wholly outside the corpus's distinct class set — so no corpus class has a measured definition-completeness result at all
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- The zero-missing-definition and zero-missing-label results are recorded only against the bfo-suite-merged scope; no definition or label metric exists for any repository-root, thats-all-folks or moral-molecules scope
  <br/>`metric:classes_missing_label:bfo-suite-merged` — verified
- classes_unmeasured_for_grounding (789) equals classes_distinct_in_corpus (789), so the measured coverage of corpus classes by the definition-completeness check is 0 of 789
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified

### PARSE-001 — The unparseable 127 are one mechanical fix plus a four-file residual, not 127 separate repairs

> ### ⚠ RECONCILIATION — NOT A RUN CONCLUSION
>
> **SUPERSEDED - partly wrong, no longer applies**
>
> The structural claim was right in kind and wrong in magnitude, and the factual base is gone. It said the 127 were "one mechanical fix plus a four-file residual". The mechanical fix was real — a six-line prefix header, applied to all 127 — but the residual was 15 files needing content repair, not four. It stayed `unresolved` in Run 1, which was the correct outcome for a finding whose repair estimate the substrate could not support.
> - 15 files needed a content repair beyond the header - 12 carrying export debris, 2 with a doubled IRI terminator, 1 with a stray quote.
> - files_not_parsing:thats-all-folks is now 0, from 127.

_Everything below this line is what the run itself concluded, unedited._

*high · proposed by Corpus*
 · contested by Interoperability, Corpus, Skeptic

- 127 of 130 ThatsAllFolks files fail to parse
  <br/>`metric:files_not_parsing:thats-all-folks` — verified
- 128 files carry undeclared prefixes, named as Justice, Schwartz, be, cohabitation, folk, goal
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified
- Representative failure: unbound vcvf: prefix at line 12
  <br/>`document:ThatsAllFolks/folk_Accomplishment.ttl` — verified
- A distinct failure mode — 'expected directive or statement' — not attributable to a missing prefix binding
  <br/>`document:ThatsAllFolks/folk_Consciousness.ttl` — verified
- Second instance of the non-prefix failure mode
  <br/>`document:ThatsAllFolks/folk_Victory.ttl` — verified
- Third instance of the non-prefix failure mode
  <br/>`document:ThatsAllFolks/folk_Understanding.ttl` — verified
- A namespace consolidation onto vcvf: was performed as a corpus-wide edit, coinciding with the prefix that is now unbound in 127 files
  <br/>`commit:f29c22dfe8e853c602fd15f623b1f0f0336cc565` — verified
- 128 files carry undeclared prefixes drawn from a six-name set disjoint from vcvf, so a vcvf: binding cannot be shown to leave those files parseable
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified
- Parse records report a single error at a single line (folk_Rigor.ttl at line 16), so the remainder of each failing file is unmeasured and the repair count cannot be derived from the error set
  <br/>`document:ThatsAllFolks/folk_Rigor.ttl` — verified
- 128 files carry a prefix from the six-name set and 123 fail on vcvf: (127 failures less three structural and one folk:), so across 130 files at least 121 carry both defects and a single vcvf: binding cannot be shown to make any of them parse
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified
- Parse records expose one error at one line per file (folk_Rigor.ttl at line 16), so the unread remainder of each failing file makes any repair-count estimate unmeasurable from the error set
  <br/>`document:ThatsAllFolks/folk_Rigor.ttl` — verified
- 128 of 130 files carry a prefix from a six-name set disjoint from vcvf while 123 fail on vcvf, forcing an overlap of at least 121 files carrying two independent binding defects
  <br/>`metric:files_with_undeclared_prefixes:thats-all-folks` — verified

### DEF-001 — 45k triples of assertional content in ThatsAllFolks rest on type definitions supplied by a single unresolved import each

*medium · proposed by Realist*
 · contested by Realist, Interoperability, Corpus, Skeptic

- taf.ttl parses with 38558 triples, 0 classes and 1 import
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- bhvtriggers.ttl parses with 6532 triples, 0 classes and 1 import
  <br/>`document:bhvtriggers.ttl` — verified
- a representative MFRC graph carries 162 triples and 0 classes
  <br/>`document:ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl` — verified
- the thats-all-folks group totals 44548 triples
  <br/>`metric:triples_sum_over_files:thats-all-folks` — verified
- ThatsAllFolks totals 44548 triples, of which folk.owl contributes 5828 as class declarations, so the module's assertional mass is not the 45k figure quoted
  <br/>`metric:triples_sum_over_files:thats-all-folks` — verified
- bhvtriggers.ttl is a repository-root file, not a ThatsAllFolks file, and its record states only '1 imports' with no resolution status
  <br/>`document:bhvtriggers.ttl` — verified
- taf.ttl's record states '1 imports' with no target IRI and no resolution outcome, so import resolvability is unmeasured rather than negative
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- repository-root is measured as 6 files, all parsing, and bhvtriggers.ttl is one of them, so it cannot contribute to the thats-all-folks triple mass the finding describes
  <br/>`metric:files_total:repository-root` — verified
- Corpus triples total 60951 (repository-root 16115 + thats-all-folks 44548 + moral-molecules 288); taf.ttl's 38558 and bhvtriggers.ttl's 6532 sit in different scopes, so no single module carries the 45k mass the finding describes
  <br/>`metric:triples_sum_over_files:repository-root` — verified
- Every file record states imports as a bare count with no target, so import resolution status is unmeasured for all three importing files in the corpus
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- repository-root is 6 files with 16115 triples and bhvtriggers.ttl is one of them, so its 6532 triples cannot be added to the thats-all-folks mass the finding names
  <br/>`metric:triples_sum_over_files:repository-root` — verified
- ThatsAllFolks/taf.ttl's record reads '1 imports' with no target and no resolution status, so import resolvability is unmeasured rather than negative
  <br/>`document:ThatsAllFolks/taf.ttl` — verified

### IMPORT-001 — The class-bearing files form no import graph; the mass sits in two importing files that declare no classes

*medium · proposed by Corpus*
 · contested by Interoperability, Corpus

- ValueCore.ttl declares 22 classes and 0 imports
  <br/>`document:ValueCore.ttl` — verified
- mft.ttl declares 25 classes and 0 imports
  <br/>`document:mft.ttl` — verified
- bhv.ttl declares 36 classes and 0 imports
  <br/>`document:bhv.ttl` — verified
- taf.ttl holds 38558 triples with 0 classes and 1 import
  <br/>`document:ThatsAllFolks/taf.ttl` — verified
- bhvtriggers.ttl holds 6532 triples with 0 classes and 1 import
  <br/>`document:bhvtriggers.ttl` — verified
- wvs.owl is the only file declaring more than one import (3)
  <br/>`document:wvs.owl` — verified
- ThatsAllFolks totals 44548 triples, dominated by the two class-free files
  <br/>`metric:triples_sum_over_files:thats-all-folks` — verified
- wvs.owl declares 356 classes together with 3 imports, contradicting the universal that class-bearing files declare none
  <br/>`document:wvs.owl` — verified
- bhvtriggers.ttl's record, like every other file record, gives an import count with no target IRI, so no import edge in the corpus can be traced to a destination
  <br/>`document:bhvtriggers.ttl` — verified
- taf.ttl (38558) and bhvtriggers.ttl (6532) together hold 45090 of the corpus's 60951 triples — 74% of the mass — with zero classes between them, while wvs.owl carries 356 classes alongside 3 imports and breaks the stated universal
  <br/>`document:wvs.owl` — verified

## archived (2)

### SCOPE-001 — The clean grounding scorecard covers a population disjoint from the corpus's own class count, so it cannot be [clipped]

*high · proposed by Skeptic*

- Grounding, definition, label and dangling-IRI checks are all scoped to bfo-suite-merged, which totals 179 classes
  <br/>`metric:classes_total:bfo-suite-merged` — verified
- 179 classes reach a BFO root, and the population the check was computed over is 179
  <br/>`metric:classes_measured_for_grounding:corpus` — verified
- 789 distinct class IRIs exist across every parsing file in the corpus
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- 789 classes are recorded as declared in the corpus but outside the grounding check's scope
  <br/>`metric:classes_unmeasured_for_grounding:corpus` — verified
- bfo-suite-merged reports 0 classes missing a definition, a perfect score over the same narrow population
  <br/>`metric:classes_missing_definition:bfo-suite-merged` — verified

### DUPLICATION-001 — folk_aligned.ttl is byte-equivalent in content to folk.owl — the 'aligned' artifact carries no alignment

*medium · proposed by Interoperability*

- ThatsAllFolks/folk.owl parses to 5828 triples and 378 classes
  <br/>`document:ThatsAllFolks/folk.owl` — verified
- folk_aligned.ttl parses to exactly the same 5828 triples and 378 classes, containing no additional alignment content
  <br/>`document:folk_aligned.ttl` — verified
- Distinct class IRIs across the corpus number 789 while the per-scope file sums total 1221 (817 + 378 + 26), a gap of 432 duplicate declarations
  <br/>`metric:classes_distinct_in_corpus:corpus` — verified
- classes_sum_over_files for repository-root is 817 and for thats-all-folks 378, both explicitly counting .ttl/.owl pairs twice
  <br/>`metric:classes_sum_over_files:repository-root` — verified

## contest rationales (8)

Why an agent disputed a finding. Kept because the reasoning is often worth more than the verdict: three agents contested INV-001 on the ground that its premise was falsified by its own evidence, and they were right.

**DEF-001**

> **Skeptic** — Two independent overruns, both already visible in the evidence set. First, the 45k mass does not exist in one module: taf.ttl's 38558 triples sit in thats-all-folks while bhvtriggers.ttl's 6532 sit in repository-root, which is measured as 6 files all parsing. Second, and more serious, 'unr [clipped]
>

**DEF-002**

> **Corpus** — The headline figure is refuted by the issue's own EV-006. If 789 classes are unmeasured and 789 distinct classes exist, the measured population lies wholly outside the corpus and coverage is 0 of 789, not 23%. The 23% reading (179/789) treats the two populations as overlapping, which the m [clipped]
>

**NAME-002**

> **Skeptic** — The title asserts three multiword conventions; EV-011 and EV-013 in the same issue state that exactly two are attested across the complete 130-file listing (CamelCase and underscore-with-lowercase-continuation), and EV-011 says explicitly that no third convention appears anywhere. A confir [clipped]
>

**PARSE-001**

> **Skeptic** — This is the finding most likely to be acted on and least supported by its evidence. It asserts a repair plan — one mechanical fix plus four residual files — that the substrate cannot underwrite for two reasons its own EV-008/EV-009/EV-010 state. First, each record reports a single error at [clipped]
>

**IMPORT-001**

> **Corpus** — The second half is sound and quantifiable: taf.ttl and bhvtriggers.ttl hold 45090 of the corpus's 60951 triples with zero classes between them. But the universal in the first clause is refuted by the issue's own EV-008 — wvs.owl declares 356 classes and 3 imports. The defensible framing is [clipped]
>

**HEALTH-001**

> **Skeptic** — The title says 'every file-level quality metric' and EV-009 refutes it in the same issue: files_not_parsing (127), files_parsing (3), files_with_undeclared_prefixes (128) and triples_sum (44548) are file-level quality metrics computed over corpus scopes, not over bfo-suite-merged. The disj [clipped]
>

**BFO-002**

> **Skeptic** — The title is an unrestricted universal over class-bearing files, and the issue's own EV-006 falsifies it: wvs.owl declares 356 classes with 3 imports whose targets the substrate does not record, so for the single largest class-declaring file 'imports no upper ontology' is unmeasured, not e [clipped]
>

**IRI-001**

> **Skeptic** — The headline number is derived in the wrong direction and the evidence set contradicts itself. The substrate supports 432 surplus declarations (1221 summed minus 789 distinct). EV-006 attributes 378 of those to the folk.owl/folk_aligned pair, leaving 54 surplus declarations elsewhere — but [clipped]
>

## decisions (28)

- **DEC-001** merged on `ISSUE:DUPLICATION-001` — merged into DUP-001 (adjudicator)
- **DEC-002** merged on `ISSUE:SCOPE-001` — merged into HEALTH-001 (adjudicator)
- **DEC-003** consensus_outcome on `ISSUE:DEF-001:status:confirmed` — unresolved (adjudicator)
- **DEC-004** consensus_outcome on `ISSUE:DEF-002:status:confirmed` — unresolved (adjudicator)
- **DEC-005** consensus_outcome on `ISSUE:PARSE-001:status:confirmed` — unresolved (adjudicator)
- **DEC-006** consensus_outcome on `ISSUE:IMPORT-001:status:confirmed` — unresolved (adjudicator)
- **DEC-007** no_action_required on `ISSUE:BFO-001` — no action this cycle (adjudicator)
- **DEC-008** no_action_required on `ISSUE:BFO-002` — no action this cycle (adjudicator)
- **DEC-009** no_action_required on `ISSUE:SHACL-001` — no action this cycle (adjudicator)
- **DEC-010** no_action_required on `ISSUE:IRI-001` — no action this cycle (adjudicator)
- **DEC-011** no_action_required on `ISSUE:NAME-001` — no action this cycle (adjudicator)
- **DEC-012** no_action_required on `ISSUE:NAME-002` — no action this cycle (adjudicator)
- **DEC-013** no_action_required on `ISSUE:SENSE-001` — no action this cycle (adjudicator)
- **DEC-014** no_action_required on `ISSUE:LANG-001` — no action this cycle (adjudicator)
- **DEC-015** no_action_required on `ISSUE:DEF-003` — no action this cycle (adjudicator)
- **DEC-016** no_action_required on `ISSUE:NAME-003` — no action this cycle (adjudicator)
- **DEC-017** no_action_required on `ISSUE:NAMESPACE-001` — no action this cycle (adjudicator)
- **DEC-018** no_action_required on `ISSUE:MAPPING-001` — no action this cycle (adjudicator)
- **DEC-019** no_action_required on `ISSUE:MAPPING-002` — no action this cycle (adjudicator)
- **DEC-020** no_action_required on `ISSUE:IRI-002` — no action this cycle (adjudicator)
- **DEC-021** no_action_required on `ISSUE:HEALTH-001` — no action this cycle (adjudicator)
- **DEC-022** no_action_required on `ISSUE:DUP-001` — no action this cycle (adjudicator)
- **DEC-023** no_action_required on `ISSUE:INVENTORY-001` — no action this cycle (adjudicator)
- **DEC-024** no_action_required on `ISSUE:HEALTH-002` — no action this cycle (adjudicator)
- **DEC-025** no_action_required on `ISSUE:VALIDATION-001` — no action this cycle (adjudicator)
- **DEC-026** no_action_required on `ISSUE:PARSE-002` — no action this cycle (adjudicator)
- **DEC-027** no_action_required on `ISSUE:COUNTING-001` — no action this cycle (adjudicator)
- **DEC-028** compression on `RETROSPECTIVE` — history archived (adjudicator)

