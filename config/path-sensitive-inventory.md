# Path-sensitive inventory — reorganization step 1

Produced 2026-08-25. Corrected after review. Nothing has moved.

Step 1 exists because a `.py`/`.ttl` sweep cannot see configuration. `.gitignore`
was missed by two drafts of the plan, and moving `examples/` without it would
have begun committing 1,127,251 bytes of generated run state.

The first version of this document repeated that class of error at smaller
scale: it globbed `*.md`, `BFO/*.md` and `BFO/remediation/*.md`, and so missed
`marep/README.md`. Every count below is now repository-wide.

---

## Configuration probe

| file | present | encodes a path |
|---|---|---|
| `.gitignore` | yes | **yes** — `examples/_run/` at line 4 |
| `pytest.ini` | yes | no — markers and `addopts` only; no `testpaths` |
| `README.md` | yes | **yes** — 18 relative link occurrences |
| `pyproject.toml` | no | — |
| `tox.ini` | no | — |
| `setup.cfg` | no | — |
| `setup.py` | no | — |
| `Makefile` | no | — |
| `.editorconfig` | no | — |
| `.pre-commit-config.yaml` | no | — |
| `.github/workflows/` | **absent** | — |

**No CI configuration exists.** Recorded so a later addition is a visible change
rather than a silent one.

`pytest.ini` carries no `testpaths`, so the step 11 test moves do not require
editing it. It stays at the repository root, classified `RETAIN`.

---

## Documentation links

Occurrences and distinct targets are different measures and are reported
separately. The plan estimated "roughly 30 cross-references."

| document | occurrences | distinct targets | wave that must update it |
|---|---:|---:|---|
| `README.md` | 18 | 17 | bfo (step 7) — 16 occurrences point at `BFO/` |
| `BFO/vcvf-triggers-review.md` | 1 | 1 | bfo (step 7) |
| `marep/README.md` | 1 | 1 | **marep (step 8)** — `../MAREP_v2.2.md` |
| **total** | **20** | **19** | |

Of the 20 occurrences, 19 are path-bearing and one is an internal anchor;
**18 require updating during moves.**

`marep/README.md → ../MAREP_v2.2.md` was missed by the first version of this
inventory. Its target moves to `docs/marep/specifications/MAREP_v2.2.md` in wave
8, while `marep/README.md` itself is `RETAIN` — so this is a link that must be
rewritten in a file that does not move, which is exactly the case a
directory-oriented sweep overlooks.

The remediation records under `BFO/remediation/` reference each other by
filename in prose rather than as markdown links, so they carry none.

---

## Path-bearing metadata outside markdown

Not links, and not code, but they name paths and will read falsely after the
moves. Recorded here so each becomes a decision rather than a discovery.

| location | value | disposition |
|---|---|---|
| `BFO/imports/cco-valuenet-extract.manifest.json` → `generated_by.script` | `BFO/remediation/generate_cco_extract.py` | must be regenerated in wave 7, when the generator moves to `tools/bfo/` |
| `MAREP_RUN1_RECONCILIATION.yaml` | `examples/_run/RUN1_STATE.yaml`, `tests/test_ontology_artifacts.py` | **historical record** — a justified allowance, not rewritten |
| `MAREP_RUN3_RECONCILIATION.yaml` | `examples/_run/RUN3_STATE.yaml` | **historical record** — a justified allowance, not rewritten |

The distinction matters. The CCO manifest asserts where its generator *is*, so a
stale value is a lie. The reconciliation files record where a file *was* when a
run observed it, so rewriting them would falsify the audit trail the whole
reconciliation model depends on. Both go in the step 6 allowlist with those
justifications.

---

## Tracked-file inventory

Derived by `build_move_manifest.py`, not by hand. Two snapshots, because this
document is itself a tracked file and conflating them is how the first version
claimed 320 while asserting it had counted itself.

| | before step 1 | after step 1 |
|---|---:|---:|
| tracked files | 320 | **321** |
| RETAIN | 228 | **230** |
| MOVE | 92 | **91** |
| UNASSIGNED | 0 | **0** |

The move count *fell* by one while a file was added. `tests/conftest.py` had been
emitted as `tests/conftest.py` — a same-path row, counted as a move and assigned
to the tests wave. It is `RETAIN`, and the validator now rejects any row whose
destination equals its source.

### Provenance, after step 1

| origin | maintenance | files |
|---|---|---:|
| upstream-valuenet | locally-modified | 145 |
| fork | unchanged | 116 |
| upstream-valuenet | unchanged | 56 |
| external-cco | generated | 2 |
| external-bfo | unchanged | 1 |
| fork | generated | 1 |
| **total** | | **321** |

### Migration waves, after step 1

| wave | rows |
|---|---:|
| bfo | 42 |
| tests | 21 |
| marep | 20 |
| original-valuenet | 7 |
| architecture | 1 |
| **total** | **91** |

---

## Step 1 gate

- [x] every path-sensitive configuration file probed and recorded
- [x] `.gitignore` identified as the one ignore rule requiring widening
- [x] `pytest.ini` confirmed to carry no `testpaths`
- [x] absence of CI configuration recorded as a fact, not an assumption
- [x] documentation links measured repository-wide, occurrences and distinct
      targets reported separately
- [x] path-bearing metadata outside markdown recorded, with rewrite-or-allow
      dispositions
- [x] pre-step and post-step tracked-file snapshots kept distinct
- [x] provenance table sums to the tracked total
- [x] working manifest regenerated: 321 tracked, 230 retain, 91 move, 0
      unassigned, exit 0
