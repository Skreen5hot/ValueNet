# Repository reorganization — plan for approval

**Status:** proposed, not started. No file has moved.
**Revised** after review. The first draft is corrected in six places, recorded
below, because two of its errors would have produced the wrong plan rather than
a merely untidy one.

---

## What the first draft got wrong

| claim | reality | consequence |
|---|---|---|
| "moving breaks every `owl:imports`" | **False.** All imports are absolute IRIs; **zero** relative paths in the suite | This was load-bearing in the choice put to you. Ontology identity and repository location are separate contracts, and the first draft conflated them. |
| "eight MAREP documents" | **10** — two reconciliation YAMLs and `RUN3_HYPOTHESES.yaml` were missed | Undercounted the move surface |
| "22 test files, 273 tests" | **21 modules + conftest; 539 collected**, 534 selected, 5 deselected | Off by a factor of two |
| root inventory | missed two `.png` diagrams and `ValueNet_stats.txt` | Files with no home in the proposed tree |
| `BFO/remediation/` → `docs/` | holds `generate_cco_extract.py`, `check_bfo_consistency.py`, a JSON Schema | Would have filed working generators as historical records |
| tests grouped by creation date | `test_competency_questions.py` spans MAREP + BFO + MFTriggers | Genuinely integration; date is not a responsibility |

The `owl:imports` error is the material one. What actually breaks on a move is
**local loaders, offline import resolution, query scopes, generators, and
documentation links** — all repairable, none semantic.

---

## Decision: hybrid separation

**Physically reorganize everything fork-authored. Leave upstream-derived paths
where upstream has them**, until upstream synchronization is formally retired or
replaced with a subtree/mirror workflow.

Measured provenance, per path, against `upstream/main`:

| area | fork-authored | upstream-repaired | upstream-unchanged |
|---|---:|---:|---:|
| `BFO/` | 42 | — | — |
| `marep/` | 24 | — | — |
| `tests/` | 22 | — | — |
| `examples/` | 8 | — | — |
| `ValueNet_code/` | 8 | — | 1 |
| `ThatsAllFolks/` | 5 | **124** | 7 |
| `MFTriggers/` | — | 12 | 2 |
| `vale2024/` | — | — | 39 |
| root `.ttl` | 1 (`wvs.ttl`) | 2 | 3 |

`ThatsAllFolks/` is the reason for the hybrid. 124 of its files are
upstream-derived and locally repaired; moving them guarantees a conflict on
every one at the next upstream merge, for no semantic gain.

### Why not `ontology/upstream/`

The name would assert a provenance that is no longer true. `ThatsAllFolks/` was
extensively repaired here, `folk.ttl` is now our maintained source,
`bhvtriggers.ttl` was repaired, `wvs.owl` became `wvs.ttl`. Use **Original
ValueNet**, with provenance recorded as data rather than implied by a directory
name:

```
unchanged-upstream | locally-repaired-upstream | fork-authored | generated | vendored-external
```

---

## Target structure

```text
ontology/
  bfo/
    core/                   valuenet-core, folk, schwartz-values
    extensions/
      moral-foundations/
      moral-epistemics/     module, scenario, CQ document
    shapes/                 core-shapes, moral-epistemics-shapes,
                            vcvf-triggers-shapes
    vendor/
      bfo/                  bfo-core.ttl
      cco/                  cco-valuenet-extract.ttl + manifest

docs/
  architecture/             this plan, layout contract, provenance index
  original-valuenet/        README material for the legacy corpus, stats, diagrams
  bfo/
    guides/                 annotationGuide, Phase4_LinguisticGrounding,
                            TestingFramework, BFOizing ValueNet, RefactorPlan
    remediation/            PHASE*.md, DECISION_RECORDS, BASELINE, SOURCE_SELECTION,
                            EXTERNAL_TERM_INVENTORY, the remediation plan
  marep/
    specifications/         MAREP_v2.1, MAREP_v2.2
    plans/                  MAREP_VALUENET_PLAN, MAREP_IMPLEMENTATION_PLAN
    runs/                   RUN{1,2,3}_FINDINGS, RECONCILIATIONs, HYPOTHESES

tools/
  original-valuenet/        repair_folk_fragments, diagnose_folk_fragments,
                            retarget_bad_trigger_objects, settle_trigger_targets,
                            add_folk_religion, declare_folk_value,
                            generate_folk_aligned
  bfo/                      generate_cco_extract, check_bfo_consistency,
                            extract-manifest.schema.json
  marep/                    report_run

marep/                      framework implementation (unmoved)
examples/marep/             walkthrough, run1_audit, run2_constraints, run3_commitments, …

tests/
  marep/                    runtime, adjudicator, agents, ingest, resume,
                            grounding_strength
  original-valuenet/        ontology_artifacts, folk_generation, trigger_shapes,
                            commitments
  bfo/                      alignment_remediation, cco_extract, core_definitions,
                            external_closure, mapping_semantics,
                            moral_epistemics_categories
  integration/              competency_questions, ontology_source,
                            constraint_metrics, duplication_metrics,
                            reasoner_scope
  conftest.py

config/
  repository-layout.yaml    the single layout contract
```

**Unmoved, deliberately:** `ThatsAllFolks/`, `MFTriggers/`, `MoralMolecules/`,
`vale2024/`, and the root `.ttl` files. Declared in the manifest and indexed
from the README rather than relocated.

---

## Step 1 is the one the first draft omitted

Layout is currently hardcoded in **three independent places**:

- `marep/ontology_source.py:43` — `GROUPS`, the corpus grouping
- `marep/competency.py:160` — `QUERY_DOCS`, executable query documents
- `ValueNet_code/generate_folk_aligned.py:50` — `SOURCE` / `TARGET`

and **20 code and test files** hardcode a corpus path:

```
BFO/remediation/generate_cco_extract.py     marep/agents.py
ValueNet_code/add_folk_religion.py          marep/cli.py
ValueNet_code/declare_folk_value.py         marep/commitments.py
ValueNet_code/diagnose_folk_fragments.py    marep/competency.py
ValueNet_code/generate_folk_aligned.py      marep/ontology_source.py
ValueNet_code/repair_folk_fragments.py      tests/test_commitments.py
ValueNet_code/retarget_bad_trigger_objects.py  tests/test_competency_questions.py
ValueNet_code/settle_trigger_targets.py     tests/test_folk_generation.py
examples/run1_audit.py                      tests/test_ontology_artifacts.py
                                            tests/test_ontology_source.py
                                            tests/test_reasoner_scope.py
```

Moving files before centralizing these means editing 20 files under a broken
tree. Centralizing first means each later move is a one-line manifest change.

`config/repository-layout.yaml` declares each component once: `path`,
`provenance`, `owner`, `role`, and whether it is `generated_from` something.

---

## Migration sequence

Separate commits throughout. **No semantic ontology edit is combined with a
relocation** — that rule is what makes each step's verification meaningful.

1. **Path abstraction.** Manifest + resolver. Nothing moves.
2. **Adopt the resolver** in MAREP grouping, query discovery, generators, tools, tests.
3. **Contract tests.** Every configured path exists; every component has exactly
   one provenance classification; no code outside the resolver hardcodes a
   corpus path.
4. **Semantic snapshot** — see below. Nothing moves.
5. **Move BFO** modules, extensions, shapes, vendor, guides, remediation, tools.
6. **Move MAREP** documents and examples.
7. **Reorganize tests**, with the explicit `integration/` group.
8. **Update READMEs and executable query scopes** (`# scope:` lines in the CQ
   and TestingFramework documents point at `BFO/` and must follow the move).
9. **Final verification.**

### Step 4: the semantic snapshot, and why it is not optional

The end-state checks in the review are right, but they are end-state. This
failure mode needs a **per-commit** invariant, because it does not fail loudly.

An hour before this plan was written, `reasoner_metrics` silently dropped from
**306 classes to 275** because the CCO extract landed in a directory its
hardcoded file list did not know about. HermiT stayed consistent. Every test
stayed green. The reasoner was simply checking less, and said so only in an
`imports_unresolved` count nobody was reading.

A move that changes *what gets loaded* looks exactly like a move that changed
nothing. So capture these before step 5 and assert equality after **every**
move commit:

| invariant | value at plan time |
|---|---:|
| corpus files discovered | 168 |
| corpus distinct triples | 104,763 |
| declared classes | 3,703 |
| `vcvf:triggers` statements | 57,578 |
| distinct trigger objects | 147 |
| BFO-layer classes (HermiT scope) | 306 |
| BFO-layer imports unresolved | 0 |
| `folk_aligned.ttl` SHA-256 | `047db3158bbf58b2e7848fe5bdea5eb3…` |
| tests collected | 539 (534 selected, 5 deselected) |

Any move that changes a number here has changed what the tooling can see, and
must be justified rather than absorbed.

### Step 9: final verification

- exactly 539 tests collect; default suite green
- every ontology file parses standalone
- offline imports resolve; **0 unresolved** in the HermiT scope
- generators deterministic — `generate_folk_aligned.py --check` exits 0
- CCO extraction reproducible to the same SHA-256
- all nine competency and sanity queries pass
- both HermiT scopes consistent, 0 unsatisfiable
- trigger SHACL conforms over the whole corpus
- no stale path outside the compatibility manifest

---

## Risks

**Upstream divergence.** We are 50 ahead, 0 behind. Leaving Original ValueNet
paths intact keeps that mergeable. If upstream sync is retired, a follow-up
plan can move them in one commit — cheap, once the resolver exists.

**The manifest becomes a second hardcoded layout.** Mitigated by step 3's test
that no module outside the resolver hardcodes a corpus path, so the manifest
cannot quietly acquire a competitor.

**Documentation link rot.** ~30 cross-references between the markdown documents.
Step 8 owns this; a link check belongs in step 9.

---

## Explicitly out of scope

Vocabulary governance, near-synonym adjudication, definition quality, the
`mft:NegativeValue` wording, the nine `SENSE-001` capitalised targets, and the
ontology versioning scheme. All are backlog items. **This plan moves files and
changes no meaning.**
