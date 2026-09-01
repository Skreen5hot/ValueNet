# SPDX-License-Identifier: Apache-2.0
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


def _validator():
    path = layout.component("tool.validate-migration-state").resolve()
    spec = importlib.util.spec_from_file_location("validate_migration_state", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VALIDATOR = _validator()

#: From the freeze tag once it exists. Read from the working tree, a
#: regenerated baseline would move the goalposts: every comparison below would
#: be against numbers computed from the same tree it is checking, which can
#: only ever agree.
#: Historical evidence: what was measured at the freeze, under conditions
#: that no longer obtain. Read from the tag, never from the working copy.
FROZEN_TEXT, FROZEN_SOURCE = VALIDATOR.frozen_text(
    "config/reorganization-baseline.json")
FROZEN = json.loads(FROZEN_TEXT)

#: The live description of HEAD. Everything the working tree is required to
#: reproduce is checked against this one.
#: The successor baseline and the matrix it cites are generated from a clean
#: commit, so between committing the measurement code and committing the
#: evidence they do not exist. That window is the only reason either may be
#: absent, and `test_a_committed_repository_carries_its_evidence` closes it.
BASELINE_PATH = REPO / "config/semantic-baseline.json"
MATRIX_PATH = REPO / "config/eol-transition-matrix.json"
BASELINE_SOURCE = "config/semantic-baseline.json"

BASELINE = (json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
            if BASELINE_PATH.is_file() else None)
MATRIX = (json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
          if MATRIX_PATH.is_file() else None)

needs_evidence = pytest.mark.skipif(
    BASELINE is None or MATRIX is None,
    reason="successor baseline or transition matrix not generated yet; they "
           "are produced from the commit that carries the measurement code")

#: Where each recorded artifact lives, by component rather than by the path
#: the baseline recorded. The CCO extract moves to ontology/bfo/vendor/cco/ in
#: the bfo wave, so the frozen path stops resolving the moment the migration
#: starts -- and a test that cannot survive the move it is checking is not a
#: check on the move.
ARTIFACT_COMPONENT = {
    "folk_source": ("original-valuenet.folk-source", None),
    "folk_aligned": ("original-valuenet.folk-aligned", None),
    "cco_extract": ("bfo.vendor-cco", "cco-valuenet-extract.ttl"),
}


def artifact_path(name: str):
    cid, child = ARTIFACT_COMPONENT[name]
    base = layout.component(cid).resolve()
    return base / child if child else base

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


@needs_evidence
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


@needs_evidence
def test_the_baseline_says_how_to_reproduce_itself():
    assert BASELINE["reproduce"]["command"].strip()
    assert BASELINE.get("input_commit"), (
        "the field was renamed from captured_at_commit: a baseline names "
        "the commit it was measured FROM, which is not the commit it "
        "lands in")
    assert BASELINE.get("input_tree_state")


@pytest.mark.parametrize("section", ["corpus", "reasoner", "artifacts", "tests"])
@needs_evidence
def test_every_section_is_present_and_populated(section):
    assert BASELINE.get(section), f"{section} is missing or empty"


@pytest.mark.parametrize("key", [
    "files_discovered", "files_parsing", "distinct_triples", "named_classes",
    "trigger_statements", "distinct_trigger_objects", "merged_ground_sha256",
])
@needs_evidence
def test_corpus_measures_are_recorded(key):
    assert key in BASELINE["corpus"], key


@needs_evidence
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


@needs_evidence
def test_the_recorded_test_identities_still_reconcile():
    """collected, selected and deselected have to add up.

    Version 3 recorded only `collected`, which cannot move when a test is
    silently deselected. Both numbers exist now so the split is visible, and
    if they stop reconciling one of them is measuring something else.
    """
    t = BASELINE["tests"]
    assert t["collected"] == t["default_selected"] + t["default_deselected"], t


@needs_evidence
def test_canonical_identities_have_no_collisions():
    """Two tests reducing to one identity make the digest ambiguous.

    The canonical id is a basename plus node path, chosen so a directory move
    does not perturb it -- which is exactly why two identically named modules
    in different directories would collide.
    """
    assert BASELINE["tests"]["canonical_id_collisions"] == [], (
        BASELINE["tests"]["canonical_id_collisions"])


@needs_evidence
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
@needs_evidence
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


@needs_evidence
def test_every_recorded_artifact_resolves():
    """Through the contract, so the check survives the wave that moves it."""
    for name in BASELINE["artifacts"]:
        assert artifact_path(name).is_file(), name


@needs_evidence
def test_bytes_are_compared_only_where_the_baseline_says_they_are_invariant():
    """A byte digest and a canonical digest answer different questions.

    folk_aligned.ttl is regenerated when its generator moves, so its bytes
    change by design and the baseline records `byte_is_invariant: false`.
    Comparing them anyway asserted that a documented transition must not
    happen -- the test would have failed precisely when the migration
    succeeded.
    """
    problems = []
    for name, rec in BASELINE["artifacts"].items():
        if not rec["byte_is_invariant"]:
            continue
        actual = hashlib.sha256(artifact_path(name).read_bytes()).hexdigest()
        if actual != rec["byte_sha256"]:
            problems.append(f"{name}: bytes changed but are recorded invariant")
    assert not problems, problems


@needs_evidence
def test_something_is_expected_to_change_its_bytes():
    """Guards the reading where every artifact is byte-invariant and the
    test above is vacuous."""
    mutable = [n for n, r in BASELINE["artifacts"].items()
               if not r["byte_is_invariant"]]
    assert mutable == ["folk_aligned"], mutable


@pytest.mark.slow
@needs_evidence
def test_the_canonical_digest_holds_for_every_artifact():
    """The invariant that has to survive the whole migration.

    Canonical for all three, including the one whose bytes are expected to
    move: what the plan promises is that nothing the ontology *means*
    changes, and the canonical form is where that claim lives.
    """
    problems = []
    for name, rec in BASELINE["artifacts"].items():
        assert rec["canonical_is_invariant"] is True, name
        actual = TOOL.canonical_digest(artifact_path(name))
        if actual != rec["canonical_sha256"]:
            problems.append(f"{name}: canonical RDF changed")
    assert not problems, problems


@needs_evidence
def test_the_baseline_being_checked_is_the_frozen_one():
    """The two baselines are read from the two places they belong.

    The name is kept because it is a collected node id. What it asserts has
    changed: the frozen baseline comes from the tag and is never read from
    the working copy, while the successor is read from the working tree
    because describing the working tree is its whole purpose.
    """
    if VALIDATOR.frozen_exists():
        assert FROZEN_SOURCE.endswith("@" + VALIDATOR.FREEZE_TAG), FROZEN_SOURCE
    else:
        assert "working copy" in FROZEN_SOURCE, FROZEN_SOURCE
    assert BASELINE_SOURCE == "config/semantic-baseline.json"
    assert BASELINE is not FROZEN


@needs_evidence
def test_the_frozen_baseline_records_what_it_cannot_show():
    """Historical evidence has to carry its own limits.

    Its corpus digest was computed with the document base taken from the
    filesystem, so it holds only for the original checkout path -- two
    byte-identical clones elsewhere produce different values. Left
    unqualified, a future reader would take a mismatch for corpus drift.
    The successor records that, and this checks the record exists.
    """
    t = BASELINE["transition"]
    assert t["supersedes"]["baseline"] == "config/reorganization-baseline.json"
    assert t["supersedes"]["tag"] == VALIDATOR.FREEZE_TAG
    assert t["supersedes"]["tool_version"] < BASELINE["tool_version"]
    why = t["document_base"]["why"]
    assert "checkout" in why and "reproducible only at the original path" in why


@needs_evidence
def test_the_matrix_measured_a_commit_and_not_a_desk():
    """Conclusion 1: the experiment ran on published input.

    A matrix produced from a dirty tree names a commit that does not
    contain what it measured, and reads identically to one that does."""
    assert MATRIX["working_tree_clean"] is True
    assert MATRIX["measured_from_tag"] == "reorg-post-move-v1"
    # Either exactly clean, or clean apart from the one evidence artifact
    # the orchestrator wrote immediately before the baseline ran. Named,
    # so "dirty" cannot broaden into a category.
    state = BASELINE["input_tree_state"]
    assert state == "clean" or state in (
        "clean apart from config/eol-transition-matrix.json",
        "clean apart from config/remediation-record.json"), state


@needs_evidence
def test_both_artifacts_describe_one_commit():
    """Conclusion 2: the baseline and the matrix are one run.

    Two artifacts each internally consistent but generated from different
    commits would still satisfy every field-shape check in this file."""
    m = BASELINE["transition"]["measured"]
    assert m["input_commit"] == MATRIX["input_commit"]
    assert m["working_tree_clean"] is True

    if BASELINE["input_commit"] == MATRIX["input_commit"]:
        return

    # They may differ, but only across a bridge that exists and holds.
    # A source-data repair moves the corpus forward while the experiment
    # stays where it was measured; the matrix is frozen because its
    # content is a comparison of three checkouts of one commit.
    #
    # This is the case the exemption exists for, so it is checked harder
    # than the equal case, not waved through: the record must name both
    # ends, the baseline must carry it, and the far end must be this
    # commit.
    assert RECORD is not None, (
        "the baseline cites a matrix from another commit and no "
        "remediation record explains the gap")
    assert RECORD["before_commit"] == MATRIX["input_commit"]
    assert RECORD["after_commit"] == BASELINE["input_commit"]
    assert m["describes_corpus_at"] == MATRIX["input_commit"]
    assert m["corpus_repaired_since"]["artifact_sha256"] == hashlib.sha256(
        RECORD_PATH.read_bytes()).hexdigest(), (
        "the baseline carries a different record than the one on disk")


@needs_evidence
def test_the_old_document_base_was_path_dependent():
    """Conclusion 3: the defect being fixed was real, and is shown.

    Cell A is one commit measured twice at two absolute paths. If those
    agreed there would be nothing here to fix, and the successor
    baseline's central claim would be unsupported."""
    pd = MATRIX["path_dependence"]
    assert pd["differ"] is True, (
        "the unhardened parser produced the same digest at two paths; "
        "either the harness reused a checkout, or the defect is not the "
        "one this baseline says it repairs")
    assert pd["A_first"] != pd["A_second"]
    assert len(pd["A_first"]) == len(pd["A_second"]) == 64


@needs_evidence
def test_every_declared_invariant_actually_holds():
    """Conclusion 4: recording an invariant is not asserting it.

    The matrix computes each invariant and writes down the answer,
    including false. Nothing so far requires the answers to be true."""
    stated = MATRIX["invariants"]
    assert stated, "no invariants were declared"
    nonbool = sorted(k for k, v in stated.items()
                     if not isinstance(v, bool))
    assert not nonbool, (
        "an invariant has to be a boolean to be true or false; %s "
        "would pass a truthiness check on any non-empty value" % nonbool)
    failed = sorted(k for k, v in stated.items() if v is not True)
    assert not failed, "the experiment reports these as false: %s" % failed


@needs_evidence
def test_the_cells_are_the_conditions_they_claim_to_be():
    """Conclusion 5: each cell's axes are the ones it is cited for.

    The matrix is an argument from the difference between three
    conditions. A mislabelled axis makes every comparison meaningless
    while leaving all the digests well-formed."""
    axes = {"A": (False, False), "B": (True, False), "C": (True, True)}
    cells = BASELINE["transition"]["measured"]["cells"]
    assert set(cells) == set(MATRIX["cells"]) == set(axes)
    for name, (hardened, lf) in axes.items():
        src = MATRIX["cells"][name]
        assert (src["hardened"], src["lf"]) == (hardened, lf), name
        rec = cells[name]
        assert (rec["hardened"], rec["lf"]) == (hardened, lf), name
        assert rec["ground"] == src["corpus"]["merged_ground_sha256"]
        assert rec["label"] == src["label"]
        assert rec["eol_distribution"] == src["eol"]["distribution"]
        assert rec["eol_aggregate_sha256"] == src["eol"]["aggregate_sha256"]


@needs_evidence
def test_hardening_the_parser_changed_no_bytes_on_disk():
    """Conclusion 6: A and B differ in code and in nothing else.

    Asserted from the per-file line-ending map rather than from the
    harness's own boolean, so a harness that computed the invariant
    wrongly does not also get to certify it."""
    a = MATRIX["cells"]["A"]["eol"]
    b = MATRIX["cells"]["B"]["eol"]
    assert a["aggregate_sha256"] == b["aggregate_sha256"]
    assert a["distribution"] == b["distribution"]
    assert a["per_file"] == b["per_file"], (
        "A and B were supposed to be byte-identical checkouts; a file "
        "listed differently means they differ in more than the parser, "
        "and the digest comparison between them measures two changes")


@needs_evidence
def test_the_lf_cell_is_actually_lf():
    """Conclusion 7: cell C is the policy, not a tree that resembles it.

    C is the condition the successor baseline describes. If normalization
    missed files, C is some third state, and the baseline documents a
    condition the repository is never in."""
    dist = MATRIX["cells"]["C"]["eol"]["distribution"]
    assert dist.get("crlf", 0) == 0 and dist.get("mixed", 0) == 0, (
        "cell C still holds CRLF in %s files and mixed endings in %s"
        % (dist.get("crlf", 0), dist.get("mixed", 0)))
    assert dist.get("lf", 0) > 0, "cell C holds no LF-terminated Turtle"


@needs_evidence
@pytest.mark.slow
def test_the_baseline_measures_the_condition_cell_c_describes():
    """Conclusion 8: the successor baseline is cell C, measured live.

    This is the join between the experiment and the artifact it
    justifies. If HEAD does not reproduce C, then either the policy is
    not in force in this checkout or the baseline describes a different
    corpus than the matrix reasoned about, and the matrix's conclusions
    have been carried to a state they were never measured on."""
    live = BASELINE["corpus"]["merged_ground_sha256"]["value"]
    cell_c = MATRIX["cells"]["C"]["corpus"]["merged_ground_sha256"]
    if RECORD is None:
        assert live == cell_c, (
            "HEAD does not reproduce cell C. Confirm .gitattributes is in "
            "force in this checkout before reading this as a corpus change")
        return

    # A repair landed after cell C was measured, so equality is now the
    # wrong assertion -- and "they differ, as expected" would be a much
    # weaker one, satisfied by any corpus change at all.
    #
    # What has to hold is that cell C plus exactly the recorded
    # substitutions is HEAD. Asserted by reverting the recorded files to
    # their pre-repair contents and re-measuring: if the result is cell
    # C, then nothing outside the record moved the corpus. Slow, because
    # it parses everything; this is the join between the experiment and
    # the artifact it justifies, and it is the only claim here that the
    # exemption could have quietly hollowed out.
    assert live != cell_c, (
        "a repair is recorded but the ground digest is unchanged")
    assert TOOL.ground_digest_with(
        REPO, {rel: _text_at(RECORD["before_commit"], rel)
               for rel in RECORD["corpus_files_changed"]}) == cell_c, (
        "reverting the recorded files does not reproduce cell C, so the "
        "corpus moved for reasons the remediation record does not name")


@needs_evidence
def test_the_successor_records_the_line_ending_transition():
    """Field for field against the artifact, not a summary of it.

    Checking that two independently written distributions sum to the
    same total is satisfied by two different wrong distributions. What
    matters is that the baseline reproduces what the harness measured,
    exactly -- down to which file and which predicate."""
    rec = BASELINE["transition"]["measured"]["line_ending_transition"]
    assert rec == MATRIX["line_ending_transition"]
    assert rec["total"] == sum(rec["files"].values()), (
        "the enumeration's total disagrees with its own per-file counts")
    assert rec["total"] == sum(rec["predicates"].values()), (
        "the same triples counted by file and by predicate should give "
        "the same total; they do not")
    assert set(rec["examples"]) == set(rec["files"]), (
        "every affected file should carry an example of what changed")


@needs_evidence
def test_the_successor_cites_the_artifact_it_was_built_from():
    """Path and digest, so a reader can tell which run this is."""
    import hashlib
    m = BASELINE["transition"]["measured"]
    assert m["artifact"] == "config/eol-transition-matrix.json"
    assert m["artifact_sha256"] == hashlib.sha256(
        MATRIX_PATH.read_bytes()).hexdigest(), (
        "the baseline cites a different matrix than the one on disk")


@needs_evidence
def test_the_recorded_invariants_match_the_artifact():
    m = BASELINE["transition"]["measured"]
    assert m["invariants"] == MATRIX["invariants"]
    assert m["path_dependence"] == MATRIX["path_dependence"]




@needs_evidence
def test_the_count_invariant_covers_every_count_there_is():
    """The invariant is named for counts, so it has to mean all
    of them.

    The compared set was hand-written and omitted
    class_declarations_summed: present, equal in all three cells, and
    outside an invariant called `corpus_counts_identical_across_cells`.
    A hand-written list does not grow when the measurement does, and
    nothing said the two had drifted apart."""
    scope = MATRIX["invariant_scope"]["corpus_counts_compared"]
    for name, cell in MATRIX["cells"].items():
        counts = sorted(k for k, v in cell["corpus"].items()
                        if isinstance(v, int) and not isinstance(v, bool))
        assert counts == sorted(scope), (
            "cell " + name + " records counts the invariant does not "
            "compare: " + str(sorted(set(counts) - set(scope))))
    assert BASELINE["transition"]["measured"]["invariant_scope"] == \
        MATRIX["invariant_scope"]
@needs_evidence
def test_the_successor_records_the_known_relative_iri():
    """The stable base makes the measurement reproducible. It does not
    make hasDataValue <1> correct, and the record says so."""
    ex = BASELINE["transition"]["known_exceptions"]["relative_iri"]
    assert ex["file"] == "ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl"
    assert "separate task" in ex["note"]
    assert ex["status"].startswith("unremediated")
    assert list(MATRIX["relative_iris"]) == [ex["file"]], (
        "the corpus holds a relative IRI the record does not mention")


@needs_evidence
def test_the_published_reproduction_command_is_one_that_works():
    """A command that exits 1 is worse than no command at all.

    The baseline cites the transition matrix and refuses one measured
    at any commit but its own. So running this builder by itself
    succeeds at exactly one commit -- the one the matrix already names
    -- and exits 1 everywhere else, including at the tag, where the
    matrix names the parent commit because the evidence is always
    committed after the input it describes. The refusal is correct;
    the instruction that ignored it was not.

    So the recorded command must be the orchestrator, and must say
    which checkout to run it from."""
    rep = BASELINE["reproduce"]
    orchestrator = layout.component("tool.build-evidence")
    assert rep["command"].split()[-1] == layout.relative(
        orchestrator.resolve()), (
        "the recorded command does not name the component the contract "
        "declares as the evidence orchestrator")
    assert orchestrator.resolve().is_file()
    assert "build_semantic_baseline" not in rep["command"], (
        "this builder refuses on its own at any commit but the one the "
        "matrix names; publishing it as the reproduction step publishes "
        "a command that exits 1")
    assert "input_commit" in rep["from"], (
        "the command works only from the commit the artifacts describe, "
        "and the instruction has to say so")


def test_the_loader_refuses_a_matrix_from_another_commit():
    """Which is why the instruction has to name the orchestrator.

    Exercised rather than described, and in both directions: a blanket
    refusal would satisfy the first half of this while making the
    artifact unusable, and would look identical in a passing suite."""
    real = BASELINE["input_commit"]
    wrong = "0" * 40
    with pytest.raises(SystemExit) as exc:
        TOOL.load_transition(REPO, wrong)
    message = str(exc.value)
    assert real[:12] in message and wrong[:12] in message, (
        "the refusal should name both commits; a reader who cannot see "
        "which two disagree cannot act on it")

    accepted = TOOL.load_transition(REPO, real)
    # The matrix names the commit it measured, which is this one only
    # when no repair has landed since.
    assert accepted["measured"]["input_commit"] == MATRIX["input_commit"]
    if RECORD is None:
        assert MATRIX["input_commit"] == real
    else:
        assert accepted["measured"]["corpus_repaired_since"][
            "after_commit"] == real, (
            "the loader accepted this commit without recording what "
            "separates it from the one the matrix measured")


@needs_evidence
def test_the_successor_declares_its_policies():
    pol = BASELINE["policy"]
    assert pol["document_base"].startswith("https://")
    assert pol["line_endings"] == "lf"


@needs_evidence
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


@needs_evidence
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


@needs_evidence
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

@needs_evidence
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
@needs_evidence
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


SENTINEL = b'{"sentinel": "this baseline must survive a refused run"}\n'


def _tool_tree(tmp_path):
    """Enough of a repository for the tool to start, and no git.

    `git rev-parse HEAD` is the first thing main() does, so a tree with no
    repository fails there -- before the half hour of corpus canonicalization
    that a later forced failure would have to sit through.
    """
    import shutil

    root = tmp_path / "tree"
    (root / "config").mkdir(parents=True)
    (root / "tools").mkdir()
    (root / "out").mkdir()
    shutil.copy2(REPO / "config/repository-layout.yaml",
                 root / "config/repository-layout.yaml")
    shutil.copytree(REPO / "marep", root / "marep",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(layout.component("tool.build-semantic-baseline").resolve(),
                 root / "tools/build_semantic_baseline.py")
    (root / "out/baseline.json").write_bytes(SENTINEL)
    return root


def test_the_baseline_is_not_written_when_the_commit_cannot_be_read(tmp_path):
    """Fail-closed, exercised rather than read.

    A baseline that does not know which commit it describes cannot be
    compared to anything later, so recording one would produce a file that
    looks like evidence and is not. The earlier form of this test searched
    the tool's source for the string "refusing to write a", which proves
    somebody typed a message, not that anything refuses.
    """
    root = _tool_tree(tmp_path)
    r = subprocess.run([sys.executable, "tools/build_semantic_baseline.py",
                        "-o", "out/baseline.json"],
                       cwd=str(root), capture_output=True, text=True)
    assert r.returncode != 0, (
        "the tool exited 0 with no git repository:\n" + r.stdout)
    assert (root / "out/baseline.json").read_bytes() == SENTINEL, (
        "a refused run replaced the existing baseline")


def test_a_partial_collection_is_refused_rather_than_recorded(tmp_path):
    """A collection error still prints the ids gathered before it failed.

    Writing a baseline from that list would record a smaller suite and call
    it the truth -- the exact shape of every other defect this file guards:
    a number that survived, standing in for a measurement that did not.
    """
    root = tmp_path / "broken"
    root.mkdir()
    (root / "test_fine.py").write_text("def test_ok():\n    assert True\n",
                                       encoding="utf-8")
    (root / "test_broken.py").write_text("def test_bad(:\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        TOOL.test_baseline(root)
    assert "refusing to write" in str(exc.value)


def test_a_clean_collection_is_accepted(tmp_path):
    """The falsification: a tool that refused every collection would pass
    the test above."""
    root = tmp_path / "clean"
    root.mkdir()
    (root / "test_fine.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8")
    result = TOOL.test_baseline(root)
    assert result["collected"] >= 1, result


def test_the_version_history_documents_every_version():
    """A version with no entry is a schema change nobody wrote down."""
    src = (layout.component("tool.build-semantic-baseline").resolve()
           .read_text(encoding="utf-8"))
    for v in range(1, TOOL.TOOL_VERSION + 1):
        assert f"#:   {v}  " in src, f"version {v} has no history entry"


def test_a_committed_repository_carries_its_evidence():
    """This test is red at exactly one commit, on purpose.

    The evidence is measured *from* a commit, so the commit that
    introduces the measurement code cannot also contain the measurements:
    they name the commit they were taken from, and that commit does not
    exist until it is made. The sequence is therefore

        1. commit the tools, the policy and these tests   <- red here
        2. python tools/marep/build_evidence.py
        3. commit config/semantic-baseline.json and
           config/eol-transition-matrix.json               <- green again

    and `build_evidence.py` exists so that step 2 is one command rather
    than a sequence somebody can stop halfway through.

    Every other time, a clean tree with no evidence means the baseline
    cites measurements nobody can find, which is the failure this whole
    pass is about. Skipping instead of failing would make that state
    indistinguishable from the intended window, so it fails, and says
    which of the two it thinks it is looking at."""
    import subprocess
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        pytest.skip("mid-procedure: the tree has uncommitted changes")
    remedy = (" If this is the commit that introduced the measurement "
              "tools, this failure is the expected one: run "
              "tools/marep/build_evidence.py and commit its two outputs.")
    assert BASELINE_PATH.is_file(), (
        "a clean tree with no successor baseline." + remedy)
    assert MATRIX_PATH.is_file(), (
        "the baseline cites a transition matrix that is not in the tree."
        + remedy)


# ======================================================================
# the source-data repair, and what it was allowed to move
# ======================================================================

#: The repair landed after the transition matrix was measured. The matrix
#: is frozen deliberately -- its content is a comparison of three
#: checkouts of one commit, so re-running it against a repaired corpus
#: would replace the experiment rather than repeat it. This record is
#: what permits the baseline to cite it anyway.
RECORD_PATH = REPO / "config/remediation-record.json"
RECORD = (json.loads(RECORD_PATH.read_text(encoding="utf-8"))
          if RECORD_PATH.is_file() else None)

needs_repair_record = pytest.mark.skipif(
    RECORD is None or BASELINE is None,
    reason="the remediation record is generated from the commit that "
           "carries the repair, so it is absent for exactly that commit")

BEFORE_TAG = "eol-hardened-v1"


def _text_at(rev, rel):
    """One file as of one commit, decoded but not parsed."""
    out = subprocess.run(["git", "show", rev + ":" + rel],
                         cwd=str(REPO), capture_output=True, text=True)
    assert out.returncode == 0, rel + " is not in " + rev[:12]
    return out.stdout


def _at_tag(rel):
    """A committed artifact as of the tag, or None if it was not there."""
    out = subprocess.run(["git", "show", BEFORE_TAG + ":" + rel],
                         cwd=str(REPO), capture_output=True, text=True)
    return json.loads(out.stdout) if out.returncode == 0 else None


@needs_repair_record
def test_the_archive_is_recorded_and_its_bytes_are_untouched():
    """Declining to repair something is a claim that needs a digest.

    The archive holds 180 further instances of the same defect. Leaving
    it alone is the decision; leaving it undocumented would make that
    decision indistinguishable from not having noticed.

    This hashes the file. It does not open it -- a test that read the
    members would make an inert artifact into a corpus, which is the one
    thing the record says it is not.
    """
    import hashlib

    archive = RECORD["not_remediated"]["archive"]
    path = REPO / archive["path"]
    assert path.is_file(), archive["path"] + " is gone"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == archive["sha256"], (
        "the archive's bytes have changed; it is recorded as preserved "
        "upstream debt and nothing in this repository should rewrite it")
    assert archive["excluded_from_live_corpus"] is True
    assert archive["members_affected"] > 0 and archive["occurrences"] > 0
    assert archive["detection"].strip(), (
        "a record of a defect nobody can re-find is a rumour")
    assert "upstream" in archive["disposition"]


@needs_repair_record
def test_the_archive_really_is_outside_the_corpus():
    """Asserted against the discovery function, not against the record.

    The record says the archive is excluded. That is the kind of claim
    that stays in a file long after it stops being true.
    """
    from marep import ontology_source as onto

    discovered = {p.relative_to(REPO).as_posix() for p in onto.discover(REPO)}
    assert RECORD["not_remediated"]["archive"]["path"] not in discovered
    assert not any(d.endswith(".zip") for d in discovered)
    assert "ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl" in discovered, (
        "the one member that IS measured has left the corpus")


@needs_repair_record
def test_the_recorded_substitutions_are_the_ones_git_shows():
    """Recomputed here rather than read.

    The record is the only thing allowing a matrix from an earlier commit
    to be cited. If its enumeration were taken on trust, the exemption
    would be a way of saying 'the corpus changed somehow' with a
    straight face.
    """
    import rdflib

    from marep import ontology_source as onto

    before = RECORD["before_commit"]
    changed = subprocess.run(
        ["git", "diff", "--name-only", "--find-renames", before, "HEAD",
         "--", "*.ttl"],
        cwd=str(REPO), capture_output=True, text=True).stdout.split()
    assert sorted(changed) == sorted(RECORD["corpus_files_changed"])

    removed, added = set(), set()
    for rel in changed:
        base = onto.public_id(rel)
        old_text = subprocess.run(["git", "show", before + ":" + rel],
                                  cwd=str(REPO), capture_output=True,
                                  text=True).stdout
        was = rdflib.Graph()
        was.parse(data=old_text, format="turtle", publicID=base)
        now = onto.parse_source(rdflib.Graph(), REPO / rel, REPO)
        fmt = lambda t: " ".join(x.n3() for x in t)  # noqa: E731
        removed |= {(rel, fmt(t)) for t in set(was) - set(now)}
        added |= {(rel, fmt(t)) for t in set(now) - set(was)}

    assert {(e["file"], e["triple"])
            for e in RECORD["substitutions"]["removed"]} == removed
    assert {(e["file"], e["triple"])
            for e in RECORD["substitutions"]["added"]} == added
    assert len(removed) == len(added) == RECORD["substitutions"]["count"] == 2, (
        "this repair was two substitutions; a third would need its own "
        "justification rather than arriving inside this one")


@needs_repair_record
def test_the_transition_matrix_was_left_frozen():
    """The experiment is not re-run to make it describe a later corpus.

    Its content is a comparison of three checkouts of one commit. Running
    it again against the repaired corpus would produce a file with the
    same name that had measured something else.
    """
    assert MATRIX == _at_tag("config/eol-transition-matrix.json"), (
        "the transition matrix differs from " + BEFORE_TAG)
    assert MATRIX["input_commit"] == RECORD["before_commit"]
    assert MATRIX["path_dependence"]["differ"] is True, (
        "the matrix's original assertion must survive this unchanged")


@needs_repair_record
def test_the_baseline_says_which_corpus_the_matrix_described():
    """A citation across a known gap has to name the gap."""
    m = BASELINE["transition"]["measured"]
    assert m["describes_corpus_at"] == RECORD["before_commit"], (
        "the baseline cites a matrix from an earlier corpus without "
        "saying so")
    repaired = m["corpus_repaired_since"]
    assert repaired["before_tag"] == BEFORE_TAG
    # The tag and the commit its matrix measured are not the same commit:
    # evidence is committed after the input it describes. Citing the tag
    # is accurate only because no Turtle file differs between the two, so
    # that is asserted here rather than left to the record.
    tag_commit = subprocess.run(
        ["git", "rev-parse", BEFORE_TAG + "^{commit}"], cwd=str(REPO),
        capture_output=True, text=True).stdout.strip()
    assert RECORD["before_tag_commit"] == tag_commit
    drift = subprocess.run(
        ["git", "diff", "--name-only", RECORD["before_commit"], tag_commit,
         "--", "*.ttl"], cwd=str(REPO),
        capture_output=True, text=True).stdout.split()
    assert not drift, (
        BEFORE_TAG + " and the commit its matrix measured hold different "
        "corpora, so the tag is not the before-state the diff describes: "
        + str(drift))
    assert repaired["after_commit"] == BASELINE["input_commit"]
    assert repaired["corpus_files_changed"] == RECORD["corpus_files_changed"]
    assert "re-derived" in repaired["verified"]


@needs_repair_record
def test_only_the_measures_the_repair_touches_have_moved():
    """Two triples changed. Everything that does not depend on them
    should be identical to the tagged state, and a repair that moved a
    reasoner verdict would be a different event needing a different
    justification."""
    old = _at_tag("config/semantic-baseline.json")
    assert old, "no baseline at " + BEFORE_TAG

    # Cardinality is unchanged: both substitutions replace a triple.
    for key in ("files_discovered", "files_parsing", "distinct_triples",
                "named_classes", "class_declarations_summed",
                "trigger_statements", "distinct_trigger_objects"):
        assert BASELINE["corpus"][key]["value"] == old["corpus"][key]["value"], (
            key + " moved; this repair substitutes triples and adds none")

    assert BASELINE["reasoner"] == old["reasoner"], (
        "a reasoner measure moved on a two-triple substitution in a FRED "
        "graph outside the BFO layer")

    assert BASELINE["artifacts"] == old["artifacts"], (
        "an unrelated artifact digest moved")

    # The ground digest must move: it covers every triple with no blank
    # node, which is exactly what the substitution changed.
    assert (BASELINE["corpus"]["merged_ground_sha256"]["value"]
            != old["corpus"]["merged_ground_sha256"]["value"]), (
        "the ground digest is unchanged, so either the repair did not "
        "land or the fingerprint cannot see a changed literal")

    # The blank-node fingerprint must NOT move, and that is a claim about
    # how far the repair reached rather than a formality: this graph holds
    # no blank node at all, so neither substituted triple can belong to a
    # component. Movement here would mean the repair touched something
    # nobody described.
    assert (BASELINE["corpus"]["merged_bnode_shape"]["value"]
            == old["corpus"]["merged_bnode_shape"]["value"]), (
        "the blank-node fingerprint moved on a substitution whose four "
        "sides are all IRIs and literals")


@needs_repair_record
def test_the_repaired_file_holds_no_blank_node():
    """Which is what makes the assertion above mean anything.

    If this graph grew a blank node later, the unchanged-fingerprint
    check would still pass while having quietly stopped saying anything.
    """
    import rdflib

    from marep import ontology_source as onto

    rel = "ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl"
    graph = onto.parse_source(rdflib.Graph(), REPO / rel, REPO)
    blank = [t for t in graph if any(isinstance(x, rdflib.BNode) for x in t)]
    assert not blank, (
        "this graph now has blank nodes, so the unchanged blank-node "
        "fingerprint no longer follows from its contents")
