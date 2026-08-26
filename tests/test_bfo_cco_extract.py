import hashlib
import json
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")
jsonschema = pytest.importorskip("jsonschema")

from jsonschema.validators import Draft202012Validator
from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS


# The repository root comes from the layout contract, not from counting
# parents. This file moves one level deeper in the tests wave, at which
# point parents[1] resolves to tests/ and every path below it is wrong
# without raising anything.
from marep.layout import repository_root  # noqa: E402

ROOT = repository_root()
EXTRACT = ROOT / "BFO" / "imports" / "cco-valuenet-extract.ttl"
MANIFEST = ROOT / "BFO" / "imports" / "cco-valuenet-extract.manifest.json"
SCHEMA = ROOT / "BFO" / "remediation" / "extract-manifest.schema.json"

CCO_AGENT = URIRef("https://www.commoncoreontologies.org/ont00001017")
CCO_AGENT_CAPABILITY = URIRef("https://www.commoncoreontologies.org/ont00001379")
CCO_INFORMATION_BEARING_ENTITY = URIRef(
    "https://www.commoncoreontologies.org/ont00000253"
)
CCO_INFORMATION_CONTENT_ENTITY = URIRef(
    "https://www.commoncoreontologies.org/ont00000958"
)
CCO_ACT_OF_OBSERVATION = URIRef("https://www.commoncoreontologies.org/ont00000037")
CCO_ACT_OF_APPRAISAL = URIRef("https://www.commoncoreontologies.org/ont00000636")
CCO_DESCRIPTIVE_ICE = URIRef("https://www.commoncoreontologies.org/ont00000853")
CCO_PRESCRIPTIVE_ICE = URIRef("https://www.commoncoreontologies.org/ont00000965")
CCO_HAS_INPUT = URIRef("https://www.commoncoreontologies.org/ont00001921")
CCO_HAS_OUTPUT = URIRef("https://www.commoncoreontologies.org/ont00001986")
CCO_INPUT_OF = URIRef("https://www.commoncoreontologies.org/ont00001841")
CCO_OUTPUT_OF = URIRef("https://www.commoncoreontologies.org/ont00001816")
BFO_MATERIAL_ENTITY = URIRef("http://purl.obolibrary.org/obo/BFO_0000040")
BFO_REALIZABLE_ENTITY = URIRef("http://purl.obolibrary.org/obo/BFO_0000017")
BFO_PROCESS = URIRef("http://purl.obolibrary.org/obo/BFO_0000015")
BFO_HAS_PARTICIPANT = URIRef("http://purl.obolibrary.org/obo/BFO_0000057")
RO_HAS_INPUT = URIRef("http://purl.obolibrary.org/obo/RO_0002233")
RO_HAS_OUTPUT = URIRef("http://purl.obolibrary.org/obo/RO_0002234")


@pytest.fixture(scope="module")
def extract_graph():
    graph = Graph()
    graph.parse(EXTRACT, format="turtle")
    return graph


def test_extract_manifest_validates_and_matches_artifact():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(
        manifest
    )
    assert hashlib.sha256(EXTRACT.read_bytes()).hexdigest() == manifest["extract_sha256"]


def test_extract_contains_canonical_cco_dependencies(extract_graph):
    assert (CCO_AGENT, RDF.type, OWL.Class) in extract_graph
    assert (CCO_INFORMATION_BEARING_ENTITY, RDF.type, OWL.Class) in extract_graph
    assert (CCO_INFORMATION_CONTENT_ENTITY, RDF.type, OWL.Class) in extract_graph
    assert (CCO_ACT_OF_OBSERVATION, RDF.type, OWL.Class) in extract_graph
    assert (CCO_ACT_OF_APPRAISAL, RDF.type, OWL.Class) in extract_graph
    assert (CCO_DESCRIPTIVE_ICE, RDF.type, OWL.Class) in extract_graph
    assert (CCO_PRESCRIPTIVE_ICE, RDF.type, OWL.Class) in extract_graph
    assert (CCO_DESCRIPTIVE_ICE, OWL.disjointWith, CCO_PRESCRIPTIVE_ICE) in extract_graph
    assert (CCO_DESCRIPTIVE_ICE, RDFS.subClassOf, CCO_INFORMATION_CONTENT_ENTITY) in extract_graph
    assert (CCO_PRESCRIPTIVE_ICE, RDFS.subClassOf, CCO_INFORMATION_CONTENT_ENTITY) in extract_graph
    assert (CCO_AGENT, RDFS.subClassOf, BFO_MATERIAL_ENTITY) in extract_graph
    assert (CCO_AGENT_CAPABILITY, RDFS.subClassOf, BFO_REALIZABLE_ENTITY) in extract_graph
    assert (CCO_HAS_INPUT, RDFS.subPropertyOf, BFO_HAS_PARTICIPANT) in extract_graph
    assert (CCO_HAS_INPUT, RDFS.domain, BFO_PROCESS) in extract_graph
    assert (CCO_HAS_OUTPUT, RDFS.subPropertyOf, BFO_HAS_PARTICIPANT) in extract_graph
    assert (CCO_HAS_OUTPUT, RDFS.domain, BFO_PROCESS) in extract_graph
    assert (CCO_INPUT_OF, OWL.inverseOf, CCO_HAS_INPUT) in extract_graph
    assert (CCO_OUTPUT_OF, OWL.inverseOf, CCO_HAS_OUTPUT) in extract_graph
    for term in (CCO_AGENT, CCO_AGENT_CAPABILITY, CCO_HAS_INPUT, CCO_HAS_OUTPUT):
        assert not list(extract_graph.objects(term, OWL.deprecated))


def test_agent_equivalence_and_relation_ranges_are_not_truncated(extract_graph):
    agent_equivalences = list(extract_graph.objects(CCO_AGENT, OWL.equivalentClass))
    assert agent_equivalences and all(isinstance(node, BNode) for node in agent_equivalences)
    assert list(extract_graph.objects(CCO_HAS_INPUT, RDFS.range))
    assert list(extract_graph.objects(CCO_HAS_OUTPUT, RDFS.range))
    for node in agent_equivalences + list(extract_graph.objects(CCO_HAS_INPUT, RDFS.range)):
        assert list(extract_graph.triples((node, None, None)))


def test_superseded_ro_terms_are_absent(extract_graph):
    assert not list(extract_graph.triples((RO_HAS_INPUT, None, None)))
    assert not list(extract_graph.triples((RO_HAS_OUTPUT, None, None)))
