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
| Textual evidence is selected and recorded by CCO information entities | same file — `TextSpanSelector` under `ont00000686` (designative ICE) and `ValueEvidenceAnnotation` under `ont00000853` (descriptive ICE); the text itself, `TextualRepresentation` and `TextSpan`, is form under BFO `BFO_0000031` (D-005) | asserted |
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

## Claims in the owner's statement

The home page carries a statement of why the suite was built, in the first
person, under the owner's name. It is a different kind of content from the rest
of this table, and it is marked as one. Where it says something about this
repository, the claim is sourced like any other. Where it says something about
the owner's reasons, or about work that is not in this repository, the source
is the owner, the page says so by attributing it, and the site reports that the
owner says it and nothing more.

| claim | source | kind |
|---|---|---|
| The suite was built as the value foundation for Integral Ethics | the owner, instructing this page on 2026-10-05 | owner statement |
| Integral Ethics is part of a larger body of work, Ethical Computation | the same instruction | owner statement |
| Its aim, its propose-constrain-decide division of labour, and that it is designed never to make the moral decision | the owner's talk *Showing the Work* (2026-09-29), whose script the owner supplied for this page; the script is not in this repository | owner statement |
| There is no finished system yet; what exists is the design, a test instrument and this ontology | the same script | owner statement |
| ValueNet was created by Stefano De Giorgis, Aldo Gangemi and Rossana Damiano | the conference-paper reference in [CITATION.cff](../../CITATION.cff) | cited |
| The suite is a refactoring of ValueNet onto the Basic Formal Ontology | [valuenet-core.ttl](../../ontology/bfo/core/valuenet-core.ttl) and the mapping annotations in [valuenet-mappings.ttl](../../ontology/bfo/core/valuenet-mappings.ttl) | asserted |
| A value is a disposition that somebody bears | valuenet-core.ttl — `ValueDisposition`, and the restriction that a value-related realizable entity inheres in some agent | asserted |
| What goes against a value is a process | same file — `ValueViolationProcess`, defined by `contravenes` | asserted |
| A reading of a text divides into which words, which value, whose value, and realized or violated | same file — `TextSpan` and `selectsTextSpan`, `isEvidenceFor` a process, that process realizing or contravening a disposition, the disposition inhering in an agent; worked through in the [annotation guide](../../docs/bfo/guides/annotationGuide.md) | asserted |

The first four rows cannot be checked from here and are not presented as if
they could. What is checked is the frame: the byline, the credit to ValueNet's
authors read from the citation record, and the two cautions in the fourth row
and the third, which `tests/site/test_home.py` requires the statement to keep.

## Claims on the home page beside the statement

| claim | source | kind |
|---|---|---|
| The three terms of the core pattern, and that a role is borne because of a position | `ValueDisposition`, `ValueRole`, `ValueRealizationProcess`, `ValueViolationProcess` in valuenet-core.ttl; each is linked to its class record, and a test resolves the links against the generated index | asserted |
| An act can contravene a value its own agent bears | the definition of `ValueViolationProcess`, and its comment that it is deliberately not disjoint with realization | quoted in substance |
| BFO is an upper ontology; CCO is reused for agents and for the information entities that record textual evidence | the imports in valuenet-core.ttl; `cco:Agent` as bearer; the CCO parents of `TextSpanSelector` and `ValueEvidenceAnnotation` | asserted |
| What is measured | [site.json](site.json) `evidence_statement`, itself sourced under "Claims about validation" above; the page is required to carry it word for word | curated, bound |
| The suite has been through a formal ontology review, and the records are in the repository | [docs/bfo/reviews/](../../docs/bfo/reviews) | present in repository |

## Claims on the documentation page

Every stop on the reading path is a link and a sentence. The link is checked on
every build: it must name a path git tracks. The sentence is curated, and says
what the document says of itself.

| claim | source | kind |
|---|---|---|
| Each document is what its line says it is | the opening of the document itself | curated, flagged |
| The review, the first sign-off and the second, and RULES 2.0 are recorded verbatim | the provenance header on each of those files | quoted in substance |
| RULES 2.0 is adopted as the project's standard, with stated readings | D-013 in [DECISION_RECORDS.md](../../docs/bfo/remediation/DECISION_RECORDS.md) | decision record |
| The open-items register is re-derived by a test | [tests/bfo/test_open_items.py](../../tests/bfo/test_open_items.py) | test |
| A sign-off covers what had been decided when it was given | the dates in the decision records against the dates on the sign-offs; at the time of writing D-015 is later than both | decision record |
| What the evidence does and does not show | "What is deliberately not claimed", above | policy |

## Claims the site must never make

- That a canonical IRI can be fetched.
- That a Pages build is a release.
- That vendored BFO or CCO classes are ValueNet-authored.
- That a mapping annotation is a logical equivalence.
- That the ontology is verified, validated, or correct.
- That a review or a sign-off shows the ontology to be any of those. A sign-off
  is a reviewer's statement about a remediation, as of the day it was given.
- That Integral Ethics is a finished system, or that it makes a moral decision.
- Anything in the first person without the name of the person saying it.
- Any count written by hand where the build could derive it.
