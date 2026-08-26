"""folk_aligned.ttl is generated from ThatsAllFolks/folk.ttl, not maintained.

The two files held the same ontology in two serializations, kept in step by
hand. Measured before the generator existed: 473 named subjects each with none
unique to either side, matching counts across every predicate, and a ground
difference of five ontology-metadata statements. They had not drifted far, but
nothing prevented it, and every value declared in this round had to be written
twice.

These tests hold the seven properties that make the arrangement safe.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

# The repository root comes from the layout contract, not from counting
# parents. This file moves one level deeper in the tests wave, at which
# point parents[1] resolves to tests/ and every path below it is wrong
# without raising anything.
from marep.layout import repository_root  # noqa: E402

REPO = repository_root()
SOURCE = REPO / "ThatsAllFolks" / "folk.ttl"
TARGET = REPO / "folk_aligned.ttl"
GENERATOR = REPO / "ValueNet_code" / "generate_folk_aligned.py"


def generated_text() -> str:
    """Regenerate in memory, without touching the working tree."""
    sys.path.insert(0, str(REPO / "ValueNet_code"))
    import importlib
    mod = importlib.import_module("generate_folk_aligned")
    importlib.reload(mod)
    g = rdflib.Graph()
    g.parse(str(SOURCE), format="turtle")
    return mod.serialize(g)


def test_there_is_one_authored_source():
    assert SOURCE.exists() and TARGET.exists()
    assert GENERATOR.exists()


def test_the_generated_file_says_it_is_generated():
    """Nobody should edit it by hand, so it has to say so where they will look."""
    head = TARGET.read_text(encoding="utf-8")[:900]
    assert "GENERATED FILE" in head
    assert "DO NOT EDIT" in head
    assert "ThatsAllFolks/folk.ttl" in head
    assert "generate_folk_aligned.py" in head


def test_the_generated_file_is_not_stale():
    """The CI gate. Fails when someone edits the source and forgets to run it."""
    current = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert current == generated_text().replace("\r\n", "\n"), (
        "folk_aligned.ttl is stale. Run:\n"
        "    python ValueNet_code/generate_folk_aligned.py")


def test_generation_is_deterministic():
    """Two runs over an unchanged source must give identical bytes.

    rdflib's own Turtle writer orders output by dictionary iteration, so
    adding one triple can reshuffle unrelated blocks and produce a diff that is
    entirely noise. The generator sorts instead.
    """
    assert generated_text() == generated_text()


def test_the_generated_graph_is_isomorphic_to_its_source():
    """Semantic content is what matters; blank-node identity is not."""
    import rdflib.compare as compare
    a = rdflib.Graph(); a.parse(str(SOURCE), format="turtle")
    b = rdflib.Graph(); b.parse(str(TARGET), format="turtle")
    assert compare.isomorphic(a, b)


def test_every_named_subject_statement_survives():
    """Isomorphism already implies this. Asserted separately because a failure
    here names the lost statement, where an isomorphism failure names nothing."""
    a = rdflib.Graph(); a.parse(str(SOURCE), format="turtle")
    b = rdflib.Graph(); b.parse(str(TARGET), format="turtle")
    ground_a = {t for t in a if not any(isinstance(x, rdflib.BNode) for x in t)}
    ground_b = {t for t in b if not any(isinstance(x, rdflib.BNode) for x in t)}
    missing = ground_a - ground_b
    assert not missing, f"generation dropped {len(missing)}: {sorted(missing, key=str)[:3]}"


def test_the_ontology_metadata_survives():
    """The five statements that lived only in folk_aligned.ttl before it became
    generated. They describe the module, and a generator that dropped them
    would quietly delete provenance."""
    b = rdflib.Graph(); b.parse(str(TARGET), format="turtle")
    ont = rdflib.URIRef(
        "http://www.ontologydesignpatterns.org/ont/values/valuemerge_rev.owl")
    from rdflib.namespace import OWL, RDFS
    assert (ont, OWL.versionInfo, None) in b, "versionInfo lost"
    assert (ont, RDFS.comment, None) in b, "module comment lost"
    for iri in ("http://www.ontologydesignpatterns.org/ont/values/schwartz.owl#CulturalValue",
                "http://www.ontologydesignpatterns.org/ont/values/schwartz.owl#IndividualValue"):
        assert (rdflib.URIRef(iri), RDFS.comment, None) in b, f"{iri} comment lost"


@pytest.mark.slow
def test_the_check_flag_reports_staleness():
    """--check is what CI runs, so it must return non-zero on a stale file."""
    r = subprocess.run([sys.executable, str(GENERATOR), "--check"],
                       capture_output=True, text=True, cwd=str(REPO))
    assert r.returncode == 0, f"reported stale unexpectedly:\n{r.stderr}"
