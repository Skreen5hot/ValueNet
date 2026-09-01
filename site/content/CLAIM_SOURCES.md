# Link map: public claims to their sources

Phase 1 deliverable of the
[publication plan](../../docs/architecture/PUBLICATION_AND_GITHUB_PAGES_PLAN.md).

Every factual claim the README or the site makes appears here with the artifact
that supports it. A claim that cannot be sourced does not ship. The Phase 1
gate — "no unsupported metrics or claims" — is checked against this table.

**Status of this document.** The mapping is verified by inspection in Phase 1.
Phase 2 converts the mechanical parts into tests: that every source named here
exists, that generated claims are produced rather than written, and that no
curated string contains a number the build could have derived.

---

## Claims about the model

| claim | source | kind |
|---|---|---|
| Values are modelled as realizable entities inhering in an agent | [valuenet-core.ttl](../../ontology/bfo/core/valuenet-core.ttl) — `ValueRelatedRealizableEntity` subclasses `BFO_0000017` | asserted |
| The disposition/role split sits below one common superclass | same file — `ValueDisposition` and `ValueRole` both subclass `ValueRelatedRealizableEntity` | asserted |
| Realization and violation are distinct processes | same file — `ValueRealizationProcess`, `ValueViolationProcess`, both subclassing `BFO_0000015` | asserted |
| Textual evidence is carried by CCO information entities | same file — `EvidenceSource`, `TextSpan`, `TextualRepresentation`, `TextSpanSelector` under `ont00000958` | asserted |
| Honesty resolves to a BFO disposition through asserted edges | [valuenet-folk.ttl](../../ontology/bfo/core/valuenet-folk.ttl) → [valuenet-schwartz-values.ttl](../../ontology/bfo/core/valuenet-schwartz-values.ttl) → core | asserted chain |
| The honesty definition quoted in the README | `skos:definition` on `HonestyDisposition` in valuenet-folk.ttl | quoted verbatim |

## Claims about modules

| claim | source | kind |
|---|---|---|
| Every module's title | one `dcterms:title` on its ontology header | extracted |
| Every module's description | one `dcterms:description` on its ontology header | extracted |
| Every module's licence | `dcterms:license` on its ontology header, CC BY 4.0 | extracted |
| Where each module lives | its logical component in [repository-layout.yaml](../../config/repository-layout.yaml) | contract |
| Class counts, definition coverage, category distribution | generated at build time | generated |
| Which modules declare zero classes | generated at build time | generated |
| Import relationships | `owl:imports` in each module | asserted |
| Why a module is excluded from the class index | [site.json](site.json) `editorial` | curated, flagged |

All eleven deliverables carry a title, a description and a licence.
None is curated: the publication-metadata cycle added the three that
were missing, taking each module's own `rdfs:label` and `rdfs:comment`
rather than authoring new prose. `site.json` no longer holds a display
name or a purpose for any module — a second description of a module is
a thing that can drift from the module.

The catalog partitions into **seven primary** modules and **four
supporting** graphs: three SHACL and one worked scenario. All eleven
are downloadable; only the primary ones with classes contribute class
records.

## Claims about mappings

| claim | source | kind |
|---|---|---|
| Correspondences are annotations, not equivalences | the four ValueNet annotation properties in [valuenet-core.ttl](../../ontology/bfo/core/valuenet-core.ttl) | asserted |
| No SKOS mapping relation is asserted anywhere in the authored modules | verified by inspection across all authored modules; zero occurrences | measured |
| Mapping predicates are published as asserted | publication plan §8.3 forbids translation | policy |

## Claims about IRIs

| claim | source | kind |
|---|---|---|
| Canonical IRIs do not currently resolve | observed HTTP state | measured |
| w3id aliases are reserved and unregistered | namespace-policy `rdfs:comment` in valuenet-core.ttl | quoted |
| The core module says the IRIs are identifiers, not fetchable URLs | the same comment, as corrected | quoted |

The namespace contradiction is **resolved**. The core module used to
call the namespace "canonical, resolvable" while it resolved to
nothing; the publication-metadata cycle corrected that annotation to
say the IRIs are identifiers and are not currently
HTTP-dereferenceable. The site and the ontology now say the same
thing, so the site is no longer declining to repeat a claim its own
source made.

## Claims about validation

| claim | source | kind |
|---|---|---|
| The corpus has a fingerprint reproducible from any checkout | [config/semantic-baseline.json](../../config/semantic-baseline.json) | generated evidence |
| Earlier digests depended on checkout location | [config/eol-transition-matrix.json](../../config/eol-transition-matrix.json) — cell A measured twice at two paths | generated evidence |
| Every source-data repair is enumerated triple by triple | [config/remediation-record.json](../../config/remediation-record.json) | generated evidence |
| A 99-file reorganization is bracketed by evidence | [config/reorganization-baseline.json](../../config/reorganization-baseline.json) | generated evidence |
| Tagged checkpoints exist | `reorg-pre-move-v1`, `reorg-post-move-v1`, `eol-hardened-v1` | git tags |
| Provenance of upstream material | [PROVENANCE.md](../../docs/architecture/PROVENANCE.md) | curated record |

**What is deliberately not claimed.** The evidence shows that measurements
reproduce and that changes are accounted for. It does not show that the
ontology is correct, complete, or validated against an external standard. The
site says what is measured and links to it; it does not upgrade that into a
quality claim.

## Claims about original ValueNet

| claim | source | kind |
|---|---|---|
| Original ValueNet is DUL-aligned | [docs/original-valuenet/README.md](../../docs/original-valuenet/README.md) and the DUL prefixes in its Turtle | asserted |
| It supplies trigger data and corpora | [MFTriggers/](../../MFTriggers), [ThatsAllFolks/](../../ThatsAllFolks) | present in repository |
| It is a mapping target, not a deprecated release | editorial position, publication plan §3.1 | policy |

## Claims the site must never make

- That a canonical IRI can be fetched.
- That a Pages build is a release.
- That vendored BFO or CCO classes are ValueNet-authored.
- That a mapping annotation is a logical equivalence.
- That the ontology is verified, validated, or correct.
- Any count written by hand where the build could derive it.
