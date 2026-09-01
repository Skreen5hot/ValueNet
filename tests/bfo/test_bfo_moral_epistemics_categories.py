# SPDX-License-Identifier: Apache-2.0
"""Phase 6 controls for moral-epistemics category separation."""

from __future__ import annotations

from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")
pyshacl = pytest.importorskip("pyshacl")
owlrl = pytest.importorskip("owlrl")

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import BNode, Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS


# The repository root comes from the layout contract, not from counting
# parents. This file moves one level deeper in the tests wave, at which
# point parents[1] resolves to tests/ and every path below it is wrong
# without raising anything.
from marep.layout import bfo_artifact, repository_root  # noqa: E402

ROOT = repository_root()
ONTOLOGY = bfo_artifact("valuenet-moral-epistemics.ttl")
SHAPES = bfo_artifact("valuenet-moral-epistemics-shapes.ttl")
SCENARIO = bfo_artifact("valuenet-moral-epistemics-scenario.ttl")

ONTOLOGY_FILES = tuple(
    bfo_artifact(name)
    for name in (
        "bfo-core.ttl",
        "cco-valuenet-extract.ttl",
        "valuenet-core.ttl",
        "valuenet-schwartz-values.ttl",
        "valuenet-moral-foundations.ttl",
        "valuenet-folk.ttl",
        "valuenet-moral-epistemics.ttl",
    )
)

VN_CORE = Namespace("https://fandaws.com/ontology/bfo/valuenet-core#")
VN_ME = Namespace("https://fandaws.com/ontology/bfo/valuenet-moral-epistemics#")
CCO = Namespace("https://www.commoncoreontologies.org/")
BFO = Namespace("http://purl.obolibrary.org/obo/")
SH = Namespace("http://www.w3.org/ns/shacl#")

PREFIXES = """
@prefix : <https://example.org/phase6#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix cco: <https://www.commoncoreontologies.org/> .
@prefix vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#> .
@prefix vn-me: <https://fandaws.com/ontology/bfo/valuenet-moral-epistemics#> .
"""


def load_graph(paths) -> Graph:
    graph = Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


@pytest.fixture(scope="module")
def ontology_graph():
    return load_graph(ONTOLOGY_FILES)


def restrictions(graph: Graph, cls: URIRef):
    for node in graph.objects(cls, RDFS.subClassOf):
        if isinstance(node, BNode) and (node, RDF.type, OWL.Restriction) in graph:
            yield node


def validate(extra: str = "", *, scenario: bool = False):
    data = load_graph(ONTOLOGY_FILES)
    if scenario:
        data.parse(SCENARIO, format="turtle")
    if extra:
        data.parse(data=PREFIXES + extra, format="turtle")
    shapes = Graph()
    shapes.parse(SHAPES, format="turtle")
    conforms, results, report = pyshacl.validate(
        data,
        shacl_graph=shapes,
        advanced=True,
        inference="rdfs",
        allow_warnings=True,
    )
    messages = [str(value) for value in results.objects(None, SH.resultMessage)]
    severities = list(results.objects(None, SH.resultSeverity))
    return bool(conforms), messages, severities, str(report)


def test_interior_moral_state_is_removed(ontology_graph):
    obsolete = VN_ME.InteriorMoralState
    assert not list(ontology_graph.triples((obsolete, None, None)))
    assert not list(ontology_graph.triples((None, None, obsolete)))


def test_acts_outputs_targets_and_status_have_distinct_categories(ontology_graph):
    assert (VN_ME.MoralAssessmentAct, RDFS.subClassOf, CCO.ont00000636) in ontology_graph
    assert (VN_ME.MoralAssessmentICE, RDFS.subClassOf, CCO.ont00000853) in ontology_graph
    assert (VN_ME.CulpabilityAscriptionICE, RDFS.subClassOf, VN_ME.MoralAssessmentICE) in ontology_graph
    assert (VN_ME.MoralCulpabilityRole, RDFS.subClassOf, BFO.BFO_0000023) in ontology_graph
    assert (VN_ME.ActOfBehavioralObservation, RDFS.subClassOf, CCO.ont00000037) in ontology_graph
    assert (VN_ME.hasInformationalInput, RDFS.range, CCO.ont00000958) in ontology_graph
    assert (VN_ME.hasInformationalOutput, RDFS.range, CCO.ont00000958) in ontology_graph
    assert (VN_ME.isWarrantedBy, RDFS.domain, VN_ME.MoralAssessmentICE) in ontology_graph


def test_culpability_ascription_describes_an_agent_without_entailing_status(ontology_graph):
    ascription_restrictions = list(restrictions(ontology_graph, VN_ME.CulpabilityAscriptionICE))
    assert any(
        (node, OWL.onProperty, CCO.ont00001982) in ontology_graph
        and (node, OWL.someValuesFrom, CCO.ont00001017) in ontology_graph
        for node in ascription_restrictions
    )
    assert not any(
        (node, OWL.someValuesFrom, VN_ME.MoralCulpabilityRole) in ontology_graph
        for node in ascription_restrictions
    )


def test_warranted_assessment_is_a_positive_defined_class(ontology_graph):
    probe = URIRef("https://example.org/phase6#warrantedAssessment")
    evidence = URIRef("https://example.org/phase6#evidence")
    graph = Graph()
    for triple in ontology_graph:
        graph.add(triple)
    graph.add((probe, RDF.type, VN_ME.MoralAssessmentICE))
    graph.add((evidence, RDF.type, VN_ME.ObservationalEvidenceICE))
    graph.add((probe, VN_ME.isWarrantedBy, evidence))
    DeductiveClosure(OWLRL_Semantics).expand(graph)
    assert (probe, RDF.type, VN_ME.WarrantedMoralAssessmentICE) in graph


def test_discernment_and_rash_judgment_overlap_is_explicitly_satisfiable(ontology_graph):
    assert (VN_ME.RashJudgmentAct, OWL.disjointWith, VN_ME.MoralDiscernmentAct) not in ontology_graph
    assert (VN_ME.MoralDiscernmentAct, OWL.disjointWith, VN_ME.RashJudgmentAct) not in ontology_graph
    assert (VN_ME.MixedMoralAssessmentAct, RDFS.subClassOf, VN_ME.MoralDiscernmentAct) in ontology_graph
    assert (VN_ME.MixedMoralAssessmentAct, RDFS.subClassOf, VN_ME.RashJudgmentAct) in ontology_graph


def test_phase6_scenario_conforms_with_the_expected_rash_judgment_warning():
    conforms, messages, severities, report = validate(scenario=True)
    assert conforms, report
    assert any("records no evidential warrant" in message for message in messages)
    assert SH.Warning in severities


def test_behavioral_observation_requires_the_observed_process():
    conforms, messages, _severities, _report = validate(
        """
:record a vn-me:BehavioralObservationICE .
"""
    )
    assert not conforms
    assert any("must describe at least one AgentBehaviorProcess" in message for message in messages)


def test_culpability_ascription_requires_a_described_agent():
    conforms, messages, _severities, _report = validate(
        """
:notAnAgent a vn-me:AgentBehaviorProcess .
:evidence a vn-me:ObservationalEvidenceICE .
:ascription a vn-me:CulpabilityAscriptionICE ;
  cco:ont00001982 :notAnAgent ;
  vn-me:isWarrantedBy :evidence .
"""
    )
    assert not conforms
    assert any("must describe at least one CCO Agent" in message for message in messages)


def test_rash_judgment_requires_an_unwarranted_ascription_output():
    conforms, messages, _severities, _report = validate(
        """
:agent a cco:ont00001017 .
:evidence a vn-me:ObservationalEvidenceICE .
:ascription a vn-me:CulpabilityAscriptionICE ;
  cco:ont00001982 :agent ;
  vn-me:isWarrantedBy :evidence .
:value a vn-core:ValueRelatedRealizableEntity .
:act a vn-me:RashJudgmentAct ;
  vn-me:hasInformationalOutput :ascription ;
  vn-core:contravenes :value .
"""
    )
    assert not conforms
    assert any("must produce at least one CulpabilityAscriptionICE" in message for message in messages)


def test_mixed_assessment_with_warranted_and_unwarranted_outputs_is_valid():
    conforms, messages, _severities, report = validate(
        """
:agent a cco:ont00001017 .
:behavior a vn-me:AgentBehaviorProcess .
:observation a vn-me:BehavioralObservationICE ;
  cco:ont00001982 :behavior .
:safetyAssessment a vn-me:SafetyAssessmentICE ;
  cco:ont00001982 :behavior ;
  vn-me:isWarrantedBy :observation .
:culpabilityAscription a vn-me:CulpabilityAscriptionICE ;
  cco:ont00001982 :agent .
:value a vn-core:ValueRelatedRealizableEntity .
:mixedAct a vn-me:MixedMoralAssessmentAct ;
  vn-me:hasInformationalOutput :safetyAssessment, :culpabilityAscription ;
  vn-core:contravenes :value .
"""
    )
    assert conforms, report
    assert any("records no evidential warrant" in message for message in messages)

