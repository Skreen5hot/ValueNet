# Repository reorganization — plan for approval

**Status:** revision 4, proposed. Nothing has moved. No semantic ontology change
is in scope.

Revision 3 was **conceptually approved** but not ready to execute: the manifest
builder committed alongside it had four execution defects. All four are fixed
and verified here. Every factual correction in both reviews was independently
checked against the repository before adoption.

---

## Corrections carried from review

| revision 2 said | verified reality |
|---|---|
| 3,703 declared classes | **2,889 named classes.** Mine counted 814 blank-node restrictions. Per-file sum is 5,402. |
| 50 commits ahead of upstream | **53** |
| 106 tests in the five `conftest`-importing modules | **105** |
| `wvs.ttl` fork-authored | **upstream-derived** — renamed from `wvs.owl` |
| six files had destinations | **six had none**: `valuenet-mappings.ttl`, `vcvf-triggers-semantics.ttl`, `vcvf-triggers-review.md`, both Phase 1 term documents, `is_v_emo_overlaps.py` |
| move upstream-unchanged docs assets | contradicted the hybrid rule |
| `.gitignore`, `pytest.ini`, `README.md` | absent from the plan entirely |

The class count is the one I most regret. This session has been spent correcting
numbers with no stated definition, and revision 2 put one into a plan as an
*invariant*.

---

## What changed in revision 4

### A generated manifest replaces the hand-written destination list

`ValueNet_code/build_move_manifest.py` derives `config/move-manifest.yaml` from
`git ls-files` and rename history. It **refuses to emit an incomplete manifest**
— it returns before writing while any file is `UNASSIGNED` or any destination is
malformed. Hand-listing missed six files; deriving closed them.

Coverage: **320 tracked files, 0 unassigned, 0 malformed.**

| disposition | files |
|---|---:|
| RETAIN — upstream-derived, path-sensitive config, `marep/` | 228 |
| MOVE | 92 |

Revision 3 reported 318 and 0 unassigned. Both were wrong: it read
`git ls-tree HEAD`, which misses staged additions, so the builder omitted
**itself and its own output**. It now reads `git ls-files`.

### Four builder defects, fixed

| defect | fix |
|---|---|
| wrote the manifest **before** returning failure, so a rejected run could overwrite a good one | returns before writing; writes atomically via `os.replace` — verified by forcing an UNASSIGNED and confirming the 320-entry manifest survived |
| prefix-stripping produced `…/moral-epistemics/.ttl` — hidden, extension-only names | explicit per-file mapping; a validator rejects empty basenames, changed extensions, undeclared renames, collisions, absolute paths and `..` |
| every test got the placeholder `REORGANIZE-IN-PLACE`, so a misfiled test was undetectable | each of the 22 test modules has an exact destination |
| git calls ignored exit status | `sh()` raises; `upstream/main` is verified to resolve before classification |

The validator earned its place immediately: it caught the *same* basename bug in
the MAREP rules that review found in the BFO ones — `MAREP_v2.1.md` was becoming
`docs/marep/specifications/1.md`. Directory prefixes and name prefixes are now
separate rule sets.

### Test destinations, explicit

| group | modules |
|---|---:|
| `tests/marep/` | 6 |
| `tests/marep/ontology/` | 5 |
| `tests/bfo/` | 6 |
| `tests/original-valuenet/` | 3 |
| `tests/integration/` | 1 |
| `tests/conftest.py` | 1 |

### Two-axis provenance

The single axis conflated independent facts. `bfo-core.ttl` is external BFO,
unchanged. The CCO extract is external CCO, generated. `folk_aligned.ttl` is
upstream-derived content, generated.

```
origin          : upstream-valuenet | fork | external-bfo | external-cco
maintenance     : unchanged | locally-modified | generated
generated_from  : optional component id
```

| origin | maintenance | files |
|---|---|---:|
| upstream-valuenet | locally-modified | 145 |
| fork | unchanged | 114 |
| upstream-valuenet | unchanged | 56 |
| external-cco | generated | 2 |
| external-bfo | unchanged | 1 |

### Rename-following, with an asserted limit

`git log --follow` recovers `wvs.owl → wvs.ttl`. It cannot recover two others,
because the edit exceeded git's similarity threshold: `folk.owl → folk.ttl`
rewrote every line converting RDF/XML to Turtle, and
`folk_Belief.ttl → folk_Religion.ttl` retargeted 623 statements. Both are
asserted in `KNOWN_UPSTREAM_DESCENT` with their reason, because the alternative
is a classifier that silently calls upstream content fork-authored and moves it.

### The upstream rule is now absolute

*Anything whose origin is `upstream-valuenet` is retained at its current path,
whatever its maintenance state, including documentation assets.*

That settles `ValueNet_stats.txt`, both `.png` diagrams, and `wvs.ttl` — all
stay. They are indexed from the new documentation rather than relocated.

### Semantic baseline: digests, not counts

Counts cannot distinguish two graphs of equal size. The baseline records
canonical RDF digests via `rdflib.compare.to_canonical_graph` over sorted
N-Triples, with each metric's definition and the command that produced it.

The load-bearing case: `ThatsAllFolks/folk.ttl` and `folk_aligned.ttl` have
**identical canonical digests** while their byte hashes differ. The full digest,
stored in the machine-readable baseline rather than abbreviated, is
`850e9340b81ecd324b0935abe5b0ff2913e1db8b7f963b712900068e57277289`. `folk_aligned.ttl`'s byte hash is
`047db3158bbf58b2e7848fe5bdea5eb34f5252b177a1ee9c01608514a2b5b525` and **must
change** when the generator moves, because the file header embeds the
generator's path. The canonical digest must not. That is the invariant; the byte
hash is a recorded, justified transition.

### Query scopes become logical component identifiers

Revision 2 moved `BFO/` at step 5 and fixed `# scope: BFO/` declarations at
step 8, leaving competency queries loading nothing for three commits. Scopes
convert to `# scope: component:bfo-query-suite` during path abstraction, before
anything moves.

### Test ownership by what a module tests, not when it was written

`test_commitments.py`, `test_constraint_metrics.py`, `test_duplication_metrics.py`
and `test_reasoner_scope.py` primarily exercise MAREP code and belong under
`tests/marep/ontology/`. `test_ontology_source.py` splits into MAREP unit tests
and live-repository integration tests.

---

## The examples hazard, in full

`.gitignore` protects exactly `examples/_run/`. All eight examples compute their
output directory relative to their own file and their repository root as
`Path(__file__).resolve().parents[1]`.

Moving them to `examples/marep/` breaks both at once: runs write to
`examples/marep/_run/`, which nothing ignores, and `parents[1]` resolves to
`examples/` rather than the repository root. The current run directory holds
**1,127,251 bytes** of state, inputs and logs.

Required before the examples move, in order:

1. add `.gitignore`, `pytest.ini`, root `README.md` and any CI config to the inventory;
2. introduce manifest-backed repository-root and run-artifact paths;
3. update all eight examples to use them;
4. widen the ignore to `examples/**/_run/`, keeping the existing rule during migration;
5. add a `git check-ignore` test for `examples/marep/_run/probe.yaml`;
6. verify a run leaves no untracked artefact.

---

## Target structure

```text
ontology/
  bfo/
    core/                   valuenet-core, folk, schwartz-values, mappings
    extensions/
      moral-foundations/
      moral-epistemics/     module, scenario, CQ document
      trigger-semantics/    vcvf-triggers-semantics
    shapes/                 core-shapes, moral-epistemics-shapes,
                            vcvf-triggers-shapes
    vendor/
      bfo/                  bfo-core.ttl
      cco/                  cco-valuenet-extract + manifest

docs/
  architecture/             this plan, layout contract, provenance index
  original-valuenet/        index of the retained legacy corpus (assets stay put)
  bfo/
    guides/                 annotationGuide, Phase4_LinguisticGrounding,
                            TestingFramework, BFOizing ValueNet, RefactorPlan,
                            vcvf-triggers-review, Phase1 term documents
    remediation/            PHASE*.md, DECISION_RECORDS, BASELINE,
                            SOURCE_SELECTION, EXTERNAL_TERM_INVENTORY, plan
  marep/
    specifications/         MAREP_v2.1, MAREP_v2.2
    plans/                  MAREP_VALUENET_PLAN, MAREP_IMPLEMENTATION_PLAN
    runs/                   RUN{1,2,3}_FINDINGS, RECONCILIATIONs, HYPOTHESES

tools/
  original-valuenet/        folk repair, diagnosis, retargeting, declaration
                            and generation tools
  bfo/                      generate_cco_extract, check_bfo_consistency,
                            extract-manifest.schema.json
  marep/                    report_run, build_move_manifest

marep/                      framework implementation (reorganize in place)
examples/marep/             the eight example programs, path-corrected

tests/
  marep/                    runtime, adjudicator, agents, ingest, resume,
                            grounding_strength
    ontology/               commitments, constraint_metrics,
                            duplication_metrics, reasoner_scope,
                            ontology_source (unit half)
  original-valuenet/        ontology_artifacts, folk_generation, trigger_shapes
  bfo/                      alignment_remediation, cco_extract,
                            core_definitions, external_closure,
                            mapping_semantics, moral_epistemics_categories
  integration/              competency_questions, ontology_source (live half)
  _support.py               importable constants and helpers
  conftest.py               fixtures only

config/
  repository-layout.yaml    the layout contract
  move-manifest.yaml        generated; 318 files, 0 unassigned
```

**Retained at current paths:** `ThatsAllFolks/`, `MFTriggers/`,
`MoralMolecules/`, `vale2024/`, all root `.ttl` files including `wvs.ttl`, both
`.png` diagrams, `ValueNet_stats.txt`, `.gitignore`, `pytest.ini`, `README.md`.

---

## Path coupling to centralize first

Layout is hardcoded in three independent modules:

- `marep/ontology_source.py` — `GROUPS`
- `marep/competency.py` — `QUERY_DOCS`
- `ValueNet_code/generate_folk_aligned.py` — `SOURCE` / `TARGET`

and **20 code and test files** hardcode a corpus path. Moving before
centralizing means editing 20 files under a broken tree.

---

## Migration sequence

Separate commits throughout. **No semantic ontology edit is combined with a
relocation.**

1. **Inventory** every tracked file and every path-sensitive configuration file,
   probing `.github/workflows`, `pyproject.toml`, `tox.ini`, `setup.cfg` rather
   than assuming none appears later.
2. **Two-axis provenance and the complete move manifest.** Gate: 0 unassigned.
3. **Layout schema, resolver, logical component identifiers, machine-readable
   semantic baseline.** Nothing moves.
4. **Adopt the resolver** in examples, query scopes, generators, tools, MAREP
   loaders and tests.
5. **Normalize test support** — `tests/_support.py` for importable constants and
   helpers, fixtures staying in `conftest.py`, all **six** `from conftest import`
   statements replaced across five modules (`test_runtime.py` has a second at
   line 50), `parents[1]` roots replaced by the resolver.
6. **Contract tests** for configured paths, ignore rules, provenance
   classification, move coverage, and semantic fingerprints.
7. **Move BFO** artifacts with their path metadata, atomically.
8. **Move MAREP** documents, tools and the corrected examples.
9. **Reorganize tests** by actual ownership, with an explicit integration group.
10. **Update documentation links**, then run the full verification gate.

The gate runs after **every** move commit, not only at the end.

### Why the gate is per-commit

An hour before revision 2 was written, `reasoner_metrics` silently dropped from
**306 classes to 275** because the CCO extract landed in a directory its
hardcoded file list did not know about. HermiT stayed consistent. Every test
stayed green. The reasoner was simply checking less.

A move that changes *what gets loaded* looks exactly like a move that changed
nothing.

### The gate

| invariant | value | definition |
|---|---|---|
| files discovered / parsing | 168 / 168 | `ontology_source.discover` then `measure_file` |
| distinct triples | 104,763 | merged corpus graph |
| distinct **named** classes | 2,889 | `owl:Class` subjects that are `URIRef` |
| per-file class declarations | 5,402 | sum over files; double-counts by design |
| `vcvf:triggers` statements | 57,578 | merged corpus |
| distinct trigger objects | 147 | objects of `vcvf:triggers` |
| BFO-layer classes | 306 | HermiT scope, including `BFO/imports/` |
| BFO-layer imports unresolved | 0 | `_unresolved_imports` |
| canonical digest, folk pair | `850e9340…57277289` | identical for source and generated; full value in the baseline |
| tests collected | 539 | 534 selected, 5 deselected |
| manifest coverage | 320 / 0 unassigned | `build_move_manifest.py` exits 0 |

Plus, after every move commit: every ontology file parses standalone; offline
imports resolve; generators deterministic; CCO extract reproducible to its
SHA-256; all nine competency and sanity queries pass; both HermiT scopes
consistent with 0 unsatisfiable; trigger SHACL conforms; no stale path outside
the manifest.

---

## Risks

**Upstream divergence.** 53 ahead, 0 behind. Retaining upstream-derived paths
keeps that mergeable. Moving repaired upstream files would raise conflict risk
but not guarantee a conflict in every file — git rename detection can merge some
cleanly. The risk is real and unquantified, which is reason enough not to take
it for tidiness.

**The manifest becomes a second hardcoded layout.** Mitigated by the step 6
contract test that no module outside the resolver hardcodes a corpus path. That
test needs a documented allowlist: the manifest builder itself, generated-file
headers that embed their generator's path, and intentional compatibility
strings.

**Documentation link rot.** Roughly 30 cross-references between markdown
documents. Step 10 owns the update; a link check belongs in the gate.

---

## Out of scope

Vocabulary governance, near-synonym adjudication, definition quality, the
`mft:NegativeValue` wording, the nine `SENSE-001` capitalised targets, and the
ontology versioning scheme. **This plan moves files and changes no meaning.**
