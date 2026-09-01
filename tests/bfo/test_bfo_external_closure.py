# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD


# The repository root comes from the layout contract, not from counting
# parents. This file moves one level deeper in the tests wave, at which
# point parents[1] resolves to tests/ and every path below it is wrong
# without raising anything.
from marep.layout import bfo_artifact, repository_root  # noqa: E402

ROOT = repository_root()
CORE_ONTOLOGY = URIRef("https://fandaws.com/ontology/bfo/valuenet-core.owl")
CCO_EXTRACT_ONTOLOGY = URIRef("https://fandaws.com/ontology/imports/cco-valuenet-extract")
CCO_EXTRACT_VERSION = URIRef(
    "https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-25-phase6"
)

PROJECT_LOGICAL_FILES = (
    "valuenet-core.ttl",
    "valuenet-schwartz-values.ttl",
    "valuenet-moral-foundations.ttl",
    "valuenet-folk.ttl",
    "valuenet-moral-epistemics.ttl",
    "valuenet-mappings.ttl",
    "valuenet-moral-epistemics-scenario.ttl",
)

AUTHORITATIVE_FILES = (
    bfo_artifact("bfo-core.ttl"),
    bfo_artifact("cco-valuenet-extract.ttl"),
)

VN_CORE = "https://fandaws.com/ontology/bfo/valuenet-core#"

MAPPING_PREDICATES = {
    URIRef(VN_CORE + "hasBroaderConceptualMatch"),
    URIRef(VN_CORE + "hasRelatedConceptualMatch"),
    URIRef(VN_CORE + "historicallyCorrespondsTo"),
}

LOGICAL_PREDICATES = {
    RDFS.subClassOf,
    RDFS.subPropertyOf,
    RDFS.domain,
    RDFS.range,
    OWL.equivalentClass,
    OWL.equivalentProperty,
    OWL.disjointWith,
    OWL.inverseOf,
    OWL.onProperty,
    OWL.someValuesFrom,
    OWL.allValuesFrom,
    OWL.hasValue,
    OWL.onClass,
    OWL.onDataRange,
    OWL.unionOf,
    OWL.intersectionOf,
    OWL.complementOf,
}

DECLARATION_TYPES = {
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.AnnotationProperty,
    OWL.NamedIndividual,
}

METAMODEL_TYPES = DECLARATION_TYPES | {
    OWL.Ontology,
    OWL.Restriction,
    RDF.Property,
}

STANDARD_PREFIXES = (
    str(RDF),
    str(RDFS),
    str(OWL),
    str(XSD),
    str(SKOS),
    str(DCTERMS),
    "http://purl.org/dc/elements/1.1/",
)

PROJECT_PREFIXES = (
    "https://fandaws.com/ontology/",
)


def load_graph(paths):
    graph = Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def is_external(term):
    if not isinstance(term, URIRef):
        return False
    text = str(term)
    return not text.startswith(STANDARD_PREFIXES + PROJECT_PREFIXES)


def classify_external_terms():
    project = load_graph(bfo_artifact(name) for name in PROJECT_LOGICAL_FILES)
    authoritative = load_graph(AUTHORITATIVE_FILES)

    logical = set()
    mapped = set()

    for subject, predicate, obj in project:
        if predicate in MAPPING_PREDICATES and is_external(obj):
            mapped.add(obj)
            continue

        if predicate == RDF.type and obj not in METAMODEL_TYPES and is_external(obj):
            logical.add(obj)

        if predicate in LOGICAL_PREDICATES:
            if is_external(subject):
                logical.add(subject)
            if is_external(obj):
                logical.add(obj)

        if is_external(predicate):
            logical.add(predicate)

    declared = {
        term
        for term in logical
        if any((term, RDF.type, declaration_type) in authoritative for declaration_type in DECLARATION_TYPES)
    }
    unknown = logical - declared
    mapping_only = mapped - logical
    return declared, mapping_only, unknown


def test_external_terms_are_classified_and_logical_dependencies_are_closed():
    declared, mapping_only, unknown = classify_external_terms()

    assert URIRef("http://purl.obolibrary.org/obo/BFO_0000015") in declared
    assert URIRef("https://www.commoncoreontologies.org/ont00001017") in declared
    assert URIRef("https://www.commoncoreontologies.org/ont00000853") in declared
    assert URIRef("https://w3id.org/spice/SON/HaidtValues#Care") in mapping_only
    assert not unknown, "Unknown external logical dependencies: " + ", ".join(
        sorted(map(str, unknown))
    )


def test_core_imports_the_pinned_cco_extract():
    core = load_graph((bfo_artifact("valuenet-core.ttl"),))
    extract = load_graph((bfo_artifact("cco-valuenet-extract.ttl"),))
    assert (CORE_ONTOLOGY, OWL.imports, CCO_EXTRACT_VERSION) in core
    assert (CCO_EXTRACT_ONTOLOGY, OWL.versionIRI, CCO_EXTRACT_VERSION) in extract
