"""Executable controls for the BFO alignment remediation plan.

Negative controls begin as strict expected failures when a defect is confirmed.
The Phase 2 and Phase 3 repairs converted every control in this module into an
ordinary regression that also checks the intended validation reason.
"""

from __future__ import annotations

from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")
pyshacl = pytest.importorskip("pyshacl")
owlrl = pytest.importorskip("owlrl")

REPO = Path(__file__).resolve().parents[1]
BFO = REPO / "BFO"
CORE = BFO / "valuenet-core.ttl"
CORE_SHAPES = BFO / "valuenet-core-shapes.ttl"
SCENARIO = BFO / "valuenet-moral-epistemics-scenario.ttl"
SCENARIO_MODULES = (
    CORE,
    BFO / "valuenet-schwartz-values.ttl",
    BFO / "valuenet-moral-foundations.ttl",
    BFO / "valuenet-folk.ttl",
    BFO / "valuenet-moral-epistemics.ttl",
    SCENARIO,
)

PREFIXES = """
@prefix : <http://example.org/alignment-control#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix cco: <https://www.commoncoreontologies.org/> .
@prefix vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#> .
"""


def validate_core(data: str) -> tuple[bool, str]:
    graph = rdflib.Graph()
    graph.parse(str(CORE), format="turtle")
    graph.parse(data=PREFIXES + data, format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(str(CORE_SHAPES), format="turtle")
    conforms, _results, report = pyshacl.validate(
        graph,
        shacl_graph=shapes,
        advanced=True,
        inference="none",
    )
    return bool(conforms), str(report)


def test_worked_scenario_conforms_to_core_shapes():
    graph = rdflib.Graph()
    for path in SCENARIO_MODULES:
        graph.parse(str(path), format="turtle")
    shapes = rdflib.Graph()
    shapes.parse(str(CORE_SHAPES), format="turtle")
    conforms, _results, report = pyshacl.validate(
        graph,
        shacl_graph=shapes,
        advanced=True,
        inference="none",
    )
    assert conforms, str(report)


def test_valid_realization_pattern_conforms():
    conforms, report = validate_core("""
    :agent a cco:ont00001017 ;
        obo:BFO_0000196 :value .
    :value a vn-core:ValueDisposition .
    :process a vn-core:ValueRealizationProcess ;
        obo:BFO_0000057 :agent ;
        obo:BFO_0000055 :value .
    """)
    assert conforms, report


def test_valid_evidence_pattern_conforms():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "an auditable text span" .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "an auditable text span" ;
        vn-core:isTextSpanOf :representation ;
        vn-core:isEvidenceFor :process .
    :process a obo:BFO_0000015 .
    """)
    assert conforms, report


def test_mismatched_value_bearer_and_process_participant_is_rejected():
    conforms, report = validate_core("""
    :agentA a cco:ont00001017 ;
        obo:BFO_0000196 :valueA .
    :agentB a cco:ont00001017 .
    :valueA a vn-core:ValueDisposition .
    :process a vn-core:ValueRealizationProcess ;
        obo:BFO_0000057 :agentB ;
        obo:BFO_0000055 :valueA .
    """)
    assert not conforms, report
    assert "bearer of each realized value must be a participant" in report


def test_realized_value_without_recorded_bearer_is_rejected():
    conforms, report = validate_core("""
    :agent a cco:ont00001017 .
    :value a vn-core:ValueDisposition .
    :process a vn-core:ValueRealizationProcess ;
        obo:BFO_0000057 :agent ;
        obo:BFO_0000055 :value .
    """)
    assert not conforms, report
    assert "has no recorded bearer" in report


def test_evidence_source_that_is_not_a_text_span_is_rejected():
    conforms, report = validate_core("""
    :agent a cco:ont00001017 ;
        vn-core:isEvidenceFor :process .
    :process a vn-core:ValueRealizationProcess .
    """)
    assert not conforms, report
    assert "must be typed as a TextSpan or ValueEvidenceAnnotation" in report


def test_evidence_target_that_is_not_a_process_is_rejected():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "an invalid target" .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "an invalid target" ;
        vn-core:isTextSpanOf :representation ;
        vn-core:isEvidenceFor :agent .
    :agent a cco:ont00001017 .
    """)
    assert not conforms, report
    assert "must point at a named individual typed as a BFO process" in report


def test_untyped_evidence_source_and_target_are_rejected():
    conforms, report = validate_core("""
    :untypedSource vn-core:isEvidenceFor :untypedTarget .
    """)
    assert not conforms, report
    assert "must be typed as a TextSpan or ValueEvidenceAnnotation" in report
    assert "must point at a named individual typed as a BFO process" in report


def test_valid_reified_evidence_annotation_with_selector_conforms():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha beta" .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "beta" ;
        vn-core:isTextSpanOf :representation .
    :selector a vn-core:TextSpanSelector ;
        vn-core:hasSourceRepresentation :representation ;
        vn-core:selectsTextSpan :span ;
        vn-core:hasStartOffset "6"^^xsd:nonNegativeInteger ;
        vn-core:hasEndOffset "10"^^xsd:nonNegativeInteger .
    :annotation a vn-core:ValueEvidenceAnnotation ;
        vn-core:hasEvidenceSource :span ;
        vn-core:hasSelector :selector ;
        vn-core:isEvidenceFor :process .
    :process a obo:BFO_0000015 .
    """)
    assert conforms, report


def test_text_span_offsets_must_be_recorded_on_a_selector():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha" .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "alpha" ;
        vn-core:isTextSpanOf :representation ;
        vn-core:hasStartOffset "0"^^xsd:nonNegativeInteger ;
        vn-core:hasEndOffset "5"^^xsd:nonNegativeInteger .
    """)
    assert not conforms, report
    assert "Offsets belong on a TextSpanSelector" in report


def test_selector_requires_a_complete_offset_pair():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha" .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "alpha" ;
        vn-core:isTextSpanOf :representation .
    :selector a vn-core:TextSpanSelector ;
        vn-core:hasSourceRepresentation :representation ;
        vn-core:selectsTextSpan :span ;
        vn-core:hasStartOffset "0"^^xsd:nonNegativeInteger .
    """)
    assert not conforms, report
    assert "exactly one non-negative end offset" in report


def test_selector_end_offset_cannot_exceed_source_text_length():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha beta" .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "beta" ;
        vn-core:isTextSpanOf :representation .
    :selector a vn-core:TextSpanSelector ;
        vn-core:hasSourceRepresentation :representation ;
        vn-core:selectsTextSpan :span ;
        vn-core:hasStartOffset "6"^^xsd:nonNegativeInteger ;
        vn-core:hasEndOffset "11"^^xsd:nonNegativeInteger .
    """)
    assert not conforms, report
    assert "exceeds the Unicode code-point length" in report


def test_selector_and_span_must_reference_the_same_representation():
    conforms, report = validate_core("""
    :carrierA a cco:ont00000253 ; obo:BFO_0000101 :representationA .
    :carrierB a cco:ont00000253 ; obo:BFO_0000101 :representationB .
    :representationA a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha" .
    :representationB a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha" .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "alpha" ;
        vn-core:isTextSpanOf :representationA .
    :selector a vn-core:TextSpanSelector ;
        vn-core:hasSourceRepresentation :representationB ;
        vn-core:selectsTextSpan :span ;
        vn-core:hasStartOffset "0"^^xsd:nonNegativeInteger ;
        vn-core:hasEndOffset "5"^^xsd:nonNegativeInteger .
    """)
    assert not conforms, report
    assert "must use the same source TextualRepresentation" in report


def test_textual_representation_and_carrier_must_be_distinct():
    conforms, report = validate_core("""
    :conflated a vn-core:TextualRepresentation, cco:ont00000253 ;
        vn-core:hasTextValue "alpha" ;
        obo:BFO_0000101 :conflated .
    """)
    assert not conforms, report
    assert "must be distinct from its cco:Information Bearing Entity carrier" in report


def test_blank_node_evidence_source_is_rejected():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha" .
    [ a vn-core:TextSpan ;
      vn-core:hasTextValue "alpha" ;
      vn-core:isTextSpanOf :representation ;
      vn-core:isEvidenceFor :process ] .
    :process a obo:BFO_0000015 .
    """)
    assert not conforms, report
    assert "subject of vn-core:isEvidenceFor must be a named individual" in report


def test_blank_node_evidence_target_is_rejected():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha" .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "alpha" ;
        vn-core:isTextSpanOf :representation ;
        vn-core:isEvidenceFor [ a obo:BFO_0000015 ] .
    """)
    assert not conforms, report
    assert "must point at a named individual typed as a BFO process" in report


def test_text_span_source_must_be_an_exact_textual_representation():
    conforms, report = validate_core("""
    :genericContent a obo:BFO_0000031 .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "alpha" ;
        vn-core:isTextSpanOf :genericContent .
    """)
    assert not conforms, report
    assert "exactly one named TextualRepresentation" in report


def test_selector_offsets_must_delimit_the_recorded_span_text():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha beta" .
    :span a vn-core:TextSpan ;
        vn-core:hasTextValue "alpha" ;
        vn-core:isTextSpanOf :representation .
    :selector a vn-core:TextSpanSelector ;
        vn-core:hasSourceRepresentation :representation ;
        vn-core:selectsTextSpan :span ;
        vn-core:hasStartOffset "6"^^xsd:nonNegativeInteger ;
        vn-core:hasEndOffset "10"^^xsd:nonNegativeInteger .
    """)
    assert not conforms, report
    assert "do not delimit the recorded TextSpan text" in report


def test_evidence_annotation_selector_must_select_its_evidence_span():
    conforms, report = validate_core("""
    :carrier a cco:ont00000253 ;
        obo:BFO_0000101 :representation .
    :representation a vn-core:TextualRepresentation ;
        vn-core:hasTextValue "alpha beta" .
    :spanA a vn-core:TextSpan ;
        vn-core:hasTextValue "alpha" ;
        vn-core:isTextSpanOf :representation .
    :spanB a vn-core:TextSpan ;
        vn-core:hasTextValue "beta" ;
        vn-core:isTextSpanOf :representation .
    :selector a vn-core:TextSpanSelector ;
        vn-core:hasSourceRepresentation :representation ;
        vn-core:selectsTextSpan :spanB ;
        vn-core:hasStartOffset "6"^^xsd:nonNegativeInteger ;
        vn-core:hasEndOffset "10"^^xsd:nonNegativeInteger .
    :annotation a vn-core:ValueEvidenceAnnotation ;
        vn-core:hasEvidenceSource :spanA ;
        vn-core:hasSelector :selector ;
        vn-core:isEvidenceFor :process .
    :process a obo:BFO_0000015 .
    """)
    assert not conforms, report
    assert "selector must select its recorded TextSpan evidence source" in report


def test_process_realizing_a_value_class_instead_of_an_instance_is_rejected():
    conforms, report = validate_core("""
    :agent a cco:ont00001017 .
    :process a vn-core:ValueRealizationProcess ;
        obo:BFO_0000057 :agent ;
        obo:BFO_0000055 vn-core:ValueDisposition .
    """)
    assert not conforms, report
    assert "value instance, not a value class IRI" in report


def test_valid_realization_pattern_using_inheres_in_conforms():
    conforms, report = validate_core("""
    :agent a cco:ont00001017 .
    :value a vn-core:ValueRole ;
        obo:BFO_0000197 :agent .
    :process a obo:BFO_0000015 ;
        obo:BFO_0000057 :agent ;
        obo:BFO_0000055 :value .
    """)
    assert conforms, report


def test_multiple_values_borne_by_same_participant_conform():
    conforms, report = validate_core("""
    :agent a cco:ont00001017 ;
        obo:BFO_0000196 :valueA, :valueB .
    :valueA a vn-core:ValueDisposition .
    :valueB a vn-core:ValueRole .
    :process a obo:BFO_0000015 ;
        obo:BFO_0000057 :agent ;
        obo:BFO_0000055 :valueA, :valueB .
    """)
    assert conforms, report


def test_multiple_recorded_bearers_use_existential_participant_contract():
    conforms, report = validate_core("""
    :agentA a cco:ont00001017 ;
        obo:BFO_0000196 :value .
    :agentB a cco:ont00001017 ;
        obo:BFO_0000196 :value .
    :value a vn-core:ValueDisposition .
    :process a obo:BFO_0000015 ;
        obo:BFO_0000057 :agentA ;
        obo:BFO_0000055 :value .
    """)
    assert conforms, report


def test_process_may_realize_one_value_and_contravene_another():
    conforms, report = validate_core("""
    :agent a cco:ont00001017 ;
        obo:BFO_0000196 :realizedValue, :contravenedValue .
    :realizedValue a vn-core:ValueDisposition .
    :contravenedValue a vn-core:ValueDisposition .
    :process a obo:BFO_0000015 ;
        obo:BFO_0000057 :agent ;
        obo:BFO_0000055 :realizedValue ;
        vn-core:contravenes :contravenedValue .
    """)
    assert conforms, report


def test_value_realization_process_is_a_defined_class():
    graph = rdflib.Graph()
    graph.parse(str(CORE), format="turtle")
    owl = rdflib.namespace.OWL
    rdf = rdflib.namespace.RDF
    vrp = rdflib.URIRef(
        "https://fandaws.com/ontology/bfo/valuenet-core#ValueRealizationProcess"
    )
    definitions = list(graph.objects(vrp, owl.equivalentClass))
    assert len(definitions) == 1
    assert (definitions[0], rdf.type, owl.Class) in graph


def test_defined_class_entails_value_realization_process_classification():
    graph = rdflib.Graph()
    graph.parse(str(CORE), format="turtle")
    graph.parse(
        data=PREFIXES + """
        :value a vn-core:ValueDisposition .
        :process a obo:BFO_0000015 ;
            obo:BFO_0000055 :value .
        """,
        format="turtle",
    )
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(graph)
    rdf = rdflib.namespace.RDF
    process = rdflib.URIRef("http://example.org/alignment-control#process")
    vrp = rdflib.URIRef(
        "https://fandaws.com/ontology/bfo/valuenet-core#ValueRealizationProcess"
    )
    assert (process, rdf.type, vrp) in graph


def test_value_realization_and_violation_processes_are_not_disjoint():
    graph = rdflib.Graph()
    graph.parse(str(CORE), format="turtle")
    owl = rdflib.namespace.OWL
    vrp = rdflib.URIRef(
        "https://fandaws.com/ontology/bfo/valuenet-core#ValueRealizationProcess"
    )
    vvp = rdflib.URIRef(
        "https://fandaws.com/ontology/bfo/valuenet-core#ValueViolationProcess"
    )
    assert (vrp, owl.disjointWith, vvp) not in graph
    assert (vvp, owl.disjointWith, vrp) not in graph
