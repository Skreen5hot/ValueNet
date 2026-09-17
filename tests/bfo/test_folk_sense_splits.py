# SPDX-License-Identifier: Apache-2.0
"""Two folk classes that defined two things each, split (R17, D-012).

The formal review of 2026-09-16 found FaithDisposition joining trust in
someone or something to belief in a religious doctrine, and OpennessDisposition
joining candour to openness to experience. A definition of that shape makes one
class stand for two dispositions a person can have independently.

Each sense now has exactly one home:

- trust or confidence without proof     -> FaithDisposition (narrowed)
- a religious system as a guide to life -> ReligionDisposition (new; it is
  folk:Religion in this repository's copy of the folk corpus, which had no
  class)
- openness to new experience            -> OpennessDisposition (narrowed; the
  sense its Schwartz mappings, Stimulation and Self-Direction, already had)
- being candid and transparent          -> CandorDisposition and
  TransparencyDisposition, which already existed under HonestyDisposition

D-014 then retired OpennessDisposition: no corpus value or value-survey item
carries it, its experience sense is already Variety, Adventure and Curiosity,
and "openness" names too many things to be any class's label. The candour sense
keeps the home D-012 gave it. `test_folk_membership.py` holds the retirement.

The three classes touched carry every annotation RULES 2.0 section 5 asks for,
the reviewer's standard that ValueNet has not adopted wholesale (R2): what was
written new here is written to it.
"""

from __future__ import annotations

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph, Namespace  # noqa: E402
from rdflib.namespace import RDFS, SKOS  # noqa: E402

from marep.layout import bfo_artifact  # noqa: E402

FOLK = Namespace("https://fandaws.com/ontology/bfo/valuenet-folk#")
CORE = Namespace("https://fandaws.com/ontology/bfo/valuenet-core#")
W3ID = Namespace("https://w3id.org/valuenet/folk#")

TOUCHED = (FOLK.FaithDisposition, FOLK.ReligionDisposition)


@pytest.fixture(scope="module")
def folk() -> Graph:
    return Graph().parse(bfo_artifact("valuenet-folk.ttl"), format="turtle")


def definition(graph: Graph, cls) -> str:
    values = [str(v) for v in graph.objects(cls, SKOS.definition)]
    assert len(values) == 1, (cls, values)
    return values[0]


def test_faith_keeps_one_sense(folk):
    text = definition(folk, FOLK.FaithDisposition).lower()
    assert "trust or confidence" in text
    for other in ("relig", "doctrine", ", or "):
        assert other not in text, (
            "FaithDisposition's definition joins a second sense again: %s"
            % text)


def test_the_religious_sense_is_its_own_class(folk):
    cls = FOLK.ReligionDisposition
    assert (cls, RDFS.subClassOf, CORE.PersonalValueDisposition) in folk
    assert "system of religious belief and practice" in definition(folk, cls)
    # The module's naming pattern, which is also what pairs a class with the
    # folk corpus value of the same name.
    assert (cls, RDFS.label, rdflib.Literal("Religion Disposition", lang="en")) in folk
    assert (cls, SKOS.altLabel, rdflib.Literal("Religion", lang="en")) in folk
    assert (cls, RDFS.seeAlso, W3ID.ReligionDisposition) in folk


def test_candour_keeps_its_home(folk):
    for home in (FOLK.CandorDisposition, FOLK.TransparencyDisposition):
        assert (home, RDFS.subClassOf, FOLK.HonestyDisposition) in folk, (
            "%s no longer carries the sense taken out of OpennessDisposition"
            % home.split("#")[-1])


@pytest.mark.parametrize("cls", TOUCHED, ids=lambda c: c.split("#")[-1])
def test_touched_classes_carry_the_rules_2_annotations(folk, cls):
    for predicate in (RDFS.subClassOf, RDFS.label, SKOS.definition,
                      RDFS.comment, SKOS.example):
        assert (cls, predicate, None) in folk, (
            "%s lacks %s" % (cls.split("#")[-1], predicate.n3(folk.namespace_manager)))
