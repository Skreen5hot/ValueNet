# SPDX-License-Identifier: Apache-2.0
"""Where a text value can live, decided by HermiT rather than by argument.

The formal review of 2026-09-16 recommended replacing `vn-core:hasTextValue`
with CCO `has text value` (`ont00001765`), on the grounds that CCO already had
the property. The reviewer later withdrew that recommendation, after the
experiment below showed that the replacement cannot be made: the CCO property's
domain is Information Bearing Entity, an IBE is a BFO object, and BFO declares
independent, specifically dependent and generically dependent continuants
pairwise disjoint. Applied to a text representation it does not reuse a
property; it changes what the subject is, and the ontology becomes inconsistent.

The decision that followed, D-005 in docs/bfo/remediation/DECISION_RECORDS.md,
separates three levels that CCO's information model has only two classes for:

    content  -> Information Content Entity   individuated by aboutness
    form     -> a non-ICE generically dependent continuant, individuated by
                the exact sequence (BFO's own elucidation: "the content or the
                pattern that multiple copies would share")
    bearer   -> Information Bearing Entity   a particular carrier

That is an argument, and arguments about categories are easy to lose track of.
This file is the argument in a form that fails if any premise changes: if BFO
drops the disjointness, if CCO changes the domain, or if someone edits the
scenarios into a different claim.

WHAT IS READ AND WHAT IS STATED

BFO core and the IBE and ICE class axioms are read from the vendored files,
through the layout contract. One CCO axiom is stated rather than read:
`has text value` rdfs:domain IBE. The vendored extract carries only terms
ValueNet uses, and under D-005 ValueNet deliberately does not use that one, so
it is absent. It was verified against the CCO v2.2 release artifact
(commit 0bc7d33e1bc09fd4693366119ab4e03cb0340042) and against v2.0
(tag v2.0-2024-11-06), which agree. The two controls below are what make that
single transcription safe: if the stated axiom did not do what it claims, the
first control would still pass and the review-applied-literally case would stop
being inconsistent, and that case is pinned.

WHAT THIS DOES NOT TEST

It reasons over small scenario graphs, not over valuenet-core.ttl. It shows
which placements are logically possible; it does not show that the published
ontology follows D-005. tests/bfo/test_text_layer_follows_d005.py does, and
landed with the ontology change.

Every run starts a JVM per scenario, so this is slow in absolute terms -- it has
taken between 40 and 107 seconds on the same code -- and it is left in the
default run anyway. A test that proves an
architectural claim and is excluded by default is a test nobody runs.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")
owlready2 = pytest.importorskip(
    "owlready2",
    reason="owlready2 is required to run HermiT. It is not yet declared in a "
           "requirements file; while it is missing, the text-value placement "
           "claims in D-005 are unverified on this machine.")

from marep.layout import bfo_artifact  # noqa: E402

if shutil.which("java") is None:  # pragma: no cover - environment guidance
    pytest.skip("HermiT needs a Java runtime on PATH. Without one, the "
                "text-value placement claims in D-005 are unverified on this "
                "machine.", allow_module_level=True)

OBO = "http://purl.obolibrary.org/obo/"
CCO = "https://www.commoncoreontologies.org/"

IBE = CCO + "ont00000253"
ICE = CCO + "ont00000958"
HAS_TEXT_VALUE = CCO + "ont00001765"
GDC = OBO + "BFO_0000031"
OBJECT = OBO + "BFO_0000030"

#: The one CCO axiom stated here rather than read from a vendored file. See the
#: module docstring for why it is absent from the extract and how it was
#: verified.
STATED_CCO_AXIOMS = """
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
<%s> a owl:DatatypeProperty ;
    rdfs:label "has text value" ;
    rdfs:domain <%s> .
""" % (HAS_TEXT_VALUE, IBE)

PREFIXES = """
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix obo:   <http://purl.obolibrary.org/obo/> .
@prefix cco:   <https://www.commoncoreontologies.org/> .
@prefix vn:    <https://example.invalid/vn#> .
@prefix ex:    <https://example.invalid/data#> .
<https://example.invalid/text-value-placement> a owl:Ontology .
"""

#: (id, expected consistency, what it establishes, scenario Turtle).
#: The first eight are the experiment the reviewer saw. The ninth is the
#: reviewer's. Ten and eleven turn the remaining arguments in D-005 into
#: evidence, and twelve is the design D-005 records, spans included.
#: Thirteen and fourteen are the reviewer's competency test for span identity.
#: Nine, twelve, thirteen and fourteen use the property's D-005 name,
#: hasTextualSequenceValue;
#: the earlier cases keep hasTextValue because they are the experiment as the
#: reviewer saw it, and a property's name has no bearing on consistency.
SCENARIOS = [
    ("01-control-cco-text-value-on-ibe", True,
     "control: CCO places a text value on an IBE, and that is consistent",
     """
     ex:page a cco:ont00000253 ; cco:ont00001765 "Honesty is the best policy." .
     """),

    ("02-control-gdc-and-ibe-disjoint", False,
     "control: nothing can be both a generically dependent continuant and an "
     "IBE; if this passes, the disjointness every other case relies on is gone",
     """
     ex:bad a obo:BFO_0000031 , cco:ont00000253 .
     """),

    ("03-ice-placement-with-local-property", True,
     "the pre-D-005 model is consistent: the review's objection was about "
     "category, which no reasoner reports",
     """
     vn:TextualRepresentation rdfs:subClassOf cco:ont00000958 .
     vn:hasTextValue a owl:DatatypeProperty ;
         rdfs:domain cco:ont00000958 ; rdfs:range xsd:string .
     ex:rep a vn:TextualRepresentation ;
         vn:hasTextValue "Honesty is the best policy." .
     """),

    ("04-review-applied-literally", False,
     "replacing the local property with CCO has text value on the same "
     "individual makes it an IBE, and it is already a GDC",
     """
     vn:TextualRepresentation rdfs:subClassOf cco:ont00000958 .
     ex:rep a vn:TextualRepresentation ;
         cco:ont00001765 "Honesty is the best policy." .
     """),

    ("05-form-level-gdc-with-local-property", True,
     "a form-level GDC outside ICE, carrying the string by a local property",
     """
     vn:TextSequence rdfs:subClassOf obo:BFO_0000031 .
     vn:hasTextValue a owl:DatatypeProperty ;
         rdfs:domain vn:TextSequence ; rdfs:range xsd:string .
     ex:rep a vn:TextSequence ;
         vn:hasTextValue "Honesty is the best policy." .
     """),

    ("06-sequence-domain-property-on-an-ibe", False,
     "the mirror of case 04: a property whose domain is the form level cannot "
     "be used on a bearer either",
     """
     vn:TextSequence rdfs:subClassOf obo:BFO_0000031 .
     vn:hasTextValue a owl:DatatypeProperty ;
         rdfs:domain vn:TextSequence ; rdfs:range xsd:string .
     ex:page a cco:ont00000253 ;
         vn:hasTextValue "Honesty is the best policy." .
     """),

    ("07-one-property-union-domain", True,
     "one property for both levels is possible only with a union domain",
     """
     vn:TextSequence rdfs:subClassOf obo:BFO_0000031 .
     vn:hasTextValue a owl:DatatypeProperty ; rdfs:range xsd:string ;
         rdfs:domain [ a owl:Class ;
                       owl:unionOf ( cco:ont00000253 vn:TextSequence ) ] .
     ex:page a cco:ont00000253 ; vn:hasTextValue "Honesty." .
     ex:rep  a vn:TextSequence ; vn:hasTextValue "Honesty." .
     """),

    ("08-two-bearers-one-sequence", True,
     "two carriers share one sequence, so the string and its offsets are "
     "stated once rather than once per copy",
     """
     vn:TextSequence rdfs:subClassOf obo:BFO_0000031 .
     vn:hasTextValue a owl:DatatypeProperty ;
         rdfs:domain vn:TextSequence ; rdfs:range xsd:string .
     ex:rep a vn:TextSequence ;
         vn:hasTextValue "Honesty is the best policy." .
     ex:file_on_disk a cco:ont00000253 ; obo:BFO_0000101 ex:rep .
     ex:file_in_git  a cco:ont00000253 ; obo:BFO_0000101 ex:rep .
     """),

    ("09-reviewer-existential-two-distinct-bearers", True,
     "the D-005 design: TextualRepresentation is a GDC that generically "
     "depends on some IBE, and two IBEs asserted distinct carry the same one",
     """
     vn:TextualRepresentation rdfs:subClassOf obo:BFO_0000031 ,
         [ a owl:Restriction ;
           owl:onProperty obo:BFO_0000084 ;
           owl:someValuesFrom cco:ont00000253 ] .
     vn:hasTextualSequenceValue a owl:DatatypeProperty ;
         rdfs:domain vn:TextualRepresentation ; rdfs:range xsd:string .
     ex:rep a vn:TextualRepresentation ;
         vn:hasTextualSequenceValue "Honesty is the best policy." .
     ex:file_on_disk a cco:ont00000253 ; obo:BFO_0000101 ex:rep .
     ex:file_in_git  a cco:ont00000253 ; obo:BFO_0000101 ex:rep .
     ex:file_on_disk owl:differentFrom ex:file_in_git .
     """),

    ("10-existential-does-not-demand-carrier-data", True,
     "why SHACL is still needed: the OWL existential states that a carrier "
     "exists, and a representation with no carrier recorded is still "
     "consistent under the open-world assumption",
     """
     vn:TextualRepresentation rdfs:subClassOf obo:BFO_0000031 ,
         [ a owl:Restriction ;
           owl:onProperty obo:BFO_0000084 ;
           owl:someValuesFrom cco:ont00000253 ] .
     ex:orphan a vn:TextualRepresentation .
     """),

    ("11-concretized-by-an-ibe", False,
     "why the definition says 'generically depends on' and not 'concretized "
     "by': BFO restricts what concretizes a GDC to a process or specifically "
     "dependent continuant, so requiring an IBE concretizer is unsatisfiable "
     "(D-004.5 already prohibits the direct assertion)",
     """
     vn:TextualRepresentation rdfs:subClassOf obo:BFO_0000031 ,
         [ a owl:Restriction ;
           owl:onProperty obo:BFO_0000058 ;
           owl:someValuesFrom cco:ont00000253 ] .
     ex:rep a vn:TextualRepresentation .
     """),

    ("12-d005-design-with-spans", True,
     "the design as D-005 records it: representation and span are both "
     "form-level GDCs, the span a continuant part of the representation, "
     "hasTextualSequenceValue with a domain covering both, two distinct carriers",
     """
     vn:TextualRepresentation rdfs:subClassOf obo:BFO_0000031 ,
         [ a owl:Restriction ;
           owl:onProperty obo:BFO_0000084 ;
           owl:someValuesFrom cco:ont00000253 ] .
     vn:TextSpan rdfs:subClassOf obo:BFO_0000031 .
     vn:isTextSpanOf a owl:ObjectProperty ;
         rdfs:subPropertyOf obo:BFO_0000176 ;
         rdfs:domain vn:TextSpan ; rdfs:range vn:TextualRepresentation .
     vn:hasTextualSequenceValue a owl:DatatypeProperty ; rdfs:range xsd:string ;
         rdfs:domain [ a owl:Class ;
                       owl:unionOf ( vn:TextualRepresentation vn:TextSpan ) ] .
     ex:rep a vn:TextualRepresentation ;
         vn:hasTextualSequenceValue "Honesty is the best policy." .
     ex:span a vn:TextSpan ; vn:isTextSpanOf ex:rep ;
         vn:hasTextualSequenceValue "Honesty" .
     ex:file_on_disk a cco:ont00000253 ; obo:BFO_0000101 ex:rep .
     ex:file_in_git  a cco:ont00000253 ; obo:BFO_0000101 ex:rep .
     ex:file_on_disk owl:differentFrom ex:file_in_git .
     """),

    ("13-same-substring-two-spans", True,
     "a span is individuated by its position, not its string: 'abc' at code "
     "points 2-4 and 'abc' at 20-22 of one representation are two spans",
     """
     vn:TextualRepresentation rdfs:subClassOf obo:BFO_0000031 ,
         [ a owl:Restriction ;
           owl:onProperty obo:BFO_0000084 ;
           owl:someValuesFrom cco:ont00000253 ] .
     vn:TextSpan rdfs:subClassOf obo:BFO_0000031 .
     vn:isTextSpanOf a owl:ObjectProperty ;
         rdfs:subPropertyOf obo:BFO_0000176 ;
         rdfs:domain vn:TextSpan ; rdfs:range vn:TextualRepresentation .
     vn:hasTextualSequenceValue a owl:DatatypeProperty ; rdfs:range xsd:string ;
         rdfs:domain [ a owl:Class ;
                       owl:unionOf ( vn:TextualRepresentation vn:TextSpan ) ] .
     ex:rep a vn:TextualRepresentation ;
         vn:hasTextualSequenceValue "xyabcdefghijklmnopqrabc" .
     ex:file a cco:ont00000253 ; obo:BFO_0000101 ex:rep .
     # "abc" at code points 2-4 and again at 20-22 of the same representation
     ex:span_at_2  a vn:TextSpan ; vn:isTextSpanOf ex:rep ;
         vn:hasTextualSequenceValue "abc" .
     ex:span_at_20 a vn:TextSpan ; vn:isTextSpanOf ex:rep ;
         vn:hasTextualSequenceValue "abc" .
     ex:span_at_2 owl:differentFrom ex:span_at_20 .
     """),

    ("14-spans-keyed-by-string-collapse", False,
     "the individuation D-005 rejects: if spans were identified by their "
     "string, the two occurrences of 'abc' would be one span, which "
     "contradicts their being different",
     """
     vn:TextualRepresentation rdfs:subClassOf obo:BFO_0000031 ,
         [ a owl:Restriction ;
           owl:onProperty obo:BFO_0000084 ;
           owl:someValuesFrom cco:ont00000253 ] .
     vn:TextSpan rdfs:subClassOf obo:BFO_0000031 .
     vn:isTextSpanOf a owl:ObjectProperty ;
         rdfs:subPropertyOf obo:BFO_0000176 ;
         rdfs:domain vn:TextSpan ; rdfs:range vn:TextualRepresentation .
     vn:hasTextualSequenceValue a owl:DatatypeProperty ; rdfs:range xsd:string ;
         rdfs:domain [ a owl:Class ;
                       owl:unionOf ( vn:TextualRepresentation vn:TextSpan ) ] .
     ex:rep a vn:TextualRepresentation ;
         vn:hasTextualSequenceValue "xyabcdefghijklmnopqrabc" .
     ex:file a cco:ont00000253 ; obo:BFO_0000101 ex:rep .
     # "abc" at code points 2-4 and again at 20-22 of the same representation
     ex:span_at_2  a vn:TextSpan ; vn:isTextSpanOf ex:rep ;
         vn:hasTextualSequenceValue "abc" .
     ex:span_at_20 a vn:TextSpan ; vn:isTextSpanOf ex:rep ;
         vn:hasTextualSequenceValue "abc" .
     ex:span_at_2 owl:differentFrom ex:span_at_20 .
     vn:TextSpan owl:hasKey ( vn:hasTextualSequenceValue ) .
     """),
]


@pytest.fixture(scope="module")
def base_graph():
    """BFO core, the IBE and ICE class axioms from the extract, and the one
    stated CCO axiom. Parsed once; each scenario works on a copy."""
    graph = rdflib.Graph()
    graph.parse(bfo_artifact("bfo-core.ttl"), format="turtle")

    extract = rdflib.Graph()
    extract.parse(bfo_artifact("cco-valuenet-extract.ttl"), format="turtle")
    for iri in (IBE, ICE):
        subject = rdflib.URIRef(iri)
        for predicate in (rdflib.RDF.type, rdflib.RDFS.subClassOf,
                          rdflib.RDFS.label):
            for obj in extract.objects(subject, predicate):
                if not isinstance(obj, rdflib.BNode):
                    graph.add((subject, predicate, obj))

    graph.parse(data=STATED_CCO_AXIOMS, format="turtle")
    return graph


def consistent(base: rdflib.Graph, scenario: str) -> bool:
    graph = rdflib.Graph()
    for triple in base:
        graph.add(triple)
    graph.parse(data=PREFIXES + scenario, format="turtle")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.owl"
        graph.serialize(path, format="xml")
        world = owlready2.World()
        with open(path, "rb") as stream:
            onto = world.get_ontology(
                "https://example.invalid/text-value-placement").load(
                    fileobj=stream)
        try:
            owlready2.sync_reasoner([onto], debug=0)
        except owlready2.OwlReadyInconsistentOntologyError:
            return False
    return True


def test_the_axioms_the_scenarios_rest_on_are_present(base_graph):
    """Without these the controls cannot fail for the right reason: an IBE
    that is not an object is not disjoint from a GDC, and every
    'inconsistent' case would quietly become consistent."""
    assert (rdflib.URIRef(IBE), rdflib.RDFS.subClassOf,
            rdflib.URIRef(OBJECT)) in base_graph, (
        "the vendored CCO extract no longer places IBE under BFO object")
    assert (rdflib.URIRef(ICE), rdflib.RDFS.subClassOf,
            rdflib.URIRef(GDC)) in base_graph, (
        "the vendored CCO extract no longer places ICE under BFO GDC")
    assert any(True for _ in base_graph.subjects(
        rdflib.RDF.type, rdflib.OWL.AllDisjointClasses)), (
        "the vendored BFO core declares no disjoint class group")


def test_the_scenarios_are_the_ones_recorded():
    """Pinned by id, so a case cannot be dropped or quietly re-purposed. The
    reviewer asked that all eight original cases and both controls stay."""
    ids = [s[0] for s in SCENARIOS]
    assert len(ids) == len(set(ids)) == 14, ids
    controls = [s for s in SCENARIOS if s[0].split("-", 2)[1] == "control"]
    assert [(s[0], s[1]) for s in controls] == [
        ("01-control-cco-text-value-on-ibe", True),
        ("02-control-gdc-and-ibe-disjoint", False)]


@pytest.mark.parametrize(
    "expected, scenario",
    [pytest.param(s[1], s[3], id=s[0]) for s in SCENARIOS])
def test_text_value_placement(base_graph, expected, scenario):
    got = consistent(base_graph, scenario)
    what = next(s[2] for s in SCENARIOS if s[3] == scenario)
    assert got is expected, (
        "expected %s, HermiT found the scenario %s -- %s"
        % ("consistent" if expected else "inconsistent",
           "consistent" if got else "inconsistent", what))
