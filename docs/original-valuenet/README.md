# Original ValueNet — index

The Original ValueNet corpus is **not relocated** by the repository
reorganization. Its files stay at the paths `upstream/main` uses, so the fork
remains mergeable. This index tells you where they are; it does not move them.

`main` is 53 commits ahead of upstream and 0 behind.

---

## Why these paths do not move

145 of these files are upstream-derived and locally repaired. Relocating them
would raise conflict risk on every future merge from
`StenDoipanni/ValueNet`, in exchange for a tidier tree. The reorganization takes
the opposite trade: fork-authored material moves, upstream-derived material
stays, and the boundary is recorded as data in `config/move-manifest.yaml`
rather than implied by directory names.

Naming a directory `upstream/` would have asserted a provenance that is no
longer true of much of this content — `ThatsAllFolks/` was extensively repaired
here, `folk.ttl` is now a maintained source, `wvs.owl` became `wvs.ttl`.

---

## The corpus

| path | contents | provenance |
|---|---|---|
| `ThatsAllFolks/` | 127 folk value trigger fragments, `folk.ttl`, `taf.ttl` | upstream, extensively repaired |
| `MFTriggers/` | Moral Foundations trigger data | upstream, repaired |
| `MoralMolecules/` | Curry's moral molecules | upstream, unchanged |
| `vale2024/` | the vale2024 role lexicon, 39 files | upstream, unchanged |
| `ValueCore.ttl` | the ValueCore ODP, version 0.4 | upstream, unchanged |
| `bhv.ttl`, `mft.ttl` | Schwartz and Haidt value modules | upstream, unchanged |
| `bhvtriggers.ttl` | Schwartz trigger data | upstream, repaired |
| `wvs.ttl` | World Value Survey module | upstream, renamed from `wvs.owl` |
| `folk_aligned.ttl` | **generated** from `ThatsAllFolks/folk.ttl` | do not edit by hand |
| `ValueNet_stats.txt`, `*.png` | corpus statistics and diagrams | upstream, unchanged |

---

## What changed here, and what it means

The fork repaired this corpus rather than merely consuming it. The repairs are
recorded in the MAREP run reports at the repository root.

| repair | scale |
|---|---|
| every fragment made a valid standalone Turtle document | 127 files, 0 → 38,949 loadable triples |
| `.owl` files carrying Turtle removed or converted | 8 files |
| mis-targeted and misspelled trigger objects corrected | `Repayment`→`Recognition`, `Strenght`→`Strength`, `Inclusion`→`Inclusiveness`, `Assertiveness`→`Assertion` |
| undeclared trigger objects settled | 9 → **0** |
| `folk:Religion` declared under `folk:Beliefs` | 480 triggers rehomed |

Two invariants hold this in place, and both run in CI:

- **every `.ttl` is a valid document on its own** — no header injection, no
  format guessing, no knowledge of where it sits in the tree;
- **every trigger object is explicitly declared** — enforced by SHACL, because
  `vcvf:triggers`'s OWL range *entails* rather than validates, and would
  silently absorb a typo as a new `vcvf:Value`.

---

## Tools

Fork-authored maintenance utilities move to `tools/original-valuenet/` in wave
9. They operate on the corpus above; their inputs do not move.

| tool | purpose |
|---|---|
| `repair_folk_fragments.py` | prefix headers and content repairs |
| `diagnose_folk_fragments.py` | read-only failure-mode diagnosis |
| `retarget_bad_trigger_objects.py` | `Repayment`, `Strenght` |
| `settle_trigger_targets.py` | the final five target decisions |
| `add_folk_religion.py`, `declare_folk_value.py` | value declarations |
| `generate_folk_aligned.py` | regenerates `folk_aligned.ttl` |

`is_v_emo_overlaps.py` is upstream and stays where it is.

---

## Related

- `docs/architecture/PROVENANCE.md` — the two-axis provenance model
- `REPO_REORGANIZATION_PLAN.md` — why these paths are retained
- `MAREP_RUN1_FINDINGS.md`, `MAREP_RUN2_FINDINGS.md`, `MAREP_RUN3_FINDINGS.md`
  — what the audits found in this corpus
