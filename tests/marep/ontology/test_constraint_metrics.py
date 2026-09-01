# SPDX-License-Identifier: Apache-2.0
"""What the corpus asserts about its own terms, and what it leaves open.

Run 2 asks what this corpus treats as true without ever saying so. A finding of
that shape — "sibling dispositions are never declared disjoint" — has no
admissible evidence under the earlier records, because the absence of an axiom
is a fact about no file, no commit and no metric.

These checks supply that evidence, and every one of them reports a population
alongside the subset carrying the axiom. The reason is the failure this module
has now made three times: a bare count invites a conclusion it does not
support. "1,840 properties have no domain" reads as 1,840 omissions, and some
of those properties may be deliberately polymorphic. The denominator forces a
finding to argue rather than point.
"""

from __future__ import annotations

from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from marep import ontology_source as onto  # noqa: E402

P = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <http://example.org/x#> .
"""


def facts_for(tmp_path: Path, **files) -> list:
    out = []
    for name, body in files.items():
        p = tmp_path / f"{name}.ttl"
        p.write_text(body, encoding="utf-8")
        out.append(onto.measure_file(p, tmp_path))
    return out


def value_of(metrics, check, scope="repository-root"):
    for m in metrics:
        if m.check == check and m.scope == scope:
            return m.value
    return None


def detail_of(metrics, check, scope="repository-root"):
    for m in metrics:
        if m.check == check and m.scope == scope:
            return m.detail
    return ""


# ======================================================================
# declaration is a corpus-wide question, not a group-wide one
# ======================================================================

def test_a_predicate_declared_in_another_file_is_not_undeclared(tmp_path: Path):
    """The BFO case, in miniature.

    The BFO layer uses BFO_0000055 without declaring it; the vendored
    bfo-core.ttl declares it and merely sits in another group. Scoping the
    lookup to the group reported four properties as undeclared when the corpus
    declares all four. A group boundary is a fact about `ontology_source`'s
    filing, not about the ontology.
    """
    facts = facts_for(
        tmp_path,
        uses=P + ":a :p :b .\n",
        declares=P + ":p a owl:ObjectProperty .\n",
    )
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "predicates_used_but_not_declared") == 0


def test_a_predicate_nothing_declares_is_reported(tmp_path: Path):
    facts = facts_for(tmp_path, uses=P + ":a :ghost :b .\n")
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "predicates_used_but_not_declared") == 1
    assert "ghost" in detail_of(metrics, "predicates_used_but_not_declared")


def test_builtin_vocabulary_is_not_counted_as_undeclared(tmp_path: Path):
    """rdf:, rdfs:, owl:, skos: and dc: are not this repository's to declare."""
    facts = facts_for(tmp_path, x=P + ":A a owl:Class ; rdfs:label 'A' ; "
                                    "rdfs:subClassOf :B .\n")
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "predicates_used_but_not_declared") == 0


# ======================================================================
# domain, range and characteristics
# ======================================================================

def test_a_property_with_no_domain_is_counted(tmp_path: Path):
    facts = facts_for(tmp_path, x=P + """
    :p a owl:ObjectProperty .
    :q a owl:ObjectProperty ; rdfs:domain :A ; rdfs:range :B .
    """)
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "properties_declared") == 2
    assert value_of(metrics, "properties_without_domain") == 1
    assert value_of(metrics, "properties_without_range") == 1


def test_the_population_travels_with_the_count(tmp_path: Path):
    """Without the denominator the count reads as a list of omissions."""
    facts = facts_for(tmp_path, x=P + ":p a owl:ObjectProperty .\n")
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert "of 1 declared" in detail_of(metrics, "properties_without_domain")


def test_an_inverse_counts_as_a_characteristic(tmp_path: Path):
    facts = facts_for(tmp_path, x=P + """
    :p a owl:ObjectProperty ; owl:inverseOf :q .
    :q a owl:ObjectProperty .
    :r a owl:ObjectProperty .
    """)
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "properties_without_characteristics") == 1


# ======================================================================
# sibling sets
# ======================================================================

def test_siblings_with_no_disjointness_are_counted(tmp_path: Path):
    facts = facts_for(tmp_path, x=P + """
    :A a owl:Class . :B a owl:Class . :Parent a owl:Class .
    :A rdfs:subClassOf :Parent . :B rdfs:subClassOf :Parent .
    """)
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "sibling_sets") == 1
    assert value_of(metrics, "sibling_sets_without_disjointness") == 1


def test_a_declared_disjointness_settles_a_sibling_set(tmp_path: Path):
    facts = facts_for(tmp_path, x=P + """
    :A a owl:Class . :B a owl:Class . :Parent a owl:Class .
    :A rdfs:subClassOf :Parent . :B rdfs:subClassOf :Parent .
    :A owl:disjointWith :B .
    """)
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "sibling_sets_without_disjointness") == 0


def test_all_disjoint_classes_settles_a_sibling_set(tmp_path: Path):
    """The list form has to count too, or the check reports false gaps."""
    facts = facts_for(tmp_path, x=P + """
    :A a owl:Class . :B a owl:Class . :Parent a owl:Class .
    :A rdfs:subClassOf :Parent . :B rdfs:subClassOf :Parent .
    [] a owl:AllDisjointClasses ; owl:members ( :A :B ) .
    """)
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "sibling_sets_without_disjointness") == 0


def test_the_sibling_check_does_not_call_openness_a_shortfall(tmp_path: Path):
    """Folk value vocabularies are meant to overlap.

    The wording is load-bearing: an agent reading this metric has to be able to
    conclude "intentionally unconstrained", which is one of the three answers
    Run 2 is scoped to produce.
    """
    facts = facts_for(tmp_path, x=P + """
    :A a owl:Class . :B a owl:Class . :Parent a owl:Class .
    :A rdfs:subClassOf :Parent . :B rdfs:subClassOf :Parent .
    """)
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert "domain question" in detail_of(metrics, "sibling_sets_without_disjointness")


# ======================================================================
# classes carrying nothing but their position
# ======================================================================

def test_a_class_with_only_a_parent_has_no_necessary_conditions(tmp_path: Path):
    facts = facts_for(tmp_path, x=P + """
    :A a owl:Class ; rdfs:subClassOf :Parent .
    :Parent a owl:Class .
    """)
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "classes_without_necessary_conditions") == 2


def test_a_restriction_counts_as_a_necessary_condition(tmp_path: Path):
    facts = facts_for(tmp_path, x=P + """
    :A a owl:Class ; rdfs:subClassOf [ a owl:Restriction ;
        owl:onProperty :p ; owl:someValuesFrom :B ] .
    """)
    metrics = onto.constraint_metrics(tmp_path, facts)
    assert value_of(metrics, "classes_without_necessary_conditions") == 0


# ======================================================================
# SHACL reach, from the other side
# ======================================================================

def test_a_populated_class_with_no_shape_is_named(tmp_path: Path):
    """The complement of shacl_focus_nodes: what the shapes fail to reach."""
    (tmp_path / "BFO").mkdir()
    (tmp_path / "BFO" / "x-shapes.ttl").write_text(
        "@prefix sh: <http://www.w3.org/ns/shacl#> .\n"
        "@prefix f: <http://www.ontologydesignpatterns.org/ont/values/x#> .\n"
        "[] a sh:NodeShape ; sh:targetClass f:Covered .\n", encoding="utf-8")
    facts = facts_for(tmp_path, data="""
@prefix f: <http://www.ontologydesignpatterns.org/ont/values/x#> .
f:one a f:Covered . f:two a f:Uncovered . f:three a f:Uncovered .
""")
    metrics = onto.shape_coverage_metrics(tmp_path, facts)
    assert value_of(metrics, "populated_classes") == 2
    assert value_of(metrics, "populated_classes_without_a_shape") == 1
    assert "Uncovered (2)" in detail_of(metrics, "populated_classes_without_a_shape")
