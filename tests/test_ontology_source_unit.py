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
