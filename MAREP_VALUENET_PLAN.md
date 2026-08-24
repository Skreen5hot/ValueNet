# Running MAREP over the full ValueNet suite

**Status:** Run 1 complete (27 findings); instruments widened in response
**Target:** every ontology module in this repository, BFO layer and DUL layer
**Remaining:** the `ThatsAllFolks` decision, then Runs 2 and 3

---

## 0. The measured starting point

Measured by `python -m marep ingest --ontology`, which is now the authority for these numbers. It replaces a hand survey that motivated this plan and got two of them wrong.

| Group | Files | Parse OK | Parse FAIL |
| --- | ---: | ---: | ---: |
| `bfo-layer` (new modules, `.ttl` + `.owl`) | 15 | 15 | 0 |
| `bfo-vendored` (`bfo-core.ttl`) | 1 | 1 | 0 |
| `repository-root` (`ValueCore`, `bhv`, `mft`, `folk_aligned`, `bhvtriggers`, `wvs`) | 6 | 6 | 0 |
| `mf-triggers` | 13 | 13 | 0 |
| `moral-molecules` | 1 | 1 | 0 |
| `vale2024` | 5 | 5 | 0 |
| `thats-all-folks` | 130 | 3 | **127** |
| **Total** | **171** | **44** | **127** |

**127 of 171 ontology files do not parse standalone, and every one of them is in `ThatsAllFolks/`.**

> **Correction.** The hand survey behind the first draft of this plan reported 128 failures across two groups, including `wvs.ttl`. `wvs.ttl` parses. So do the six BFO `.owl` files the first version of the measurement tool also condemned. Both were the same mistake — guessing serialization from the file extension — and the tool made it before the tool caught it. The lesson is not about `wvs.ttl`; it is that the numbers a retrospective reasons over must come from something reproducible, because a survey run once by hand is exactly as fallible as a first draft of a script and leaves no trace when it is wrong.

The `ThatsAllFolks` failures share one cause: the `folk_*.ttl` files carry no `@prefix` declarations at all while using `folk:`, `vcvf:`, `owl:` and `skos:`. They are fragments meant to be read alongside a parent that declares the prefixes, not standalone documents. Whether that is a defect or an undocumented convention is exactly the kind of question a retrospective exists to settle — and not one I should settle unilaterally, because the answer depends on intent I do not have.

This table is the reason to point the retrospective at `ThatsAllFolks` and the DUL layer first. The BFO layer has been audited to exhaustion this week. The 127 that do not parse are the ones nobody has looked at.

---

## 1. The problem this plan has to solve first

MAREP grounds every confirmed finding in a substrate record (§7, §8.3.1), and `marep/ingest.py` builds that substrate from **git history** — commits, pull requests, CI runs.

That works for a retrospective *about work done*. It does not work for a retrospective *about the state of an artifact*. "127 files do not parse" is not a fact about any commit; it is a fact about the repository as it stands. Under the current ingest, a finding like that has no admissible evidence and can never leave `proposed`.

So the plan is in three parts, and the first two are prerequisites rather than the retrospective itself.

---

## 2. Prerequisite A — an ontology source for the substrate — **BUILT**

*Status: `marep/ontology_source.py`, wired into `ingest.build(ontology=True)` and
`python -m marep ingest --ontology`. 12 tests. A full-corpus scan emits 237
records: 171 `document`, 51 `metric`, 15 `commit`.*

The prediction in §8 held, though not in the way stated. The source did not emit
a shape the grounding gate refused; it emitted **false facts the gate would have
happily accepted**, which is worse. Four, all caught by inspecting the first
output rather than by any test:

* Six BFO files reported as unparseable. They parse — every `.owl` here is
  Turtle, and rdflib was guessing format from the suffix. A substrate asserting
  a failure that did not happen is worse than one omitting the check.
* `classes_total:bfo-layer` emitted twice with different values, because group
  metrics and suite metrics shared a scope. Two numbers answering to one
  reference, invisible to the schema because the ids differ.
* `OBI`, `RO` and `MFTriggers` reported as undeclared prefixes in files that
  declare everything — the regex was reading prose inside `rdfs:comment`.
* `classes_total` for a group summed per-file counts, so a module kept as both
  `.ttl` and `.owl` counted twice: 360 for a layer holding 179. Renamed to
  `classes_sum_over_files`, with the double-count stated in the record.

And one design flaw the tests caught: `Substrate.resolve` matched only on record
**id**, which is minted positionally. Adding a file to a scanned directory
shifts every later id and silently breaks evidence an earlier retrospective
cited — so `ingest.py`'s stability claim was an overstatement. Resolution now
accepts id or `ref`, `ref` being content-derived and durable, and §8.3 of the
spec records which to prefer.

### As built

`marep/ontology_source.py` measures the corpus; `ingest.build(ontology=True)` turns the measurements into substrate records. The point is not to check the ontology — the checks already existed, run by hand — it is to make ontology facts **citable**, so judgement about them can be grounded.

### Record types it emits

| Type | One per | Payload |
| --- | --- | --- |
| `document` | ontology file | path, sha256, byte size, parse status, triple count, class count, declared imports |
| `metric` | validation output | check name, scope, numeric result, tool and version |

### The checks that become `metric` records

Every one of these is deterministic, and every one has been run by hand during this week's work. That is the argument for automating them: they are already the evidence base, just not yet addressable.

* parse status per file, and per group
* dangling IRIs — referenced but never declared, per module
* classes reaching a BFO root, versus total classes
* classes missing `rdfs:label`; missing `skos:definition` or `IAO_0000115`
* `.ttl` / `.owl` isomorphism per pair
* HermiT: consistency, and unsatisfiable class count
* SHACL: violations and warnings per shapes file
* competency questions: rows returned per question
* `TestingFramework.md` Query 1 and Query 3 hit counts
* duplicate-triple ratio per file (the `ClosureHaidtValueFrames` problem, generalised)
* prefix declared-versus-used per file (the `ThatsAllFolks` problem, generalised)
* malformed IRIs in files that nonetheless parse — rdflib warns "does not look like a valid URI" on part of the corpus, and because those files *do* parse, `files_not_parsing` says nothing about them. Found while running the composition test. Not yet emitted, so a finding about it would be uncitable.

### Why this is the load-bearing piece

It closes the same circularity the git ingest closed. Without it, an agent claiming "the folk module is ungrounded" is making an assertion; with it, the claim resolves to `MET-0043: classes_reaching_bfo_root, scope=valuenet-folk, value=136/136`. The grounding gate then does real work instead of blocking everything.

**Actual:** ~390 lines plus 12 tests, no new dependencies. All three checks that were missing are now built: duplicate-triple ratio (`duplication_metrics`), and the competency questions and `TestingFramework.md` queries (`marep/competency.py`, emitting `query_rows` and `queries_passing`). Building the last one found that `TestingFramework` Query 1 took 282 seconds over 2,610 triples, so it had never actually been run.

---

## 3. Prerequisite B — the analytical agents — **BUILT**

*Status: `marep/agents.py` and `marep/anthropic_agents.py`, 18 tests. The full
roster runs all six phases end to end in `examples/full_retrospective.py`
against the real corpus, with zero rejections and no model calls.*

One correction to the design below, arrived at while building it. The plan said
`@Skeptic` needs a special capability because at threshold 0.7 a lone dissenter
can never swing a vote. That was true and the conclusion was wrong: the
Skeptic's power is not in the tally but in `proposed → contested`, since Phase 4
cannot exit while anything is contested (§13.4). One agent contesting therefore
forces adjudication of any finding — more authority than a vote share would
give it, already present in the transition graph, and a test pins it. Inventing
a capability would have obscured a mechanism that already worked.

One design decision worth recording. When an agent confirms an issue whose
evidence does not verify, it records its endorsement in `confirmed_by` but does
*not* propose the status change. Proposing it would have the Runtime refuse the
whole update, losing the agent's position along with the illegal transition.
The gate still bars confirmation; the opinion survives.

### As designed

MAREP had a Runtime and an Adjudicator and **no agents**. Phase 1 is Independent Gathering and there was nothing to gather from.

§4 requires epistemic diversity and forbids two agents covering the same ground. The default roster in the spec (`@Developer`, `@QA`, `@DeliveryManager`) is shaped for a software sprint and is wrong for an ontology. Proposed roster:

| Agent | Reads | Looks for |
| --- | --- | --- |
| `@Realist` | class axioms, reasoner output | BFO category errors, punning, unsatisfiability, dispositions modelled as processes and vice versa |
| `@Lexicographer` | labels, definitions, altLabels | missing or circular definitions, OBO naming conventions, definitions that restate the label |
| `@Interoperability` | IRIs, imports, mappings, prefixes | dangling references, namespace drift, unresolvable imports, `skos` mappings that assert more than they should |
| `@Corpus` | file-level metrics | parse health, duplication, fragments, files nobody imports, scale asymmetries |
| `@Skeptic` | everything the others produce | unsupported inference, findings that restate a metric without interpreting it, false consensus |

Two design constraints carried from the review of MAREP itself:

* **`@Skeptic` must be able to block.** At `standard_threshold: 0.7` with a five-agent roster, confirmation needs 4 of 5, so 2 dissenters block and a lone Skeptic is never pivotal. Either set `tie_break: skeptic` or give the role a bounded forced-re-vote. A Skeptic that cannot affect an outcome is decoration.
* **Agents get scoped reads (§14.1), not the corpus.** 84,149 triples will not fit in a context and do not need to. Agents read the `metric` and `document` records — a few hundred rows — and request specific file content only when a finding requires it.

**Actual:** ~430 lines across two modules plus 18 tests, sharing the backend protocol the Adjudicator defines. `ScriptedAgentBackend` runs the roster with no API key; `SilentAgentBackend` models an agent with nothing to say.

---

## 3a. Run 1 result, and what it changed

*27 findings — 21 confirmed, 4 unresolved, 2 archived, none left proposed. Every
one carried 100% verified evidence. Full log: `examples/_run/run1-complete.log`.*

Eight of the 27 were about the measuring apparatus rather than the ontology,
and they were right. Acted on before running anything else, because running
further audits with instruments that measure a quarter of the corpus would
repeat the error those findings identify:

* **Upper-ontology rooting is now asked corpus-wide, and asked properly.**
  Run 1's literal suggestion — widen the BFO grounding check — would have
  swapped one distortion for another. `ThatsAllFolks` would have read 2/378
  grounded and looked catastrophic, when 376 of its 378 classes root correctly
  in DOLCE. The check now asks *what* a class roots in. The real finding is
  larger than the one reported: **2,269 classes reach no upper ontology at
  all**, including 379 in the DUL layer proper, all 26 in `MoralMolecules`, and
  all 1,861 in `vale2024`.
* **SHACL now reports its denominator.** `shacl_violations: 0` was being read as
  a clean bill of health for a corpus 127 of whose files never entered the data
  graph. It now sits beside `shacl_focus_nodes` and `shacl_files_validated` —
  14 nodes across 6 files — so "checked and clean" is distinguishable from
  "not checked".
* **The conversational-opener rule cost six sound findings.** All six
  `conversational_artifact` rejections fired on the word "No", killing titles
  like "No upper ontology is imported". §18.3 now rejects `No`/`Yes`/`Just`
  only when a comma follows. This was a defect identified when the spec was
  written and deliberately left; it took a live run to make the cost concrete.

The eight `reopen_blocked` rejections were the §16.4 guard working correctly.

### Resolved since

`ThatsAllFolks` held **50,737 `vcvf:triggers` statements** that did not load,
because the 127 fragment files declared none of the prefixes they used.
PARSE-002 found the failures were *not* one uniform missing prefix, which
contradicted the assumption this plan started with, and left open whether the
fragments were a defect or an undocumented include convention.

Settled as a defect. Each fragment now carries its own six prefix
declarations, with fifteen further content repairs, and
`test_every_fragment_parses_standalone` holds the invariant that a `.ttl` file
in this repository is a valid document on its own. The corpus went from 0
loadable triples to 38,949. The same principle then removed the eight `.owl`
files, seven of which held Turtle: correctness belongs in the artifact, not in
a reader that knows which extensions to disbelieve.

---

## 4. Scope: three retrospectives, not one

One run over 158 files would produce a shallow pass over everything. Better to run three, each with a coherent question, and let the third build on the first two.

### Run 1 — `ThatsAllFolks` and the DUL layer *(highest value)*

The 128 non-parsing files, `wvs.ttl`, `bhvtriggers.ttl`, `folk_aligned.ttl`, `MoralMolecules`. Nobody has audited these. The central question is the one I deliberately did not answer above: are the prefix-less `folk_*.ttl` files a broken module or an undocumented include convention, and what follows either way?

### Run 2 — what the corpus should assert and does not

*Rescoped. The original Run 2 was a calibration pass over the BFO layer: run the
agents across ground already covered by hand, and read the overlap as evidence
the system works. The reasoner survey has since supplied that calibration more
cheaply and more precisely than a live run would have, so the budget is better
spent on a question nothing has asked yet.*

The survey found every group consistent with zero unsatisfiable classes, and
then found that for four of the seven this was **guaranteed before the reasoner
started**. `mf-triggers`, `moral-molecules`, `thats-all-folks` and `vale2024`
declare no disjointness, no cardinality, no functionality and no complement
between them: 143,717 of the corpus's 162,446 triples contain nothing a
reasoner could contradict. The BFO layer's own modules contribute two such
axioms. Only `repository-root` — 30 contradiction axioms over 694 individuals —
is a genuine test, and it is the only group whose cost reflects that, at 1,382
seconds against 29 for a graph three times larger.

A corpus that cannot be found inconsistent is not thereby sound. It is
unconstrained. So Run 2 asks:

**What does this corpus treat as true that it never states, and where should
each of those statements live?**

Every candidate has to be sorted into one of three, and the sorting is the
deliverable rather than a by-product:

* **OWL** — where the constraint should license entailment. Disjointness
  between sibling value dispositions, domain and range on the trigger
  properties, inverse pairs, functionality. The test is whether a reasoner
  should be able to *derive* something from it, or detect a contradiction.
* **SHACL** — where the constraint should validate instances but must not
  entail. Required fields, cardinality on annotation data, value patterns,
  datatype conformance. The test is whether violating it should make a
  dataset invalid rather than make the ontology inconsistent. OWL's open-world
  reading makes most data-quality rules silently vacuous as OWL axioms, and
  several of the likeliest candidates here are exactly that shape.
* **Intentionally unconstrained** — and this is a real answer, not a residue.
  Folk value vocabularies are meant to overlap; forcing disjointness on
  `KindnessDisposition` and `GenerosityDisposition` would encode a claim the
  domain does not make. A finding that says "leave this open, and here is why"
  is worth as much as one that proposes an axiom, and the roster is told so
  explicitly.

Expected shape of the yield, from what the instruments already show: 2,269
classes reaching no upper ontology, shapes reaching 14 focus nodes across 6 of
165 files, whole groups with no domain or range on their properties, and
sibling classes under a shared parent with nothing said about how they relate.

**Out of scope.** Duplicate-triple cleanup, at 50% in `mf-triggers` and 46% in
`thats-all-folks`, is tracked separately and deliberately excluded — it is a
question about storage, not about what the ontology claims, and mixing the two
would let a cheap mechanical finding crowd out the expensive conceptual ones.

### Run 3 — cross-layer

The relationship between the two layers: `valuenet-mappings` coverage, whether the BFO layer's `skos:broadMatch` claims are defensible, whether the trigger corpus reaches the BFO dispositions, what the DUL layer has that the BFO layer dropped. The MFT violations gap was one instance of this; there are probably others.

---

## 5. Execution

For each run:

```
python -m marep ingest --sprint valuenet-<scope> --ontology --since ... --until ...
python -m marep init   --sprint valuenet-<scope> --roster Realist,Lexicographer,Interoperability,Corpus,Skeptic
# Phase 1  agents gather in parallel under CAS
# Phase 2  Adjudicator merges duplicates under an exclusive lock
# Phase 3  agents evaluate; grounding gate binds every confirmation
# Phase 4  Adjudicator adjudicates contradictions and votes
# Phase 5  actions proposed against confirmed findings
# Phase 6  compression, then deliverables
python -m marep report
```

Budget per run: `per_retrospective_total` around 400k tokens, `compression_reserve` 80k, `per_turn_context` 16k. That last number is what forces scoped reads to be real rather than aspirational.

---

## 6. What could go wrong, and what that would tell us

| Risk | Signal | Reading |
| --- | --- | --- |
| Agents restate metrics as findings | issues whose title paraphrases their only evidence | the prompts are asking for retrieval, not judgement |
| Everything lands `unresolved` | high unresolved count, low confirmed | the ontology source is emitting too few citable facts — a §2 problem, not an agent problem |
| Findings I already know about, and nothing else | Run 2 output matches this week's commits | the system works and adds nothing; stop after Run 1 |
| Adjudicator over-merges | distinct defects collapsed in Phase 2 | contradicts the live result, where it declined to merge two findings sharing a commit; would be new information |
| Cost overrun | budget exhausted before Phase 5 | scoped reads are not scoped; check `token_ledger.consumed_by_agent` |

The third row is the one to take seriously. It is a real possible outcome that this produces nothing new on the BFO layer, and the honest response is to say so and stop, not to run the other two anyway.

---

## 7. Order of work

1. **Ontology source** (§2) — nothing else is possible without it.
2. **Agents** (§3) — with `@Skeptic` given actual power.
3. **Run 1** on `ThatsAllFolks` and the DUL layer, where the unexamined material is.
4. Read the output. Decide whether Runs 2 and 3 are worth their cost.

Steps 1 and 2 are ordinary engineering with tests, in the pattern already established. Step 3 is the first time MAREP does the thing it was built for, on a corpus large enough to be a real test rather than a demonstration.

---

## 8. One thing worth deciding before starting

Every live defect this week was in the deterministic half — the Runtime, the schema, the budgets, the transition graph — and none in the model's judgement. Five separate bugs across three live runs, all mine, none caught by 79 unit tests.

That pattern predicts where Run 1 will break: not in what the agents conclude, but in the ontology source emitting a record shape that the grounding gate then refuses. Building §2 with that expectation, and testing it against deliberately awkward inputs before spending tokens on agents, is the cheapest way to avoid burning a run.
