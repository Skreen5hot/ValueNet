# SPDX-License-Identifier: Apache-2.0
"""Competency questions and sanity queries, executed and emitted as records.

The last of the three checks `MAREP_VALUENET_PLAN` §2 lists as missing. A
competency question is the most direct evidence there is for the question Run 2
asks: the ontology was built to answer it, and either it can or it cannot.

Two things this module refuses to know.

**Which files a query needs.** All six competency questions answer, but CQ6
returns nothing over `BFO/` alone and answers only once `MFTriggers/` is
loaded. That was recorded in prose in the document's preamble, which means the
queries were correct only for a reader who had read the preamble — the same
arrangement as the 127 fragments that parsed only if you knew the convention,
and the eight `.owl` files that were Turtle. So each query declares its own
scope, in a `# scope:` comment inside the query text. It stays a valid SPARQL
comment, so the query still runs unchanged anywhere else.

**What counts as passing.** The two documents have opposite polarity.
`valuenet-moral-epistemics-CQ.md` asks questions the ontology should be able to
answer, so an empty result is a failure. `TestingFramework.md` searches for
defects — classes with two disjoint parents, missing metadata, redundant
`skos:broadMatch` — so a non-empty result is the failure. A single "every query
must return rows" rule would assert that finding no defects is a defect. Each
query says which it is in an `# expect:` comment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .ontology_source import Metric

#: A fenced sparql block. The first block in a document is the shared prefix
#: preamble when it declares prefixes and asks nothing.
_BLOCK = re.compile(r"```sparql\n(.*?)```", re.S)
_HEADING = re.compile(r"^#{2,3}\s*((?:CQ|Query\s*)\d+)[.:]?\s*(.*)$", re.M)
_SCOPE = re.compile(r"^\s*#\s*scope:\s*(.+)$", re.M | re.I)
_EXPECT = re.compile(r"^\s*#\s*expect:\s*(rows|no-rows)\s*$", re.M | re.I)


@dataclass
class Query:
    """One query, with everything needed to run and judge it."""

    label: str
    title: str
    sparql: str
    scopes: tuple[str, ...] = ()
    expect: str = "rows"
    doc: str = ""

    @property
    def ref(self) -> str:
        return f"{Path(self.doc).stem}:{self.label}" if self.doc else self.label


@dataclass
class QueryResult:
    query: Query
    rows: int = 0
    error: str = ""
    #: True when the query did what its document says it should.
    passed: bool = False
    detail: str = field(default="")


def extract(text: str, doc: str = "") -> list[Query]:
    """Every runnable query in a markdown document, with its declared scope."""
    blocks = _BLOCK.findall(text)
    if not blocks:
        return []
    preamble = ""
    body = list(blocks)
    first = blocks[0]
    if "PREFIX" in first.upper() and not re.search(r"\b(SELECT|ASK|CONSTRUCT)\b",
                                                   first, re.I):
        preamble, body = first, blocks[1:]

    titles = [(a.replace(" ", ""), b) for a, b in _HEADING.findall(text)]
    out: list[Query] = []
    for i, raw in enumerate(body):
        scope_m = _SCOPE.search(raw)
        expect_m = _EXPECT.search(raw)
        label, title = titles[i] if i < len(titles) else (f"Q{i + 1}", "")
        out.append(Query(
            label=label,
            title=title.strip(),
            sparql=preamble + "\n" + raw,
            scopes=tuple(s for s in (scope_m.group(1).split() if scope_m else ())),
            expect=(expect_m.group(1).lower() if expect_m else "rows"),
            doc=doc,
        ))
    return out


#: Graphs by scope, so that six queries sharing `# scope: BFO/` load it once.
#: Reloading per query took seven minutes for nine queries, almost all of it
#: spent parsing `MFTriggers/` repeatedly for the one query that needs it.
_SCOPE_CACHE: dict[tuple, tuple] = {}


def clear_scope_cache() -> None:
    """Drop the cache. Tests that write scopes into a tmp_path need this."""
    _SCOPE_CACHE.clear()


def load_scope(repo: Path, scopes: tuple[str, ...]):
    """The merged graph for a scope declaration, and how many files it held."""
    import rdflib

    key = (str(repo), scopes)
    hit = _SCOPE_CACHE.get(key)
    if hit is not None:
        return hit
    g = rdflib.Graph()
    loaded = 0
    for scope in scopes:
        target = _resolve_scope(repo, scope)
        paths = [target] if target.is_file() else sorted(target.rglob("*.ttl"))
        for p in paths:
            try:
                g.parse(str(p), format="turtle")
                loaded += 1
            except Exception:
                continue
    _SCOPE_CACHE[key] = (g, loaded)
    return g, loaded


def _resolve_scope(repo: Path, scope: str) -> Path | None:
    """A scope is a component id or a literal path.

    Component ids survive relocation; literal paths do not. `# scope: BFO/`
    would have left the competency queries loading nothing for the three
    commits between the BFO move and the documentation pass, and a query that
    loads nothing returns nothing, which reads as a failing ontology rather
    than a broken path.
    """
    if scope.startswith("component:"):
        from . import layout
        return layout.component(scope[len("component:"):]).resolve(repo)
    return repo / scope


def run(repo: Path, query: Query) -> QueryResult:
    """Execute one query over exactly the scope it declares."""
    if not query.scopes:
        return QueryResult(query, error="no '# scope:' declared in the query",
                           detail="a query that does not say what it needs can only "
                                  "be run by someone who already knows")
    g, loaded = load_scope(repo, query.scopes)
    if loaded == 0:
        return QueryResult(query, error=f"scope {' '.join(query.scopes)} loaded nothing")
    try:
        rows = len(list(g.query(query.sparql)))
    except Exception as exc:
        return QueryResult(query, error=" ".join(str(exc).split())[:140])

    passed = rows > 0 if query.expect == "rows" else rows == 0
    return QueryResult(
        query, rows=rows, passed=passed,
        detail=f"{loaded} file(s), {len(g)} triples, expected "
               f"{'a non-empty answer' if query.expect == 'rows' else 'no results'}")


def run_document(repo: Path, doc: Path) -> list[QueryResult]:
    text = doc.read_text(encoding="utf-8", errors="replace")
    rel = str(doc.relative_to(repo)).replace("\\", "/")
    return [run(repo, q) for q in extract(text, rel)]


#: Documents holding executable queries. A document not listed here is prose.
#: Resolved through the layout contract so the documents can move. The literal
#: tuple is kept as a fallback only for a tree with no contract.
_FALLBACK_QUERY_DOCS = ("ontology/bfo/extensions/moral-epistemics/valuenet-moral-epistemics-CQ.md",
                        "docs/bfo/guides/TestingFramework.md")


def query_docs() -> tuple[str, ...]:
    from . import layout
    try:
        return tuple(layout.relative(c.resolve())
                     for c in layout.query_documents())
    except layout.LayoutMissing:
        return _FALLBACK_QUERY_DOCS


QUERY_DOCS = query_docs()


def competency_metrics(repo: Path, docs: tuple[str, ...] = QUERY_DOCS) -> list[Metric]:
    """One record per query, plus a per-document summary.

    Emitted even when everything passes. A finding of the form "CQ6 reaches one
    value through 51,048 trigger statements" needs the row count to be a record
    it can cite, and a passing query that emits nothing is indistinguishable
    from a query that was never run.
    """
    out: list[Metric] = []
    for rel in docs:
        path = repo / rel
        if not path.exists():
            out.append(Metric("competency_doc_missing", rel, 1,
                              detail="listed in QUERY_DOCS but not on disk",
                              tool="rdflib"))
            continue
        results = run_document(repo, path)
        if not results:
            continue
        stem = Path(rel).stem
        for r in results:
            if r.error:
                out.append(Metric("query_error", r.query.ref, 1,
                                  detail=f"{r.error}. {r.detail}".strip(),
                                  tool="rdflib"))
                continue
            out.append(Metric("query_rows", r.query.ref, r.rows,
                              detail=f"{r.query.title[:80]}; {r.detail}",
                              tool="rdflib"))
        answered = sum(1 for r in results if r.passed)
        out.append(Metric("queries_passing", stem, answered,
                          detail=f"of {len(results)} in {rel}; a query passes by "
                                 f"matching its own '# expect:' declaration, which "
                                 f"differs between documents", tool="rdflib"))
    return out
