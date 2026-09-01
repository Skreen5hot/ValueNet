# SPDX-License-Identifier: Apache-2.0
"""Ontology substrate records, end to end through `ingest`.

The unit half of these tests is in `test_ontology_source_unit.py` and measures
`ontology_source` on its own. These build an entire substrate document and ask
whether the ontology records inside it validate, stay deterministic, and can
actually be cited — which is the only question that matters at the end: a
metric nobody can resolve grounds nothing.

Split from that file rather than left beside it because the two have different
owners in the reorganized tree. Keeping them together would have put an
integration test under `tests/marep/ontology/` on the strength of a shared
import.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from marep import ingest

from _support import FRAGMENT, TURTLE, write_ttl

# ======================================================================
# false fact 3, at the substrate level
# ======================================================================



def test_build_rejects_a_duplicate_reference(tmp_path: Path):
    """The guard that would have caught it at the substrate level."""
    result = ingest.build("s", "2020-01-01", "2030-01-01", repo=tmp_path, include_github=False)
    dup = dict(result.document["records"][0]) if result.document["records"] else None
    if dup is None:
        pytest.skip("no records to duplicate in an empty repo")
    result.document["records"].append({**dup, "id": "ZZZ-9999"})
    seen: dict[tuple, str] = {}
    errs = []
    for rec in result.document["records"]:
        key = (rec["type"], rec["ref"])
        if key in seen:
            errs.append(key)
        seen[key] = rec["id"]
    assert errs, "the guard must see a repeated (type, ref)"

# ======================================================================
# substrate integration
# ======================================================================



def test_ontology_records_validate_and_are_deterministic(tmp_path: Path):
    write_ttl(tmp_path, "a.ttl", TURTLE)
    write_ttl(tmp_path, "b.ttl", FRAGMENT)
    a = ingest.build("s", "2020-01-01", "2030-01-01", repo=tmp_path,
                     include_github=False, ontology=True)
    b = ingest.build("s", "2020-01-01", "2030-01-01", repo=tmp_path,
                     include_github=False, ontology=True)
    assert not a.errors, a.errors
    assert a.document == b.document, "same corpus must give the same substrate"
    assert a.counts["document"] == 2
    assert a.counts["metric"] > 0



def test_a_finding_about_the_ontology_can_now_be_grounded(tmp_path: Path):
    """The whole point: an unparseable file becomes citable evidence."""
    from marep import Substrate

    write_ttl(tmp_path, "good.ttl", TURTLE)
    write_ttl(tmp_path, "fragment.ttl", FRAGMENT)
    result = ingest.build("s", "2020-01-01", "2030-01-01", repo=tmp_path,
                          include_github=False, ontology=True)
    path = ingest.write(result, tmp_path / "SPRINT_INPUT.yaml")
    substrate = Substrate.load(path)

    rec = next(r for r in result.document["records"]
               if r["type"] == "metric" and r["payload"]["check"] == "files_not_parsing")
    # Both citation forms resolve. The ref is the durable one: identifiers are
    # positional and shift when the corpus gains a file.
    assert substrate.resolve({"type": "metric", "ref": rec["ref"]}) is True
    assert substrate.resolve({"type": "metric", "ref": rec["id"]}) is True
    assert substrate.resolve({"type": "commit", "ref": rec["ref"]}) is False, "type must match"
    assert substrate.resolve({"type": "metric", "ref": "no-such-check:nowhere"}) is False



def test_ontology_types_are_not_reported_as_gaps(tmp_path: Path):
    write_ttl(tmp_path, "a.ttl", TURTLE)
    result = ingest.build("s", "2020-01-01", "2030-01-01", repo=tmp_path,
                          include_github=False, ontology=True)
    gaps = {c["type"] for c in result.document["coverage"] if not c["available"]}
    assert "document" not in gaps and "metric" not in gaps



def test_without_the_flag_they_remain_declared_gaps(tmp_path: Path):
    write_ttl(tmp_path, "a.ttl", TURTLE)
    result = ingest.build("s", "2020-01-01", "2030-01-01", repo=tmp_path,
                          include_github=False)
    gaps = {c["type"]: c.get("reason", "") for c in result.document["coverage"]
            if not c["available"]}
    assert "document" in gaps and "metric" in gaps
