# ValueNet publication, README, and GitHub Pages plan

**Status:** revision 2, sign-off candidate; repository review corrections
incorporated. Implementation has not started.

**Date:** 2026-09-01

**Scope:** public documentation, static-site generation, class discovery,
model visualization, ontology downloads, and GitHub Pages deployment. No
ontology semantics change is authorized by this plan.

---

## 1. Outcome

Publish a clear public entry point for **BFO-Aligned ValueNet** that lets a
visitor:

1. understand why values are represented as BFO realizable entities;
2. distinguish BFO-Aligned ValueNet from the original DUL-aligned ValueNet;
3. search authored ontology classes and read their definitions;
4. inspect a small set of explanatory models;
5. download canonical Turtle modules with provenance and checksums; and
6. reach the technical documentation and validation evidence without having to
   understand the repository's remediation history first.

The root `README.md` remains the repository landing page. A static HTML site is
built from `site/` and deployed to GitHub Pages by GitHub Actions.

---

## 2. Why this work is ready

The publication layer is being built after, not during, ontology stabilization:

- the original ValueNet corpus, BFO-aligned modules, and MAREP infrastructure
  have separate ownership boundaries;
- all canonical BFO paths are stable under `ontology/bfo/`;
- the repository has reproducible semantic fingerprints and audited transition
  records;
- the reorganization and EOL-hardening checkpoints are tagged and published,
  and the later source-data remediation commits and evidence are published;
- the current complete suite passes with only two understood conditional skips;
  and
- remaining worktree metadata and archived upstream source debt do not affect
  the live ontology or the proposed site.

The site must consume these controls; it must not create a second, hand-edited
description of the ontology that can drift from them.

---

## 3. Publication principles

### 3.1 Product hierarchy

Public material presents the repository in this order:

1. **BFO-Aligned ValueNet** — the maintained, primary public ontology suite.
2. **Original ValueNet** — the DUL-aligned source tradition and mapping target.
3. **MAREP** — the audit and evaluation framework that supports quality claims.

MAREP is evidence about the work, not a prerequisite for understanding or
using the ontology.

### 3.2 Authority

- Turtle files are authoritative for ontology terms and axioms.
- `config/repository-layout.yaml` is authoritative for component paths.
- Generated class-search data is never edited by hand.
- Curated explanatory prose may interpret the ontology but may not invent
  classes, mappings, guarantees, or metrics.
- Historical remediation records remain historical. They are linked, not
  rewritten as current product copy.

### 3.3 Simplicity

The first site is static HTML, CSS, JavaScript, JSON, SVG, and downloadable
files. It has:

- no server;
- no database;
- no user accounts;
- no browser-side OWL reasoner;
- no hosted SPARQL endpoint;
- no analytics or tracking by default; and
- no required third-party runtime CDN.

### 3.4 Reproducibility

The same commit built twice must produce the same public data, checksums, and
download bundle. Generated output is deployed as an Actions artifact and is not
committed unless a later decision explicitly changes that policy.

If the site displays a build time, it is derived from the source commit (for
example through `SOURCE_DATE_EPOCH`), not from the builder's wall clock. A
timestamp must not make two builds of one commit differ.

---

## 4. Launch-blocking decisions

These decisions must be recorded before public deployment. Local implementation
may begin while they are pending.

| decision | recommended default | owner/action |
|---|---|---|
| Project-authored license | choose and add one root `LICENSE`; do not infer a license from vendored BFO or CCO files | repository owner approves |
| Third-party attribution | add `THIRD_PARTY_NOTICES.md` separating original ValueNet, BFO, CCO, and other upstream material | ontology lead verifies |
| Citation | add `CITATION.cff` with title, authors, repository URL, preferred citation, and version policy | repository owner supplies authorship/citation |
| Initial public URL | `https://skreen5hot.github.io/ValueNet/` | repository owner confirms casing and account |
| Canonical namespace relationship | documentation site only for v1; state visibly that `https://fandaws.com/ontology/bfo/...` IRIs are identifiers that do not currently resolve, and do not claim dereferenceability unless routing is configured and tested | ontology lead decides later custom-domain work |
| Existing namespace annotation | `valuenet-core.ttl` currently calls the namespace “canonical, resolvable”; either configure and test resolution or correct that annotation in a separately scoped RDF change before launch | ontology lead resolves the contradiction |
| Download version label | label the Pages build `latest from main` plus its full commit; reserve “release” for a signed-off Git tag or GitHub Release | dev team implements |

The absence of a root license and citation record is a **launch blocker**, not a
blocker to building and reviewing the site locally.

Adding license annotations inside `.ttl` files is not silently included. If
desired, it is a separate controlled ontology-annotation change with its own RDF
delta and evidence update.

### 4.1 Known namespace limitation

The home, explorer detail, and download pages must state plainly:

> Canonical ValueNet IRIs identify ontology entities but are not currently
> HTTP-dereferenceable. Use the explorer, repository source links, or module
> downloads to inspect their definitions.

Canonical IRIs remain copyable and searchable. The site must not turn an IRI
click into a silent 404, label the namespace “resolvable”, or imply that the
GitHub Pages project URL is the ontology namespace. Making the canonical domain
dereferenceable is future routing/content-negotiation work outside this plan.

The current `valuenet-core.ttl` ontology comment says the namespace is
“canonical, resolvable,” which conflicts with the observed HTTP state. The site
must not repeat that claim. Before launch, either resolution is configured and
verified or the ontology annotation is corrected through a separate,
evidence-bearing RDF change; this site plan itself authorizes neither.

---

## 5. Information architecture

The initial site contains six public destinations.

### 5.1 Home

- one-sentence ValueNet purpose;
- the practical value of BFO alignment;
- the core disposition/role/realization pattern;
- module summary;
- links to Explore, Models, Downloads, and Documentation; and
- a short, honest quality statement linked to evidence.

### 5.2 Explore classes

- text search over labels, identifiers, IRIs, definitions, and synonyms;
- filters for module and ontological category;
- result cards with label, compact identifier, definition excerpt, category,
  and module;
- a detail panel or stable query-string view containing the full definition,
  IRI, named parents, mappings, source module, and source-file link; and
- authoritative `skos:definition` text only; the build rejects an indexed
  class without one rather than creating an empty UI state or generated prose.

### 5.3 Models

At minimum, publish three purpose-built BFO diagrams:

1. **Core realization pattern** — Agent, ValueDisposition or ValueRole, and
   ValueRealizationProcess.
2. **Moral-foundation pattern** — foundation dispositions and the violation
   processes that contravene them.
3. **Interoperability path** — original ValueNet terms, reviewed ValueNet
   mapping annotations, lexical trigger data, TextSpan evidence, and
   BFO-aligned values.

Each model must include a prose explanation, textual alternative, and links to
the classes it depicts. Existing original-ValueNet diagrams may appear only in
an explicitly labelled historical/original section.

### 5.4 Modules

For every authored public BFO module, show:

- purpose;
- canonical namespace;
- source path;
- imports or external dependencies;
- class count derived at build time;
- definition coverage derived at build time;
- relationships to other modules; and
- individual download link.

Vendored BFO and CCO dependencies are identified separately and are not
presented as ValueNet-authored modules.

`ontology/bfo/extensions/trigger-semantics/vcvf-triggers-semantics.ttl` is an
authored public semantics extension and receives a module card and download. It
intentionally declares zero classes: it supplies annotation semantics for the
upstream `vcvf:triggers` property. Zero is displayed as a measured property of
the module, not treated as a discovery failure. The file contributes to the
interoperability model but not to the class index.

### 5.5 Downloads

- individual canonical `.ttl` modules;
- a deterministic BFO-Aligned ValueNet bundle;
- `SHA256SUMS` or equivalent JSON manifest;
- source commit and build timestamp policy;
- license and third-party notices; and
- links to tagged releases when a release exists.

The site build copies source bytes into its deployment artifact. It does not
serialize RDF again, normalize Turtle, or create a second ontology
representation.

### 5.6 Documentation

Public links should prioritize:

- BFO alignment rationale;
- annotation guide;
- competency questions and worked scenario;
- testing framework;
- provenance summary;
- original ValueNet overview; and
- validation/evidence summary.

Detailed phase exit reviews and MAREP run records remain accessible through the
repository but are not primary navigation.

---

## 6. README rewrite contract

Replace the current historical-first README with a concise repository landing
page using this order:

1. title and one-paragraph purpose;
2. BFO-Aligned ValueNet value proposition;
3. core model in one diagram and one short example;
4. module table;
5. quick start: view, download, parse, and cite;
6. links to the class explorer and models;
7. original ValueNet versus BFO-Aligned ValueNet;
8. validation and reproducibility statement;
9. repository layout for contributors;
10. license, attribution, and citation.

README rules:

- lead with the maintained BFO suite;
- describe original ValueNet respectfully as the source tradition, not as a
  defective product;
- use “BFO-Aligned ValueNet” consistently;
- keep MAREP to a short quality/evidence section;
- do not copy volatile counts into prose when they can be generated or linked;
- use repository-relative links;
- do not use absolute links pinned to an obsolete upstream commit for local
  assets; and
- keep the README useful when viewed outside GitHub Pages.

---

## 7. Proposed implementation layout

```text
site/
  src/
    index.html
    explore/index.html
    models/index.html
    modules/index.html
    downloads/index.html
    documentation/index.html
    assets/
      css/site.css
      js/explorer.js
      models/*.svg
  content/
    site.json                 curated titles, navigation, and public copy
  schemas/
    class-index.schema.json
    download-manifest.schema.json

tools/site/
  build_site.py               orchestrates one deterministic build
  build_class_index.py        RDF-to-JSON extraction
  build_downloads.py          byte-preserving copies, bundle, checksums
  check_site.py               links, schemas, paths, and invariants

requirements-site.txt         pinned build/test dependencies

tests/site/
  test_class_index.py
  test_downloads.py
  test_site_build.py
  test_public_links.py

.github/workflows/
  pages.yml

_site/                        generated and gitignored
```

Names may change during implementation, but the separation must remain:
authored site source, deterministic builders, generated deployment output, and
tests.

Add logical component identifiers for the site, builders, generated artifact,
and public download scope to `config/repository-layout.yaml`. Consumers use
those identifiers rather than counting parent directories.

---

## 8. Class-index contract

### 8.1 Default scope

Index the authored BFO-Aligned ValueNet modules:

- `valuenet-core.ttl`;
- `valuenet-schwartz-values.ttl`;
- `valuenet-folk.ttl`;
- `valuenet-moral-foundations.ttl`;
- `valuenet-moral-epistemics.ttl`; and
- `valuenet-mappings.ttl` where it contributes mappings to indexed terms.

Use the pinned BFO core and CCO extract only as **classification support** for
the transitive category rule below. Their classes do not become search records.

Do not silently include:

- vendored BFO or CCO classes;
- SHACL node/property shapes;
- scenario individuals;
- original ValueNet classes; or
- trigger datasets.

`vcvf-triggers-semantics.ttl` is also excluded from class-record generation
because it declares no classes. It remains in the authored module catalog,
download scope, and interoperability model.

Those resources may be linked or added through an explicit later filter, but
they must not inflate the authored class catalog.

### 8.2 Record schema

Each indexed class record contains:

```json
{
  "id": "stable compact or encoded identifier",
  "iri": "absolute class IRI",
  "label": "human-readable label",
  "definition": "authoritative skos:definition",
  "module": "logical module id",
  "source": "repository-relative Turtle path",
  "category": "disposition | role | process | information | other",
  "parents": ["absolute named parent IRIs"],
  "mappings": [
    {"predicate": "ValueNet mapping annotation IRI", "target": "mapped IRI"}
  ],
  "synonyms": ["optional ontology-supplied synonym"]
}
```

Exact names are finalized with the JSON Schema before implementation. Required
class fields are never `null`; absent optional mappings or synonyms are empty
lists, never guessed values.

### 8.3 Extraction rules

- Discover source files through logical component identifiers.
- Parse with the repository's stable public-ID policy.
- Select named `owl:Class` resources only.
- Read definitions from `skos:definition`. Do not fall back to comments or
  generate display definitions from labels.
- Include only named direct parents in the initial UI.
- Derive `category` by transitive closure over named `rdfs:subClassOf` edges in
  the authored modules plus the pinned BFO core and CCO extract. Blank-node
  restrictions do not supply category edges. Include the class itself when
  testing the roots.
- Map the following roots exactly:

  | category | root |
  |---|---|
  | `disposition` | `http://purl.obolibrary.org/obo/BFO_0000016` |
  | `role` | `http://purl.obolibrary.org/obo/BFO_0000023` |
  | `process` | `http://purl.obolibrary.org/obo/BFO_0000015` |
  | `information` | `https://www.commoncoreontologies.org/ont00000958` |

- If a class reaches no declared category root, assign `other` and include it
  in a generated review report. If it reaches roots belonging to more than one
  distinct category, fail the build. Reaching multiple roots that all map to
  the same category is not ambiguous.
- The `other` report contains the class IRI, named parents, and reviewed reason.
  The expected v1 member is
  `https://fandaws.com/ontology/bfo/valuenet-core#ValueRelatedRealizableEntity`:
  it is a subclass of BFO realizable entity and the common superclass of
  `ValueDisposition` and `ValueRole`, so it deliberately sits above rather than
  inside that category split. A new or different `other` member fails pending
  review; `other` is not a silent catch-all for a broken support graph.
- Repository review executed this rule over the live 187-class population and
  measured 151 dispositions, 15 processes, 12 information entities, 8 roles,
  1 reviewed `other`, and 0 multi-category classes. These are planning-snapshot
  results, not frozen totals; the builder derives and reports the live values.
- Never derive category from an IRI suffix, label text, filename, or regular
  expression.
- Extract mapping assertions using exactly these ValueNet annotation
  properties under
  `https://fandaws.com/ontology/bfo/valuenet-core#`:
  `ontologyEntityMapping`, `hasBroaderConceptualMatch`,
  `hasRelatedConceptualMatch`, and `historicallyCorrespondsTo`.
- Preserve the asserted mapping predicate. Do not translate these assertions
  into `skos:exactMatch`, `skos:broadMatch`, or another SKOS relation, and do
  not infer an assertion of the currently unused superproperty merely for
  display.
- Preserve complete IRIs in data even when compact labels are displayed.
- Sort output deterministically by normalized label and IRI.
- Reject duplicate IRIs with contradictory labels, definitions, or modules.
- Reject HTML injection: RDF text is rendered with DOM `textContent`, never
  inserted as untrusted HTML.

### 8.4 Definition-quality gate

Every authored indexed class must have at least one `rdfs:label`, one
`skos:definition`, and one named direct parent. A missing value is a hard build
failure; v1 has no definition or parent allowlist.

Repository review measured 187 authored classes and found all 187 complete on
all three fields. That is a planning observation, not a frozen count: the
builder reports and tests the live population by module so a later class cannot
fall outside the gate merely because a hand-written total stayed at 187.

---

## 9. Explorer behavior

The first version uses browser-side search without a framework dependency.

Search fields:

- label;
- compact identifier;
- full IRI;
- definition;
- ontology-supplied synonyms; and
- module name.

Ranking order:

1. exact label or identifier;
2. label prefix;
3. label token;
4. synonym;
5. definition or IRI substring.

Behavioral requirements:

- search works from a GitHub project subpath, not only `/`;
- the query and selected class can be represented in the URL;
- keyboard navigation and visible focus are supported;
- empty, loading, no-result, and error states are explicit;
- filters can be cleared without reloading;
- results never imply inference beyond recorded axioms; and
- JavaScript failure leaves navigation, explanatory content, and downloads
  usable.

---

## 10. Download contract

The build defines one reviewed list of downloadable authored modules. For each
file it records:

- logical module id;
- source repository path;
- output filename;
- byte length;
- SHA-256;
- canonical namespace;
- source commit; and
- authorship/license category.

The bundle:

- contains only the reviewed public files plus license, attribution, citation,
  and checksum records;
- preserves source `.ttl` bytes exactly;
- uses deterministic ordering and archive metadata;
- excludes vendored dependencies unless the download page explicitly labels a
  separate “with dependencies” bundle; and
- excludes MAREP run artifacts, tests, source archives, and remediation logs.

A test compares every deployed `.ttl` byte-for-byte with its authoritative
source and recomputes every published checksum.

---

## 11. Accessibility, security, and privacy

Required before deployment:

- semantic landmarks and heading order;
- associated labels for every form control;
- complete keyboard operation;
- visible focus;
- sufficient color contrast;
- meaningful SVG titles/descriptions or adjacent text alternatives;
- responsive layout at narrow and wide widths;
- reduced-motion preference honored;
- no unsafe `innerHTML` for ontology-derived data;
- no secrets or write-capable tokens in client code;
- no tracking, cookies, or external analytics in v1; and
- no third-party scripts required for core operation.

---

## 12. GitHub Pages deployment

Use a custom GitHub Actions workflow rather than publishing the repository's
existing `docs/` directory. GitHub documents this as the supported route when a
site has a custom build process:

- <https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site>
- <https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site>

Workflow behavior:

### Pull requests

1. check out the proposed commit;
2. install pinned site-build dependencies;
3. run existing tests relevant to ontology inputs;
4. build `_site/`;
5. run schemas, link checks, download-byte checks, and deterministic-build
   checks; and
6. upload a preview/build artifact without deploying.

### `main`

1. repeat the same build and checks from the pushed commit;
2. upload the Pages artifact;
3. deploy through the `github-pages` environment; and
4. report the deployed URL and commit.

Deployment requires repository-owner configuration in **Settings → Pages →
GitHub Actions**. The workflow must use the least GitHub permissions required
by the official Pages actions. No `gh-pages` branch or generated-site commit is
required.

Actions being enabled is necessary but does not reveal the current Pages
publishing source. As of the revision-2 review on 2026-09-01, both the expected
public URL `https://skreen5hot.github.io/ValueNet/` and the public repository
Pages API returned HTTP 404, so no public site appears to be serving from
`docs/` or another source. Before Phase 7, the repository owner still records
the actual **Settings → Pages** source. If it is `docs/`, confirm explicitly
that no private or unindexed consumer relies on it before switching to Actions.

---

## 13. Phased implementation

### Evidence cadence for added tests

The current semantic baseline records the complete test population and its
canonical-identity digest. Adding `tests/site/` therefore changes evidence even
though it changes no ontology. An unchanged full-suite digest is not a valid
gate for this work.

At the start of implementation, freeze the **set of pre-site canonical test
identities**. At every later gate:

- every pre-site identity must remain present;
- no canonical identity may collide;
- reviewed site tests may add identities; and
- the live complete-suite counts and full digest must match the newly generated
  semantic baseline.

For each phase that adds, removes, renames, or reparametrizes tests:

1. commit the implementation and tests so the evidence tool has a clean,
   checkable input commit;
2. run `python tools/marep/build_evidence.py --remediation`;
3. commit the resulting `config/semantic-baseline.json` and
   `config/remediation-record.json` together; and
4. run the phase gate again on that clean evidence commit.

`config/eol-transition-matrix.json` remains byte-identical to
`eol-hardened-v1`; site work must not regenerate it. The remediation record
continues to bridge the matrix's measured commit to the current clean input as
required by its loader. A phase that changes no test identity does not perform
evidence churn merely because HEAD moved.

### Phase 0 — publication contract

Deliverables:

- approved license decision;
- `LICENSE`;
- `THIRD_PARTY_NOTICES.md`;
- `CITATION.cff`;
- confirmed public URL and naming convention;
- reviewed authored-module download scope; and
- recorded decision on whether ontology-file license annotations are a
  separate task.

Gate:

- repository owner and ontology lead sign off the license, attribution,
  citation, naming, and download boundary.

No deployment occurs before this gate.

This phase is greenfield: repository review found no root `LICENSE`,
`THIRD_PARTY_NOTICES.md`, `CITATION.cff`, `.github/`, or dependency requirements
file to migrate. `requirements-site.txt` is therefore the repository's first
pinned dependency file and must name only dependencies the site build or site
tests actually import.

### Phase 1 — README and public content architecture

Deliverables:

- rewritten `README.md`;
- `site/content/site.json` or approved equivalent;
- page-level content outlines; and
- link map from public claims to ontology or evidence sources.

Gate:

- all links resolve;
- BFO-Aligned ValueNet is primary;
- original ValueNet and MAREP roles are unambiguous;
- no unsupported metrics or claims; and
- the README remains understandable without the site.

### Phase 2 — deterministic site foundation

Deliverables:

- `site/src/` shell and shared navigation;
- site configuration and relative-path strategy;
- build orchestrator;
- `_site/` ignore rule;
- logical component identifiers; and
- initial site tests.

Gate:

- clean build from a fresh checkout;
- second build at the same commit is byte-identical;
- all pages work under a non-root base path such as `/ValueNet/`; and
- generated files leave the working tree clean.

### Phase 3 — ontology class index

Deliverables:

- class-index JSON Schema;
- RDF-to-JSON generator;
- generated index in the build artifact;
- module and definition-coverage report; and
- generator unit and integration tests.

Gate:

- exact reviewed module scope;
- unique class IRIs;
- every class has `rdfs:label`, `skos:definition`, and a named direct parent,
  with no v1 allowlist;
- the reviewed `other` set and rationale match;
- mappings and named parents resolve without invented terms; and
- generator output is deterministic.

### Phase 4 — explorer UI

Deliverables:

- search and ranking;
- module/category filters;
- class detail view and stable URLs;
- responsive and keyboard-accessible interaction; and
- no-JavaScript fallback navigation.

Gate:

- representative searches for core, Schwartz, folk, moral-foundation, and
  moral-epistemics terms return the expected classes;
- exact identifier search ranks first;
- malformed or ontology-supplied text cannot inject markup; and
- accessibility review passes.

### Phase 5 — models and downloads

Deliverables:

- three BFO-specific accessible diagrams;
- models page and textual alternatives;
- byte-preserving individual downloads;
- deterministic bundle;
- checksum/download manifest; and
- module cards populated from generated data.

Gate:

- every depicted class and property exists in the declared module;
- every model link opens the expected explorer record;
- deployed Turtle files match source bytes;
- checksums recompute; and
- archive contents match the reviewed module boundary.

### Phase 6 — full quality gate

Deliverables:

- link and schema report;
- browser/responsive review record;
- accessibility review record;
- fresh-checkout build record;
- existing-suite comparison captured after the final edit; and
- public-content sign-off.

Gate:

- the pre-site canonical test-identity set is a subset of the final set, with
  no missing identity or collision; the full count and digest are expected to
  change for reviewed site-test additions and must match the regenerated
  semantic baseline;
- all site tests pass;
- no ontology `.ttl` file changed under this plan;
- the working tree is clean after build and test;
- README, site, data, and downloads agree on paths and module names; and
- license/citation/attribution are visible from both README and site.

### Phase 7 — Pages deployment and verification

Deliverables:

- `.github/workflows/pages.yml`;
- Pages repository setting enabled by the owner;
- successful deployment from `main`;
- production link, search, model, and download smoke test; and
- deployment record naming the commit.

Gate:

- production site serves from the configured project subpath;
- direct navigation to nested pages works;
- search index loads without console errors;
- every public download and checksum works; and
- no deployment step changes `main` or creates an unreviewed branch.

---

## 14. Test strategy

### Generator tests

- fixture graphs test labels, definitions, parents, mappings, duplicates, and
  missing fields;
- a falsification proves each scope exclusion is enforced;
- live integration tests compare the index to the exact component membership;
- stable public IDs are used for every parse; and
- generated JSON validates against its schema.

### Download tests

- source and deployed bytes match;
- checksum manifest is complete and exact;
- bundle membership is exact in both directions;
- archive generation is deterministic; and
- no vendor, test, run artifact, or source archive leaks into the authored
  bundle.

### Site tests

- internal links and fragment targets resolve;
- repository source links exist at the measured commit;
- all internal asset URLs work under `/ValueNet/`;
- navigation is usable without JavaScript;
- ontology-derived strings are rendered as text;
- public pages contain license and citation links; and
- build failure propagates as a non-zero workflow result.

### Manual/browser checks

- keyboard-only explorer use;
- narrow mobile and wide desktop layouts;
- current Chrome, Edge, Firefox, and Safari behavior;
- high zoom and long definitions;
- visible focus and contrast;
- reduced motion; and
- download behavior from the deployed site.

---

## 15. Risks and controls

| risk | control |
|---|---|
| README and site contradict each other | share generated module metadata; test links and names |
| Original and BFO ValueNet are conflated | product hierarchy and a dedicated comparison section |
| Vendored BFO/CCO classes appear authored | exact index and download membership |
| Definitions are guessed or omitted for display | require `skos:definition` on every indexed class; no fallback or v1 allowlist |
| Site works locally but fails under project path | relative URLs plus `/ValueNet/` build test |
| A generated index becomes stale | build from source on every workflow run; do not hand-edit |
| Downloads differ from repository source | byte comparison and checksum tests |
| A bundle implies a release when it is `main` | display full commit and use “latest from main” |
| Public reuse terms are ambiguous | Phase 0 license, attribution, and citation gate |
| Historical engineering records dominate navigation | curated documentation page; deep records remain repository links |
| A visual model overstates OWL semantics | class/property existence tests plus ontology-lead review |
| Browser code introduces an injection path | no `innerHTML` for RDF-derived text; targeted falsification |
| Build tools mutate the repository | generate only under ignored `_site/`; clean-tree gate |

---

## 16. Explicit non-goals

This plan does not authorize:

- changing ontology axioms or annotations;
- renaming canonical namespaces;
- repacking upstream source archives;
- repairing the remaining archived `hasDataValue` instances;
- building a SPARQL service or API;
- executing OWL reasoning in the browser;
- creating an ontology editor;
- exposing MAREP run state as an interactive application;
- adding user tracking, accounts, comments, or submissions;
- moving historical documentation merely to make the site tree tidier; or
- moving any existing release/evidence tag.

Any such work requires a separately reviewed scope.

---

## 17. Dev-team handoff checklist

Before starting:

- [ ] Confirm Phase 0 owners and decisions.
- [ ] Capture the clean starting commit and current test identities.
- [ ] Confirm `main` and `origin/main` relationship.
- [ ] Confirm Pages URL/base path.
- [ ] Review the exact authored module list.
- [ ] Confirm no `.ttl` change is included in this branch.

Before each phase commit:

- [ ] Run the phase-specific tests after the last edit.
- [ ] Build from a clean or explicitly understood tree state.
- [ ] Confirm generated output did not enter Git unintentionally.
- [ ] Record measured results rather than carrying forward an earlier count.

Before deployment:

- [ ] Complete Phase 0 governance files.
- [ ] Run the complete existing and site suites.
- [ ] Build and verify from a fresh checkout at another path.
- [ ] Review the rendered pages, diagrams, and downloads.
- [ ] Confirm the deployment commit is a fast-forwarded reviewed commit.
- [ ] Obtain explicit authorization before enabling Pages or pushing deployment
      configuration.

---

## 18. Sign-off

After reviewer and owner sign-off, commit this plan by itself as the planning
baseline **before Phase 0**. It is not a Phase 0 deliverable: Phase 0 implements
the governance decisions the committed plan authorizes. Keeping the plan in its
own commit makes later scope changes visible and prevents an implementation
commit from quietly rewriting its authority.

Approval of this plan authorizes implementation of Phases 0–6 in the
repository. It does **not** authorize:

- selecting a project license without owner approval;
- changing ontology RDF;
- changing repository settings;
- deploying GitHub Pages; or
- pushing implementation commits.

Phase 7 requires explicit repository-owner authorization after the full quality
gate passes.
