# SPDX-License-Identifier: Apache-2.0
"""The class index publishes what the ontology asserts, or it fails.

Every field is extracted. So the interesting tests are not that the
extraction works on today's data -- it does, and one integration test
says so -- but that it refuses the four things it must never do: choose
between ambiguous values, invent a missing one, infer a category from a
name, or translate a mapping predicate into a stronger relation.

The refusals are exercised on synthetic graphs, so they hold whatever the
corpus happens to contain.
"""

from __future__ import annotations

import importlib.util
import json

import pytest
import rdflib
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS

from marep import layout

REPO = layout.repository_root()


def _module():
    path = layout.component("tool.build-class-index").resolve()
    spec = importlib.util.spec_from_file_location("build_class_index", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B = _module()

SCHEMA = json.loads(
    (layout.component("site.schemas").resolve() / "class-index.schema.json")
    .read_text(encoding="utf-8"))

EX = "https://ex.invalid/m#"
BFO_DISPOSITION = "http://purl.obolibrary.org/obo/BFO_0000016"
BFO_ROLE = "http://purl.obolibrary.org/obo/BFO_0000023"


# ======================================================================
# refusals, on graphs constructed for the purpose
# ======================================================================


def test_two_labels_are_a_refusal_not_a_choice():
    """Which label reaches the site would otherwise depend on traversal
    order, and the reader would never know a second existed."""
    g = rdflib.Graph()
    node = rdflib.URIRef(EX + "C")
    g.add((node, RDFS.label, rdflib.Literal("One")))
    g.add((node, RDFS.label, rdflib.Literal("Two")))
    with pytest.raises(SystemExit) as exc:
        B.one(g, node, RDFS.label, "rdfs:label", EX + "C")
    assert "2 values" in str(exc.value)
    assert "traversal order" in str(exc.value)


def test_a_missing_definition_is_a_refusal_not_a_fallback():
    """Borrowing the label would put text on the public site that the
    ontology does not assert."""
    g = rdflib.Graph()
    node = rdflib.URIRef(EX + "C")
    g.add((node, RDFS.label, rdflib.Literal("Has a label")))
    with pytest.raises(SystemExit) as exc:
        B.one(g, node, SKOS.definition, "skos:definition", EX + "C")
    assert "no fallback" in str(exc.value)


def test_a_class_reaching_two_categories_is_a_refusal():
    """A class that is both a disposition and a role is an ontology
    question. Picking one here would answer it silently."""
    parents = {EX + "C": {BFO_DISPOSITION, BFO_ROLE}}
    with pytest.raises(SystemExit) as exc:
        B.category_of(EX + "C", parents)
    assert "two categories" in str(exc.value)


def test_category_comes_from_edges_and_never_from_the_name():
    """A class named ...Disposition with no path to the disposition root
    is `other`, and one named nothing of the kind that reaches the root
    is a disposition. The name is not evidence."""
    named_but_unattached = B.category_of(EX + "LooksLikeADisposition", {})
    assert named_but_unattached == "other"

    unremarkable = B.category_of(
        EX + "Thing", {EX + "Thing": {BFO_DISPOSITION}})
    assert unremarkable == "disposition"


def test_the_class_itself_counts_as_its_own_ancestor():
    """So a root imported directly classifies, rather than needing a
    parent edge that does not exist."""
    assert B.category_of(BFO_ROLE, {}) == "role"


def test_only_the_four_valuenet_predicates_are_mapping_predicates():
    """SKOS relations are absent by design: a historical correspondence
    is a weaker claim than an equivalence, and publishing it as one would
    strengthen it."""
    assert len(B.MAPPING_PREDICATES) == 4
    for name in ("hasBroaderConceptualMatch", "hasRelatedConceptualMatch",
                 "historicallyCorrespondsTo", "ontologyEntityMapping"):
        assert any(p.endswith("#" + name) for p in B.MAPPING_PREDICATES), name
    for banned in (SKOS.exactMatch, SKOS.broadMatch, SKOS.closeMatch,
                   SKOS.relatedMatch, OWL.equivalentClass):
        assert str(banned) not in B.MAPPING_PREDICATES, banned


def test_the_four_category_roots_are_the_declared_ones():
    assert B.CATEGORY_ROOTS == {
        "http://purl.obolibrary.org/obo/BFO_0000016": "disposition",
        "http://purl.obolibrary.org/obo/BFO_0000023": "role",
        "http://purl.obolibrary.org/obo/BFO_0000015": "process",
        "https://www.commoncoreontologies.org/ont00000958": "information",
    }


def test_the_reviewed_other_set_is_the_single_expected_class():
    """`other` is not a catch-all. A second member means either a class
    outside the four roots or a support graph that failed to load, and
    both deserve a look rather than a silent bucket."""
    assert B.REVIEWED_OTHER == {
        "https://fandaws.com/ontology/bfo/valuenet-core#"
        "ValueRelatedRealizableEntity"}


# ======================================================================
# the index built from the live ontology
# ======================================================================


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("index")
    assert B.main(["--index", str(out / "class-index.json"),
                   "--coverage", str(out / "coverage.json")]) == 0
    return (json.loads((out / "class-index.json").read_text(encoding="utf-8")),
            json.loads((out / "coverage.json").read_text(encoding="utf-8")))


def test_the_index_validates_against_its_schema(built):
    from jsonschema import Draft7Validator

    index, _coverage = built
    errors = sorted(Draft7Validator(SCHEMA).iter_errors(index),
                    key=lambda e: list(e.path))
    assert not errors, "; ".join(
        "%s: %s" % ("/".join(str(x) for x in e.path), e.message[:100])
        for e in errors[:5])


def test_the_scope_is_the_five_class_producing_modules(built):
    """Exactly the modules the catalog marks indexed -- not the eleven
    deliverables, and not the two that declare no classes."""
    index, _c = built
    keys = {m["key"] for m in index["modules"]}
    assert keys == {"valuenet-core", "valuenet-schwartz-values",
                    "valuenet-folk", "valuenet-moral-foundations",
                    "valuenet-moral-epistemics"}


def test_no_vendored_class_became_a_record(built):
    """BFO and CCO are classification support. Their classes resolve
    parents and hold the roots; none is published as ValueNet's."""
    index, _c = built
    for record in index["classes"]:
        assert record["iri"].startswith("https://fandaws.com/"), record["iri"]
        assert "obolibrary" not in record["iri"]
        assert "commoncoreontologies" not in record["iri"]


def test_every_class_iri_and_identifier_is_unique(built):
    index, _c = built
    iris = [r["iri"] for r in index["classes"]]
    ids = [r["id"] for r in index["classes"]]
    assert len(set(iris)) == len(iris)
    assert len(set(ids)) == len(ids)


def test_every_record_is_complete(built):
    """Complete by construction: the build refuses rather than emitting a
    gap. Asserted anyway, because "the build would have failed" is not a
    property a reader of the data can check."""
    index, _c = built
    for r in index["classes"]:
        assert r["label"].strip()
        assert r["definition"].strip()
        assert r["parents"]
        assert r["category"] in {"disposition", "role", "process",
                                 "information", "other"}


def test_every_named_parent_resolves(built):
    """Against terms something declares to be a class, not against a
    prefix that looks right.

    The first version of this test accepted any parent whose IRI began
    with the obolibrary or CCO prefix. A typo in a BFO identifier keeps
    the prefix, so the check passed exactly the case it existed to
    catch.
    """
    import rdflib
    from rdflib.namespace import OWL, RDF

    from marep import ontology_source as onto

    index, _c = built
    declared = {r["iri"] for r in index["classes"]}
    for cid in B.SUPPORT_COMPONENTS:
        graph, _source = B.load(cid)
        declared |= {str(c) for c in graph.subjects(RDF.type, OWL.Class)
                     if isinstance(c, rdflib.URIRef)}
    declared |= set(B.CATEGORY_ROOTS)

    unresolved = [(r["id"], p) for r in index["classes"]
                  for p in r["parents"] if p not in declared]
    assert not unresolved, unresolved[:5]


def test_mapping_targets_are_asserted_iris_and_need_not_be_indexed(built):
    """The mappings point at other vocabularies. Requiring the target to
    be an indexed class would delete every real correspondence."""
    index, _c = built
    known = {r["iri"] for r in index["classes"]}
    seen, external = 0, 0
    for r in index["classes"]:
        for m in r["mappings"]:
            seen += 1
            assert m["predicate"] in B.MAPPING_PREDICATES, m["predicate"]
            assert m["target"].startswith(("http://", "https://"))
            if m["target"] not in known:
                external += 1
    assert seen, "no mapping was indexed at all"
    assert external, (
        "every mapping target is an indexed class, which would mean the "
        "mappings point inward rather than at the vocabularies they relate to")


def test_uncategorised_is_exactly_the_reviewed_class(built):
    index, coverage = built
    others = [r["iri"] for r in index["classes"] if r["category"] == "other"]
    assert set(others) == B.REVIEWED_OTHER
    assert coverage["uncategorised"] == sorted(B.REVIEWED_OTHER)


def test_the_output_is_sorted_and_not_in_graph_order(built):
    """rdflib iteration order is not stable, so a build that leaked it
    would differ between runs for no reason in the data."""
    index, _c = built
    labels = [(r["label"].casefold(), r["iri"]) for r in index["classes"]]
    assert labels == sorted(labels)
    for r in index["classes"]:
        assert r["parents"] == sorted(r["parents"])
        assert r["synonyms"] == sorted(r["synonyms"])
        assert r["mappings"] == sorted(
            r["mappings"], key=lambda m: (m["predicate"], m["target"]))
    assert index["modules"] == sorted(index["modules"],
                                      key=lambda m: m["key"])


def test_two_builds_produce_identical_bytes(tmp_path):
    """The property the site's verifiability rests on."""
    import hashlib

    digests = []
    for name in ("a", "b"):
        out = tmp_path / name
        assert B.main(["--index", str(out / "i.json"),
                       "--coverage", str(out / "c.json")]) == 0
        digests.append(hashlib.sha256(
            (out / "i.json").read_bytes()).hexdigest())
    assert digests[0] == digests[1]


# The digest of everything the index says about the ontology, with
# provenance removed. Recomputed by the test below from the normalisation
# written beside it -- not a figure copied out of a report. An earlier
# revision of this project cited a class-index digest that nothing in the
# tree could reproduce, which is how a number nobody can check survives.
NORMALISED_CONTENT = (
    "3e54f08bfaebd1e49798aac6982738f9dc345e47cdc2a8eddd09276737a3942c")

PROVENANCE_KEYS = {"source_commit"}
CONTENT_KEYS = {"classes", "format_version", "generated_by", "modules"}


def _normalised(index):
    """The index minus the fields that change without the corpus changing.

    source_commit moves every commit, so a digest including it measures
    the repository's history rather than what was extracted.
    """
    kept = {k: v for k, v in index.items() if k not in PROVENANCE_KEYS}
    return json.dumps(kept, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def test_no_field_escapes_the_content_or_provenance_split(built):
    """Guards the digest below.

    If a build timestamp were added, the pin would start failing on every
    run and the obvious repair would be to loosen it. Naming both sets
    means a new field is a decision about which side it falls on.
    """
    index, _coverage = built
    assert set(index) == CONTENT_KEYS | PROVENANCE_KEYS, (
        "the index gained or lost a top-level field; classify it as content "
        "or provenance before the digest below can mean anything")


def test_the_extracted_content_is_unchanged(built):
    """A pin, so that a change to the corpus or to the extractor is
    something somebody decided rather than something that happened.

    This is the measure the publication plan calls the normalised
    class-index content digest. It is expected to change when the
    ontology changes -- that is the point -- but only deliberately.
    """
    import hashlib

    index, _coverage = built
    digest = hashlib.sha256(_normalised(index).encode("utf-8")).hexdigest()
    assert digest == NORMALISED_CONTENT, (
        "the extracted class content changed. If that was intended, set "
        "NORMALISED_CONTENT to %s and say in the commit what changed and "
        "why." % digest)


def test_the_pin_ignores_provenance_but_not_content(built):
    """Falsifies the normalisation itself: a digest that ignored too much
    would pass this file's other tests without measuring anything."""
    import hashlib

    index, _coverage = built
    moved = dict(index, source_commit="0" * 40)
    assert _normalised(moved) == _normalised(index), (
        "the digest tracks the commit, so it would change on every commit")

    edited = json.loads(json.dumps(index))
    edited["classes"][0]["definition"] += " altered"
    assert _normalised(edited) != _normalised(index), (
        "the digest does not track definitions, so it is not measuring the "
        "content it claims to")
    assert (hashlib.sha256(_normalised(edited).encode("utf-8")).hexdigest()
            != NORMALISED_CONTENT)


def test_module_metadata_is_extracted_not_curated(built):
    """Each module's title, description and licence come from its own
    ontology header. site.json holds none of them."""
    index, _c = built
    site = json.loads(
        (layout.component("site.content").resolve() / "site.json")
        .read_text(encoding="utf-8"))
    blob = json.dumps(site)
    for m in index["modules"]:
        assert m["title"].strip() and m["description"].strip()
        assert m["license"] == "https://creativecommons.org/licenses/by/4.0/"
        assert m["title"] not in blob, (
            m["key"] + "'s title also appears in site.json")


def test_the_coverage_report_counts_what_the_index_holds(built):
    index, coverage = built
    assert coverage["classes"] == len(index["classes"])
    assert coverage["with_definition"] == len(index["classes"])
    # Per module, and per field: a global "187 of 187" stays at 100% while
    # one module loses every definition and another gains classes.
    for key, c in coverage["modules"].items():
        rows = [r for r in index["classes"] if r["module"] == key]
        assert c["classes"] == len(rows)
        assert c["with_label"] == sum(1 for r in rows if r["label"].strip())
        assert c["with_definition"] == sum(
            1 for r in rows if r["definition"].strip())
        assert c["with_named_parent"] == sum(1 for r in rows if r["parents"])
        assert c["with_label"] == c["with_definition"] == c["classes"], (
            key + " has a coverage gap, which the build should have refused")
    assert set(coverage["modules"]) == {m["key"] for m in index["modules"]}
    by_cat = {}
    for r in index["classes"]:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    assert coverage["categories"] == by_cat


def test_the_index_names_the_commit_it_was_read_from(built):
    import subprocess

    index, coverage = built
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO),
                          capture_output=True, text=True).stdout.strip()
    assert index["source_commit"] == head
    assert coverage["source_commit"] == head


def test_the_generated_data_is_not_committed():
    """It is generated into the artifact. A committed copy is a second
    description of the ontology that can drift from the ontology."""
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "--", "_site", "site/src/data"],
        cwd=str(REPO), capture_output=True, text=True).stdout.strip()
    assert not tracked, tracked.splitlines()[:3]


def test_the_builder_itself_derives_category_from_edges(monkeypatch):
    """Not just the helper it is supposed to call.

    A first falsification replaced the builder's `category_of` call with
    `"disposition" if iri.endswith("Disposition")` and the whole suite
    passed: on this corpus every class named that way is one, so the
    shortcut produced identical output. The unit test above proved a
    property of a function nothing required the builder to use.

    So the builder is run over a module constructed to disagree with
    itself: a class named `...Disposition` whose edges reach the role
    root, and a class named nothing in particular whose edges reach the
    disposition root. A name-based rule gets both backwards.
    """
    ns = "https://fandaws.com/ontology/bfo/valuenet-probe#"
    ont = rdflib.URIRef("https://fandaws.com/ontology/bfo/valuenet-probe.owl")
    misleading = rdflib.URIRef(ns + "MisleadingDisposition")
    plain = rdflib.URIRef(ns + "Unremarkable")

    module = rdflib.Graph()
    module.add((ont, RDF.type, OWL.Ontology))
    module.add((ont, DCTERMS.title, rdflib.Literal("Probe")))
    module.add((ont, DCTERMS.description, rdflib.Literal("A probe module.")))
    module.add((ont, DCTERMS.license, rdflib.URIRef(
        "https://creativecommons.org/licenses/by/4.0/")))
    for node, label, parent in (
            (misleading, "Misleading Disposition", BFO_ROLE),
            (plain, "Unremarkable", BFO_DISPOSITION)):
        module.add((node, RDF.type, OWL.Class))
        module.add((node, RDFS.label, rdflib.Literal(label)))
        module.add((node, SKOS.definition, rdflib.Literal("A probe class.")))
        module.add((node, RDFS.subClassOf, rdflib.URIRef(parent)))

    support = rdflib.Graph()
    for root in (BFO_ROLE, BFO_DISPOSITION):
        support.add((rdflib.URIRef(root), RDF.type, OWL.Class))

    entry = {"key": "valuenet-probe", "component": "probe", "indexed": True}
    monkeypatch.setattr(B, "catalog", lambda: [entry])
    monkeypatch.setattr(B, "REVIEWED_OTHER", set())
    monkeypatch.setattr(
        B, "load",
        lambda cid: (module, "probe.ttl") if cid == "probe"
        else (rdflib.Graph() if cid == B.OVERLAY_COMPONENT else support,
              cid + ".ttl"))

    index, _coverage = B.build()
    got = {r["id"]: r["category"] for r in index["classes"]}
    assert got == {"probe:MisleadingDisposition": "role",
                   "probe:Unremarkable": "disposition"}, got


# ======================================================================
# pipeline refusals, on modules built to be wrong
#
# Each of these once passed. The generator accepted a parent nothing
# declared, two modules claiming one class, a header chosen by traversal
# order, a mapping target silently dropped, a label that was not text,
# and an invalid record written to disk unvalidated. The unit tests above
# could not see any of it, because each defect lived in the pipeline
# rather than in a helper.
# ======================================================================


CC_BY = "https://creativecommons.org/licenses/by/4.0/"
PROBE_NS = "https://fandaws.com/ontology/bfo/probe#"


def _module_graph(ns, classes, headers=1, license_literal=False):
    """A minimal well-formed module, deviating only where asked."""
    g = rdflib.Graph()
    for n in range(headers):
        ont = rdflib.URIRef("https://fandaws.com/ontology/bfo/probe%d.owl" % n)
        g.add((ont, RDF.type, OWL.Ontology))
        g.add((ont, DCTERMS.title, rdflib.Literal("Probe")))
        g.add((ont, DCTERMS.description, rdflib.Literal("A probe module.")))
        g.add((ont, DCTERMS.license,
               rdflib.Literal(CC_BY) if license_literal
               else rdflib.URIRef(CC_BY)))
    for local, parent, extra in classes:
        node = rdflib.URIRef(ns + local)
        g.add((node, RDF.type, OWL.Class))
        g.add((node, RDFS.label, rdflib.Literal(local)))
        g.add((node, SKOS.definition, rdflib.Literal("A probe class.")))
        g.add((node, RDFS.subClassOf, rdflib.URIRef(parent)))
        for p, o in extra:
            g.add((node, p, o))
    return g


def _support():
    g = rdflib.Graph()
    for root in (BFO_ROLE, BFO_DISPOSITION):
        g.add((rdflib.URIRef(root), RDF.type, OWL.Class))
    return g


def _run(monkeypatch, modules, support=None):
    """Run the real build over synthetic modules."""
    entries = [{"key": k, "component": k, "indexed": True} for k, _g in modules]
    graphs = dict(modules)
    support = support if support is not None else _support()
    monkeypatch.setattr(B, "catalog", lambda: entries)
    monkeypatch.setattr(B, "REVIEWED_OTHER", set())
    monkeypatch.setattr(
        B, "load",
        lambda cid: (graphs[cid], cid + ".ttl") if cid in graphs
        else (rdflib.Graph() if cid == B.OVERLAY_COMPONENT else support,
              cid + ".ttl"))
    return B.build()


def test_a_parent_nothing_declares_is_refused_despite_a_real_prefix(
        monkeypatch):
    """The permissive version accepted any IRI appearing as a subject of
    any triple, and the integration test accepted anything with a
    BFO-looking prefix. Both pass a typo carrying one stray annotation.

    Here the parent has an impeccable obolibrary IRI and one annotation,
    and nothing declares it a class.
    """
    ghost = "http://purl.obolibrary.org/obo/BFO_9999999"
    support = _support()
    support.add((rdflib.URIRef(ghost), RDFS.label, rdflib.Literal("Ghost")))

    module = _module_graph(PROBE_NS, [("Orphan", ghost, [])])
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe", module)], support=support)
    assert "nothing declares to be a class" in str(exc.value)
    assert ghost in str(exc.value)


def test_the_same_class_declared_by_two_modules_is_refused(monkeypatch):
    """Compact identifiers are module-prefixed, so two modules claiming
    one class produced two records with different ids and different
    module attributions, and the uniqueness check saw no collision."""
    shared = [("Shared", BFO_DISPOSITION, [])]
    a = _module_graph(PROBE_NS, shared)
    b = _module_graph(PROBE_NS, shared)
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe-a", a), ("probe-b", b)])
    assert "declared by both" in str(exc.value)


def test_two_ontology_headers_are_refused(monkeypatch):
    """`next(...)` took whichever came first, so the module's title and
    licence depended on traversal order."""
    module = _module_graph(PROBE_NS, [("C", BFO_DISPOSITION, [])], headers=2)
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe", module)])
    assert "owl:Ontology resources" in str(exc.value)


def test_a_non_iri_mapping_target_is_refused_not_dropped(monkeypatch):
    """Silently omitting it publishes the class as unmapped while the
    ontology says otherwise."""
    predicate = rdflib.URIRef(B.MAPPING_PREDICATES[0])
    module = _module_graph(
        PROBE_NS,
        [("C", BFO_DISPOSITION, [(predicate, rdflib.Literal("not an IRI"))])])
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe", module)])
    assert "non-IRI target" in str(exc.value)


def test_a_label_that_is_not_a_literal_is_refused(monkeypatch):
    """An IRI stringifies to something that looks like a name and would be
    published as one."""
    module = _module_graph(PROBE_NS, [("C", BFO_DISPOSITION, [])])
    node = rdflib.URIRef(PROBE_NS + "C")
    module.remove((node, RDFS.label, None))
    module.add((node, RDFS.label, rdflib.URIRef("https://ex.invalid/looks-ok")))
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe", module)])
    assert "not a literal" in str(exc.value)


def test_a_licence_that_is_not_an_iri_is_refused(monkeypatch):
    """The licence is an identifier, not prose about one."""
    module = _module_graph(PROBE_NS, [("C", BFO_DISPOSITION, [])],
                           license_literal=True)
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe", module)])
    assert "not an IRI" in str(exc.value)


def test_classes_in_two_namespaces_are_refused(monkeypatch):
    """The namespace was invented by string-replacing ".owl" with "#",
    which asserts nothing about the classes and happens to match. Derived
    from the class IRIs, a module that straddles two fails."""
    module = _module_graph(PROBE_NS, [("A", BFO_DISPOSITION, [])])
    other = rdflib.URIRef("https://fandaws.com/ontology/bfo/elsewhere#B")
    module.add((other, RDF.type, OWL.Class))
    module.add((other, RDFS.label, rdflib.Literal("B")))
    module.add((other, SKOS.definition, rdflib.Literal("A probe class.")))
    module.add((other, RDFS.subClassOf, rdflib.URIRef(BFO_DISPOSITION)))
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe", module)])
    assert "namespaces" in str(exc.value)


def test_the_namespace_is_derived_from_the_class_iris(monkeypatch):
    """And is the one the classes actually live in."""
    module = _module_graph(PROBE_NS, [("C", BFO_DISPOSITION, [])])
    index, _coverage = _run(monkeypatch, [("probe", module)])
    assert index["modules"][0]["namespace"] == PROBE_NS


def test_the_pipeline_validates_against_the_schema_before_writing(
        monkeypatch, tmp_path):
    """Validation lived only in the test suite, so a generator change that
    broke the contract shipped and was reported afterwards, against an
    artifact already on disk.

    Forced by making the builder emit a record the schema rejects.
    """
    good, _c = B.build()
    broken = json.loads(json.dumps(good))
    broken["classes"][0]["category"] = "not-a-category"
    monkeypatch.setattr(B, "build", lambda: (broken, {"modules": {}}))

    with pytest.raises(SystemExit) as exc:
        B.main(["--index", str(tmp_path / "i.json"),
                "--coverage", str(tmp_path / "c.json")])
    assert "does not satisfy" in str(exc.value)
    assert not (tmp_path / "i.json").exists(), (
        "an invalid index was written before validation refused it")


def test_the_schema_is_published_at_the_id_it_claims():
    """A schema naming a URL the build does not serve is a dangling
    reference in the document whose job is to say what the data must look
    like."""
    site = json.loads(
        (layout.component("site.content").resolve() / "site.json")
        .read_text(encoding="utf-8"))
    expected = (site["deployment"]["public_url"]
                + "schemas/class-index.schema.json")
    assert SCHEMA["$id"] == expected, SCHEMA["$id"]


def test_a_mapping_on_an_undeclared_subject_is_refused(monkeypatch):
    """The gap the outward walk left.

    Mappings are emitted by visiting each indexed class, so an assertion
    whose subject is not indexed is never visited. A misspelled ValueNet
    IRI keeps the namespace and looks entirely plausible; before the
    reverse scan it vanished without a trace anywhere.
    """
    predicate = rdflib.URIRef(B.MAPPING_PREDICATES[0])
    module = _module_graph(PROBE_NS, [("Real", BFO_DISPOSITION, [])])
    typo = rdflib.URIRef(PROBE_NS + "Reall")
    module.add((typo, predicate, rdflib.URIRef("https://ex.invalid/target")))

    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe", module)])
    assert "neither an indexed class nor a declared property" in str(exc.value)
    assert "Reall" in str(exc.value)


def test_a_mapping_on_a_declared_property_is_recorded_not_dropped(
        monkeypatch):
    """Two exist in the live ontology, on contravenes and
    dyadicOppositeOf. A class index cannot carry them, but out of scope
    and lost are different things."""
    predicate = rdflib.URIRef(B.MAPPING_PREDICATES[0])
    module = _module_graph(PROBE_NS, [("Real", BFO_DISPOSITION, [])])
    prop = rdflib.URIRef(PROBE_NS + "relatesTo")
    module.add((prop, RDF.type, OWL.ObjectProperty))
    module.add((prop, predicate, rdflib.URIRef("https://ex.invalid/target")))

    index, coverage = _run(monkeypatch, [("probe", module)])
    assert coverage["mappings_on_properties"] == [{
        "subject": str(prop), "predicate": str(predicate),
        "target": "https://ex.invalid/target"}]
    assert all(not r["mappings"] for r in index["classes"]), (
        "a property mapping was attributed to a class")


def test_every_asserted_mapping_reaches_the_index(monkeypatch):
    """Both directions, on the live ontology: nothing asserted is missing
    and nothing emitted is unasserted."""
    index, coverage = B.build()
    emitted = {(r["iri"], m["predicate"], m["target"])
               for r in index["classes"] for m in r["mappings"]}
    on_properties = {(m["subject"], m["predicate"], m["target"])
                     for m in coverage["mappings_on_properties"]}

    annotations = rdflib.Graph()
    for entry in B.catalog():
        graph, _s = B.load(entry["component"])
        annotations += graph
    overlay, _s = B.load(B.OVERLAY_COMPONENT)
    annotations += overlay

    asserted = {(str(s), p, str(o))
                for p in B.MAPPING_PREDICATES
                for s, o in annotations.subject_objects(rdflib.URIRef(p))}
    assert asserted == emitted | on_properties, (
        "asserted but nowhere: %s; emitted but unasserted: %s"
        % (sorted(asserted - (emitted | on_properties))[:3],
           sorted((emitted | on_properties) - asserted)[:3]))
    assert on_properties, (
        "no property mapping was found, so this test is not exercising the "
        "case that motivated the reverse scan")


def test_the_overlay_declaring_a_class_is_refused(monkeypatch):
    """The overlay contributes mappings and is not indexed, so a class
    declared there would be absent from the catalog with nothing saying
    so."""
    overlay = rdflib.Graph()
    stray = rdflib.URIRef(PROBE_NS + "DeclaredInTheOverlay")
    overlay.add((stray, RDF.type, OWL.Class))

    module = _module_graph(PROBE_NS, [("C", BFO_DISPOSITION, [])])
    entries = [{"key": "probe", "component": "probe", "indexed": True}]
    monkeypatch.setattr(B, "catalog", lambda: entries)
    monkeypatch.setattr(B, "REVIEWED_OTHER", set())
    monkeypatch.setattr(
        B, "load",
        lambda cid: (module, "probe.ttl") if cid == "probe"
        else (overlay, "overlay.ttl") if cid == B.OVERLAY_COMPONENT
        else (_support(), cid + ".ttl"))

    with pytest.raises(SystemExit) as exc:
        B.build()
    assert "loaded as a mapping overlay" in str(exc.value)


def test_the_live_overlay_declares_no_classes():
    """Asserted against the file, so the guard above is not policing an
    empty set."""
    graph, source = B.load(B.OVERLAY_COMPONENT)
    classes = [str(c) for c in graph.subjects(RDF.type, OWL.Class)
               if isinstance(c, rdflib.URIRef)]
    assert not classes, source + " declares " + str(classes[:3])
    assert len(graph) > 0, source + " is empty, so this proves nothing"


def test_a_blank_node_ontology_header_beside_a_named_one_is_refused(
        monkeypatch):
    """Filtering blank nodes out before counting meant a module with one
    named header and one blank-node header counted a single header and
    passed, leaving a second ontology description unread."""
    module = _module_graph(PROBE_NS, [("C", BFO_DISPOSITION, [])])
    module.add((rdflib.BNode(), RDF.type, OWL.Ontology))
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe", module)])
    assert "owl:Ontology resources" in str(exc.value)


def test_an_ontology_declared_only_on_a_blank_node_is_refused(monkeypatch):
    """A module has to be nameable to be cited, linked or downloaded."""
    module = _module_graph(PROBE_NS, [("C", BFO_DISPOSITION, [])])
    for header in list(module.subjects(RDF.type, OWL.Ontology)):
        module.remove((header, None, None))
    blank = rdflib.BNode()
    module.add((blank, RDF.type, OWL.Ontology))
    module.add((blank, DCTERMS.title, rdflib.Literal("Nameless")))
    module.add((blank, DCTERMS.description, rdflib.Literal("No IRI.")))
    module.add((blank, DCTERMS.license, rdflib.URIRef(CC_BY)))

    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, [("probe", module)])
    assert "blank node" in str(exc.value)
