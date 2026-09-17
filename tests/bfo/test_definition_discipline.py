# SPDX-License-Identifier: Apache-2.0
"""Definition discipline, gated against what is recorded rather than hoped for.

Two checks from the formal review of 2026-09-16, both measured over the five
authored modules.

GENUS (R16). A definition should open with the class it specializes: "a moral
value disposition to ..." under MoralValueDisposition, not "a disposition to
...". The measure: after an initial article, the definition begins with the
label of one of the class's asserted named parents, compared case-insensitively
with "ICE" read as "information content entity" -- the labels abbreviate and
the definitions do not, and without that two correct definitions read as
wrong. It checks the genus only and says nothing about the differentia.

On 2026-09-16 every module but folk was brought to zero. Folk had 84, and its
curation waited on R15, the decision about which folk classes belong at all:
normalising definitions first would curate classes that may be removed. So the
84 were recorded by name, and the gate is equality. D-014 decided membership:
five of the 84 were removed, and four more aligned under the general parent they
moved to. The folk curation pass that followed corrected the other 75, so every
module is at zero. A new misalignment anywhere
fails. So does fixing one without removing it from the record, which is how
paying the debt down shows up in a diff instead of disappearing into it.

DISJUNCTION (R17). A definition of the form "to X, or a Y" is two definitions
of two things. The pattern is deliberately narrow -- a comma, "or", then an
article or an infinitive -- because 107 definitions contain "or" and nearly all
of them are lists, and a check that fires on every list is one nobody reads.
It is a warning: a reviewed hit is reported, not failed, because splitting a
definition is a content decision. An unreviewed hit fails until someone looks.
When it was written it fired on exactly one definition, FaithDisposition, which
D-012 split; it fires on none now.

ANNOTATIONS (R18, D-013). RULES 2.0, adopted as ValueNet's standard, asks every
term for a label, a definition, a comment and an example. Every authored class
and property has the first two. The last two were mostly missing, so the gap is
recorded by name, per module and annotation, as it stood at adoption, and the
gate is equality again: a new term without them fails, and so does annotating a
recorded one without removing it. Folk's gap waited on R15, like its genera,
and was closed by the same curation pass: no term now lacks either.
"""

from __future__ import annotations

import re
import warnings

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS, SKOS  # noqa: E402

from marep.layout import bfo_artifact  # noqa: E402

MODULES = ("valuenet-core.ttl", "valuenet-schwartz-values.ttl",
           "valuenet-moral-foundations.ttl", "valuenet-moral-epistemics.ttl",
           "valuenet-folk.ttl")
#: Where the labels of CCO and BFO parents come from.
SUPPORT = ("bfo-core.ttl", "cco-valuenet-extract.ttl")

#: Misaligned genera, by module. Folk's 84, recorded on 2026-09-16, fell to 75
#: with D-014 and to none with the folk curation pass. Every module is zero and
#: must stay there.
RECORDED_MISALIGNED = {
    "valuenet-core.ttl": frozenset(),
    "valuenet-schwartz-values.ttl": frozenset(),
    "valuenet-moral-foundations.ttl": frozenset(),
    "valuenet-moral-epistemics.ttl": frozenset(),
    "valuenet-folk.ttl": frozenset(),
}

DISJUNCTION = re.compile(r",\s+or\s+(?:a|an|the|to)\b|;\s+or\b", re.I)

#: Reviewed disjunctive definitions, and why each is still there. Empty since
#: D-012 split FaithDisposition, the only one there was.
REVIEWED_DISJUNCTIONS: dict[str, str] = {}


#: Terms lacking an annotation RULES 2.0 requires. At adoption (D-013) the
#: non-folk modules lacked 32 comments and 60 examples, written the same day;
#: folk's 134 of each waited on R15 and were written after D-014. None remain.
#: Labels and definitions are complete and must stay so.
RECORDED_UNANNOTATED: dict[tuple[str, str], frozenset] = {}

ANNOTATIONS = {"label": RDFS.label, "definition": SKOS.definition,
               "comment": RDFS.comment, "example": SKOS.example}
TERM_TYPES = (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
              OWL.AnnotationProperty)
AUTHORED = "https://fandaws.com/ontology/bfo/"


def normalise(text: str) -> str:
    text = re.sub(r"\bICE\b", "information content entity", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def misaligned(module: Graph, labels: Graph) -> set:
    found = set()
    for cls in module.subjects(RDF.type, OWL.Class):
        if not isinstance(cls, URIRef):
            continue
        definition = module.value(cls, SKOS.definition)
        if definition is None:
            continue  # absence is another test's business
        genera = [normalise(str(label))
                  for parent in module.objects(cls, RDFS.subClassOf)
                  if isinstance(parent, URIRef)
                  for label in labels.objects(parent, RDFS.label)]
        text = re.sub(r"^(?:an?|the)\s+", "", normalise(str(definition)))
        if not any(text.startswith(genus) for genus in genera):
            found.add(str(cls).rsplit("#", 1)[-1])
    return found


@pytest.fixture(scope="module")
def graphs():
    modules = {name: Graph().parse(bfo_artifact(name), format="turtle")
               for name in MODULES}
    labels = Graph()
    for name in MODULES + SUPPORT:
        labels.parse(bfo_artifact(name), format="turtle")
    return modules, labels


# ---------------------------------------------------------------- the measure


CONTROLS = """
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex:   <https://example.invalid/genus#> .
ex:Parent a owl:Class ; rdfs:label "Moral Value Disposition" .
ex:Record a owl:Class ; rdfs:label "Moral Assessment ICE" .
ex:Aligned a owl:Class ; rdfs:subClassOf ex:Parent ;
    skos:definition "A moral value disposition to be fair." .
ex:Misaligned a owl:Class ; rdfs:subClassOf ex:Parent ;
    skos:definition "A disposition to be fair." .
ex:Expanded a owl:Class ; rdfs:subClassOf ex:Record ;
    skos:definition "A moral assessment information content entity that says so." .
"""


def test_the_measure_separates_aligned_from_misaligned():
    """Both directions, and the abbreviation: a measure that flagged
    nothing, or everything, or every ICE, would each fail here."""
    graph = Graph().parse(data=CONTROLS, format="turtle")
    assert misaligned(graph, graph) == {"Misaligned"}


# ---------------------------------------------------------------- the gate


@pytest.mark.parametrize("name", MODULES)
def test_misaligned_genera_are_exactly_the_recorded_ones(graphs, name):
    modules, labels = graphs
    found = misaligned(modules[name], labels)
    recorded = RECORDED_MISALIGNED[name]
    assert not found - recorded, (
        "%s: definitions that do not open with an asserted parent: %s"
        % (name, sorted(found - recorded)))
    assert not recorded - found, (
        "%s: aligned now, so remove from RECORDED_MISALIGNED in this commit: "
        "%s" % (name, sorted(recorded - found)))


def test_the_record_covers_every_module(graphs):
    modules, _labels = graphs
    assert set(RECORDED_MISALIGNED) == set(modules)


# ---------------------------------------------------------------- disjunction


def test_the_disjunction_pattern_finds_two_senses_and_not_a_list():
    assert DISJUNCTION.search(
        "to trust someone or something, or a belief in a doctrine")
    assert DISJUNCTION.search("to rest; or to act")
    assert not DISJUNCTION.search(
        "processes of censure, correction, restitution, forgiveness, or "
        "sanction")
    assert not DISJUNCTION.search("right, wrong, obligatory, or forbidden")


def test_disjunctive_definitions_are_reviewed(graphs):
    modules, _labels = graphs
    hits = {}
    for graph in modules.values():
        for cls in graph.subjects(RDF.type, OWL.Class):
            definition = graph.value(cls, SKOS.definition)
            if definition is not None and DISJUNCTION.search(str(definition)):
                hits[str(cls).rsplit("#", 1)[-1]] = str(definition)

    unreviewed = sorted(set(hits) - set(REVIEWED_DISJUNCTIONS))
    assert not unreviewed, (
        "definitions that may join two senses with 'or', not yet reviewed: "
        + "; ".join("%s: %s" % (n, hits[n]) for n in unreviewed))
    resolved = sorted(set(REVIEWED_DISJUNCTIONS) - set(hits))
    assert not resolved, (
        "no longer disjunctive, so remove from REVIEWED_DISJUNCTIONS: %s"
        % resolved)
    for name in sorted(hits):
        warnings.warn("%s is disjunctive and still open. %s"
                      % (name, REVIEWED_DISJUNCTIONS[name]), UserWarning)


# ---------------------------------------------------------------- annotations


def unannotated(module: Graph, predicate) -> set:
    terms = {s for kind in TERM_TYPES for s in module.subjects(RDF.type, kind)
             if isinstance(s, URIRef) and str(s).startswith(AUTHORED)}
    return {str(s).rsplit("#", 1)[-1] for s in terms
            if (s, predicate, None) not in module}


@pytest.mark.parametrize("name", MODULES)
@pytest.mark.parametrize("annotation", sorted(ANNOTATIONS))
def test_missing_annotations_are_exactly_the_recorded_ones(graphs, name,
                                                           annotation):
    modules, _labels = graphs
    found = unannotated(modules[name], ANNOTATIONS[annotation])
    recorded = RECORDED_UNANNOTATED.get((name, annotation), frozenset())
    assert not found - recorded, (
        "%s: terms without an %s, which RULES 2.0 requires (D-013): %s"
        % (name, annotation, sorted(found - recorded)))
    assert not recorded - found, (
        "%s: annotated now, so remove from RECORDED_UNANNOTATED in this "
        "commit: %s" % (name, sorted(recorded - found)))


def test_the_annotation_measure_sees_classes_and_properties():
    graph = Graph().parse(data="""
    @prefix owl:  <http://www.w3.org/2002/07/owl#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    @prefix vn:   <https://fandaws.com/ontology/bfo/probe#> .
    @prefix ex:   <https://example.invalid/upstream#> .
    vn:Commented a owl:Class ; rdfs:comment "c" .
    vn:Bare a owl:Class .
    vn:bareProperty a owl:ObjectProperty .
    ex:Upstream a owl:Class .
    """, format="turtle")
    assert unannotated(graph, RDFS.comment) == {"Bare", "bareProperty"}
