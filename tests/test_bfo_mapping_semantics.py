"""Phase 5 controls for mapping semantics and the selected OWL 2 DL profile."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS


ROOT = Path(__file__).resolve().parents[1]
BFO_DIR = ROOT / "BFO"

ONTOLOGY_FILES = tuple(
    BFO_DIR / name
    for name in (
        "bfo-core.ttl",
        "imports/cco-valuenet-extract.ttl",
        "valuenet-core.ttl",
        "valuenet-schwartz-values.ttl",
        "valuenet-moral-foundations.ttl",
        "valuenet-folk.ttl",
        "valuenet-moral-epistemics.ttl",
        "valuenet-mappings.ttl",
        "valuenet-moral-epistemics-scenario.ttl",
    )
)

VN_CORE = Namespace("https://fandaws.com/ontology/bfo/valuenet-core#")
VN_ME = Namespace("https://fandaws.com/ontology/bfo/valuenet-moral-epistemics#")
CCO = Namespace("https://www.commoncoreontologies.org/")

PROJECT_MAPPING_PREDICATES = {
    VN_CORE.hasBroaderConceptualMatch,
    VN_CORE.hasRelatedConceptualMatch,
    VN_CORE.historicallyCorrespondsTo,
}

CANONICAL_SKOS_MAPPING_PREDICATES = {
    SKOS.broadMatch,
    SKOS.closeMatch,
    SKOS.exactMatch,
    SKOS.narrowMatch,
    SKOS.relatedMatch,
}

ENTITY_TYPES = (
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.AnnotationProperty,
)


@pytest.fixture(scope="module")
def ontology_graph():
    graph = Graph()
    for path in ONTOLOGY_FILES:
        graph.parse(path, format="turtle")
    return graph


def _individual_positions(graph: Graph) -> dict[URIRef, set[str]]:
    """Return every named resource used in an OWL individual position.

    Annotation assertions are deliberately absent: annotating an ontology
    entity does not make it an OWL individual. Object/data property assertions
    and named-class type assertions do.
    """

    classes = set(graph.subjects(RDF.type, OWL.Class))
    object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    data_properties = set(graph.subjects(RDF.type, OWL.DatatypeProperty))
    positions: dict[URIRef, set[str]] = defaultdict(set)

    for subject, predicate, obj in graph:
        if predicate == RDF.type and obj in classes and isinstance(subject, URIRef):
            positions[subject].add(f"rdf:type {obj}")
        if predicate in object_properties:
            if isinstance(subject, URIRef):
                positions[subject].add(f"subject of {predicate}")
            if isinstance(obj, URIRef):
                positions[obj].add(f"object of {predicate}")
        if predicate in data_properties and isinstance(subject, URIRef):
            positions[subject].add(f"subject of {predicate}")

    return positions


def _format_positions(terms: set[URIRef], positions: dict[URIRef, set[str]]) -> str:
    return "\n".join(
        f"- {term}: {', '.join(sorted(positions[term]))}" for term in sorted(terms, key=str)
    )


def _has_named_subclass_path(graph: Graph, source: URIRef, target: URIRef) -> bool:
    """Return whether source reaches target through named rdfs:subClassOf axioms."""

    pending = [source]
    visited: set[URIRef] = set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        for superclass in graph.objects(current, RDFS.subClassOf):
            if superclass == target:
                return True
            if isinstance(superclass, URIRef) and superclass not in visited:
                pending.append(superclass)
    return False


def test_canonical_skos_mapping_properties_are_not_asserted(ontology_graph):
    assertions = [
        triple
        for predicate in CANONICAL_SKOS_MAPPING_PREDICATES
        for triple in ontology_graph.triples((None, predicate, None))
    ]
    assert not assertions, "Canonical SKOS mappings require separate skos:Concept individuals"


def test_mapping_inventory_has_the_adjudicated_phase5_counts(ontology_graph):
    counts = Counter(
        predicate
        for predicate in PROJECT_MAPPING_PREDICATES
        for _subject, _predicate, _obj in ontology_graph.triples((None, predicate, None))
    )
    assert counts == Counter(
        {
            VN_CORE.hasBroaderConceptualMatch: 45,
            VN_CORE.hasRelatedConceptualMatch: 5,
            VN_CORE.historicallyCorrespondsTo: 17,
        }
    )


def test_project_mapping_vocabulary_is_annotation_only(ontology_graph):
    ontology_entities = set().union(
        *(set(ontology_graph.subjects(RDF.type, kind)) for kind in ENTITY_TYPES)
    )
    for predicate in PROJECT_MAPPING_PREDICATES:
        assert (predicate, RDF.type, OWL.AnnotationProperty) in ontology_graph
        assert (predicate, RDF.type, OWL.ObjectProperty) not in ontology_graph
        assert (predicate, RDF.type, OWL.DatatypeProperty) not in ontology_graph
        assert not list(ontology_graph.subjects(OWL.onProperty, predicate))
        assertions = list(ontology_graph.subject_objects(predicate))
        assert assertions
        assert all(subject in ontology_entities for subject, _obj in assertions)
        assert all(isinstance(obj, URIRef) for _subject, obj in assertions)


def test_reviewed_cco_mappings_remain_subclass_paths_not_equivalences(ontology_graph):
    expected = {
        (VN_ME.ObservationalEvidenceICE, CCO.ont00000853),
        (VN_ME.SafetyAssessmentICE, CCO.ont00000853),
        (VN_ME.MoralNormICE, CCO.ont00000965),
        (VN_ME.MoralDiscernmentAct, CCO.ont00000636),
    }
    for source, target in expected:
        assert _has_named_subclass_path(ontology_graph, source, target)
        assert (source, OWL.equivalentClass, target) not in ontology_graph
        assert (target, OWL.equivalentClass, source) not in ontology_graph


def test_owl2dl_entity_kinds_do_not_overlap(ontology_graph):
    declarations = {
        kind: set(ontology_graph.subjects(RDF.type, kind)) for kind in ENTITY_TYPES
    }
    conflicts = []
    for index, left in enumerate(ENTITY_TYPES):
        for right in ENTITY_TYPES[index + 1 :]:
            overlap = declarations[left] & declarations[right]
            if overlap:
                conflicts.append((left, right, sorted(overlap, key=str)))
    assert not conflicts, f"OWL entity-kind conflicts: {conflicts}"


def test_owl2dl_restriction_properties_are_declared_logical_properties(ontology_graph):
    logical_properties = set(ontology_graph.subjects(RDF.type, OWL.ObjectProperty))
    logical_properties.update(ontology_graph.subjects(RDF.type, OWL.DatatypeProperty))
    unknown = {
        prop
        for prop in ontology_graph.objects(None, OWL.onProperty)
        if isinstance(prop, URIRef) and prop not in logical_properties
    }
    assert not unknown, "Undeclared restriction properties: " + ", ".join(
        sorted(map(str, unknown))
    )


def test_no_class_iri_is_used_in_individual_position(ontology_graph):
    positions = _individual_positions(ontology_graph)
    classes = set(ontology_graph.subjects(RDF.type, OWL.Class))
    conflicts = classes & positions.keys()
    assert not conflicts, "Class IRIs used in individual position:\n" + _format_positions(
        conflicts, positions
    )


def test_no_property_iri_is_used_in_individual_position(ontology_graph):
    positions = _individual_positions(ontology_graph)
    properties = set().union(
        set(ontology_graph.subjects(RDF.type, OWL.ObjectProperty)),
        set(ontology_graph.subjects(RDF.type, OWL.DatatypeProperty)),
        set(ontology_graph.subjects(RDF.type, OWL.AnnotationProperty)),
    )
    conflicts = properties & positions.keys()
    assert not conflicts, "Property IRIs used in individual position:\n" + _format_positions(
        conflicts, positions
    )


def test_individual_position_reporter_detects_a_class_object_property_assertion():
    example = Namespace("https://example.org/profile-test#")
    graph = Graph()
    graph.add((example.MappedClass, RDF.type, OWL.Class))
    graph.add((example.mapsTo, RDF.type, OWL.ObjectProperty))
    graph.add((example.MappedClass, example.mapsTo, example.Target))

    positions = _individual_positions(graph)
    assert example.MappedClass in positions
    assert positions[example.MappedClass] == {f"subject of {example.mapsTo}"}
