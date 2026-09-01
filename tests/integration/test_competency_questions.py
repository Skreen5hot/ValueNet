# SPDX-License-Identifier: Apache-2.0
"""The documented queries have to keep working, automatically.

Nine SPARQL queries live in two markdown documents and were, until now, run by
hand or not at all. Both are load-bearing. The competency questions are the
stated case that `valuenet-moral-epistemics` does what it was built for, and
the `TestingFramework.md` queries are the stated case that the BFO layer has no
double-disjoint parentage, no missing metadata and no redundant
the broader conceptual mapping annotation. Nothing checked either claim, so breaking the scenario file
would have silently retired six of them and no test would have noticed.

Two properties are asserted here beyond "the queries run".

**Each query declares what it needs.** CQ6 returns nothing over `BFO/` and
answers only with `MFTriggers/` loaded. That was true and written down in the
document's preamble, which made the query correct only for a reader who had
read the preamble — the same arrangement as the 127 fragments that parsed only
if you knew the convention. A `# scope:` comment inside the query moves it into
the artifact.

**Each query declares what passing means.** The two documents have opposite
polarity: an empty competency question is a failure, and a non-empty sanity
check is a failure. A single rule would assert that finding no defects is a
defect.
"""

from __future__ import annotations

from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from marep import competency  # noqa: E402

# The repository root comes from the layout contract, not from counting
# parents. This file moves one level deeper in the tests wave, at which
# point parents[1] resolves to tests/ and every path below it is wrong
# without raising anything.
from marep.layout import repository_root  # noqa: E402

REPO = repository_root()

#: Every query in every listed document, collected at import so each becomes
#: its own test case and a failure names the query rather than the document.
ALL_QUERIES = [
    q
    for rel in competency.QUERY_DOCS
    if (REPO / rel).exists()
    for q in competency.extract((REPO / rel).read_text(encoding="utf-8"), rel)
]


def test_there_are_queries_to_run():
    """Guards the failure where the extractor silently matches nothing.

    Without this, a change to the fence format or the heading pattern empties
    the parametrised list and the whole file passes by testing zero queries.
    """
    assert len(ALL_QUERIES) >= 9, (
        f"only {len(ALL_QUERIES)} queries extracted from "
        f"{list(competency.QUERY_DOCS)}; the documents hold at least nine")


@pytest.mark.parametrize("query", ALL_QUERIES, ids=lambda q: q.ref)
def test_every_query_declares_its_scope(query):
    """A query that does not say what it needs can only be run by someone who
    already knows, which is the arrangement this repository keeps removing."""
    assert query.scopes, (
        f"{query.ref} declares no '# scope:'. Add one as a SPARQL comment "
        "inside the query so the file states what it must be run against.")


@pytest.mark.parametrize("query", ALL_QUERIES, ids=lambda q: q.ref)
def test_every_query_declares_what_passing_means(query):
    assert query.expect in ("rows", "no-rows"), (
        f"{query.ref} has no usable '# expect:' declaration")


#: Scopes cheap enough to execute on every test run, named by component id.
#: The BFO tree is ten files and 2,610 triples and queries over it finish in
#: milliseconds; CQ6 additionally loads MFTriggers, which is 24,684 triples and
#: turns a sub-second suite into a four-minute one.
#:
#: This held the literal "BFO/" until the scopes became component ids, at which
#: point nothing matched and all nine queries were marked slow — 8 tests
#: silently left the default run while the collected total stayed 539. A
#: deselection is invisible in a passing suite, which is why the frozen
#: baseline records the selected/deselected split and not just the total.
CHEAP_SCOPES = frozenset({"component:bfo.ontology-tree"})


def _case(q):
    cheap = set(q.scopes) <= CHEAP_SCOPES
    return pytest.param(q, id=q.ref,
                        marks=() if cheap else (pytest.mark.slow,))


@pytest.mark.parametrize("query", [_case(q) for q in ALL_QUERIES])
def test_every_query_does_what_its_document_claims(query):
    """Runs by default for BFO-scoped queries; CQ6 is slow-marked by scope."""
    result = competency.run(REPO, query)
    assert not result.error, f"{query.ref} failed to run: {result.error}"
    if query.expect == "rows":
        assert result.rows > 0, (
            f"{query.ref} returned nothing over {' '.join(query.scopes)}. "
            f"The document presents it as a question this ontology can answer: "
            f"{query.title[:80]}")
    else:
        assert result.rows == 0, (
            f"{query.ref} found {result.rows} result(s) over "
            f"{' '.join(query.scopes)}. This is a sanity check, so a non-empty "
            f"answer is the defect: {query.title[:80]}")


# ======================================================================
# the extractor itself
# ======================================================================

DOC = """# Doc

```sparql
PREFIX : <http://example.org/x#>
```

## CQ1. A question with an answer

```sparql
# scope: data/
# expect: rows
SELECT ?s WHERE { ?s ?p ?o }
```

## Query 2: A check that should find nothing

```sparql
# scope: data/
# expect: no-rows
SELECT ?s WHERE { ?s :missing ?o }
```
"""


def test_the_preamble_is_not_treated_as_a_query():
    queries = competency.extract(DOC, "doc.md")
    assert len(queries) == 2
    assert [q.label for q in queries] == ["CQ1", "Query2"]


def test_the_preamble_is_prepended_to_each_query():
    """Without this every query fails on an undefined prefix."""
    queries = competency.extract(DOC, "doc.md")
    assert all("PREFIX" in q.sparql for q in queries)


def test_polarity_is_read_per_query():
    queries = competency.extract(DOC, "doc.md")
    assert [q.expect for q in queries] == ["rows", "no-rows"]


def test_a_query_with_no_scope_is_an_error_not_a_pass(tmp_path: Path):
    """The dangerous failure: an unrunnable query reported as fine."""
    q = competency.Query(label="X", title="t", sparql="SELECT ?s WHERE { ?s ?p ?o }")
    result = competency.run(tmp_path, q)
    assert result.error
    assert not result.passed


def test_polarity_decides_the_verdict(tmp_path: Path):
    competency.clear_scope_cache()
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "d.ttl").write_text(
        "@prefix : <http://example.org/x#> .\n:a :p :b .\n", encoding="utf-8")
    wants_rows = competency.Query(
        label="A", title="t", scopes=("data/",), expect="rows",
        sparql="SELECT ?s WHERE { ?s ?p ?o }")
    wants_none = competency.Query(
        label="B", title="t", scopes=("data/",), expect="no-rows",
        sparql="SELECT ?s WHERE { ?s ?p ?o }")
    assert competency.run(tmp_path, wants_rows).passed is True
    assert competency.run(tmp_path, wants_none).passed is False
