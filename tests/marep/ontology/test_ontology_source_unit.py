"""Unit tests for the ontology substrate source (MAREP v2.2 §7).

The failure mode this component has to avoid is not crashing — it is asserting
something false. A substrate record is what a finding cites to become
`confirmed`, so a wrong metric produces a wrong finding that looks grounded.
Every test below pins a false fact the first run actually emitted.

These exercise `ontology_source` directly: a corpus on disk in, metrics out.
The tests that build a whole substrate through `ingest` live in
`test_ontology_source_integration.py`, because the two halves answer to
different owners once the tests tree is split by subject — this file follows
`marep/ontology`, that one follows the integration group.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from marep import ontology_source as onto

from _support import FRAGMENT, TURTLE, write_ttl

# ======================================================================
# false fact 1: the extension is not the format
# ======================================================================



def test_owl_extension_holding_turtle_still_parses(tmp_path: Path):
    """The first run reported six good BFO files as unparseable.

    Those six .owl files held Turtle, and trusting the suffix produced a
    metric asserting a failure that had not happened. The repository no longer
    contains them — every ontology file is now a .ttl holding Turtle, and
    `test_ontology_artifacts` asserts it — so this covers foreign input rather
    than anything committed here. Kept because the defect it describes is a
    property of the measuring code, which will meet such a file again.
    """
    p = write_ttl(tmp_path, "module.owl", TURTLE)
    facts = onto.measure_file(p, tmp_path)
    assert facts.parses is True
    assert facts.parsed_as == "turtle"
    assert facts.classes == 1



def test_a_genuinely_broken_file_still_reports_failure(tmp_path: Path):
    p = write_ttl(tmp_path, "broken.ttl", "@prefix : <http://x/> .\n:a :b ")
    facts = onto.measure_file(p, tmp_path)
    assert facts.parses is False
    assert facts.parse_error

# ======================================================================
# false fact 2: prose is not a prefix
# ======================================================================



def test_prefixes_inside_literals_are_not_uses(tmp_path: Path):
    """The first run reported OBI, RO and MFTriggers as undeclared prefixes in
    files that declare everything, because the text appeared inside an
    rdfs:comment."""
    assert onto.undeclared_prefixes(TURTLE) == []



def test_prefix_check_is_not_applied_to_rdf_xml(tmp_path: Path):
    """A Turtle rule run over RDF/XML reads prose as prefixes.

    folk.owl was reported as using undeclared prefixes named "Justice",
    "cohabitation" and "have" — English words followed by colons inside XML
    text nodes.
    """
    xml = """<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
  <rdf:Description rdf:about="http://example.org/A">
    <rdfs:comment>Justice: a value. See also cohabitation: shared living.</rdfs:comment>
  </rdf:Description>
</rdf:RDF>
"""
    p = tmp_path / "doc.owl"
    p.write_text(xml, encoding="utf-8")
    facts = onto.measure_file(p, tmp_path)
    assert facts.parses and facts.parsed_as == "xml"
    assert facts.undeclared_prefixes == [], \
        "a Turtle prefix rule must not be applied to RDF/XML"



def test_an_unparseable_file_still_gets_the_prefix_check(tmp_path: Path):
    """That is the case where naming the missing prefix is most useful."""
    p = tmp_path / "frag.ttl"
    p.write_text(FRAGMENT, encoding="utf-8")
    facts = onto.measure_file(p, tmp_path)
    assert not facts.parses
    assert facts.undeclared_prefixes == ["folk", "vcvf"]



def test_a_real_undeclared_prefix_is_still_caught():
    assert onto.undeclared_prefixes(FRAGMENT) == ["folk", "vcvf"]



def test_comments_are_not_scanned():
    text = '@prefix owl: <http://www.w3.org/2002/07/owl#> .\n# see foo:bar for detail\n'
    assert onto.undeclared_prefixes(text) == []

# ======================================================================
# false fact 3: two numbers answering to one reference
# ======================================================================



def test_metric_references_are_unique(tmp_path: Path):
    """`classes_total:bfo-layer` was emitted twice with different values.

    The schema cannot catch it — the ids differ — so evidence citing that
    reference would resolve to whichever record happened to be found first.
    """
    for n in range(3):
        write_ttl(tmp_path, f"m{n}.ttl", TURTLE)
    facts = [onto.measure_file(p, tmp_path) for p in onto.discover(tmp_path)]
    metrics = onto.group_metrics(facts) + onto.suite_metrics(tmp_path, facts)
    refs = [m.ref for m in metrics]
    assert len(refs) == len(set(refs)), f"duplicate refs: {sorted({r for r in refs if refs.count(r) > 1})}"

# ======================================================================
# a scoped check has to measure its own scope
# ======================================================================



def test_the_grounding_check_reports_what_it_does_not_cover(tmp_path: Path):
    """Three live agents read `classes_reaching_bfo_root: 179/179` as "the
    ontology is grounded". It does not say that: the check is scoped to one
    layer, and the rest of the corpus is simply unmeasured.

    Putting the scope in the record's ref was not enough. An absence has to be
    measured to be citable, rather than left to be inferred from the presence
    of something narrower.
    """
    write_ttl(tmp_path, "a.ttl", TURTLE)
    write_ttl(tmp_path, "b.ttl", TURTLE.replace("example.org/A", "example.org/B"))
    facts = [onto.measure_file(p, tmp_path) for p in onto.discover(tmp_path)]
    metrics = {m.check: m for m in onto.suite_metrics(tmp_path, facts)}

    if "classes_distinct_in_corpus" not in metrics:
        pytest.skip("suite metrics need the BFO modules present")
    total = metrics["classes_distinct_in_corpus"].value
    measured = metrics["classes_measured_for_grounding"].value
    unmeasured = metrics["classes_unmeasured_for_grounding"].value
    assert total == measured + unmeasured, "the three numbers must reconcile"



def test_distinct_class_count_does_not_double_count_pairs(tmp_path: Path):
    """`classes_sum_over_files` counts a .ttl/.owl pair twice by design.
    The corpus figure must not, or it repeats the error it exists to correct.
    """
    write_ttl(tmp_path, "m.ttl", TURTLE)
    write_ttl(tmp_path, "m.owl", TURTLE)
    facts = [onto.measure_file(p, tmp_path) for p in onto.discover(tmp_path)]
    union = set()
    for f in facts:
        union |= f.class_iris
    assert len(union) == 1, "one class declared in two serializations is one class"
    assert sum(f.classes for f in facts) == 2, "the per-file sum still counts both"

# ======================================================================
# sums are sums
# ======================================================================



def test_group_counts_say_they_are_sums(tmp_path: Path):
    """A module kept as both .ttl and .owl contributes twice.

    Calling that `classes_total` invites a finding to cite 360 classes for a
    layer holding 179.
    """
    write_ttl(tmp_path, "m.ttl", TURTLE)
    write_ttl(tmp_path, "m.owl", TURTLE)
    facts = [onto.measure_file(p, tmp_path) for p in onto.discover(tmp_path)]
    metrics = {m.check: m for m in onto.group_metrics(facts)}
    assert "classes_sum_over_files" in metrics
    assert "classes_total" not in metrics
    assert metrics["classes_sum_over_files"].value == 2, "the same module counted twice"
    assert "twice" in metrics["classes_sum_over_files"].detail

# ======================================================================
# a check must not mistake "grounded elsewhere" for "ungrounded"
# ======================================================================

BFO_ROOTED = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
<http://example.org/A> a owl:Class ; rdfs:subClassOf obo:BFO_0000016 .
"""

DUL_ROOTED = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> .
<http://example.org/B> a owl:Class ; rdfs:subClassOf dul:Description .
"""

UNROOTED = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
<http://example.org/C> a owl:Class .
"""

# ======================================================================
# a check must not mistake "grounded elsewhere" for "ungrounded"
# ======================================================================



def test_dul_rooted_classes_are_not_reported_as_ungrounded(tmp_path: Path):
    """Run 1 said the hygiene checks covered 179 of ~2,900 classes, which was
    true. Widening the BFO check alone would have swapped one distortion for
    another: the DUL layer is grounded in DOLCE, and a BFO-only question calls
    it broken. The check asks what a class roots in, not whether it roots in BFO.
    """
    write_ttl(tmp_path, "bfo.ttl", BFO_ROOTED)
    write_ttl(tmp_path, "dul.ttl", DUL_ROOTED)
    write_ttl(tmp_path, "none.ttl", UNROOTED)
    facts = [onto.measure_file(p, tmp_path) for p in onto.discover(tmp_path)]
    m = {(x.check, x.scope): x.value for x in onto.rooting_metrics(tmp_path, facts)}

    scope = "repository-root"
    assert m[("classes_declared", scope)] == 3
    assert m[("classes_rooted_in_bfo", scope)] == 1
    assert m[("classes_rooted_in_dul", scope)] == 1, "DUL rooting is rooting"
    assert m[("classes_with_no_upper_root", scope)] == 1, "only the genuine orphan"



def test_shacl_reports_the_denominator(tmp_path: Path):
    """`0 violations` over a graph nothing targets is vacuous. Run 1 read it as
    a clean bill of health for a corpus most of which never entered the graph.
    """
    metrics = {m.check for m in onto.shacl_metrics(Path(".").resolve())}
    if not metrics:
        pytest.skip("no shapes present")
    assert "shacl_focus_nodes" in metrics, "a violation count needs a denominator"
    assert "shacl_files_validated" in metrics

# ======================================================================
# the document base, and what resolves against it
# ======================================================================

#: The one relative IRI reference known to exist in the corpus.
#:
#: `ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl` writes
#: `ns7:hasDataValue <1>`, which is a relative IRI reference and not the
#: number it looks like. It is upstream source-data debt with its own
#: remediation task; a stable base makes the measurement reproducible
#: without making the term correct.
KNOWN_RELATIVE_IRIS = {
    "ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl":
        ["ThatsAllFolks/MFRC_1k_graphs/1"],
}


def test_the_document_base_is_absolute_and_versioned():
    """A relative base would put the checkout path back in the graph, and
    an unversioned one would let the rule change without any baseline
    showing that it had."""
    assert onto.SOURCE_BASE.startswith("https://")
    assert onto.SOURCE_BASE.endswith("/v1/"), onto.SOURCE_BASE


def test_the_public_id_is_derived_from_the_relative_path():
    got = onto.public_id("ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl")
    assert got == onto.SOURCE_BASE + \
        "ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl"
    # a path with a space has to survive as a usable IRI
    # A synthetic name with a space. The repository does contain one, but
    # naming it here would put a literal that moved into this file and
    # the coverage inventory would demand an allowance for an example.
    assert " " not in onto.public_id("docs/A Name With Spaces.md")
    assert "%20" in onto.public_id("docs/A Name With Spaces.md")


def test_identical_bytes_at_two_paths_are_two_documents(tmp_path: Path):
    """The cache key includes the path, not only the checksum.

    Two copies of a file containing a relative IRI resolve it against
    their own bases, so they are different graphs. Keyed by checksum
    alone the second copy silently received the first one's absolute
    IRIs."""
    onto.clear_graph_cache()
    body = ("@prefix ex: <https://example.invalid/> ." + chr(10)
            + "ex:s ex:p <1> ." + chr(10))
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    for d in ("a", "b"):
        (tmp_path / d / "g.ttl").write_text(body, encoding="utf-8")
    facts = [onto.measure_file(p, tmp_path) for p in onto.discover(tmp_path)]
    assert len(facts) == 2
    objects = set()
    for f in facts:
        for _s, _p, o in onto.graph_for(tmp_path, f):
            objects.add(str(o))
    assert len(objects) == 2, (
        "the two copies resolved to one IRI, so one cache entry served "
        "both documents: " + str(objects))


@pytest.mark.slow
def test_the_corpus_holds_no_unrecorded_relative_iri():
    """Every IRI that resolved against the base is accounted for.

    A relative IRI is invisible until something resolves it, and what it
    resolves to depends on where the file is. One of them made the whole
    corpus digest a function of the checkout directory for the entire
    migration. A second one appearing unannounced is the same defect
    again, so it fails here rather than being absorbed."""
    import rdflib
    from marep import layout

    repo = layout.repository_root()
    found: dict[str, set] = {}
    for path in onto.discover(repo):
        rel = path.relative_to(repo).as_posix()
        fact = onto.measure_file(path, repo)
        if not fact.parses:
            continue
        # Against the base itself, not the file's own public id. A
        # relative reference replaces the last path segment, so `<1>` in
        # .../MFRC_1k_graphs/357_GRAPH.ttl resolves to
        # .../MFRC_1k_graphs/1 and never begins with the document's own
        # id. Matching on that found nothing at all, including the one
        # occurrence known to be there.
        for triple in onto.graph_for(repo, fact):
            for term in triple:
                if isinstance(term, rdflib.URIRef) and \
                        str(term).startswith(onto.SOURCE_BASE):
                    found.setdefault(rel, set()).add(
                        str(term)[len(onto.SOURCE_BASE):])

    unexpected = {f: sorted(v) for f, v in found.items()
                  if sorted(v) != KNOWN_RELATIVE_IRIS.get(f)}
    assert not unexpected, (
        "relative IRI reference(s) not in the recorded inventory. Each one resolves "
        "against the document base, so it is a term whose value depends on "
        "where the file sits: " + str(unexpected))
    missing = set(KNOWN_RELATIVE_IRIS) - set(found)
    assert not missing, (
        "the recorded relative IRI is gone from " + str(missing) + "; if it was "
        "fixed, remove it from KNOWN_RELATIVE_IRIS in the same commit")

#: A file whose content depends on its document base: a relative IRI as
#: an import, another as a class. Both resolve against whatever base the
#: parser was given, so measuring it twice from two roots is the direct
#: test of whether the base is stable.
BASE_SENSITIVE = (
    "@prefix owl: <http://www.w3.org/2002/07/owl#> ." + chr(10)
    + "<> a owl:Ontology ; owl:imports <other.ttl> ." + chr(10)
    + "<Thing> a owl:Class ." + chr(10)
)


def _plant(root: Path) -> Path:
    d = root / "sub"
    d.mkdir(parents=True)
    (d / "g.ttl").write_text(BASE_SENSITIVE, encoding="utf-8")
    return root


def test_the_same_relative_path_under_two_roots_measures_the_same(tmp_path: Path):
    """Two roots, one relative path, identical bytes.

    Everything a measurement reports about this file has to come from the
    file, not from where the file is. While measure_file let rdflib take
    the base from the absolute path, the imports and the class IRI
    differed between two roots holding byte-identical content -- and the
    corpus digest inherited the difference, which is how it came to
    depend on the checkout directory.

    The cache is cleared between roots on purpose. Keyed by content alone
    the second root would be served the first root's graph and the test
    would pass without measuring anything."""
    roots = [_plant(tmp_path / "r1"),
             _plant(tmp_path / "a-considerably-longer-root-name")]

    seen = []
    for root in roots:
        onto.clear_graph_cache()
        facts = [onto.measure_file(q, root) for q in onto.discover(root)]
        assert len(facts) == 1 and facts[0].parses, facts
        merged = onto.merged_graph(root, facts)
        seen.append({
            "rel": facts[0].rel,
            "imports": sorted(facts[0].imports or []),
            "class_iris": sorted(facts[0].class_iris),
            "triples": sorted("%s %s %s" % (a.n3(), b.n3(), c.n3())
                              for a, b, c in merged),
        })

    assert seen[0] == seen[1], (
        "the same file measured differently from two roots; the document "
        "base is still coming from the filesystem"
    )
    blob = str(seen[0])
    assert str(roots[0]) not in blob and str(roots[1]) not in blob, (
        "a root path leaked into the measurement")
    assert onto.SOURCE_BASE in blob, (
        "nothing resolved against the stable base, so this file no longer "
        "exercises the property it was written for")
