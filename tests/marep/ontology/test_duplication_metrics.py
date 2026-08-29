"""Distinct content, not summed content.

Every count in `group_metrics` is a sum over files. That is honest about what
it does, but it leaves no way to ask how much distinct content a group holds,
and the gap is large: `mf-triggers` sums to 24,684 triples and merges to
12,364. Just under half of it is restatement.

The reason this is worth a metric rather than a footnote is that an agent has
already misread a count of this kind — two files with 5,828 triples each were
reported as duplicates of one another, and they are not isomorphic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from marep import ontology_source as onto  # noqa: E402

A = """@prefix : <http://example.org/x#> .
:a :p :b . :c :p :d .
"""
B = """@prefix : <http://example.org/x#> .
:a :p :b . :e :p :f .
"""


def facts_for(tmp_path: Path, **files) -> list:
    out = []
    for name, body in files.items():
        p = tmp_path / f"{name}.ttl"
        p.write_text(body, encoding="utf-8")
        out.append(onto.measure_file(p, tmp_path))
    return out


def by_check(metrics, check):
    return {m.scope: m.value for m in metrics if m.check == check}


def test_a_shared_triple_is_counted_once(tmp_path: Path):
    facts = facts_for(tmp_path, one=A, two=B)
    metrics = onto.duplication_metrics(tmp_path, facts)
    # four triples summed, three distinct: :a :p :b appears in both files
    assert by_check(metrics, "triples_distinct_in_group")["repository-root"] == 3
    assert by_check(metrics, "duplicate_triple_ratio")["repository-root"] == 0.25


def test_no_overlap_means_no_duplication(tmp_path: Path):
    facts = facts_for(tmp_path, one=A, two="""@prefix : <http://example.org/x#> .
:x :p :y .
""")
    metrics = onto.duplication_metrics(tmp_path, facts)
    assert by_check(metrics, "duplicate_triple_ratio")["repository-root"] == 0


def test_the_summed_count_is_kept_in_the_detail(tmp_path: Path):
    """Both numbers travel together, so neither can be cited as the other."""
    facts = facts_for(tmp_path, one=A, two=B)
    m = next(m for m in onto.duplication_metrics(tmp_path, facts)
             if m.check == "triples_distinct_in_group")
    assert "4 summed over 2 files" in m.detail


def test_unparseable_files_are_left_out(tmp_path: Path):
    """A file that does not parse has no triples to merge or to sum."""
    facts = facts_for(tmp_path, good=A, bad="@prefix : <http://example.org/x#> .\n:a :p ")
    metrics = onto.duplication_metrics(tmp_path, facts)
    assert by_check(metrics, "triples_distinct_in_group")["repository-root"] == 2
