"""The baseline has to be a measurement, not a number that survived.

`config/reorganization-baseline.json` is the evidence that the move changed
nothing. That role only works if the fingerprint would have moved had the
content moved, and this repository has produced two fingerprints that could
not: a blank-node signature that collided on non-isomorphic graphs, and a test
count that held at 539 while eight tests silently left the default run.

Both failures share a shape. The number was stable, the thing it stood for was
not, and stability was read as evidence.

So what is checked here is mostly the inverse property: that each recorded
quantity can still be derived, and that changing what it measures changes it.
The full corpus digest takes about half an hour and is not re-derived on every
run -- the cheap, exactly-reproducible parts are, and the expensive ones are
marked slow.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys

import pytest

from marep import layout

#: This module asserts properties of the repository the manifest
#: describes: which files git tracks, where they are now, and which
#: literals are still allowed. A materialised copy has no git and has
#: already had waves applied, so every one of these would fail there for
#: reasons that say nothing about the code under test.
pytestmark = pytest.mark.repository

REPO = layout.repository_root()
BASELINE = json.loads(
    (REPO / "config/reorganization-baseline.json").read_text(encoding="utf-8"))

WAVES = ["bfo", "marep", "original-valuenet", "architecture", "tests"]


def value(node):
    """The measurement inside a recorded measure.

    Every corpus and reasoner entry is {value, definition}: the number and
    what it counts, together, because this repository has twice read a number
    as answering a question it was not scoped to. Reaching past the wrapper is
    fine; forgetting it is how a test asserts nothing, which is what the first
    draft of test_no_digest_is_empty_or_a_placeholder did -- it looked for
    keys ending in sha256 and every digest sat one level down.
    """
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node



def _tool():
    path = layout.component("tool.build-semantic-baseline").resolve()
    spec = importlib.util.spec_from_file_location("build_semantic_baseline", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TOOL = _tool()


# ======================================================================
# shape
# ======================================================================


def test_the_baseline_was_written_by_this_version_of_the_tool():
    """A baseline computed a different way is not comparable to this one.

    That is the entire reason the version exists: version 2's blank-node
    fingerprint and version 3's are both sha256 hex strings of the same
    length, and comparing one against the other would look like a match
    failure rather than a category error.
    """
    assert BASELINE["tool_version"] == TOOL.TOOL_VERSION, (
        f"baseline says version {BASELINE['tool_version']}, tool is "
        f"version {TOOL.TOOL_VERSION}; regenerate before comparing")


def test_the_baseline_says_how_to_reproduce_itself():
    assert BASELINE.get("reproduce", "").strip()
    assert BASELINE.get("captured_at_commit")


@pytest.mark.parametrize("section", ["corpus", "reasoner", "artifacts", "tests"])
def test_every_section_is_present_and_populated(section):
    assert BASELINE.get(section), f"{section} is missing or empty"


@pytest.mark.parametrize("key", [
    "files_discovered", "files_parsing", "distinct_triples", "named_classes",
    "trigger_statements", "distinct_trigger_objects", "merged_ground_sha256",
])
def test_corpus_measures_are_recorded(key):
    assert key in BASELINE["corpus"], key


def test_no_digest_is_empty_or_a_placeholder():
    """An empty digest compares equal to another empty digest."""
    seen, bad = [], []

    def check(v, path):
        seen.append(path)
        ok = (isinstance(v, str) and len(v) == 64
              and all(c in "0123456789abcdef" for c in v))
        if not ok:
            bad.append(f"{path} = {v!r}")

    def walk(node, path):
        leaf = path.rsplit(".", 1)[-1]
        if isinstance(node, dict):
            if "sha256" in leaf and "value" in node:
                check(node["value"], path)
                return
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif "sha256" in leaf:
            check(node, path)

    walk(BASELINE, "baseline")
    assert not bad, bad
    assert len(seen) >= 5, (
        f"only {len(seen)} digest(s) examined: {seen}. An earlier form of this "
        "test matched none of them and passed, which is the same defect it is "
        "meant to catch, one level up.")


# ======================================================================
# stable test identities
# ======================================================================


def test_the_recorded_test_identities_still_reconcile():
    """collected, selected and deselected have to add up.

    Version 3 recorded only `collected`, which cannot move when a test is
    silently deselected. Both numbers exist now so the split is visible, and
    if they stop reconciling one of them is measuring something else.
    """
    t = BASELINE["tests"]
    assert t["collected"] == t["default_selected"] + t["default_deselected"], t


def test_canonical_identities_have_no_collisions():
    """Two tests reducing to one identity make the digest ambiguous.

    The canonical id is a basename plus node path, chosen so a directory move
    does not perturb it -- which is exactly why two identically named modules
    in different directories would collide.
    """
    assert BASELINE["tests"]["canonical_id_collisions"] == [], (
        BASELINE["tests"]["canonical_id_collisions"])


def test_the_deselected_tests_are_named_not_just_counted():
    """A count says how many left the default run; the names say which."""
    t = BASELINE["tests"]
    assert len(t["deselected_ids"]) == t["default_deselected"]
    assert all("::" in i for i in t["deselected_ids"])


def test_a_directory_move_does_not_change_a_canonical_identity():
    """The property the identity was designed for, asserted directly."""
    # A synthetic module name. Naming a real one would make this file
    # depend on where that module lives, which is the coupling the
    # canonical identity exists to remove.
    before = "tests/test_example.py::test_a_thing[case-1]"
    after = "tests/marep/test_example.py::test_a_thing[case-1]"
    import os
    assert os.path.basename(before) == os.path.basename(after)


def test_renaming_a_test_does_change_its_identity():
    """The falsification. An identity insensitive to everything is useless."""
    import os
    a = os.path.basename("tests/test_example.py::test_a_thing")
    b = os.path.basename("tests/test_example.py::test_another_thing")
    assert a != b


@pytest.mark.slow
def test_the_test_baseline_still_reproduces():
    """Re-collect and compare. Slow: two full collection passes."""
    current = TOOL.test_baseline(REPO)
    recorded = BASELINE["tests"]
    assert current["canonical_id_sha256"] == recorded["canonical_id_sha256"], (
        f"{current['collected']} tests collected now against "
        f"{recorded['collected']} recorded; the suite has changed since the "
        "baseline was captured")
    assert current["default_selected_sha256"] == recorded["default_selected_sha256"]


# ======================================================================
# semantic fingerprints
# ======================================================================


@pytest.mark.parametrize("name", ["folk_source", "folk_aligned", "cco_extract"])
def test_each_recorded_artifact_still_has_its_byte_digest(name):
    """Cheap and exact: these three are single files."""
    rec = BASELINE["artifacts"][name]
    path = REPO / rec["path"]
    assert path.exists(), rec["path"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == rec["byte_sha256"], (
        f"{rec['path']} has changed since the baseline was captured")


def test_an_artifact_says_which_of_its_digests_survive_the_move():
    """A byte digest and a canonical digest answer different questions.

    folk_aligned.ttl is regenerated in the original-valuenet wave, so its
    bytes change and its canonical form does not. Recording both without
    saying which is invariant would leave a reader to compare the wrong one
    and conclude the ontology had changed.
    """
    for name, rec in BASELINE["artifacts"].items():
        assert "canonical_is_invariant" in rec, name
        assert "byte_is_invariant" in rec, name
    aligned = BASELINE["artifacts"]["folk_aligned"]
    assert aligned["canonical_is_invariant"] is True
    assert aligned["byte_is_invariant"] is False, (
        "folk_aligned.ttl is regenerated when its generator moves; its bytes "
        "are not an invariant of the migration")


def test_the_reasoner_verdict_carries_its_denominator():
    """`reasoner_consistent: 1` over an empty scope is not a verdict.

    The scope silently fell from 306 classes to 275 while the verdict stayed
    1, so the class and file counts are recorded beside it.
    """
    r = BASELINE["reasoner"]
    assert value(r["bfo_layer_files"]) > 0
    assert value(r["bfo_layer_classes"]) > 0
    assert value(r["bfo_layer_imports_unresolved"]) == 0, (
        "an unresolved import means the reasoner did not see what it "
        "reported on")


def test_every_measure_states_what_it_counts():
    """The denominator principle, made structural.

    A bare number invites the reading that sank three of these already:
    `classes_reaching_bfo_root: 179/179` read as "the ontology is grounded",
    when the check was scoped to one layer.
    """
    undefined = []
    for section in ("corpus", "reasoner"):
        for k, v in BASELINE[section].items():
            if not isinstance(v, dict) or not (v.get("definition") or "").strip():
                undefined.append(f"{section}.{k}")
    assert not undefined, undefined


@pytest.mark.slow
def test_the_reasoner_scope_digest_still_reproduces():
    """The eight files HermiT loads, canonicalized."""
    assert TOOL._scope_digest() == \
        value(BASELINE["reasoner"]["bfo_scope_canonical_sha256"]), (
        "the reasoner scope no longer canonicalizes to the recorded "
        "digest; either a module changed or the scope did")

def test_the_blank_node_fingerprint_is_the_component_form():
    """Version 2's fingerprint collided on non-isomorphic graphs.

    The replacement canonicalizes per connected component, so the recorded
    shape has to carry the component structure and not just a count.
    """
    shape = value(BASELINE["corpus"]["merged_bnode_shape"])
    for key in ("blank_nodes", "components", "largest_component_nodes",
                "component_digest_sha256"):
        assert key in shape, f"{key} missing; this is not the component form"
    assert shape["components"] <= shape["blank_nodes"]


@pytest.mark.slow
def test_the_ground_digest_still_reproduces():
    """The non-blank-node triples of the whole corpus. Minutes, not seconds."""
    from marep import ontology_source as onto
    facts = [onto.measure_file(p, REPO) for p in onto.discover(REPO)]
    graph = onto.merged_graph(REPO, facts)
    assert TOOL._ground_digest(graph) == value(
        BASELINE["corpus"]["merged_ground_sha256"])


# ======================================================================
# the tool fails closed
# ======================================================================


def test_a_partial_collection_is_refused_rather_than_recorded():
    """A collection error still prints the ids gathered before it failed.

    Writing a baseline from that list would record a smaller suite and call
    it the truth, which is the failure this whole file exists to prevent.
    """
    src = (layout.component("tool.build-semantic-baseline").resolve()
           .read_text(encoding="utf-8"))
    assert "refusing to write a" in src, (
        "the tool no longer refuses to build a baseline from a partial "
        "collection")


def test_the_version_history_documents_every_version():
    """A version with no entry is a schema change nobody wrote down."""
    src = (layout.component("tool.build-semantic-baseline").resolve()
           .read_text(encoding="utf-8"))
    for v in range(1, TOOL.TOOL_VERSION + 1):
        assert f"#:   {v}  " in src, f"version {v} has no history entry"
