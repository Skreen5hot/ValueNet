"""Definition-quality and extension controls for remediation Phase 4."""

from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS


ROOT = Path(__file__).resolve().parents[1]
BFO_DIR = ROOT / "BFO"
CORE_FILE = BFO_DIR / "valuenet-core.ttl"
VN = "https://fandaws.com/ontology/bfo/valuenet-core#"
FOLK = "https://fandaws.com/ontology/bfo/valuenet-folk#"
BFO = "http://purl.obolibrary.org/obo/"
CCO = "https://www.commoncoreontologies.org/"


CORE_CLASS_GENUS_PREFIXES = {
    "ValueRelatedRealizableEntity": "A realizable entity that",
    "ValueDisposition": "A disposition that",
    "ValueRole": "A role that",
    "MoralValueDisposition": "A value disposition whose",
    "PersonalValueDisposition": "A value disposition whose",
    "ValueRealizationProcess": "A process that",
    "ValueViolationProcess": "A process that",
    "EvidenceSource": "An information content entity that",
    "TextualRepresentation": "An information content entity that",
    "TextSpan": "An evidence source that",
    "TextSpanSelector": "An information content entity that",
    "ValueEvidenceAnnotation": "An evidence source that",
}

FORBIDDEN_WEAK_PHRASES = (
    "corresponds to",
    "pertains to",
    "related to",
    "associated with",
    "is a value",
)

FOLK_CLUSTER_LEAVES = {
    "Foundational Concepts": "KindnessDisposition",
    "Achievement & Growth": "DiligenceDisposition",
    "Community & Social Connection": "CharityDisposition",
    "Integrity & Principle": "CandorDisposition",
    "Security & Stability": "CleanlinessDisposition",
    "Freedom & Autonomy": "PrivacyDisposition",
    "Well-being & Harmony": "MindfulnessDisposition",
    "Justice & Fairness": "EquityDisposition",
    "Power & Influence": "StatusDisposition",
    "Experiential & Stimulation": "ExplorationDisposition",
    "Discipline & Restraint": "ChastityDisposition",
    "Intellectual": "UnderstandingDisposition",
}


@pytest.fixture(scope="module")
def core_graph():
    graph = Graph()
    graph.parse(CORE_FILE, format="turtle")
    return graph


def project_class(local_name: str) -> URIRef:
    return URIRef(VN + local_name)


def has_subclass_path(graph: Graph, child: URIRef, ancestor: URIRef) -> bool:
    pending = [child]
    seen = set()
    while pending:
        current = pending.pop()
        if current == ancestor:
            return True
        if current in seen:
            continue
        seen.add(current)
        pending.extend(
            parent
            for parent in graph.objects(current, RDFS.subClassOf)
            if isinstance(parent, URIRef)
        )
    return False


def test_every_named_core_class_has_one_genus_differentia_definition(core_graph):
    named_classes = {
        subject
        for subject in core_graph.subjects(RDF.type, OWL.Class)
        if isinstance(subject, URIRef) and str(subject).startswith(VN)
    }
    expected_classes = {project_class(name) for name in CORE_CLASS_GENUS_PREFIXES}
    assert named_classes == expected_classes

    for local_name, expected_prefix in CORE_CLASS_GENUS_PREFIXES.items():
        definitions = list(core_graph.objects(project_class(local_name), SKOS.definition))
        assert len(definitions) == 1, local_name
        definition = str(definitions[0])
        assert definition.startswith(expected_prefix), (local_name, definition)
        lowered = definition.lower()
        for weak_phrase in FORBIDDEN_WEAK_PHRASES:
            assert weak_phrase not in lowered, (local_name, weak_phrase, definition)


def test_value_related_extension_is_exactly_dispositions_or_roles(core_graph):
    value_related = project_class("ValueRelatedRealizableEntity")
    expected_members = {
        project_class("ValueDisposition"),
        project_class("ValueRole"),
    }
    unions = []
    for expression in core_graph.objects(value_related, OWL.equivalentClass):
        head = core_graph.value(expression, OWL.unionOf)
        if head is not None:
            unions.append(set(core_graph.items(head)))
    assert unions == [expected_members]


def test_value_categories_retain_verified_bfo_parents_and_agent_bearer(core_graph):
    value_related = project_class("ValueRelatedRealizableEntity")
    value_disposition = project_class("ValueDisposition")
    value_role = project_class("ValueRole")
    assert (value_related, RDFS.subClassOf, URIRef(BFO + "BFO_0000017")) in core_graph
    assert (value_disposition, RDFS.subClassOf, URIRef(BFO + "BFO_0000016")) in core_graph
    assert (value_role, RDFS.subClassOf, URIRef(BFO + "BFO_0000023")) in core_graph

    restrictions = [
        node
        for node in core_graph.objects(value_related, RDFS.subClassOf)
        if isinstance(node, BNode)
    ]
    assert any(
        (node, OWL.onProperty, URIRef(BFO + "BFO_0000197")) in core_graph
        and (node, OWL.someValuesFrom, URIRef(CCO + "ont00001017")) in core_graph
        for node in restrictions
    )


def test_process_definitions_match_their_equivalent_class_relations(core_graph):
    cases = {
        "ValueRealizationProcess": URIRef(BFO + "BFO_0000055"),
        "ValueViolationProcess": project_class("contravenes"),
    }
    for local_name, relation in cases.items():
        cls = project_class(local_name)
        expressions = list(core_graph.objects(cls, OWL.equivalentClass))
        assert len(expressions) == 1
        head = core_graph.value(expressions[0], OWL.intersectionOf)
        assert head is not None
        restrictions = [item for item in core_graph.items(head) if isinstance(item, BNode)]
        assert any(
            (restriction, OWL.onProperty, relation) in core_graph
            and (
                restriction,
                OWL.someValuesFrom,
                project_class("ValueRelatedRealizableEntity"),
            )
            in core_graph
            for restriction in restrictions
        )


def test_moral_and_personal_value_dispositions_are_not_forced_disjoint(core_graph):
    moral = project_class("MoralValueDisposition")
    personal = project_class("PersonalValueDisposition")
    assert (moral, OWL.disjointWith, personal) not in core_graph
    assert (personal, OWL.disjointWith, moral) not in core_graph


def test_one_leaf_from_each_folk_cluster_remains_a_valid_specialization():
    graph = Graph()
    for path in (
        CORE_FILE,
        BFO_DIR / "valuenet-schwartz-values.ttl",
        BFO_DIR / "valuenet-folk.ttl",
    ):
        graph.parse(path, format="turtle")

    value_related = project_class("ValueRelatedRealizableEntity")
    disposition = URIRef(BFO + "BFO_0000016")
    for cluster, local_name in FOLK_CLUSTER_LEAVES.items():
        leaf = URIRef(FOLK + local_name)
        assert (leaf, RDF.type, OWL.Class) in graph, cluster
        assert has_subclass_path(graph, leaf, value_related), cluster
        assert has_subclass_path(graph, leaf, disposition), cluster
        children = {
            child
            for child in graph.subjects(RDFS.subClassOf, leaf)
            if isinstance(child, URIRef)
        }
        assert not children, (cluster, local_name, sorted(map(str, children)))


def test_folk_value_role_control_remains_a_role_specialization():
    graph = Graph()
    for path in (CORE_FILE, BFO_DIR / "valuenet-folk.ttl"):
        graph.parse(path, format="turtle")
    role = URIRef(FOLK + "ProfessionalismRole")
    assert has_subclass_path(graph, role, project_class("ValueRelatedRealizableEntity"))
    assert has_subclass_path(graph, role, URIRef(BFO + "BFO_0000023"))


def test_moral_foundation_leaf_remains_a_moral_disposition_specialization():
    graph = Graph()
    for path in (CORE_FILE, BFO_DIR / "valuenet-moral-foundations.ttl"):
        graph.parse(path, format="turtle")
    care = URIRef(
        "https://fandaws.com/ontology/bfo/valuenet-moral-foundations#CareDisposition"
    )
    assert has_subclass_path(graph, care, project_class("MoralValueDisposition"))
    assert has_subclass_path(graph, care, project_class("ValueRelatedRealizableEntity"))
    assert has_subclass_path(graph, care, URIRef(BFO + "BFO_0000016"))
