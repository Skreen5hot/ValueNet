# SPDX-License-Identifier: Apache-2.0
"""A corpus digest moves for two very different reasons.

Either the ontology says something new, or it says the same things and
only its description of itself changed. The remediation ledger claims to
tell those apart, and this file is where that claim is falsified rather
than trusted.

The classifier is a pure function of two triple sets, so every case here
is constructed directly. None of them needs a commit to exist, which is
what makes the hostile cases cheap enough to write.
"""

from __future__ import annotations

import importlib.util

import pytest
import rdflib
from rdflib.namespace import OWL, RDF, RDFS, SKOS

from marep import layout

REPO = layout.repository_root()


def _module():
    path = layout.component("tool.build-remediation-record").resolve()
    spec = importlib.util.spec_from_file_location("rr_classify", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R = _module()

ONT = rdflib.URIRef("https://ex.invalid/module.owl")
CLS = rdflib.URIRef("https://ex.invalid/module#Thing")
PROP = rdflib.URIRef("https://ex.invalid/module#relatesTo")
LICENCE = rdflib.URIRef("https://creativecommons.org/licenses/by/4.0/")
DCT_LICENSE = rdflib.URIRef("http://purl.org/dc/terms/license")


def base(restriction_filler=CLS):
    """A header, a class, and one OWL restriction on a blank node."""
    g = set()
    g.add((ONT, RDF.type, OWL.Ontology))
    g.add((CLS, RDF.type, OWL.Class))
    g.add((CLS, SKOS.definition, rdflib.Literal("An original definition.")))
    b = rdflib.BNode()
    g.add((CLS, RDFS.subClassOf, b))
    g.add((b, RDF.type, OWL.Restriction))
    g.add((b, OWL.onProperty, PROP))
    g.add((b, OWL.someValuesFrom, restriction_filler))
    return g


def delta(was, now):
    """The ground-triple enumeration, in the shape the ledger stores."""
    def entries(diff):
        return [{"file": "x.ttl", "triple": " ".join(t.n3() for t in trip)}
                for trip in diff]
    gw = R.ground(was)
    gn = R.ground(now)
    return entries(gn - gw), entries(gw - gn)


def classify(was, now):
    added, removed = delta(was, now)
    cls, _b, _a = R.classify_change(was, now, added, removed)
    return cls


def test_a_header_annotation_is_publication_metadata():
    """The permitted case, so the refusals below are specific."""
    was = base()
    now = set(was) | {(ONT, DCT_LICENSE, LICENCE)}
    cls = classify(was, now)
    assert cls["change_class"] == "publication-metadata"
    assert cls["header_subjects_only"] and cls["header_predicates_only"]
    assert cls["named_classes_unchanged"] and cls["subclass_edges_unchanged"]
    assert cls["blank_node_shape_unchanged"]


def test_a_blank_node_only_change_is_not_publication_metadata():
    """The defect this check was added for.

    Repointing an OWL restriction changes what the ontology says. It
    moves no ground triple, no named class, and no named-to-named
    subclass edge -- so the four conditions that existed before the
    fingerprint was measured are all blind to it, and every one of them
    reports "unchanged".

    Only the blank-node fingerprint can see it, which is why
    publication-metadata requires it.
    """
    other = rdflib.URIRef("https://ex.invalid/module#Other")
    was = base()
    now = base(restriction_filler=other)

    added, removed = delta(was, now)
    assert not added and not removed, (
        "this edit is supposed to move no ground triple; if it does, the "
        "test is no longer exercising the blind spot")

    cls = classify(was, now)
    assert cls["named_classes_unchanged"], "precondition"
    assert cls["subclass_edges_unchanged"], "precondition"
    assert cls["blank_node_shape_unchanged"] is False, (
        "the fingerprint did not move on a repointed restriction")
    assert cls["change_class"] == "content-change"


def test_a_changed_class_definition_is_not_publication_metadata():
    """A definition is what the ontology says, not how it describes itself.

    The first allowlist admitted any annotation predicate, which would
    have classified an edited skos:definition on a class as publication
    metadata. The subject test is what refuses it: the subject is a
    class, not a resource the graph types owl:Ontology.
    """
    was = base()
    now = {t for t in was if t[1] != SKOS.definition}
    now.add((CLS, SKOS.definition, rdflib.Literal("A different meaning.")))

    cls = classify(was, now)
    assert cls["header_subjects_only"] is False, (
        "a class subject was accepted as an ontology header")
    assert cls["header_predicates_only"] is False, (
        "skos:definition is in the header allowlist")
    assert cls["change_class"] == "content-change"


def test_a_header_predicate_on_a_class_is_still_refused():
    """Subject and predicate are checked independently.

    rdfs:comment is an approved header predicate. On a class it is not
    header metadata, and passing one test must not carry the other.
    """
    was = base()
    now = set(was) | {(CLS, RDFS.comment, rdflib.Literal("about the class"))}
    cls = classify(was, now)
    assert cls["header_predicates_only"] is True
    assert cls["header_subjects_only"] is False
    assert cls["change_class"] == "content-change"


def test_a_new_class_is_not_publication_metadata():
    was = base()
    now = set(was)
    new = rdflib.URIRef("https://ex.invalid/module#Added")
    now.add((new, RDF.type, OWL.Class))
    cls = classify(was, now)
    assert cls["named_classes_unchanged"] is False
    assert cls["change_class"] == "content-change"


def test_a_repointed_named_subclass_edge_is_not_publication_metadata():
    parent = rdflib.URIRef("https://ex.invalid/module#Parent")
    was = set(base()) | {(CLS, RDFS.subClassOf, parent)}
    now = {t for t in was if t != (CLS, RDFS.subClassOf, parent)}
    now.add((CLS, RDFS.subClassOf,
             rdflib.URIRef("https://ex.invalid/module#Elsewhere")))
    cls = classify(was, now)
    assert cls["subclass_edges_unchanged"] is False
    assert cls["change_class"] == "content-change"


def test_an_empty_change_is_not_publication_metadata():
    """Nothing changed is not a licence to call anything metadata.

    `all()` over an empty sequence is true, so a change with no touched
    subjects or predicates would otherwise satisfy both conditions
    vacuously.
    """
    was = base()
    cls = classify(was, set(was))
    assert cls["header_subjects_only"] is False
    assert cls["header_predicates_only"] is False
    assert cls["change_class"] == "content-change"


def test_the_approved_header_predicates_exclude_definitions():
    """Stated as a property of the allowlist, so widening it is visible."""
    assert str(DCT_LICENSE) in R.HEADER_PREDICATES
    for excluded in (SKOS.definition, SKOS.scopeNote, RDFS.domain,
                     RDFS.range, OWL.imports):
        assert str(excluded) not in R.HEADER_PREDICATES, excluded
