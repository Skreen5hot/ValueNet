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

Rendering is not tested here. Whether the boxes overlap and how a screen
reader announces the figures are browser questions and belong to the Phase 6
gate.

Which way an arrow points is not one of them, although this docstring used to
say so. It is in the markup -- the box a path starts at and the box it ends
at, where its marker is -- and the mapping in diagram 3 was drawn backwards
for as long as nothing read it: HaidtValues#Care pointing at the care
disposition, when the Turtle asserts the reverse and the property is not
symmetric. The formal review of 2026-09-16 found it.
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


CONTRAVENES = "https://fandaws.com/ontology/bfo/valuenet-core#contravenes"


def _asserted_triples():
    """(process, predicate, disposition) from the OWL restrictions."""
    from rdflib.namespace import OWL, RDFS

    graph = rdflib.Graph()
    for component in ("bfo.module.core", "bfo.module.moral-foundations"):
        onto.parse_source(graph, layout.component(component).resolve(), REPO)
    predicate = rdflib.URIRef(CONTRAVENES)
    found = set()
    for restriction in graph.subjects(OWL.onProperty, predicate):
        targets = list(graph.objects(restriction, OWL.someValuesFrom))
        for owner in graph.subjects(RDFS.subClassOf, restriction):
            if targets:
                found.add((local(str(owner)), local(CONTRAVENES),
                           local(str(targets[0]))))
    return found


def _drawn_triples():
    """(source, predicate, target) from the diagram's edge metadata.

    The predicate is read from the edge, not assumed. Comparing only
    source and target left the relation unchecked: redrawing the six
    edges with any other declared property would have kept both sets
    equal and passed the existence check, because the replacement exists.
    """
    return {(local(source), local(predicate), local(target))
            for predicate, source, target in re.findall(
                r'data-property="([^"]+)"\s+data-source="([^"]+)"'
                r'\s+data-target="([^"]+)"', PAGE)}


def _written_triples():
    """(first link, marked predicate, second link) per item.

    Order inside the item matters: the sentence runs process, predicate,
    disposition, which is the direction the restriction is asserted in.
    The predicate is marked up rather than inferred from the prose, so
    rewording the sentence cannot silently change what it claims.
    """
    section = PAGE[PAGE.index("<h3>Description of diagram 2</h3>"):
                   PAGE.index('<h2 id="m3">')]
    found = set()
    for item in re.findall(r"<li>(.*?)</li>", section, re.S):
        linked = re.findall(r'\.\./explore/\?class=([^"&]+)', item)
        predicates = re.findall(r'data-property="([^"]+)"', item)
        if len(linked) == 2 and len(predicates) == 1:
            found.add((local(linked[0]), local(predicates[0]),
                       local(linked[1])))
    return found


def test_the_three_accounts_of_the_pairs_are_the_same_set():
    """Exact triples, in both directions, across all three accounts.

    Two rounds of this check were weaker than they looked. The first
    asserted `A before B, or A is present`, whose right branch is true
    whenever the process is named anywhere. The second compared ordered
    pairs and caught a swapped target, but omitted the predicate: the six
    edges could have been relabelled with any other declared property and
    both sets would still have matched.
    """
    asserted, drawn, written = (_asserted_triples(), _drawn_triples(),
                                _written_triples())
    assert len(asserted) == 6, asserted
    assert all(t[1] == "contravenes" for t in asserted), asserted
    assert drawn == asserted, (
        "the diagram and the ontology disagree; drawn only: %s; asserted "
        "only: %s" % (sorted(drawn - asserted), sorted(asserted - drawn)))
    assert written == asserted, (
        "the written alternative and the ontology disagree; written only: "
        "%s; asserted only: %s"
        % (sorted(written - asserted), sorted(asserted - written)))


def test_a_different_real_property_would_be_caught():
    """Guards the comparison against dropping the predicate again.

    Substituting a property that genuinely exists is the case the pair
    comparison could not see, so it is exercised here directly rather
    than trusted.
    """
    asserted = _asserted_triples()
    other = "dyadicOppositeOf"
    relabelled = {(s, other, t) for s, _p, t in asserted}
    assert relabelled != asserted, (
        "the comparison ignores the predicate, so relabelling every edge "
        "with another declared property would pass")


def test_swapping_two_targets_would_be_caught():
    """The earlier guard, kept: a set of triples catches a swap only
    while the components stay ordered."""
    asserted = _asserted_triples()
    swapped = set(asserted)
    (p1, r1, d1), (p2, r2, d2) = sorted(asserted)[:2]
    swapped -= {(p1, r1, d1), (p2, r2, d2)}
    swapped |= {(p1, r1, d2), (p2, r2, d1)}
    assert swapped != asserted, "a swap is invisible to this comparison"


def test_no_original_valuenet_diagram_is_reproduced():
    """Its licence is unidentified, so nothing of it may be redistributed
    -- including a redrawing presented as the original."""
    assert "Original ValueNet diagrams" in PAGE
    assert "licence has not been identified" in PAGE
    assert "<img" not in PAGE, "the page embeds a raster image"


# ============================================ edges point the right way


VN_CORE = "https://fandaws.com/ontology/bfo/valuenet-core#"

#: The mapping annotation properties. Their direction is an assertion, not a
#: layout choice: none of them is symmetric.
MAPPING_PROPERTIES = (VN_CORE + "historicallyCorrespondsTo",
                      VN_CORE + "hasBroaderConceptualMatch",
                      VN_CORE + "hasRelatedConceptualMatch")


def svgs() -> list[str]:
    """One string per diagram, so that boxes are only compared with boxes
    in the same coordinate space. The care disposition is drawn in two
    diagrams at two different places."""
    return re.findall(r"<svg\b.*?</svg>", PAGE, re.S)


def boxes(svg: str) -> list[tuple]:
    return [(iri,) + tuple(map(float, geometry)) for iri, *geometry in
            re.findall(r'<g data-iri="([^"]+)">\s*<rect[^>]*?\sx="([\d.]+)"'
                       r'\s+y="([\d.]+)"\s+width="([\d.]+)"'
                       r'\s+height="([\d.]+)"', svg)]


def labelled_edges(svg: str):
    """(property, first point, last point) for each path followed directly
    by its label. The arrowhead is on the last point: every edge here uses
    marker-end."""
    for d, prop in re.findall(
            r'<path class="dg-edge[^"]*"[^>]*?\sd="([^"]+)"\s*/>\s*'
            r'<text class="dg-edge-label"[^>]*?data-property="([^"]+)"', svg):
        numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", d)]
        yield prop, (numbers[0], numbers[1]), (numbers[-2], numbers[-1])


def nearest(drawn: list[tuple], point: tuple) -> str:
    def distance(box):
        _iri, x, y, w, h = box
        dx = max(x - point[0], 0, point[0] - (x + w))
        dy = max(y - point[1], 0, point[1] - (y + h))
        return (dx * dx + dy * dy) ** 0.5
    return min(drawn, key=distance)[0]


def asserted_mappings() -> rdflib.Graph:
    """The published modules, without shapes, scenario data or vendored
    upstream: the set the Phase 5 audit counted."""
    graph = rdflib.Graph()
    tree = layout.component("bfo.ontology-tree").resolve()
    for path in sorted(tree.rglob("*.ttl")):
        relative = path.relative_to(tree).as_posix()
        if ("shapes" in relative or "scenario" in relative
                or relative.startswith("vendor/")):
            continue
        graph.parse(path, format="turtle")
    return graph


def test_every_drawn_mapping_points_the_way_it_is_asserted():
    """The arrow runs from the entity the mapping is asserted on to the
    entity it maps to. Reading the source and target from the path's first
    and last points is the check this page did not have."""
    graph = asserted_mappings()
    checked = []
    for svg in svgs():
        drawn = boxes(svg)
        for prop, start, end in labelled_edges(svg):
            if prop not in MAPPING_PROPERTIES:
                continue
            source, target = nearest(drawn, start), nearest(drawn, end)
            assert (rdflib.URIRef(source), rdflib.URIRef(prop),
                    rdflib.URIRef(target)) in graph, (
                "the diagram draws %s %s %s, which is not asserted%s"
                % (local(source), local(prop), local(target),
                   " -- the reverse is" if (rdflib.URIRef(target),
                                            rdflib.URIRef(prop),
                                            rdflib.URIRef(source)) in graph
                   else ""))
            checked.append((local(source), local(target)))
    assert checked, (
        "no mapping edge was recognised in any diagram, so this checked "
        "nothing")


def test_the_mapping_counts_written_beside_the_diagram_are_the_ontologys():
    """Two numbers typed into the page. The first version said "one of 67
    such assertions" beside a historicallyCorrespondsTo edge; 67 is every
    mapping assertion, and 17 of them are that property."""
    section = PAGE[PAGE.index("<h3>Description of diagram 3</h3>"):]
    match = re.search(r"one of\s+(\d+)\s+such assertions, and of\s+(\d+)\s+"
                      r"mapping assertions overall", section)
    assert match, "the mapping counts are no longer where this test reads them"
    graph = asserted_mappings()
    historical = len(list(graph.subject_objects(
        rdflib.URIRef(VN_CORE + "historicallyCorrespondsTo"))))
    every = sum(len(list(graph.subject_objects(rdflib.URIRef(p))))
                for p in MAPPING_PROPERTIES)
    assert (int(match.group(1)), int(match.group(2))) == (historical, every), (
        "the page says %s and %s; the ontology has %d and %d"
        % (match.group(1), match.group(2), historical, every))
