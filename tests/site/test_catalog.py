# SPDX-License-Identifier: Apache-2.0
"""The public catalog, and the bindings it claims to have.

`site.json` said every module key was bound through the layout contract
while the contract held only directory groups. The binding it described
did not exist, so a catalog entry could have named a file that was never
there and nothing would have failed.

These are the controls for what replaced that: eleven per-file
components, a catalog that partitions into seven primary and four
supporting, ontology headers that supply their own titles, and a
`site.json` that no longer carries a second copy of anything the ontology
already says.
"""

from __future__ import annotations

import json

import pytest
import rdflib
from rdflib.namespace import DCTERMS, OWL, RDF

from marep import layout
from marep import ontology_source as onto

REPO = layout.repository_root()
SITE = json.loads(
    (layout.component("site.content").resolve() / "site.json")
    .read_text(encoding="utf-8"))
CATALOG = SITE["catalog"]

CC_BY_4 = rdflib.URIRef("https://creativecommons.org/licenses/by/4.0/")


def entries():
    return CATALOG["primary"] + CATALOG["supporting"]


def header(component_id):
    """The ontology header of one bound deliverable."""
    path = layout.component(component_id).resolve()
    graph = onto.parse_source(rdflib.Graph(), path, REPO)
    subjects = [s for s in graph.subjects(RDF.type, OWL.Ontology)
                if isinstance(s, rdflib.URIRef)]
    return graph, subjects


def test_the_catalog_partitions_into_seven_primary_and_four_supporting():
    """The split is the point, not the total.

    Seven modules carry the ontology; four graphs constrain or illustrate
    it. Presenting eleven module cards would invite a reader to read a
    SHACL shape as part of the vocabulary.
    """
    assert len(CATALOG["primary"]) == 7, [e["key"] for e in CATALOG["primary"]]
    assert len(CATALOG["supporting"]) == 4, [e["key"]
                                             for e in CATALOG["supporting"]]
    keys = [e["key"] for e in entries()]
    assert len(set(keys)) == 11, "a catalog key is repeated"


def test_every_catalog_entry_binds_to_a_component_that_resolves():
    """The claim site.json makes about itself.

    Before the per-file components existed this was false and unfalsifiable
    at the same time: nothing named a file, so nothing could fail to.
    """
    seen = {}
    for entry in entries():
        cid = entry["component"]
        path = layout.component(cid).resolve()
        assert path.is_file(), cid + " resolves to " + str(path)
        assert path.suffix == ".ttl", cid
        assert cid not in seen, cid + " is bound twice"
        seen[cid] = path
    assert len(seen) == 11
    assert len(set(seen.values())) == 11, (
        "two components resolve to the same file: "
        + str(sorted(str(v) for v in seen.values())))


def test_every_deliverable_has_exactly_one_header_title_and_description():
    """Extraction needs exactly one of each, or it is a choice rather than
    a reading. Phase 3 takes these values directly."""
    for entry in entries():
        cid = entry["component"]
        graph, subjects = header(cid)
        assert len(subjects) == 1, (
            "%s declares %d owl:Ontology resources" % (cid, len(subjects)))
        ont = subjects[0]
        for prop, name in ((DCTERMS.title, "dcterms:title"),
                           (DCTERMS.description, "dcterms:description")):
            values = list(graph.objects(ont, prop))
            assert len(values) == 1, (
                "%s has %d %s values; extraction needs exactly one"
                % (cid, len(values), name))
            assert str(values[0]).strip(), cid + " has an empty " + name


def test_every_deliverable_carries_the_exact_project_licence():
    """CC BY 4.0, as the IRI and not as prose about it."""
    for entry in entries():
        cid = entry["component"]
        graph, subjects = header(cid)
        licences = list(graph.objects(subjects[0], DCTERMS.license))
        assert licences == [CC_BY_4], (
            "%s declares %r, expected exactly [%s]"
            % (cid, [str(x) for x in licences], CC_BY_4))


def test_site_json_holds_no_second_copy_of_a_derived_value():
    """A module described in two places is a module whose two descriptions
    can disagree.

    Titles, descriptions and counts come from the ontology and the build.
    What stays here is identity, the component binding, the indexing
    status, and an editorial note where a decision needs explaining.
    """
    permitted = {"key", "component", "indexed", "editorial"}
    for entry in entries():
        extra = set(entry) - permitted
        assert not extra, entry["key"] + " carries " + str(sorted(extra))

    blob = json.dumps(SITE)
    for banned in ("display_name", '"purpose"', '"title"', '"description"'):
        assert banned not in blob, (
            "site.json contains " + banned + ", which the ontology or the "
            "build already supplies")


def test_an_editorial_note_is_present_exactly_where_a_decision_needs_one():
    """Present when excluded, absent when not, and never carrying a number.

    The first version of this test scored notes by looking for the words
    "because" or "rather than", which is a keyword heuristic wearing the
    clothes of a control: it failed a note that gave its reason with "so".
    What can actually be checked is that a note exists exactly where a
    decision was made, and that it states no quantity the build derives.
    """
    for entry in entries():
        note = entry.get("editorial")
        if entry["indexed"]:
            assert note is None, (
                entry["key"] + " is indexed and needs no explanation, but "
                "carries one: " + str(note))
            continue
        assert note and note.strip(), (
            entry["key"] + " is excluded from the index with no reason given")
        digits = [c for c in note if c.isdigit()]
        assert not digits, (
            entry["key"] + " states a number in curated copy: " + note
            + " -- counts come from the build")


def test_the_indexed_entries_are_the_ones_with_classes():
    """Indexing status is a claim about the file, so it is checked against
    the file."""
    for entry in entries():
        graph, _ = header(entry["component"])
        named = {c for c in graph.subjects(RDF.type, OWL.Class)
                 if isinstance(c, rdflib.URIRef)}
        if entry["indexed"]:
            assert named, (
                entry["key"] + " is marked indexed but declares no classes")
        else:
            assert not named, (
                entry["key"] + " declares " + str(len(named))
                + " classes but is excluded from the index")


def test_the_supporting_group_is_shapes_and_the_scenario():
    """Named, so the group cannot quietly acquire a module."""
    keys = {e["key"] for e in CATALOG["supporting"]}
    assert keys == {
        "valuenet-core-shapes", "valuenet-moral-epistemics-shapes",
        "vcvf-triggers-shapes", "valuenet-moral-epistemics-scenario"}
    for entry in CATALOG["supporting"]:
        assert entry["indexed"] is False, entry["key"]


def test_the_catalog_covers_every_authored_turtle_deliverable():
    """Both directions: nothing in the catalog that is not authored, and
    nothing authored that the catalog omits."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "disposition_catalog", REPO / "tools/licensing/disposition.py")
    D = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(D)

    authored = {r.path for r in D.classify()
                if r.disposition == D.CONTENT and r.path.endswith(".ttl")}
    bound = {layout.component(e["component"]).resolve()
             .relative_to(REPO).as_posix() for e in entries()}
    assert bound == authored, (
        "catalog and authored deliverables differ: "
        + str(sorted(bound ^ authored)))
