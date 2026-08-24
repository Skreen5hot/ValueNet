"""The reasoner verdict has to carry its own reach.

`reasoner_consistent: 1` was the most over-readable number this repository
produces. It was true of the BFO layer while that layer contained no
individuals at all and declared 32 axioms capable of causing a contradiction
against 277 `subClassOf` — a check almost nothing could have failed, reported
in a form indistinguishable from a check that had searched hard and found
nothing.

That is the same defect as the four false facts `ontology_source` was fixed for
before, and as the equal triple counts that let an agent conclude `folk.owl` and
`folk_aligned.ttl` were duplicates when they are not isomorphic: an accurate
number that invites a conclusion it does not support. These tests hold the
denominators next to the verdict.

None of them need a JRE. The helpers are pure functions of a graph, which is
why they were extracted from `reasoner_metrics` in the first place.
"""

from __future__ import annotations

import pytest

rdflib = pytest.importorskip("rdflib")

from marep import ontology_source as onto  # noqa: E402


def graph_of(turtle: str):
    g = rdflib.Graph()
    g.parse(data=turtle, format="turtle")
    return g


PREAMBLE = """
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix : <http://example.org/x#> .
"""


# ======================================================================
# an import is resolved if anything answers to the IRI, under either name
# ======================================================================

def test_version_iri_resolves_an_import():
    """The BFO case: imported by version IRI, declared by ontology IRI.

    Matching ontology IRIs alone reported BFO 2020 as an unresolved import
    while every one of its axioms was loaded.
    """
    g = graph_of(PREAMBLE + """
    <http://example.org/mine> a owl:Ontology ;
        owl:imports <http://purl.obolibrary.org/obo/bfo/2020/bfo-core.ttl> .
    <http://purl.obolibrary.org/obo/bfo.owl> a owl:Ontology ;
        owl:versionIRI <http://purl.obolibrary.org/obo/bfo/2020/bfo-core.ttl> .
    """)
    assert onto._unresolved_imports(g) == set()


def test_ontology_iri_resolves_an_import():
    g = graph_of(PREAMBLE + """
    <http://example.org/mine> a owl:Ontology ;
        owl:imports <http://example.org/other> .
    <http://example.org/other> a owl:Ontology .
    """)
    assert onto._unresolved_imports(g) == set()


def test_a_genuinely_absent_import_is_still_reported():
    """The check must not become permissive in the course of becoming correct."""
    g = graph_of(PREAMBLE + """
    <http://example.org/mine> a owl:Ontology ;
        owl:imports <http://example.org/nowhere> .
    """)
    assert onto._unresolved_imports(g) == {"http://example.org/nowhere"}


# ======================================================================
# the machinery that lets a reasoner run fail
# ======================================================================

def test_subclass_axioms_alone_cannot_fail():
    """A taxonomy with no disjointness is consistent by construction."""
    g = graph_of(PREAMBLE + """
    :A a owl:Class . :B a owl:Class . :C a owl:Class .
    :B rdfs:subClassOf :A . :C rdfs:subClassOf :B .
    """)
    assert onto._contradiction_axioms(g) == 0


def test_disjointness_counts_as_machinery():
    g = graph_of(PREAMBLE + """
    :A a owl:Class . :B a owl:Class .
    :A owl:disjointWith :B .
    """)
    assert onto._contradiction_axioms(g) == 1


def test_all_disjoint_classes_counts():
    g = graph_of(PREAMBLE + """
    [] a owl:AllDisjointClasses ; owl:members ( :A :B :C ) .
    """)
    assert onto._contradiction_axioms(g) == 1


# ======================================================================
# ABox size
# ======================================================================

def test_a_pure_tbox_has_no_individuals():
    g = graph_of(PREAMBLE + """
    :A a owl:Class . :p a owl:ObjectProperty . :A rdfs:subClassOf :B .
    """)
    assert onto._individuals(g) == 0


def test_individuals_typed_by_a_domain_class_are_counted():
    """Counting only owl:NamedIndividual misses individuals typed directly."""
    g = graph_of(PREAMBLE + """
    :A a owl:Class .
    :bob a :A .
    :alice a owl:NamedIndividual, :A .
    """)
    assert onto._individuals(g) == 2


# ======================================================================
# the caveat: a passing verdict must say what it did not check
# ======================================================================

def test_a_weak_run_says_so():
    caveat = onto._verdict_caveat(individuals=0, contradiction=32, unresolved=set())
    assert "no individuals" in caveat
    assert "32" in caveat


def test_an_absent_import_is_named_in_the_caveat():
    caveat = onto._verdict_caveat(individuals=10, contradiction=900,
                                  unresolved={"http://example.org/nowhere"})
    assert "1 import" in caveat


def test_a_strong_run_carries_no_caveat():
    """The caveat has to be able to be empty, or it is noise rather than signal."""
    assert onto._verdict_caveat(individuals=500, contradiction=900,
                                unresolved=set()) == ""


def test_the_verdict_never_travels_alone():
    """Whatever else changes, these three records ship together.

    The regression this guards against is someone trimming the emitted metrics
    back to the verdict, which is the state that made `reasoner_consistent: 1`
    citable as evidence of soundness.
    """
    import inspect
    src = inspect.getsource(onto.reasoner_metrics)
    for name in ("reasoner_individuals", "reasoner_contradiction_axioms",
                 "reasoner_imports_unresolved"):
        assert name in src, f"{name} is no longer emitted alongside the verdict"
    assert "_verdict_caveat" in src
