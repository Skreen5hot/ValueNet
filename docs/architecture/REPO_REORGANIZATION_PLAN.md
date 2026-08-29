# Repository reorganization — plan for approval

**Status:** revision 5, final sign-off candidate; conferral correction
incorporated. Nothing has moved. No semantic ontology change is in scope.

Revision 4 corrected the manifest builder and closed the known mapping defects.
Revision 5 closes the remaining execution-control gaps: it distinguishes the
current planning snapshot from the frozen pre-move baseline, defines the
manifest's lifecycle, makes validation transition-aware, and replaces the stale
fixed test-count invariant with a two-baseline rule. Every factual correction in
the prior reviews was independently checked against the repository before
adoption.

---

## Decision summary

This is a **hybrid physical reorganization**:

- Original ValueNet material whose origin is `upstream-valuenet` stays at its
  upstream-compatible path, including locally repaired ontologies and unchanged
  documentation assets.
- Fork-authored Original ValueNet repair and generation utilities move to
  `tools/original-valuenet/`; this does not move their upstream-derived inputs.
- Fork-authored BFO ValueNet, moral-extension, shape, vendor, tool and
  remediation artifacts move under `ontology/bfo/`, `tools/bfo/` and
  `docs/bfo/`.
- The MAREP implementation remains under `marep/`; its documents, tools and
  examples move under `docs/marep/`, `tools/marep/` and `examples/marep/`.
- Tests move into BFO, MAREP, Original ValueNet and integration ownership
  groups only after shared support and repository paths are normalized.

The reorganization changes layout and path metadata, not ontology meaning.

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

## What changed in revision 5

Five controls are now explicit and are approval conditions rather than implied
implementation details:

1. **320 / 228 / 92 is the current builder snapshot, not the final move
   invariant.** One of those 92 rows is the no-op
   `tests/conftest.py → tests/conftest.py`; step 2 reclassifies it as `RETAIN`
   and adds a validator rule forbidding identical source and destination paths.
   Preparatory commits then add the layout contract, baseline and contract
   tests, so the working manifest is regenerated after each preparatory commit
   through step 6.
2. **The manifest is frozen exactly once.** After step 6 passes, the generated
   manifest and machine-readable baseline are committed and that commit is
   tagged `reorg-pre-move-v1`; the gate logs the tag's resolved full commit id.
   They are inputs to the move steps and are not reclassified from the partially
   moved tree.
3. **Validation understands partial migration.** For every frozen `MOVE` entry,
   exactly one of source or destination must be tracked; for every `RETAIN`
   entry, the original path must remain tracked. Every tracked file must be
   represented, and destinations must remain unique and safe.
4. **Test counts use two baselines.** The independently verified original suite
   remains 539 collected / 534 selected / 5 deselected. After support
   normalization, contract-test additions and the `test_ontology_source.py`
   split, step 6 freezes a new pre-move collection count and normalized test-id
   set. Every physical move must preserve that frozen set.
5. **No stale final file count is asserted early.** The target tree records the
   manifest as generated and frozen after step 6; its final count is whatever
   the clean pre-move tracked tree contains at that gate.

These controls resolve the final review findings without changing the hybrid
layout decision or the move classification.

**Sign-off correction:** `tests/` remains a non-package. Step 5 adds only
`tests/_support.py` and imports it as `from _support import …`. It does not add
`tests/__init__.py`, because doing so changes collection semantics and makes the
existing top-level `conftest` imports fail before their replacement.

---

## Revision 4 foundation retained

### A generated manifest replaces the hand-written destination list

`ValueNet_code/build_move_manifest.py` derives `config/move-manifest.yaml` from
`git ls-files` and rename history. It **refuses to emit an incomplete manifest**
— it returns before writing while any file is `UNASSIGNED` or any destination is
malformed. Hand-listing missed six files; deriving closed them.

Coverage: **320 tracked files, 0 unassigned, 0 malformed.**

| disposition | files |
|---|---:|
| RETAIN — upstream-derived, path-sensitive config, `marep/` | 228 |
| destination rows currently reported as MOVE | 92 |

One of the 92 is `tests/conftest.py → tests/conftest.py`. Revision 5's step-2
validator treats that as a malformed no-op and reclassifies it as `RETAIN`
before assigning waves.

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

That table is the 22-module planning snapshot. Before the freeze, the
ontology-source split and three contract modules replace it with a larger exact
mapping; the builder must reject any new test without a declared destination.

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

Counts cannot distinguish two graphs of equal size. The step 3 baseline records
canonical RDF digests via `rdflib.compare.to_canonical_graph` over sorted
N-Triples, with each metric's definition and the command that produced it.

The load-bearing case: `ThatsAllFolks/folk.ttl` and `folk_aligned.ttl` have
**identical canonical digests** while their byte hashes differ. The full digest,
to be stored in the machine-readable baseline rather than abbreviated, is
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
  architecture/             this plan, layout/provenance index and execution
                            guidance
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
                            ontology_source_unit
  original-valuenet/        ontology_artifacts, folk_generation, trigger_shapes
  bfo/                      alignment_remediation, cco_extract,
                            core_definitions, external_closure,
                            mapping_semantics, moral_epistemics_categories
  integration/              competency_questions,
                            ontology_source_integration,
                            repository_layout_contract,
                            reorganization_manifest, semantic_baseline
  _support.py               importable constants and helpers
  conftest.py               fixtures only

config/
  repository-layout.yaml    the layout contract
  reorganization-baseline.json
  move-manifest.yaml        generated; frozen after the step 6 pre-move gate
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

## Manifest and baseline lifecycle

The manifest has three deliberately different states. Treating them as one was
the source of the stale completeness claim.

### 1. Planning snapshot — current

The checked-in manifest describes the repository as it exists for approval:
**320 tracked, 228 `RETAIN`, 92 destination rows, 0 unassigned**. It proves that
every current file has a disposition. It is not yet the input to `git mv`:
`tests/conftest.py` is a same-path destination and must become `RETAIN`, leaving
91 actual moves before preparatory files alter the counts.

### 2. Working pre-move manifest — steps 1 through 6

The builder is rerun after every preparatory commit. New layout, baseline,
support and contract-test files must be given explicit dispositions in the same
commit that introduces them. A catch-all test destination is forbidden. Every
run must exit zero before the next preparatory step begins.

Each actual `MOVE` row also gains exactly one explicit migration wave. The
assignment is stored in the row; execution never infers it from the path.

| wave | permitted destination prefixes |
|---|---|
| `bfo` | `ontology/bfo/`, `docs/bfo/`, `tools/bfo/` |
| `marep` | `docs/marep/`, `tools/marep/`, `examples/marep/` |
| `original-valuenet` | `tools/original-valuenet/` |
| `architecture` | `docs/architecture/` |
| `tests` | `tests/marep/`, `tests/bfo/`, `tests/original-valuenet/`, `tests/integration/` |

This makes the examples assignment unambiguous: `examples/ → examples/marep/`
is the MAREP wave. The step-2 gate reports each wave's count and mechanically
asserts that their sum equals the number of non-no-op `MOVE` rows, with no row
omitted or assigned twice. A source equal to its destination is malformed and
must be `RETAIN`, not assigned a wave.

Applied read-only to the current manifest, those prefix constraints partition
all 91 actual moves with 0 unmatched: **BFO 42, MAREP 20, Original ValueNet 7,
architecture 1, tests 21**. These are planning counts only; step 2 stores the
assignments explicitly, and step 6 freezes the counts after preparatory files
have been added.

### 3. Frozen pre-move manifest — after step 6

With a clean worktree, generate and commit:

- `config/move-manifest.yaml`, containing every tracked source, its exact
  destination or `RETAIN`, provenance axes, generator and migration wave;
- `config/reorganization-baseline.json`, containing the semantic fingerprints,
  test baselines, tool versions and commands needed to reproduce them; and
- `config/repository-layout.yaml`, containing logical component identifiers and
  resolved paths.

Tag that commit `reorg-pre-move-v1`. The baseline records that stable ref; the
CI/reviewer execution record logs the full commit id to which it resolves before
the first move without adding another tracked file. This avoids the
self-reference problem of trying to write a commit's own not-yet-known id into
that commit.

From step 7 onward, the frozen manifest is **read, never regenerated or
reclassified**. Regeneration against a half-moved tree would turn completed
destinations into new sources and destroy the audit trail.

### Transition-state validation

After each move commit, validation is against the frozen manifest:

- for every `MOVE` row, exactly one of its source or destination is tracked;
- for every `RETAIN` row, its original path is tracked and no destination is
  permitted;
- every tracked file is represented exactly once;
- no two rows resolve to the same destination;
- no path is absolute, contains `..`, has an empty basename, changes extension,
  equals its source, or performs an undeclared rename; and
- completed rows are in the current or an earlier migration wave; pending rows
  are in a later wave.

The validator must remain callable after its own move from `ValueNet_code/` to
`tools/marep/`. A forced unassigned row, collision, missing source, duplicate
source-and-destination pair, identical source and destination, and failed Git
command are negative contract tests; each must return non-zero without replacing
the frozen manifest.

---

## Migration sequence

Separate commits throughout. **No semantic ontology edit is combined with a
relocation.**

1. **Inventory** every tracked file and every path-sensitive configuration file,
   probing `.github/workflows`, `pyproject.toml`, `tox.ini`, `setup.cfg` rather
   than assuming none appears later. Regenerate the working manifest.
2. **Two-axis provenance and working manifest.** Recheck all rename descent,
   give every current file an exact disposition, and assign every move to one
   migration wave. Reclassify the same-path `tests/conftest.py` row as `RETAIN`.
   Gate: 0 unassigned, 0 malformed or no-op moves, per-wave counts reported, and
   wave partition complete.
3. **Layout contract, resolver and baseline machinery.** Add
   `config/repository-layout.yaml`, the transition-state validator, logical
   component identifiers, reproducible semantic-fingerprint generation, and
   the human-readable architecture/provenance and Original ValueNet indexes
   named in the target tree. The layout contract includes a structured
   `path_allowances` list; every entry has an id, matched string or pattern,
   category, justification, owner, and either `permanent: true` or a
   `remove_after_wave`. Every new tracked document is created before the freeze
   and explicitly classified. Nothing moves. Regenerate the working manifest.
4. **Adopt the resolver** in examples, query scopes, generators, tools, MAREP
   loaders and tests. Add `examples/**/_run/` while retaining
   `examples/_run/`; verify both old and new run locations are ignored.
   Regenerate the working manifest.
5. **Normalize test support and split mixed ownership.** Add only
   `tests/_support.py`; do not add `tests/__init__.py`. Import constants and
   helpers as `from _support import …`, using the same rootdir insertion that
   currently makes top-level `conftest` importable, while keeping fixtures only
   in `conftest.py`. Replace all **six** `from conftest import` statements across
   five modules (`test_runtime.py` has a second at line 50), and replace
   `parents[1]` roots with the resolver. Give `_support.py` an explicit retained
   disposition. Split `test_ontology_source.py` into the uniquely named
   `test_ontology_source_unit.py` and `test_ontology_source_integration.py`
   before the manifest is frozen, and add exact mappings for both. Regenerate
   the working manifest.
6. **Contract tests and freeze.** Add the uniquely named
   `test_repository_layout_contract.py`, `test_reorganization_manifest.py` and
   `test_semantic_baseline.py` for configured paths, ignore rules, provenance
   classification, move and wave coverage, transition states, fail-closed
   manifest writes, stable test identities and semantic fingerprints. Give each
   an exact integration destination. Populate the structured path allowlist and
   test that every exception matches an intentional occurrence, every occurrence
   is covered, overlapping entries fail, justifications are non-empty, and an
   allowance fails after its removal wave. Regenerate the manifest, capture the
   new pre-move test baseline, pass the full gate, commit the three configuration
   artifacts, tag the commit `reorg-pre-move-v1`, and record its resolved commit
   id. This is the last generation of the manifest.
7. **Move the BFO wave** — ontology modules, vendor extracts, BFO tools and BFO
   documentation — with their path metadata and links in one atomic commit.
8. **Move the MAREP wave** — specifications, plans, run records, MAREP tools and
   corrected examples — with their path metadata and links atomically.
9. **Move the Original ValueNet wave** — fork-authored repair and generation
   tools only. No upstream-origin file moves.
10. **Move the architecture wave** — this plan and the architecture documents —
    with their links updated atomically.
11. **Move the tests wave** to the frozen exact destinations. This is relocation
    only: the split and support refactor were completed before the freeze.
12. **Final integration and documentation pass.** Run the allowance-lifecycle
    check: every temporary entry whose removal wave has completed must be gone;
    every remaining permanent entry must still match an occurrence and retain
    its justification and owner. Check all links and run the full verification
    gate.

The gate runs after **every** move commit, not only at the end.

### Why the gate is per-commit

An hour before revision 2 was written, `reasoner_metrics` silently dropped from
**306 classes to 275** because the CCO extract landed in a directory its
hardcoded file list did not know about. HermiT stayed consistent. Every test
stayed green. The reasoner was simply checking less.

A move that changes *what gets loaded* looks exactly like a move that changed
nothing.

### Approval snapshot

The semantic values below remain invariants throughout preparation and moves.
Their definitions and reproduction commands are stored in the machine-readable
baseline rather than inferred from labels.

| invariant | value | definition |
|---|---|---|
| files discovered / parsing | 168 / 168 | `ontology_source.discover` then `measure_file` |
| distinct triples | 104,763 | merged corpus graph |
| distinct **named** classes | 2,889 | `owl:Class` subjects that are `URIRef` |
| per-file class declarations | 5,402 | sum over files; double-counts by design |
| `vcvf:triggers` statements | 57,578 | merged corpus |
| distinct trigger objects | 147 | objects of `vcvf:triggers` |
| BFO-layer classes | 306 | HermiT scope, including the configured CCO extract |
| BFO-layer imports unresolved | 0 | `_unresolved_imports` |
| canonical digest, folk pair | `850e9340b81ecd324b0935abe5b0ff2913e1db8b7f963b712900068e57277289` | source and generated graphs are identical |

The following are **current planning evidence**, not numbers to copy blindly
into the move gate:

| planning measure | current value | treatment before moves |
|---|---:|---|
| tests | 539 collected; 534 selected (532 passed, 2 skipped); 5 deselected | preserve coverage through preparation, then replace with the step 6 frozen baseline |
| manifest | 320 tracked; 228 retain; 92 destination rows, including 1 same-path no-op; 0 unassigned | reclassify the no-op, regenerate through step 6, then freeze the resulting count |

### Frozen test identity

Step 6 stores the complete collected node-id list and its SHA-256. For comparison
across directory moves, the canonical id is the test module's basename plus the
remainder of its pytest node id, including class, function and parameter id. The
pre-freeze split gives the two ontology-source modules unique basenames. The
collector rejects canonical-id collisions. After the freeze, both the collected
count and canonical-id set are exact invariants; pass count alone is
insufficient.

### Gate after every move commit

Every move wave must satisfy all of the following before the next begins:

- transition-state manifest validation passes against `reorg-pre-move-v1`;
- frozen tracked-file coverage and frozen test count/id set are unchanged;
- every ontology file parses standalone and the semantic table above matches;
- offline imports resolve and both HermiT scopes are consistent with 0
  unsatisfiable classes;
- generators are deterministic, the CCO extract reproduces to its SHA-256, all
  nine competency and sanity queries pass, and trigger SHACL conforms;
- `git check-ignore` protects both migration-era example run paths, an example
  run leaves no untracked artefact, and no stale path exists outside the
  structured allowlist;
- the allowance-lifecycle check rejects unmatched, overlapping, unjustified or
  expired entries for the completed wave; and
- documentation links touched by the wave resolve, with the full link check
  passing at the final gate.

---

## Execution control and rollback

Every migration wave starts from a clean worktree and is one reviewable commit.
`git mv` preserves history; path-reference and compatibility updates required by
that wave travel in the same commit. RDF comments or headers may change only
where path metadata requires it; canonical graph fingerprints must not.

A failed gate stops execution. No later wave begins while a failure is open.
The team either fixes the same wave and reruns the gate or reverts that whole
wave with a normal revert commit. It does not rewrite published history.

Adding or deleting a tracked file after the freeze is not an ordinary move. It
requires pausing execution, documenting the reason, amending and refreezing the
manifest under a new tag, and obtaining renewed approval. An upstream fetch may
inform review but must not change the provenance base during an active run.

Immediate stop conditions are: an unresolved or multiply assigned manifest
row; a changed canonical test-id set; a semantic fingerprint mismatch; a newly
unresolved import; a reasoner scope reduction; a failed query or SHACL gate; an
unignored generated run artefact; or an unapproved hardcoded path.

---

## Risks

**Upstream divergence.** 53 ahead, 0 behind. Retaining upstream-derived paths
keeps that mergeable. Moving repaired upstream files would raise conflict risk
but not guarantee a conflict in every file — git rename detection can merge some
cleanly. The risk is real and unquantified, which is reason enough not to take
it for tidiness.

**The manifest becomes a second hardcoded layout.** Mitigated by the step 6
contract test that no module outside the resolver hardcodes a corpus path. That
test uses the structured allowance list for the manifest builder itself,
generated-file headers that embed their generator's path, and intentional
compatibility strings. Zero-match, overlapping, unjustified and expired entries
fail, so the allowlist cannot silently become a stale-path archive.

**Documentation link rot.** Roughly 30 cross-references between markdown
documents. Each wave owns links it touches; step 12 owns the repository-wide
check.

---

## Sign-off decision

Approval of revision 5 means the reviewers accept:

1. the hybrid rule: every `upstream-valuenet` path remains where upstream keeps
   it, while fork-authored BFO, MAREP, tooling, test and architecture material
   moves to the target structure;
2. the two-axis provenance model and the known-descent assertions for the two
   renames Git cannot infer;
3. the current 320-file manifest as complete **planning evidence**, with the
   final move manifest intentionally regenerated and frozen only after all
   preparatory files exist;
4. the original 539-test result as the review baseline, with the step 6 frozen
   count and canonical-id set becoming the relocation invariant;
5. the five atomic migration waves and the per-wave semantic, reasoner, query,
   SHACL, generator, path, ignore, link and test gates; and
6. the stop-and-refreeze rule for any post-freeze tracked-path addition,
   deletion or relocation outside the approved source-to-destination rows.

No physical move is authorized until steps 1–6 are complete, the working tree
is clean, the manifest has 0 unassigned and 0 malformed or same-path rows, every
actual move belongs to exactly one wave, the full verification gate passes, and
`reorg-pre-move-v1` resolves to the reviewed freeze commit. Meeting those
conditions is the execution sign-off gate; failure of any one blocks step 7.

---

## Out of scope

Vocabulary governance, near-synonym adjudication, definition quality, the
`mft:NegativeValue` wording, the nine `SENSE-001` capitalised targets, and the
ontology versioning scheme. **This plan moves files and changes no meaning.**
