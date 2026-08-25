# Phase 1 Exit Review — Authoritative Vocabulary Closure

Date: 2026-08-24

Status: **Complete**

## Outcome

The BFO layer now has a version-pinned, source-complete logical dependency for the CCO terms it uses. The incomplete RO and CCO stubs and the unnecessary IAO annotation dependency have been removed from project modules.

## Source Decisions Implemented

| Dependency | Resolution |
| --- | --- |
| CCO Agent (`ont00001017`) | Reused from a generated CCO 2.2 extract with its Agent Capability dependency and defining equivalence |
| Informational input parent | Replaced RO `RO_0002233` with CCO ERO `ont00001921` |
| Informational output parent | Replaced RO `RO_0002234` with CCO ERO `ont00001986` |
| IAO definition (`IAO_0000115`) | Removed the unneeded `skos:definition` subproperty assertions; no IAO import is required |
| CCO mapping targets | Canonical labels, definitions, parents, and relevant disjointness verified; mapping strength remains a Phase 5 decision |
| SKOS mapping properties | Confirmed as OWL object properties over SKOS concepts; current class mappings remain pending Phase 5 conversion under D-003 |

## Generated Dependency

- Extract: `BFO/imports/cco-valuenet-extract.ttl`
- Root terms: Agent, has input, has output
- Closure: Agent Capability, inverse properties, recursive OWL blank-node expressions, and referenced declarations
- Triple count: 139
- Version IRI: `https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-24`
- SHA-256: `0058b9fe35eaac8842e4dbc1116d751f4e57f747f2ea81f17556cd9c886eb2c2`
- Generator: `BFO/remediation/generate_cco_extract.py`
- Manifest: `BFO/imports/cco-valuenet-extract.manifest.json`
- Reproducibility: a second independent generation produced the same SHA-256

## Project Module Changes

1. `valuenet-core.ttl` imports the pinned CCO extract and no longer contains a project-authored CCO Agent stub.
2. `valuenet-core.ttl` and `valuenet-folk.ttl` no longer assert `skos:definition rdfs:subPropertyOf IAO_0000115`.
3. `valuenet-moral-epistemics.ttl` no longer declares partial RO stubs.
4. `hasInformationalInput` specializes CCO ERO `ont00001921`.
5. `hasInformationalOutput` specializes CCO ERO `ont00001986`.

## Verification Evidence

### Automated suite

- 480 passed
- 2 skipped
- 5 deselected
- 6 strict expected failures
- 9 warnings
- elapsed time: 65.78 seconds

The six expected failures are the intentionally preserved Phase 2 and Phase 3 negative controls. No Phase 1 check is expected to fail.

### Extract and closure controls

- Manifest validates against JSON Schema Draft 2020-12.
- Extract checksum matches its manifest.
- Required CCO defining axioms, inverse properties, ranges, and non-deprecation checks pass.
- External dependencies are classified as authoritative/declarative, mapping-only, or unknown.
- Unknown external logical dependencies: 0.
- Core import of the extract is asserted and tested.

### HermiT

| Scope | Files | Triples | Declared classes | Consistent | Unsatisfiable named classes |
| --- | ---: | ---: | ---: | --- | ---: |
| TBox | 7 | 2,505 | 281 | Yes | 0 |
| TBox plus scenario | 8 | 2,579 | 281 | Yes | 0 |

The reasoner check is offline and reproducible through `BFO/remediation/check_bfo_consistency.py`; import triples are removed only from its temporary already-merged validation graph to prevent network resolution.

## Exit Criteria

- [x] Exact upstream releases, commits, licenses, and inspected checksums recorded.
- [x] CCO ERO searched before relation reuse.
- [x] Required CCO terms supplied with relevant logical closure.
- [x] Incomplete external stubs removed from project modules.
- [x] Unknown external logical dependency count is zero.
- [x] Extract generation is checksum-verified and repeatable.
- [x] Full automated suite passes apart from the six explicitly deferred negative controls.
- [x] TBox and scenario are consistent with no unsatisfiable named classes.

## Deferred Work

- Mapping-property conversion and mapping-target adjudication remain in Phase 5.
- Bearer/participant realization enforcement begins in Phase 2.
- Evidence-source and evidence-target SHACL repair begins in Phase 3.
