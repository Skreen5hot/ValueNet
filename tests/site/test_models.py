# SPDX-License-Identifier: Apache-2.0
"""The diagrams depict the ontology, or they do not ship.

A diagram is the easiest thing in a publication to get quietly wrong. It
is drawn once, read often, and nothing about it fails when the ontology
moves underneath it. So every term it names carries its IRI in the markup
and is resolved here against the file that declares it.

This caught two errors while the page was being written: a term drawn as
`HaidtValues#care` when the asserted mapping target is `#Care`, and an
edge labelled with a BFO property number that the vendored extract does
not contain.

Rendering is not tested here. Whether the boxes overlap, whether the
arrowheads point where they appear to, and how a screen reader announces
the figures are browser questions and belong to the Phase 6 gate.
"""

from __future__ import annotations

import importlib.util
import json
import re

import pytest
import rdflib

from marep import layout, ontology_source as onto

REPO = layout.repository_root()
SRC = layout.component("site.source").resolve()
PAGE = (SRC / "models/index.html").read_text(encoding="utf-8")


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = _load("models_downloads", "tools/site/build_downloads.py")

#: Terms from vocabularies every RDF consumer already has. Listed rather
#: than pattern-matched, so adding one is a decision.
WELL_KNOWN = {
    "http://www.w3.org/2000/01/rdf-schema#subClassOf",
}

DIAGRAMS = 3


def depicted(attribute: str) -> list[str]:
    return sorted(set(re.findall(r'%s="([^"]+)"' % attribute, PAGE)))


def local(iri: str) -> str:
    """The name after the last separator.

    Three forms reach this. ValueNet and BFO write fragments after `#`,
    CCO writes the identifier after the last `/`, and the explorer links
    use the compact `module:Name`. Handling only the first two left the
    written pairs prefixed and comparing unequal to the same pairs read
    out of the ontology.
    """
    return re.split(r"[#/]", iri)[-1].rsplit(":", 1)[-1]


@pytest.fixture(scope="module")
def declared(class_index):
    """Every IRI this repository or its vendored dependencies declare.

    Three sources, because a diagram legitimately names three kinds of
    thing: terms this suite authors, upstream terms it aligns to, and
    upstream terms it merely points at from a mapping.
    """
    found: dict[str, str] = {}

    for record in B.entries("0" * 40):
        path = REPO / record["source"]
        for iri in B.declared_iris(path, record["namespace"],
                                   record["ontology_iri"]):
            found[iri] = record["id"]

    vendored = rdflib.Graph()
    for component in ("bfo.vendor-bfo", "bfo.vendor-cco"):
        target = layout.component(component).resolve()
        members = (sorted(target.rglob("*.ttl")) if target.is_dir()
                   else [target])
        for member in members:
            onto.parse_source(vendored, member, REPO)
    for subject in vendored.subjects():
        if isinstance(subject, rdflib.URIRef):
            found.setdefault(str(subject), "vendored upstream")

    for record in class_index["classes"]:
        for mapping in record["mappings"]:
            found.setdefault(mapping["target"], "asserted mapping target")
    return found


def test_every_depicted_class_exists_where_the_diagram_says(declared):
    """The control. A box naming a term nothing declares is a drawing of
    an ontology this repository does not have."""
    unknown = [iri for iri in depicted("data-iri")
               if iri not in declared and iri not in WELL_KNOWN]
    assert not unknown, (
        "the diagrams name %d term(s) no reviewed module, vendored "
        "dependency or asserted mapping declares: %s" % (len(unknown), unknown))


def test_every_depicted_property_exists(declared):
    """Edge labels are claims too. This caught BFO_0000053, which is not
    in the vendored extract -- the current numbering is BFO_0000196."""
    unknown = [iri for iri in depicted("data-property")
               if iri not in declared and iri not in WELL_KNOWN]
    assert not unknown, unknown


def test_the_diagrams_actually_depict_something(declared):
    """Guards the two tests above: both pass vacuously on a page with no
    diagrams, which is exactly what a broken build would produce."""
    assert len(depicted("data-iri")) >= 15, depicted("data-iri")
    assert len(depicted("data-property")) >= 5, depicted("data-property")
    assert PAGE.count("<svg") == DIAGRAMS


def test_authored_terms_are_attributed_to_an_authored_module(declared):
    """A ValueNet IRI resolving to "vendored upstream" would mean the
    suite is redeclaring somebody else's term."""
    for iri in depicted("data-iri") + depicted("data-property"):
        if iri.startswith("https://fandaws.com/"):
            assert declared.get(iri, "").startswith("valuenet") or \
                   declared.get(iri, "").startswith("vcvf"), \
                   "%s is attributed to %r" % (iri, declared.get(iri))


# ============================================================ the links


def test_every_explorer_link_names_a_real_class(class_index):
    """A model page that links to a class the index does not hold sends a
    reader to an error state, and the link is the whole point of drawing
    the term.

    The index is generated for the test. Reading the build artifact made
    this skip in a clean clone, and a skipped link check reads exactly
    like a passing one.
    """
    known = {record["id"] for record in class_index["classes"]}
    linked = sorted(set(re.findall(r'\.\./explore/\?class=([^"&]+)', PAGE)))
    assert linked, "the diagrams link to no classes at all"
    missing = [i for i in linked if i not in known]
    assert not missing, missing


def test_the_textual_alternative_describes_exactly_what_is_drawn():
    """An alternative has to be equivalent, not a superset.

    The first version of this page listed two extra relations inside the
    description of diagram 3 -- true, asserted, and not in the picture.
    A reader relying on the text would have believed the figure showed
    them. They are now in prose beside the list, where prose may say more
    than the drawing does; the list may not.
    """
    drawn = {local(iri) for iri in depicted("data-iri")}
    for block in re.findall(r'<ul class="alt-text">(.*?)</ul>', PAGE, re.S):
        linked = set(re.findall(r'\.\./explore/\?class=([^"&]+)', block))
        stray = sorted(i for i in linked
                       if i.split(":", 1)[-1] not in drawn)
        assert not stray, (
            "the alternative names %s, which the diagram does not draw"
            % stray)


def test_every_drawn_class_is_in_the_alternative():
    """The other direction: a box nobody wrote down is a box a reader
    using the text never learns about."""
    described = " ".join(re.findall(r'<ul class="alt-text">(.*?)</ul>',
                                    PAGE, re.S))
    missing = [iri for iri in depicted("data-iri")
               if local(iri) not in described]
    assert not missing, missing


# ==================================================== the alternatives


def test_every_diagram_has_a_title_and_a_description():
    """SVG needs both to be announced as a figure rather than skipped."""
    assert PAGE.count('role="img"') == DIAGRAMS
    assert PAGE.count("<title id=") == DIAGRAMS
    assert PAGE.count("<desc id=") == DIAGRAMS
    for match in re.finditer(r'aria-labelledby="(\S+) (\S+)"', PAGE):
        for ident in match.groups():
            assert 'id="%s"' % ident in PAGE, ident


def test_every_diagram_has_a_written_description_in_the_page():
    """A `desc` is a summary. The plan asks for a textual alternative, so
    each diagram is also written out where anyone can read it."""
    assert PAGE.count("<h3>Description of diagram") == DIAGRAMS
    assert PAGE.count('class="alt-text"') >= DIAGRAMS - 1


def test_the_written_description_covers_every_pair_in_diagram_two():
    """The one diagram whose content is a list, so completeness is
    checkable: six pairs drawn, six pairs written."""
    section = PAGE[PAGE.index("<h3>Description of diagram 2</h3>"):
                   PAGE.index("<h2 id=\"m3\">")]
    for process in ("HarmProcess", "CheatingProcess", "BetrayalProcess",
                    "SubversionProcess", "DegradationProcess",
                    "OppressionProcess"):
        assert process in section, process
    # Counted over list items: the paragraph introducing the section also
    # uses the word, and counting raw occurrences made this test depend
    # on the prose around it.
    items = re.findall(r"<li>(.*?)</li>", section, re.S)
    assert len([i for i in items if "contravenes" in i]) == 6, len(items)


def _asserted_pairs():
    """(process, disposition) from the OWL restrictions."""
    from rdflib.namespace import OWL, RDFS

    graph = rdflib.Graph()
    for component in ("bfo.module.core", "bfo.module.moral-foundations"):
        onto.parse_source(graph, layout.component(component).resolve(), REPO)
    contravenes = rdflib.URIRef(
        "https://fandaws.com/ontology/bfo/valuenet-core#contravenes")
    found = set()
    for restriction in graph.subjects(OWL.onProperty, contravenes):
        targets = list(graph.objects(restriction, OWL.someValuesFrom))
        for owner in graph.subjects(RDFS.subClassOf, restriction):
            if targets:
                found.add((local(str(owner)), local(str(targets[0]))))
    return found


def _drawn_pairs():
    """(source, target) from the diagram's edge metadata."""
    return {(local(a), local(b)) for a, b in re.findall(
        r'data-source="([^"]+)"\s+data-target="([^"]+)"', PAGE)}


def _written_pairs():
    """(first link, second link) from each item of the alternative.

    Order inside the item matters: the sentence runs process contravenes
    disposition, which is the direction the property is asserted in.
    """
    section = PAGE[PAGE.index("<h3>Description of diagram 2</h3>"):
                   PAGE.index('<h2 id="m3">')]
    found = set()
    for item in re.findall(r"<li>(.*?)</li>", section, re.S):
        linked = re.findall(r'\.\./explore/\?class=([^"&]+)', item)
        if len(linked) == 2:
            found.add((local(linked[0]), local(linked[1])))
    return found


def test_the_three_accounts_of_the_pairs_are_the_same_set():
    """Exact sets, in both directions, across all three.

    The previous version asserted `A before B, or A is present`, whose
    right branch is true whenever the process is named anywhere. Swapping
    the Care and Fairness targets passed it, because every name still
    appeared somewhere in the section. A vacuous check on a diagram is
    worse than none: it reads as coverage.
    """
    asserted, drawn, written = (_asserted_pairs(), _drawn_pairs(),
                                _written_pairs())
    assert len(asserted) == 6, asserted
    assert drawn == asserted, (
        "the diagram and the ontology disagree; drawn only: %s; asserted "
        "only: %s" % (sorted(drawn - asserted), sorted(asserted - drawn)))
    assert written == asserted, (
        "the written alternative and the ontology disagree; written only: "
        "%s; asserted only: %s"
        % (sorted(written - asserted), sorted(asserted - written)))


def test_swapping_two_targets_would_be_caught():
    """Guards the comparison above against becoming order-insensitive.

    A set of pairs catches a swap only while the pairs stay ordered; if
    the parsing ever returned unordered pairs this would still pass on
    correct data and stop catching anything.
    """
    asserted = _asserted_pairs()
    swapped = set(asserted)
    (p1, d1), (p2, d2) = sorted(asserted)[:2]
    swapped -= {(p1, d1), (p2, d2)}
    swapped |= {(p1, d2), (p2, d1)}
    assert swapped != asserted, "a swap is invisible to this comparison"


def test_no_original_valuenet_diagram_is_reproduced():
    """Its licence is unidentified, so nothing of it may be redistributed
    -- including a redrawing presented as the original."""
    assert "Original ValueNet diagrams" in PAGE
    assert "licence has not been identified" in PAGE
    assert "<img" not in PAGE, "the page embeds a raster image"
