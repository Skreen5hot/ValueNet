# Path-sensitive inventory — reorganization step 1

Produced 2026-08-25 against `8d9c414`. Nothing has moved.

Step 1 exists because a `.py`/`.ttl` sweep cannot see configuration. `.gitignore`
was missed by two drafts of the plan, and moving `examples/` without it would
have begun committing 1,127,251 bytes of generated run state.

---

## Configuration probe

Probed for every file the plan names plus the usual suspects.

| file | present | encodes a path |
|---|---|---|
| `.gitignore` | yes | **yes** — `examples/_run/` at line 4 |
| `pytest.ini` | yes | no — markers and `addopts` only; no `testpaths` |
| `README.md` | yes | **yes** — 17 relative links |
| `pyproject.toml` | no | — |
| `tox.ini` | no | — |
| `setup.cfg` | no | — |
| `setup.py` | no | — |
| `Makefile` | no | — |
| `.editorconfig` | no | — |
| `.pre-commit-config.yaml` | no | — |
| `.github/workflows/` | **absent** | — |

**No CI configuration exists.** The plan's instruction to probe rather than
assume was right, and the probe is recorded here so a later addition is a
visible change rather than a silent one.

`pytest.ini` carries no `testpaths`, so the step 11 test moves do not require
editing it. It stays at the repository root and is classified `RETAIN`.

---

## Correction to the plan

The plan estimates **"roughly 30 cross-references between markdown documents."**
Measured: **18 relative links across 2 documents.**

| document | relative links |
|---|---:|
| `README.md` | 17 |
| `BFO/vcvf-triggers-review.md` | 1 |

The remediation records under `BFO/remediation/` reference each other by
filename in prose rather than as markdown links, so they carry none. The link
surface is smaller than assumed and concentrated almost entirely in one file.

That does not reduce the work — the README's 17 links point at `BFO/` paths that
the BFO wave moves, so they must travel with it — but it does mean the step 12
repository-wide check is verifying a much smaller surface than the plan implies.

### README link targets, by destination wave

| target | links | wave that moves it |
|---|---:|---|
| `BFO/…` ontology modules, shapes, scenario, CQ | 12 | BFO (step 7) |
| `BFO/` directory and guides | 3 | BFO (step 7) |
| `MFTriggers/` | 1 | none — `RETAIN` |
| other | 1 | — |

---

## Tracked-file inventory

Derived by `build_move_manifest.py`, not by hand.

| | count |
|---|---:|
| tracked files | 320 |
| RETAIN | 228 |
| MOVE | 92 |
| UNASSIGNED | **0** |

Provenance, two axes:

| origin | maintenance | files |
|---|---|---:|
| upstream-valuenet | locally-modified | 145 |
| fork | unchanged | 114 |
| upstream-valuenet | unchanged | 56 |
| external-cco | generated | 2 |
| external-bfo | unchanged | 1 |

---

## Step 1 gate

- [x] every path-sensitive configuration file probed and recorded
- [x] `.gitignore` identified as the one ignore rule requiring widening
- [x] `pytest.ini` confirmed to carry no `testpaths`
- [x] absence of CI configuration recorded as a fact, not an assumption
- [x] documentation link surface measured rather than estimated
- [x] working manifest regenerated: 320 tracked, 0 unassigned, exit 0
- [x] this inventory given an explicit `RETAIN` disposition in the same commit
