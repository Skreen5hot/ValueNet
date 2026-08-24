"""Commitments that live outside the axioms, measured rather than sampled.

Run 1 reported on the alignment layer by reading files that did not parse, and
undercounted badly: it says three value terms take a French gloss, where the
loadable graph holds 889 French Wiktionary triggers against 2,769 English. It
also read `<dbpedia:An_Education> vcvf:triggers folk:Education` as aligning the
value Education to a film. The triple runs the other way and says the film's
page is a lexical trigger for the value, which is a different and far more
defensible claim.

Both mistakes were the best available from broken files. Both are the kind a
measurement should make impossible, so direction and denominators are asserted
here rather than left for an agent to infer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from marep import commitments as com, ontology_source as onto  # noqa: E402

TRIG = ("@prefix folk: <http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#> .\n"
        "@prefix vcvf: <http://www.ontologydesignpatterns.org/ont/values/"
        "valuecore_with_value_frames.owl#> .\n")


def facts_for(tmp_path: Path, **files):
    onto.clear_graph_cache()
    out = []
    for name, body in files.items():
        p = tmp_path / f"{name}.ttl"
        p.write_text(body, encoding="utf-8")
        out.append(onto.measure_file(p, tmp_path))
    return out


def value_of(metrics, check, scope="repository-root"):
    for m in metrics:
        if m.check == check and m.scope == scope:
            return m.value
    return None


def detail_of(metrics, check, scope="repository-root"):
    for m in metrics:
        if m.check == check and m.scope == scope:
            return m.detail
    return ""


# ======================================================================
# direction: the mistake MAPPING-002 made
# ======================================================================

def test_a_foreign_subject_is_not_a_foreign_object(tmp_path: Path):
    """<film> triggers <value> is a trigger claim; the reverse is equivalence."""
    facts = facts_for(tmp_path, d=TRIG + """
    <http://dbpedia.org/resource/An_Education> vcvf:triggers folk:Education .
    """)
    m = com.mapping_metrics(tmp_path, facts)
    assert value_of(m, "triggers_with_foreign_subject") == 1
    assert value_of(m, "triggers_with_foreign_object") == 0


def test_the_direction_is_spelled_out_not_implied(tmp_path: Path):
    facts = facts_for(tmp_path, d=TRIG + """
    <http://dbpedia.org/resource/X> vcvf:triggers folk:Y .
    """)
    detail = detail_of(com.mapping_metrics(tmp_path, facts),
                       "triggers_with_foreign_subject")
    assert "SUBJECT" in detail
    assert "not that" in detail


# ======================================================================
# language editions: the fact LANG-001 undercounted
# ======================================================================

def test_language_editions_are_counted_not_sampled(tmp_path: Path):
    facts = facts_for(tmp_path, d=TRIG + """
    <http://en.wiktionary.org/wiki/a> vcvf:triggers folk:A .
    <http://en.wiktionary.org/wiki/b> vcvf:triggers folk:B .
    <http://fr.wiktionary.org/wiki/c> vcvf:triggers folk:C .
    """)
    m = com.mapping_metrics(tmp_path, facts)
    assert value_of(m, "wiktionary_language_editions") == 2
    assert value_of(m, "wiktionary_non_english_triggers") == 1
    assert "of 3" in detail_of(m, "wiktionary_non_english_triggers")


# ======================================================================
# IRI ownership: same-group variants are not contested ownership
# ======================================================================

def test_variants_within_a_group_are_separated_from_cross_group(tmp_path: Path):
    """2,240 IRIs are declared in more than one file and it reads as pervasive
    contested ownership; most are one ontology's parameter variants."""
    (tmp_path / "vale2024").mkdir()
    body = ("@prefix : <http://example.org/x#> .\n"
            "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
            ":Shared a owl:Class .\n")
    for n in ("a", "b"):
        (tmp_path / "vale2024" / f"{n}.ttl").write_text(body, encoding="utf-8")
    onto.clear_graph_cache()
    facts = [onto.measure_file(p, tmp_path)
             for p in sorted((tmp_path / "vale2024").glob("*.ttl"))]
    m = com.iri_ownership_metrics(tmp_path, facts)
    assert value_of(m, "class_iris_declared_in_multiple_files", "corpus") == 1
    assert value_of(m, "class_iris_declared_across_groups", "corpus") == 0


def test_a_class_declared_in_two_groups_is_flagged(tmp_path: Path):
    (tmp_path / "vale2024").mkdir()
    body = ("@prefix : <http://example.org/x#> .\n"
            "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
            ":Shared a owl:Class .\n")
    (tmp_path / "vale2024" / "a.ttl").write_text(body, encoding="utf-8")
    (tmp_path / "root.ttl").write_text(body, encoding="utf-8")
    onto.clear_graph_cache()
    facts = [onto.measure_file(tmp_path / "vale2024" / "a.ttl", tmp_path),
             onto.measure_file(tmp_path / "root.ttl", tmp_path)]
    m = com.iri_ownership_metrics(tmp_path, facts)
    assert value_of(m, "class_iris_declared_across_groups", "corpus") == 1


# ======================================================================
# meaning resting on a name
# ======================================================================

def test_a_class_with_no_definition_text_is_counted(tmp_path: Path):
    facts = facts_for(tmp_path, d="""
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix : <http://example.org/x#> .
    :Bare a owl:Class ; rdfs:label "Bare" .
    :Defined a owl:Class ; rdfs:comment "what it means" .
    """)
    m = com.lexical_metrics(tmp_path, facts)
    assert value_of(m, "classes_without_definition_text") == 1
    assert "of 2" in detail_of(m, "classes_without_definition_text")


def test_names_differing_only_by_separator_collide(tmp_path: Path):
    facts = facts_for(tmp_path, d="""
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix : <http://example.org/x#> .
    :Personal_focus a owl:Class .
    :PersonalFocus a owl:Class .
    :Unrelated a owl:Class .
    """)
    m = com.lexical_metrics(tmp_path, facts)
    assert value_of(m, "local_names_colliding_on_normalisation") == 1
    assert "Personal" in detail_of(m, "local_names_colliding_on_normalisation")
