# Page-level content outlines

Phase 1 deliverable of the
[publication plan](../../docs/architecture/PUBLICATION_AND_GITHUB_PAGES_PLAN.md).
These outlines fix what each public page says and where every claim on it comes
from. They are the contract Phase 2–5 implementation builds against; they are
not markup.

Two rules apply to every page:

- **Generated beats curated.** Anything derivable from the ontology — class
  counts, definition coverage, category distribution, module class totals,
  checksums — is produced by the build and never written into
  [site.json](site.json) or into these outlines. Where a page shows both,
  generated values are visually distinguishable from curated prose.
- **A claim with no source does not ship.** Every factual statement traces to a
  Turtle file, a generated artifact, or an evidence record. The mapping is in
  [CLAIM_SOURCES.md](CLAIM_SOURCES.md).

---

## Home

| block | content | source |
|---|---|---|
| Hero | Site name, tagline, one-sentence summary | curated (`site.json`) |
| Why BFO | Three points: bearer, realization, interoperability | curated, each illustrated by a real class |
| Core pattern | The realization diagram, with a link into Models | generated class links |
| Modules at a glance | Authored module names and purposes, with class counts | curated purpose + generated counts |
| Quality statement | One short paragraph, linked to evidence | curated tone, linked artifacts |
| IRI notice | The non-dereferenceable notice | `site.json` notices |

The home page must be readable by someone who has never heard of BFO. It states
what a value *is* in this model before it states which upper ontology supplies
the scaffolding.

## Explore classes

| block | content | source |
|---|---|---|
| Search field | Label, compact id, IRI, definition, synonyms, module | generated class index |
| Filters | Module, category | generated facets |
| Result card | Label, compact id, definition excerpt, category, module | generated |
| Detail view | Full definition, IRI, named parents, mappings, source module and file link | generated |
| Empty / loading / error | Explicit distinct states | curated strings |

Every indexed class carries a label, a `skos:definition`, and a named parent, so
there is **no "definition not supplied" state** — a missing value fails the
build instead. The detail view shows the asserted mapping predicate by name; it
never displays a SKOS relation the ontology does not assert.

IRIs are shown as selectable text with a copy affordance, never as anchors,
because they do not resolve.

## Models

Three diagrams, each with prose, a textual alternative, and links into the
explorer for every class depicted:

1. **Core realization pattern** — agent, `ValueDisposition` or `ValueRole`,
   `ValueRealizationProcess`.
2. **Moral-foundation pattern** — foundation dispositions and the
   `ValueViolationProcess` terms that contravene them.
3. **Interoperability path** — original ValueNet terms, the ValueNet mapping
   annotations, lexical trigger data, `TextSpan` evidence, BFO-aligned values.

A diagram may depict only classes and properties that exist in the module it
names, and may not imply an axiom the ontology does not assert — in particular
no diagram edge may read as `owl:equivalentClass` where the ontology asserts an
annotation. Original-ValueNet diagrams appear only in a labelled historical
section.

## Modules

Two sections, because the eleven deliverables are not one kind of
thing.

**Primary modules** (seven): purpose, canonical namespace, source path,
imports, class count, definition coverage, relationships, download
link. Title and description are extracted from the ontology header;
counts and coverage are generated. Two of the seven legitimately show
zero classes, rendered as a measured value with the editorial reason
beside it.

**Validation and examples** (four): three SHACL graphs and one worked
scenario. Published, downloadable, and in the authored bundle, but
contributing no class records — a shape constrains rather than
declares, and a scenario is individuals. Presented in their own
section so a reader is not invited to read a constraint graph as part
of the vocabulary.

Vendored BFO and CCO appear in a separate, clearly labelled
dependencies section and are in neither count.

Nothing on these cards is written in `site.json`. It holds the
identity, the component binding, the indexing status, and an editorial
note where a decision needs explaining; everything a reader sees comes
from the ontology or the build.
## Downloads

Individual modules, a deterministic bundle, and a checksum manifest. Each entry
shows byte length, SHA-256, canonical namespace, and the full source commit.
The build label is "latest from main" plus that commit; "release" is reserved
for a signed-off tag.

Deployed Turtle is byte-identical to repository source — the build copies bytes
and never re-serializes. License and attribution links sit on this page, and
until Phase 0 issues them the page carries the license-pending notice rather
than a link to a file that does not exist.

## About and credits

| block | content | source |
|---|---|---|
| Acknowledgment | The one-sentence credit, repeated in the footer of every page | curated (`site.json`) |
| Authorship | Why the AI agents are credited but not listed as authors | curated |
| Computational contributors | Claude with its recorded model identifier; Codex at product level | curated |
| Original ValueNet | The source tradition and its author | curated |
| Upstream ontologies | BFO and CCO under their own licences | curated |

The acknowledgment appears in the footer of every page, not only here. A credit reachable only by navigating to it is one most readers never see, and the assistance was substantive enough that understating it would misdescribe the work.

## Documentation

Curated links, in reading order: BFO alignment rationale, annotation guide,
competency questions and worked scenario, testing framework, provenance,
original ValueNet overview, validation and evidence summary.

Phase exit reviews and MAREP run records stay reachable in the repository but
are not primary navigation. This page is a reading path, not an index of
everything.

---

## What Phase 1 deliberately leaves out

- **No links to the deployed site.** It does not exist. The README and these
  outlines describe the explorer and models as planned; links are added when
  Phase 7 deploys, not before.
- **No license, citation, or attribution links.** Phase 0 issues those files.
  Until then the notice states that no terms are granted, rather than linking
  to a missing file.
- **No counts in curated copy.** Every number a reader sees comes from the
  build.
