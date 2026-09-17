# SPDX-License-Identifier: Apache-2.0
"""The published text layer is the one D-005 decided.

tests/bfo/test_text_value_placement.py shows which placements of a text value
are logically possible, over small scenario graphs, and says in so many words
that it does not show the published ontology follows the decision. This file
does, in three ways.

- Structure. The superclasses D-005 names are the only named superclasses the
  four text-layer classes have, and the terms retired with it --
  `vn-core:hasTextValue` (D-005 item 5) and `vn-core:EvidenceSource` (R10 of
  the review response) -- are declared and used nowhere in the BFO tree.
- Wording. The two definitions and the property declaration are read out of
  the decision record and compared with the module, so the record and the
  ontology cannot drift apart without a failure.
- Reasoning. HermiT runs over the suite and the worked scenario and must
  classify neither class, and none of the scenario's text individuals, as
  information content. A selector and an evidence annotation in the same run
  must be classified as information content, which shows the check can see
  ICE membership when it holds.

One boundary is pinned as well, because nothing else would show it. CCO 2.2
defines Information Content Entity as *equivalent to* a generically dependent
continuant that is about some entity, so asserting that a representation or a
span is about something -- directly, or through `designates` or `describes` --
would re-classify it as information content, consistently, with nothing to
report it. D-011 makes both classes disjoint with ICE, which turns that
assertion into an inconsistency. The boundary test holds it there, and holds a
selector designating a span consistent, so the disjointness is shown to bite
only where it should.

Like the placement test this starts a JVM per reasoning run and is left in the
default run for the same reason.
"""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import BNode, Graph, Namespace, URIRef  # noqa: E402
from rdflib.collection import Collection  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS, SKOS  # noqa: E402

from marep import layout  # noqa: E402
from marep.layout import bfo_artifact, repository_root  # noqa: E402

VN_CORE = Namespace("https://fandaws.com/ontology/bfo/valuenet-core#")
SCENARIO_NS = Namespace(
    "https://fandaws.com/ontology/bfo/valuenet-moral-epistemics-scenario#")
CCO = Namespace("https://www.commoncoreontologies.org/")
OBO = Namespace("http://purl.obolibrary.org/obo/")

GDC = OBO.BFO_0000031
GENERICALLY_DEPENDS_ON = OBO.BFO_0000084
IBE = CCO.ont00000253
ICE = CCO.ont00000958
DESIGNATIVE_ICE = CCO.ont00000686
DESCRIPTIVE_ICE = CCO.ont00000853
DESIGNATES = CCO.ont00001916
IS_ABOUT = CCO.ont00001808

CORE = bfo_artifact("valuenet-core.ttl")
DECISIONS = repository_root() / "docs/bfo/remediation/DECISION_RECORDS.md"

#: The suite as tools/bfo/check_bfo_consistency.py reasons over it, plus the
#: worked scenario, which is where the text individuals are.
SUITE = tuple(bfo_artifact(name) for name in (
    "bfo-core.ttl",
    "cco-valuenet-extract.ttl",
    "valuenet-core.ttl",
    "valuenet-schwartz-values.ttl",
    "valuenet-moral-foundations.ttl",
    "valuenet-folk.ttl",
    "valuenet-moral-epistemics.ttl",
    "valuenet-moral-epistemics-scenario.ttl",
))

#: Retired terms and where each retirement is decided.
RETIRED = {
    VN_CORE.hasTextValue: "D-005 item 5",
    VN_CORE.EvidenceSource: "R10 of the formal review response",
}


def load(paths) -> Graph:
    graph = Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


@pytest.fixture(scope="module")
def core() -> Graph:
    return load((CORE,))


def named_superclasses(graph: Graph, cls: URIRef) -> set:
    return {o for o in graph.objects(cls, RDFS.subClassOf)
            if isinstance(o, URIRef)}


def restrictions(graph: Graph, cls: URIRef):
    for node in graph.objects(cls, RDFS.subClassOf):
        if isinstance(node, BNode) and (node, RDF.type, OWL.Restriction) in graph:
            yield (graph.value(node, OWL.onProperty),
                   graph.value(node, OWL.someValuesFrom))


def d005() -> str:
    text = DECISIONS.read_text(encoding="utf-8")
    start = text.index("## D-005")
    return text[start:text.index("\n## ", start + 1)]


def decided_item(number: int) -> str:
    match = re.search(r"^%d\. (.*?)(?=^\d+\. |^### |\Z)" % number, d005(),
                      re.S | re.M)
    assert match, "D-005 has no item %d" % number
    return match.group(1)


# ------------------------------------------------------------------ structure


def test_the_retired_terms_are_declared_and_used_nowhere():
    """Everything under the BFO tree except vendored upstream: modules,
    shapes and the scenario, since a shape path or scenario triple naming a
    retired term would keep it alive."""
    tree = layout.component("bfo.ontology-tree").resolve()
    found = []
    for path in sorted(tree.rglob("*.ttl")):
        if path.relative_to(tree).as_posix().startswith("vendor/"):
            continue
        graph = load((path,))
        for term, decision in RETIRED.items():
            if (term, None, None) in graph or (None, term, None) in graph \
                    or (None, None, term) in graph:
                found.append("%s still names %s, retired by %s"
                             % (path.relative_to(tree).as_posix(),
                                term.split("#")[-1], decision))
    assert not found, "\n".join(found)


def test_representation_and_span_are_form_level_not_information_content(core):
    """D-005 items 2 and 4. Only named superclasses are compared, as a set,
    so an extra parent -- EvidenceSource was one -- fails as surely as a
    missing one."""
    assert named_superclasses(core, VN_CORE.TextualRepresentation) == {GDC}
    assert (GENERICALLY_DEPENDS_ON, IBE) in set(
        restrictions(core, VN_CORE.TextualRepresentation)), (
        "TextualRepresentation has lost its existential carrier restriction")
    assert named_superclasses(core, VN_CORE.TextSpan) == {GDC}


def test_representation_and_span_are_disjoint_with_information_content(core):
    """D-011. Without these two axioms an aboutness assertion re-classifies
    form as content silently; with them it is an error a reasoner reports."""
    for cls in (VN_CORE.TextualRepresentation, VN_CORE.TextSpan):
        assert (cls, OWL.disjointWith, ICE) in core, (
            "%s is not disjoint with information content entity"
            % cls.split("#")[-1])


def test_selector_designates_and_evidence_annotation_describes(core):
    """D-005 item 8 and R10. The selector is about the span it picks out, so
    selectsTextSpan specializes CCO designates: a CCO consumer asking what a
    selector designates reaches the span, and the local property keeps the
    range that the shapes and competency questions rely on."""
    assert named_superclasses(core, VN_CORE.TextSpanSelector) == {DESIGNATIVE_ICE}
    assert named_superclasses(core, VN_CORE.ValueEvidenceAnnotation) == {DESCRIPTIVE_ICE}
    assert (VN_CORE.selectsTextSpan, RDFS.subPropertyOf, DESIGNATES) in core


def test_is_evidence_for_states_no_domain(core):
    """R10 asked that the documentary domain name the two approved subject
    classes. OWL 2 DL allows only an IRI as an annotation property's domain,
    and the two share no named parent below information content -- which is
    where the span no longer is -- so the domain is removed and SHACL, which
    already names both classes, is what enforces it."""
    assert (VN_CORE.isEvidenceFor, RDFS.domain, None) not in core
    assert (VN_CORE.isEvidenceFor, RDFS.range, OBO.BFO_0000015) in core


# -------------------------------------------------------------------- wording


@pytest.mark.parametrize("item, cls", [
    (3, VN_CORE.TextualRepresentation),
    (4, VN_CORE.TextSpan),
])
def test_the_definition_is_the_one_d005_records(core, item, cls):
    match = re.search(r"Its definition is: \*(.+?)\*", decided_item(item))
    assert match, "D-005 item %d no longer records a definition" % item
    recorded = match.group(1)
    published = [str(d) for d in core.objects(cls, SKOS.definition)]
    assert len(published) == 1, published
    assert published[0][:1].lower() + published[0][1:] == recorded, (
        "%s is defined as %r in the module and %r in D-005 item %d"
        % (cls.split("#")[-1], published[0], recorded, item))


def test_the_text_property_is_declared_as_d005_records(core):
    """The Turtle block in D-005 item 5, parsed, must be in the module: every
    ground triple, and a domain that is the union it records and nothing
    else."""
    block = re.search(r"```turtle\n(.*?)```", decided_item(5), re.S)
    assert block, "D-005 item 5 no longer carries the declaration"
    recorded = Graph()
    recorded.parse(data="\n".join(line[3:] if line.startswith("   ") else line
                                  for line in block.group(1).splitlines()),
                   format="turtle")
    prop = VN_CORE.hasTextualSequenceValue
    for s, p, o in recorded:
        if isinstance(s, BNode) or isinstance(o, BNode):
            continue
        assert (s, p, o) in core, "the module lacks %s %s %s" % (
            s.n3(), p.n3(), o.n3())

    def union(graph):
        domains = list(graph.objects(prop, RDFS.domain))
        assert len(domains) == 1, domains
        members = graph.value(domains[0], OWL.unionOf)
        assert members is not None, "the domain is not a union"
        return set(Collection(graph, members))

    assert union(core) == union(recorded) == {
        VN_CORE.TextualRepresentation, VN_CORE.TextSpan}


# ------------------------------------------------------------------ reasoning

try:
    import owlready2
except ImportError:  # pragma: no cover - environment guidance
    owlready2 = None


def reason(graph: Graph):
    """HermiT over one merged graph. Returns the world, or None if the
    graph is inconsistent. Skips rather than fails without a reasoner, and
    only the reasoning tests: the structural ones above need neither."""
    if owlready2 is None:  # pragma: no cover - environment guidance
        pytest.skip("owlready2 is required to run HermiT; without it the "
                    "published text layer's classification is unverified "
                    "on this machine.")
    if shutil.which("java") is None:  # pragma: no cover - environment guidance
        pytest.skip("HermiT needs a Java runtime on PATH; without one the "
                    "published text layer's classification is unverified "
                    "on this machine.")
    for triple in list(graph.triples((None, OWL.imports, None))):
        graph.remove(triple)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "merged.owl"
        graph.serialize(path, format="xml")
        world = owlready2.World()
        with open(path, "rb") as stream:
            onto = world.get_ontology(
                "https://example.invalid/text-layer-follows-d005").load(
                    fileobj=stream)
        try:
            owlready2.sync_reasoner([onto], debug=0)
        except owlready2.OwlReadyInconsistentOntologyError:
            return None
    return world


def types(world, iri: URIRef) -> set:
    entity = world[str(iri)]
    assert entity is not None, "%s is not in the reasoned graph" % iri
    return {str(getattr(c, "iri", c)) for c in entity.INDIRECT_is_a}


@pytest.fixture(scope="module")
def suite():
    world = reason(load(SUITE))
    assert world is not None, (
        "HermiT found the suite with the worked scenario inconsistent")
    return world


def test_hermit_does_not_classify_text_as_information_content(suite):
    for cls in (VN_CORE.TextualRepresentation, VN_CORE.TextSpan):
        ancestors = types(suite, cls)
        assert str(GDC) in ancestors, cls
        assert str(ICE) not in ancestors, (
            "%s is entailed to be information content" % cls.split("#")[-1])
    for individual in ("transcriptRepresentation1", "textSpan1", "textSpan2"):
        got = types(suite, SCENARIO_NS[individual])
        assert str(ICE) not in got, (
            "%s is inferred to be information content" % individual)
        assert str(IBE) not in got, (
            "%s is inferred to be an information bearing entity" % individual)


def test_hermit_does_classify_selectors_and_annotations_as_information_content(suite):
    """The positive control for the test above, in the same reasoning run."""
    assert str(ICE) in types(suite, SCENARIO_NS.textSpanSelector1)
    assert str(ICE) in types(suite, SCENARIO_NS.evidenceAnnotation1)


BOUNDARY = """
@prefix obo:     <http://purl.obolibrary.org/obo/> .
@prefix cco:     <https://www.commoncoreontologies.org/> .
@prefix vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#> .
@prefix ex:      <https://example.invalid/boundary#> .
ex:carrier a cco:ont00000253 ; obo:BFO_0000101 ex:representation .
ex:representation a vn-core:TextualRepresentation ;
    vn-core:hasTextualSequenceValue "Honesty is the best policy." .
ex:conduct a obo:BFO_0000015 .
"""


SPAN = """
ex:span a vn-core:TextSpan ; vn-core:isTextSpanOf ex:representation ;
    vn-core:hasTextualSequenceValue "Honesty" .
"""


@pytest.mark.parametrize("extra, consistent", [
    ("", True),
    ("ex:representation cco:ont00001808 ex:conduct .", False),
    (SPAN + "ex:span cco:ont00001916 ex:conduct .", False),
    (SPAN + "ex:selector a vn-core:TextSpanSelector ; "
            "cco:ont00001916 ex:span .", True),
], ids=["no-aboutness", "representation-is-about-something",
        "span-designates-something", "selector-designates-the-span"])
def test_aboutness_asserted_of_form_is_inconsistent(extra, consistent):
    """D-011. Aboutness of a representation, or designation by a span through
    a subproperty of is about, contradicts the disjointness. Aboutness *of*
    a span, by a selector, is what selectors are for and stays consistent.
    Reasoned over BFO, the extract and core alone, so the result is about
    those axioms and not about anything the other modules add."""
    graph = load((bfo_artifact("bfo-core.ttl"),
                  bfo_artifact("cco-valuenet-extract.ttl"), CORE))
    graph.parse(data=BOUNDARY + extra, format="turtle")
    world = reason(graph)
    assert (world is not None) is consistent, (
        "HermiT found this %s" % ("inconsistent" if world is None
                                  else "consistent"))
    if world is not None:
        assert str(ICE) not in types(
            world, URIRef("https://example.invalid/boundary#representation"))


DIRECT = """
@prefix cco:     <https://www.commoncoreontologies.org/> .
@prefix vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#> .
@prefix ex:      <https://example.invalid/direct#> .
"""


@pytest.mark.parametrize("form", ["TextualRepresentation", "TextSpan"])
@pytest.mark.parametrize("also_content, consistent", [
    (False, True),
    (True, False),
], ids=["form-only", "form-and-information-content"])
def test_form_typed_as_information_content_is_inconsistent(
        form, also_content, consistent):
    """D-011's contract, asserted directly rather than reached through
    aboutness: one individual typed as a form-level text class and as
    Information Content Entity is inconsistent. The reviewer suggested it on
    2026-09-17 (FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF_2.md), so that a
    change to the disjointness fails here even if the aboutness routes above
    were to change with it. The form-only case is its control."""
    graph = load((bfo_artifact("bfo-core.ttl"),
                  bfo_artifact("cco-valuenet-extract.ttl"), CORE))
    kinds = "vn-core:" + form + (", cco:ont00000958" if also_content else "")
    graph.parse(data=DIRECT + "ex:x a %s .\n" % kinds, format="turtle")
    world = reason(graph)
    assert (world is not None) is consistent, (
        "HermiT found ex:x, typed %s, %s"
        % (kinds, "inconsistent" if world is None else "consistent"))
