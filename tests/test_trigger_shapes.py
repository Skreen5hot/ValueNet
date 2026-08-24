"""The trigger shapes must catch the defects that were repaired by hand.

A SHACL run that reports nothing is worth nothing on its own. This corpus has
been through three audits establishing that a clean result which could not have
been dirty is not evidence, so these tests plant each defect the round actually
found and require the shapes to fail on it.

Why SHACL rather than OWL, concretely: `vcvf:triggers` declares
`rdfs:range vcvf:Value`, and a range *entails*. Every one of these defects was
absorbed by that inference instead of being reported —

    folk:Repayment    102 triggers, declared nowhere, a whole-file mis-target
    folk:Strenght     122 triggers, a misspelling of a declared value
    folk:Belief       480 triggers, a religion lexicon under a name nobody
                      declared, while the declared folk:Beliefs received none

— each inferred into `vcvf:Value` membership by the very statements that were
wrong.
"""

from __future__ import annotations

from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")
pyshacl = pytest.importorskip("pyshacl")

REPO = Path(__file__).resolve().parents[1]
SHAPES = REPO / "BFO" / "vcvf-triggers-shapes.ttl"

PREFIX = """
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix vcvf: <http://www.ontologydesignpatterns.org/ont/values/valuecore_with_value_frames.owl#> .
@prefix folk: <http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#> .
"""

#: A well-formed trigger statement, the shape of all 57,578 in the corpus.
GOOD = PREFIX + """
folk:Health a owl:Class, owl:NamedIndividual, folk:FolkValue .
<http://en.wiktionary.org/wiki/health> vcvf:triggers folk:Health .
"""


def violations(turtle: str):
    data = rdflib.Graph()
    data.parse(data=turtle, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(str(SHAPES), format="turtle")
    conforms, results, _ = pyshacl.validate(
        data, shacl_graph=shapes, advanced=True, inference="none")
    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    from rdflib.namespace import RDF
    return conforms, [str(results.value(r, SH.resultMessage))
                      for r in results.subjects(RDF.type, SH.ValidationResult)]


def test_a_well_formed_trigger_statement_passes():
    """Without this the rest proves only that the shapes reject everything."""
    conforms, msgs = violations(GOOD)
    assert conforms, msgs


# ======================================================================
# the defects this round repaired by hand
# ======================================================================

def test_an_undeclared_object_is_caught():
    """The folk:Strenght case. OWL's range would infer it to be a Value."""
    conforms, msgs = violations(PREFIX + """
    <http://en.wiktionary.org/wiki/strength> vcvf:triggers folk:Strenght .
    """)
    assert not conforms
    assert any("no rdf:type" in m for m in msgs), msgs


def test_a_mistargeted_object_is_caught_when_undeclared():
    """The folk:Repayment case: 102 triggers pointing at a name nobody declared."""
    conforms, msgs = violations(PREFIX + """
    <http://en.wiktionary.org/wiki/recognition> vcvf:triggers folk:Repayment .
    """)
    assert not conforms


def test_a_reversed_statement_is_caught():
    """Direction. The corpus has 18,668 statements one way and zero the other,
    and nothing enforced it. A value in subject position with an external
    resource as object reverses the claim from "this page evokes the value" to
    "this value is that page"."""
    conforms, msgs = violations(PREFIX + """
    folk:Education a owl:Class, owl:NamedIndividual, folk:FolkValue .
    folk:Education vcvf:triggers <http://dbpedia.org/resource/An_Education> .
    """)
    assert not conforms
    assert any("must be a ValueNet value" in m for m in msgs), msgs


def test_a_blank_node_subject_is_caught():
    conforms, msgs = violations(PREFIX + """
    folk:Health a owl:Class, owl:NamedIndividual, folk:FolkValue .
    [] vcvf:triggers folk:Health .
    """)
    assert not conforms
    assert any("must be an IRI" in m for m in msgs), msgs


# ======================================================================
# what the shapes must NOT reject
# ======================================================================

def test_heterogeneous_subjects_are_allowed():
    """Trigger sources span 12 hosts by design. A shape narrowing the subject
    would reject the corpus wholesale."""
    conforms, msgs = violations(PREFIX + """
    folk:Health a owl:Class, owl:NamedIndividual, folk:FolkValue .
    <http://babelnet.org/rdf/s00092811v>            vcvf:triggers folk:Health .
    <http://yago-knowledge.org/resource/wordnet_x>  vcvf:triggers folk:Health .
    <https://w3id.org/framester/data/framestercore/MedicalConditions>
                                                    vcvf:triggers folk:Health .
    <http://premon.fbk.eu/resource/fn17-x>          vcvf:triggers folk:Health .
    <http://fr.wiktionary.org/wiki/sante>           vcvf:triggers folk:Health .
    """)
    assert conforms, msgs


def test_non_folk_value_namespaces_are_allowed():
    """22 trigger objects live in the SON namespaces and are properly declared."""
    conforms, msgs = violations(PREFIX + """
    @prefix mft: <https://w3id.org/spice/SON/HaidtValues#> .
    mft:MFT_Value a owl:Class .
    <https://w3id.org/spice/SON/HaidtValues#Care> a owl:Class, mft:MFT_Value .
    <http://en.wiktionary.org/wiki/care> vcvf:triggers
        <https://w3id.org/spice/SON/HaidtValues#Care> .
    """)
    assert conforms, msgs


# ======================================================================
# the corpus itself
# ======================================================================

@pytest.mark.slow
def test_the_corpus_conforms():
    """Meaningful only because the tests above prove these shapes can fail."""
    from marep import ontology_source as onto
    onto.clear_graph_cache()
    facts = [f for f in (onto.measure_file(p, REPO) for p in onto.discover(REPO))
             if f.parses]
    data = onto.merged_graph(REPO, facts)
    shapes = rdflib.Graph()
    shapes.parse(str(SHAPES), format="turtle")
    conforms, results, text = pyshacl.validate(
        data, shacl_graph=shapes, advanced=True, inference="none")
    assert conforms, text[:2000]
