"""Constants and helpers shared across test modules.

Separated from `conftest.py` because the two files answer to different rules.
pytest owns `conftest.py`: it collects it automatically, and everything in it
is reachable from any test in the directory whether or not that test says so.
Fixtures need that. Plain constants and helper functions do not, and putting
them there made six modules import from a file pytest was already loading for
its own reasons — a dependency no import statement in either direction
declares.

So `conftest.py` keeps fixtures only, and everything a test has to name for
itself lives here and is imported explicitly.

There is deliberately no `tests/__init__.py`. `tests/` is on `sys.path`
because pytest inserts a rootdir-relative conftest's directory when the
directory is not a package, which is what made `from conftest import ...`
work; `from _support import ...` resolves by the same mechanism. Adding an
`__init__.py` would make `tests` a package, remove that insertion, and break
both forms at once.

Two groups, and they are unrelated: a sprint substrate for the MAREP runtime
tests, and a small ontology corpus for the ontology-source tests. They share
a file because the plan calls for exactly one support module, not because
they have anything to do with each other.
"""

from __future__ import annotations

from pathlib import Path

# ======================================================================
# MAREP substrate: a small but complete sprint
# ======================================================================

ROSTER = ["Developer", "QA", "Architect", "Skeptic"]

SUBSTRATE_DOC = {
    "sprint": {"id": "sprint-42", "started": "2026-08-01", "ended": "2026-08-14"},
    "records": [
        {"id": "CI-1204", "type": "ci_run", "ref": "gh-actions/12841",
         "timestamp": "2026-08-09T11:04:00Z", "summary": "Release 42.3 rollback failed"},
        {"id": "DEP-0311", "type": "deploy", "ref": "deploy/42.3",
         "timestamp": "2026-08-09T10:55:00Z", "summary": "Release 42.3 to production"},
        {"id": "TIC-7781", "type": "ticket", "ref": "PROJ-7781",
         "timestamp": "2026-08-10T09:00:00Z", "summary": "Staging/prod runtime divergence"},
        {"id": "NOTE-001", "type": "note", "ref": "retro-note-1",
         "timestamp": "2026-08-14T16:00:00Z", "summary": "Team felt review load was heavy"},
        {"id": "CI-1300", "type": "ci_run", "ref": "gh-actions/13000",
         "timestamp": "2026-08-12T08:00:00Z", "summary": "Flaky integration suite"},
    ],
    "coverage": [
        {"type": "incident", "available": False, "reason": "no incident tracker integration"},
        {"type": "metric", "available": False, "reason": "metrics pipeline not wired to retro"},
        {"type": "ci_run", "available": True},
    ],
}


def issue(iid="DEPLOY-002", status="proposed", evidence=None, **kw):
    ev = evidence if evidence is not None else [{
        "id": "EV-001",
        "claim": "Rollback of release 42.3 required manual intervention",
        "source": {"type": "ci_run", "ref": "CI-1204"},
        "submitted_by": "Developer",
    }]
    out = {"id": iid, "title": "Deployment instability", "severity": "medium",
           "status": status, "evidence": ev}
    out.update(kw)
    return out


def upd(uid, base, agent_sections):
    """Build an update envelope."""
    d = {"update_id": uid, "base_version": base}
    d.update(agent_sections)
    return d


# ======================================================================
# Ontology corpus: two files, one valid and one not
# ======================================================================

#: A well-formed document. The comment matters: it names two external IRIs in
#: prose, which is what made the prefix scanner report `OBI` and `RO` as
#: undeclared prefixes.
TURTLE = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://example.org/A> a owl:Class ;
  rdfs:label "A" ;
  rdfs:comment "Compare OBI:has specified input and RO:has input." .
"""

#: One of the 127 fragments, reproduced exactly: it uses two prefixes and
#: declares neither, so it parses only beside a parent that supplies them.
FRAGMENT = """### a fragment with no prefix declarations at all
<http://en.wiktionary.org/wiki/accomplishment> vcvf:triggers folk:Accomplishment .
"""


def write_ttl(tmp: Path, name: str, text: str) -> Path:
    """Write one corpus file and return its path.

    Named without a leading underscore because it crosses a module boundary.
    It was `_write`, which said "private to this file" while two files
    imported it.
    """
    p = tmp / name
    p.write_text(text, encoding="utf-8")
    return p
