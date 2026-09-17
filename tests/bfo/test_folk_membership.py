# SPDX-License-Identifier: Apache-2.0
"""Folk membership is what D-014 decided, read from the decision itself.

D-014 closed R15 of the formal review response: which folk values belong in
the BFO folk module, and how each of the 278 corpus values is carried. The
decision lives in two places -- the record in DECISION_RECORDS.md and its
tables in R15_FOLK_MEMBERSHIP_PROPOSAL.md -- and the ontology is a third. Each
test here reads the record and checks the ontology against it, so the two
cannot drift apart without a failure: a class quietly restored, a label added
for a word the record calls a correspondence, a correspondence dropped.

What the tables settle:

- Table A1, the lexical synonyms: `skos:altLabel` on the class, because the
  word names the same concept.
- Table A2, the correspondences: `vn-core:hasRelatedConceptualMatch` in
  valuenet-mappings.ttl, from the class to the corpus value's IRI, because the
  word evokes the class without naming it -- and so never a label.
- Table A4, the exclusions: config/folk-membership.json, the one kind no
  triple carries.

`test_folk_coverage.py` measures the same result by kind without the record.
"""

from __future__ import annotations

import json
import re

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph, Literal, URIRef  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS, SKOS  # noqa: E402

from marep import layout  # noqa: E402
from marep.layout import bfo_artifact, repository_root  # noqa: E402

ROOT = repository_root()
DECISIONS = ROOT / "docs/bfo/remediation/DECISION_RECORDS.md"
TABLES = ROOT / "docs/bfo/remediation/R15_FOLK_MEMBERSHIP_PROPOSAL.md"

FOLK = "https://fandaws.com/ontology/bfo/valuenet-folk#"
SCHWARTZ = "https://fandaws.com/ontology/bfo/valuenet-schwartz-values#"
CORE = "https://fandaws.com/ontology/bfo/valuenet-core#"
ME = "https://fandaws.com/ontology/bfo/valuenet-moral-epistemics#"
ODP = "http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#"
W3ID = "https://w3id.org/valuenet/folk#"
RELATED = URIRef(CORE + "hasRelatedConceptualMatch")
PREFIXES = {"core": CORE, "folk": FOLK, "schwartz": SCHWARTZ,
            "schwartz-values": SCHWARTZ}


def normalise(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def iri(name: str) -> URIRef:
    """`ThriftDisposition` is a folk class; a prefixed name says its module."""
    prefix, _, local = name.rpartition(":")
    return URIRef((PREFIXES[prefix] if prefix else FOLK) + local)


# ------------------------------------------------------------ the record


@pytest.fixture(scope="module")
def decision() -> str:
    text = DECISIONS.read_text(encoding="utf-8")
    start = text.index("## D-014")
    return text[start:text.index("\n## ", start + 1)]


def item(decision: str, number: int) -> str:
    start = decision.index("\n%d. **" % number)
    end = decision.find("\n%d. **" % (number + 1), start)
    return decision[start:end if end > 0 else decision.index("### Rationale")]


def table(title: str) -> list[list[str]]:
    """The rows of one R15 table, as cells."""
    text = TABLES.read_text(encoding="utf-8")
    start = text.index("### " + title)
    end = text.index("\n#", start + 1)
    rows = [line for line in text[start:end].splitlines()
            if line.startswith("| ") and not line.startswith("| corpus value")]
    return [[cell.strip() for cell in row.strip("|").split(" | ")]
            for row in rows]


# ------------------------------------------------------------ the ontology


@pytest.fixture(scope="module")
def folk() -> Graph:
    return Graph().parse(bfo_artifact("valuenet-folk.ttl"), format="turtle")


@pytest.fixture(scope="module")
def mappings() -> Graph:
    return Graph().parse(bfo_artifact("valuenet-mappings.ttl"), format="turtle")


@pytest.fixture(scope="module")
def every_module() -> Graph:
    graph = Graph()
    for path in layout.component("bfo.ontology-tree").resolve().rglob("*.ttl"):
        graph.parse(path, format="turtle")
    return graph


# ------------------------------------------------------------ removals


def removed(decision) -> list[str]:
    names = re.findall(r"`(\w+Disposition)`", item(decision, 7))
    assert len(names) == 7, names
    return names


def test_the_removed_classes_are_gone_from_every_module(decision, every_module):
    """Removal is an IRI break (D-014 item 7), so nothing may still use one:
    not a parent, not a mapping, not a shape."""
    for name in removed(decision):
        term = URIRef(FOLK + name)
        uses = ([t for t in every_module.triples((term, None, None))]
                + [t for t in every_module.triples((None, None, term))])
        assert not uses, "%s is removed and still used: %s" % (name, uses[:3])


def test_openness_is_no_classs_label(folk):
    """Openness names the Big Five trait, a VIA strength and Schwartz's
    openness to change. Retiring the class must not move the word onto
    another one, OpenMindednessDisposition least of all."""
    for predicate in (RDFS.label, SKOS.altLabel):
        for _cls, value in folk.subject_objects(predicate):
            assert normalise(str(value)) not in {"openness",
                                                 "opennessdisposition"}


def test_prudence_no_longer_leans_on_discretion(every_module):
    """D-014: the dependency is removed, and no replacement is forced."""
    prudence = URIRef(ME + "PrudenceDisposition")
    assert (prudence, RELATED, URIRef(SCHWARTZ + "SecurityDisposition")) in every_module
    for _p, value in every_module.predicate_objects(prudence):
        assert "Discretion" not in str(value), value


# ------------------------------------------------------------ re-parenting


def test_folk_powers_subclasses_are_placed_as_decided(folk):
    """Status satisfies Schwartz Power's differentia; the other four do not,
    and go under the general parent with a related match where D-014 records
    one (item 8)."""
    parent = {
        "StatusDisposition": SCHWARTZ + "PowerDisposition",
        "ControlDisposition": CORE + "PersonalValueDisposition",
        "LeadershipDisposition": CORE + "PersonalValueDisposition",
        "InfluenceDisposition": CORE + "PersonalValueDisposition",
        "RecognitionDisposition": CORE + "PersonalValueDisposition",
    }
    related = {
        "StatusDisposition": set(),
        "ControlDisposition": {SCHWARTZ + "PowerDisposition"},
        "LeadershipDisposition": {SCHWARTZ + "PowerDisposition"},
        "InfluenceDisposition": set(),
        "RecognitionDisposition": {SCHWARTZ + "PowerDisposition",
                                   SCHWARTZ + "AchievementDisposition"},
    }
    for name, expected in parent.items():
        cls = URIRef(FOLK + name)
        assert set(map(str, folk.objects(cls, RDFS.subClassOf))) == {expected}, name
        assert set(map(str, folk.objects(cls, RELATED))) == related[name], name


def test_control_is_not_narrowed_to_fit_a_parent(folk):
    definition = str(folk.value(URIRef(FOLK + "ControlDisposition"), SKOS.definition))
    assert "or the course of events" in definition


# ------------------------------------------------------------ what stays


def test_the_classes_kept_under_m6_are_still_declared(decision, folk):
    kept = re.findall(r"\| `(\w+Disposition)` \|", item(decision, 9))
    assert len(kept) == 6, kept
    for name in kept:
        assert (URIRef(FOLK + name), RDF.type, OWL.Class) in folk, name


# ------------------------------------------------------------ additions


def added(decision) -> list[tuple[str, str, str]]:
    rows = re.findall(r"^\s*\| `(\w+Disposition)` \| `([\w:-]+)` \| (.+?) \|$",
                      item(decision, 10), re.M)
    assert len(rows) == 6, rows
    return rows


def test_the_added_classes_are_the_ones_recorded(decision, folk):
    """Parent and definition as the record states them. For the two worded
    "A Patriotism Disposition is a Loyalty Disposition that ...", the
    definition carries the definiens after "is", as every module definition
    does (item 10)."""
    for name, parent, recorded in added(decision):
        cls = URIRef(FOLK + name)
        assert (cls, RDFS.subClassOf, iri(parent)) in folk, (name, parent)
        recorded = recorded.strip('"')
        if " is a " in recorded:
            recorded = recorded.split(" is ", 1)[1]
        actual = str(folk.value(cls, SKOS.definition))
        assert normalise(actual) == normalise(recorded), (name, actual)


def test_the_added_classes_carry_every_annotation_and_pair_with_their_value(
        decision, folk):
    """D-013 asks a new term for all of them, and the back-link is what pairs
    the class with the corpus value it is."""
    corpus = {normalise(row[0]) for row in table("A3.")}
    for name, _parent, _definition in added(decision):
        cls = URIRef(FOLK + name)
        for predicate in (RDFS.label, SKOS.altLabel, SKOS.definition,
                          RDFS.comment, SKOS.example):
            assert folk.value(cls, predicate) is not None, (name, predicate)
        assert (cls, RDFS.seeAlso, URIRef(W3ID + name)) in folk, name
        assert normalise(name[:-len("Disposition")]) in corpus, name


# ------------------------------------------------------------ labels and correspondences


def test_the_synonyms_are_the_records_alternative_labels(folk):
    rows = table("A1.")
    assert len(rows) == 9, rows
    for value, cls, label, *_rest in rows:
        cls = URIRef(FOLK + cls.strip("`"))
        assert (cls, SKOS.altLabel, Literal(label, lang="en")) in folk, (value, cls)


def test_the_correspondences_are_the_records_and_nothing_else(folk, mappings):
    """Every row of Table A2 is a related match from each named class to the
    corpus value, and the mapping layer holds no corpus correspondence the
    table does not. None is also a label: a correspondence says the word does
    not name the class."""
    expected = set()
    for value, targets, *_rest in table("A2."):
        for target in re.findall(r"`([\w:]+)`", targets):
            expected.add((str(iri(target)), normalise(value)))
    assert len(expected) == 150, len(expected)

    asserted = {(str(s), normalise(str(o)[len(ODP):]))
                for s, o in mappings.subject_objects(RELATED)
                if str(o).startswith(ODP)}
    assert asserted == expected, (sorted(asserted - expected)[:5],
                                  sorted(expected - asserted)[:5])
    for predicate in (URIRef(CORE + "historicallyCorrespondsTo"),
                      URIRef(CORE + "hasBroaderConceptualMatch")):
        assert not [o for o in mappings.objects(None, predicate)
                    if str(o).startswith(ODP)], predicate

    labels = {normalise(str(v)) for v in folk.objects(None, SKOS.altLabel)}
    labels |= {normalise(str(v)) for v in folk.objects(None, RDFS.label)}
    assert not {value for _s, value in expected} & labels


def test_the_exclusions_are_the_records(folk):
    recorded = {normalise(row[0]) for row in table("A4.")}
    assert len(recorded) == 25
    record = json.loads(layout.component("config.folk-membership").resolve()
                        .read_text(encoding="utf-8"))
    assert record["decision"] == "D-014"
    assert {normalise(row["value"]) for row in record["excluded"]} == recorded


def test_religions_comment_states_where_folk_religion_came_from(folk):
    """D-012's provenance correction: the corpus value is this repository's
    addition, not an upstream one."""
    comment = str(folk.value(URIRef(FOLK + "ReligionDisposition"), RDFS.comment))
    assert "added to its copy of the folk corpus" in comment
    assert "the upstream corpus has no such value" in comment
