# Phase 1 Authoritative Source Selection

## Status

**Phase 1 source selection and extract wiring complete.** Upstream artifacts remain immutable; the generated project extract is checksum-pinned and reproducible.

Selection date: 2026-08-24

All extracts must be generated from immutable release tags or version IRIs. An unversioned branch, `latest` redirect, or PURL may be recorded as a discovery endpoint but must not be the provenance identity of a committed extract.

## Selected Sources

| Dependency | Selected release | Immutable identifier | License | Intended use |
| --- | --- | --- | --- | --- |
| Common Core Ontologies (CCO) | 2.2 | annotated tag object `d846c40f6dc7ccd2bbca213f616d26e0fe1bf271`; commit `0bc7d33e1bc09fd4693366119ab4e03cb0340042` | BSD-3-Clause | Agent closure; CCO mapping targets; CCO ERO input/output relations |
| Relation Ontology (RO) | 2025-12-17 | tag/commit `13620e1d75465c6504c755d2fdfa706922e9b7e7` | CC0-1.0 | Comparison source for the currently referenced `RO_0002233` and `RO_0002234`; not recommended for the repaired dependency |
| Information Artifact Ontology (IAO) | 2026-03-30 | tag/commit `3006aedacbf813ffd1d2ac15cda10766ca9ed388` | CC-BY-4.0 | Canonical declaration of `IAO_0000115`; comparison source if the project retains the subproperty assertion |
| SKOS Reference | W3C Recommendation, 2009-08-18 | `https://www.w3.org/TR/2009/REC-skos-reference-20090818/` | W3C document terms | Normative interpretation of SKOS mapping properties; not authorization to map OWL classes directly as concepts |

## Primary Sources

- CCO release: <https://github.com/CommonCoreOntology/CommonCoreOntologies/releases/tag/v2.2>
- CCO license: <https://github.com/CommonCoreOntology/CommonCoreOntologies/blob/v2.2/LICENSE>
- RO release: <https://github.com/oborel/obo-relations/releases/tag/v2025-12-17>
- RO license: <https://github.com/oborel/obo-relations/blob/v2025-12-17/LICENSE.txt>
- IAO release: <https://github.com/information-artifact-ontology/IAO/releases/tag/v2026-03-30>
- IAO license: <https://github.com/information-artifact-ontology/IAO/blob/v2026-03-30/LICENSE>
- SKOS Recommendation: <https://www.w3.org/TR/2009/REC-skos-reference-20090818/>

## Selection Rationale and Constraints

### CCO 2.2

CCO 2.2 is the latest published release as of the selection date. Its release includes a merged distribution, module archive, and checksums and states that the release artifacts were reasoned over and profile-validated. The project must use the release artifact rather than the moving `develop` branch. CCO 3.0 is planned but is not a released source and is therefore excluded.

Artifact-level inspection established that CCO 2.2 ERO already provides:

- `ont00001921` **has input**, a subproperty of BFO `has participant`, with domain `process` and a range that includes generically dependent continuants; and
- `ont00001986` **has output**, with the same superproperty, domain, and broad range pattern.

These are a better semantic fit for `hasInformationalInput` and `hasInformationalOutput` than the current RO parents. The RO definitions require material-entity participation or state change, while the project properties intentionally range over generically dependent continuants. Phase 1 therefore recommends replacing the two RO parent assertions with the CCO ERO properties and eliminating the local RO stubs.

### RO 2025-12-17

The selected RO release is the latest published release as of the selection date. The canonical `ro.owl` PURL remains useful for discovery, but the extract manifest must identify the release tag and source-file checksum. Any inverse, domain, range, subproperty, characteristic, or deprecation axioms attached to the selected terms are part of the required closure review.

### IAO 2026-03-30

The selected IAO release is the latest published release as of the selection date. Because its license requires attribution, a committed extract must retain source attribution, license URI, source release, retrieval date, and modification notice. The selected source only declares `IAO_0000115` as an annotation property; the BFO modules gain no required domain entailment from making `skos:definition` its subproperty. Phase 1 recommends removing the project-authored subproperty assertions rather than importing IAO solely for this declaration.

### SKOS

The SKOS Recommendation declares `broadMatch`, `closeMatch`, `exactMatch`, `narrowMatch`, and `relatedMatch` as OWL object properties. SKOS semantic relations have `skos:Concept` as domain and range. Therefore importing canonical SKOS while applying these properties directly between OWL classes would entail that the class IRIs also denote SKOS concepts. Under D-003, class-to-class alignment assertions must default to annotation-only project properties or be reified through distinct concept individuals.

## Required Extract Manifest Fields

Each committed extract must have a sidecar manifest containing at least:

| Field | Requirement |
| --- | --- |
| `extract_id` | Stable project identifier |
| `source_project` | CCO, RO, or IAO |
| `source_release` | Exact tag or version IRI |
| `source_commit` | Full commit hash, resolved before extraction |
| `source_artifact_url` | Immutable tagged source URL |
| `source_sha256` | SHA-256 of the downloaded upstream artifact |
| `retrieved_on` | ISO date |
| `license` | SPDX identifier and canonical license URL |
| `root_terms` | Requested term IRIs |
| `closure_policy` | Included logical/annotation dependencies |
| `generated_by` | Script and version/commit |
| `extract_sha256` | SHA-256 of the committed extract |
| `modifications` | Serialization, filtering, and hand-edit declarations |

## Inspected Artifact Checksums

These checksums identify the exact source files inspected from the pinned clones. They are not yet checksums of project extracts.

| Source file | SHA-256 |
| --- | --- |
| CCO `src/cco-merged/CommonCoreOntologiesMerged.ttl` | `f6d1f7008fb0589baa7ab898f9b236f87b04cab3c4c98fa4b367268ea0cc22d4` |
| CCO `src/cco-modules/ExtendedRelationOntology.ttl` | `37edea7ae67967a2154a6a6fa46b9805f0c30e0ceb68d420d787a8aae73aed15` |
| CCO `src/cco-modules/AgentOntology.ttl` | `b3e0a02ddc9a752386004faca8c91e8b0d34f699d65dcd5c36364d00897a9b15` |
| RO `src/ontology/ro-edit.owl` | `a531cc5f4b46f8e0f67fc7b3e37c5bc1a63eb71e8b8895ce542db564a9fc0d9a` |
| IAO `src/ontology/iao-edit.owl` | `f32ba4f95213b483f9cc47074c71052c2d08243fb657334f421b9aa0a27d93ab` |

## Import Gate — Passed Before Wiring

Phase 1 cannot edit an ontology import until all of the following are true:

1. [x] Full release commit hashes and artifact checksums are recorded.
2. [x] CCO ERO has been searched from the selected release artifact.
3. [x] Required CCO root-term closures and deprecation status are reviewed.
4. [x] License/attribution metadata is prepared.
5. [x] Extract generation is scripted and byte-for-byte repeatable.
6. [x] The closure test passes with no unknown logical dependency.

The initial Phase 1 extract contained 139 triples and had SHA-256 `0058b9fe35eaac8842e4dbc1116d751f4e57f747f2ea81f17556cd9c886eb2c2`. A second independent generation produced the same hash, after which `valuenet-core.ttl` imported version IRI `https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-24`.

Phase 3 extended the same pinned CCO 2.2 source closure with Information Bearing Entity (`ont00000253`) and Information Content Entity (`ont00000958`). Generator version 2 produced a 195-triple revision with SHA-256 `be14d627b9aeb0d4335d152637d4e55371f4f3c859e4266c47ae3b138b223035`; during that phase the core imported `https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-25`. The source release, commit, source checksum, license, and closure policy were unchanged.

Phase 5 promoted four previously annotation-only CCO mappings to reviewed superclass axioms. Generator version 3 adds Act of Appraisal (`ont00000636`), Descriptive Information Content Entity (`ont00000853`), and Prescriptive Information Content Entity (`ont00000965`) as roots and follows their complete selected logical closure. The result contains 324 triples, has version IRI `https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-25-phase5`, and has SHA-256 `f255212d6b5ec905f84c961909589bf44017ed977d6fc5bafa7504d783840838`. The source release, commit, source checksum, license, and closure policy are unchanged; the distinct imported version IRI prevents this expanded extract from overwriting the Phase 3 artifact identity.

Phase 6 adds CCO Act of Observation (`ont00000037`) as the verified superclass of `ActOfBehavioralObservation`. Generator version 4 follows that root's complete selected logical closure. The result contains 330 triples, has version IRI `https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-25-phase6`, and has SHA-256 `70add8bd654ede359575e1fdd3e1beac7b39fc09775d3c8474f8272e8896b421`. The source release, commit, source checksum, license, and closure policy remain unchanged.
