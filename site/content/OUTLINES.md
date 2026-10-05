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
| Why I built this | The owner's reason for the work, in the first person, under a byline | owner statement — see below |
| Core pattern | What somebody holds, what happens when they act on it, what happens when it is gone against; a link into Models | curated, each term linked to its real class |
| Why BFO | A one-sentence gloss of BFO and CCO, then three points: bearer, realization, interoperability | curated |
| Quality statement | What is measured, that the suite was formally reviewed, and what neither shows | curated (`site.json` `evidence_statement`), linked into Documentation |
| Where to go next | One line for each of the other pages | curated |
| IRI notice | The non-dereferenceable notice | `site.json` notices |

The home page must be readable by someone who has never heard of BFO. It states
what a value *is* in this model before it states which upper ontology supplies
the scaffolding, and it uses neither acronym before saying what it stands for.

**The owner statement.** Added 2026-10-05, on the owner's instruction. It is the
only first-person passage on the site and the only content that is about
something outside this repository: Integral Ethics, the larger work this suite
was built to serve. It is published as the owner's statement of purpose, under
their name, and not as a finding. Three things hold it:

- It carries a byline, and nothing outside its section speaks in the first
  person.
- Where it says ValueNet was refactored here, it names the people who created
  ValueNet, as [CITATION.cff](../../CITATION.cff) credits them.
- It says of the larger system that it is designed never to make the moral
  decision and that it does not exist yet. Both sentences stay.

Its wording is the owner's to change. The text lives on the page and is not
copied into `site.json`, because a second copy of somebody's own words is a
copy that can come to differ from what they said.

**Two blocks changed from the Phase 1 outline.** "Core pattern" was to be the
realization diagram; it is prose with class links, and the diagram stays on the
Models page, where the tests that check it against the ontology already read it.
"Modules at a glance" is not built: a module's purpose written here would be a
second description of the module, which is the thing `site.json` was changed to
stop carrying. The Modules page generates it, and the home page links there.

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

Curated links, in reading order, each with a sentence saying what the document
is. The Phase 1 outline listed seven stops: BFO alignment rationale, annotation
guide, competency questions and worked scenario, testing framework, provenance,
original ValueNet overview, validation and evidence summary. The page was built
on 2026-10-05, after the formal review and its remediation, so it also carries
what that work produced.

| section | documents | source |
|---|---|---|
| 1. Start with the model | `README.md`, `BFOizing ValueNet.md` (the rationale), `docs/original-valuenet/README.md` | curated links |
| 2. Use it | `annotationGuide.md`, `valuenet-moral-epistemics-CQ.md`; the worked scenario by a link to Downloads, where it is published | curated links |
| 3. How it is checked | `TestingFramework.md`, the `tests/` directory | curated links |
| 4. The decisions | `DECISION_RECORDS.md`, `FORMAL_REVIEW_2026-09-16_RULES_2.0.md` (the definition standard D-013 adopts), `R15_FOLK_MEMBERSHIP_PROPOSAL.md` | curated links |
| 5. The formal review | `FORMAL_REVIEW_2026-09-16.md`, `FORMAL_REVIEW_2026-09-16_RESPONSE.md`, `FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF.md`, `FORMAL_REVIEW_2026-09-16_POST_SIGNOFF_UPDATE.md`, `FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF_2.md` | curated links |
| 6. What is still open | `OPEN_ITEMS.md` | curated link |
| 7. Evidence and provenance | `semantic-baseline.json`, `eol-transition-matrix.json`, `remediation-record.json`, `PROVENANCE.md`, `quality-report.json` | curated links |
| 8. Terms and credit | `LICENSE`, `CITATION.cff`, `ACKNOWLEDGMENTS.md`, `THIRD_PARTY_NOTICES.md` | curated links |
| 9. Continuing the work | `HANDOFF.md`, `PUBLICATION_AND_GITHUB_PAGES_PLAN.md` | curated links |

Phase exit reviews and MAREP run records stay reachable in the repository but
are not primary navigation: the page ends by pointing at the two directories
that hold them. This page is a reading path, not an index of everything.

**Every document link leaves the site, and only for the repository.** These
documents are not copied into the build; each link opens one on GitHub, on the
branch the site is built from. That is the single exception to "no reference with a scheme", and
it is as narrow as it sounds: an anchor, to this repository as `CITATION.cff`
names it, on `main`, to a path git tracks. `tools/site/check_site.py` enforces
it on every build and `tests/site/test_public_links.py` shows each way it
refuses. Anything that loads from another origin is still refused, as before.

**Two sentences are part of the contract.** Under the review: a sign-off covers
what had been decided when it was given. Under the evidence: it shows that the
measurements reproduce and that the changes are accounted for, and does not show
that the ontology is correct. A list of reviews and records reads as a verdict
unless the page says it is not one.

**No counts.** The page does not say how many decisions, sign-offs or records
there are. Its only figures are its own section numbers.

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
