"""The move manifest has to describe this repository, exactly once each.

`config/move-manifest.yaml` is generated, and a generated file is easy to
trust for the wrong reason: it was produced by a program, so it looks like a
measurement. It is a measurement of whatever the program happened to classify,
and four separate defects in the builder were found by reading rather than by
running -- it wrote before failing, produced destinations like `/.ttl`, gave
tests placeholder destinations, and ignored git's exit codes.

What is asserted here is the manifest's contract with the repository: every
tracked file appears exactly once, every row has a disposition somebody chose,
the waves partition the moves, and no upstream-origin file moves at all.

The last one is the plan's rule and the easiest to break by accident. The fork
may reorganize what it wrote. Relocating a file that came from upstream turns
every future merge into a conflict, and the conflict appears in someone else's
work long after the commit that caused it.
"""

from __future__ import annotations

import posixpath
import subprocess
import sys

import pytest

yaml = pytest.importorskip("yaml")

from marep import layout  # noqa: E402

#: This module asserts properties of the repository the manifest
#: describes: which files git tracks, where they are now, and which
#: literals are still allowed. A materialised copy has no git and has
#: already had waves applied, so every one of these would fail there for
#: reasons that say nothing about the code under test.
pytestmark = pytest.mark.repository

REPO = layout.repository_root()


def _validator():
    import importlib.util
    path = layout.component("tool.validate-migration-state").resolve()
    spec = importlib.util.spec_from_file_location("validate_migration_state", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VALIDATOR = _validator()

#: From the freeze tag once it exists. The working copy is exactly what a
#: check must not trust after the freeze: an edit to the manifest could make a
#: broken tree look valid, which is what the tag is for.
MANIFEST_TEXT, MANIFEST_SOURCE = VALIDATOR.frozen_text("config/move-manifest.yaml")
ROWS = yaml.safe_load(MANIFEST_TEXT)["components"]

WAVES = ["bfo", "marep", "original-valuenet", "architecture", "tests"]
ORIGINS = {"upstream-valuenet", "fork", "external-cco", "external-bfo"}
MAINTENANCE = {"unchanged", "locally-modified", "generated"}

MOVES = [r for r in ROWS if r["destination"] != "RETAIN"]


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=str(REPO),
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return [p for p in out.stdout.splitlines() if p]


# ======================================================================
# coverage: every file, exactly once
# ======================================================================


def test_every_frozen_row_is_present_at_exactly_one_of_its_paths():
    """The validator's XOR rule, applied to coverage.

    Comparing tracked files against source paths alone was correct exactly
    while nothing had moved. After the bfo wave those 42 files sit at their
    destinations, and this reported 42 missing and 42 extra while the
    transition validator -- reading the same frozen manifest and applying
    the same rule -- reported none. A coverage check that contradicts the
    validator on a state the plan requires is not a second opinion, it is a
    false alarm that would have to be ignored five times.

    A RETAIN row has one legal location. A MOVE row has two, and exactly
    one of them must hold the file: neither means it is lost, both mean an
    interrupted move left a copy and no path is authoritative.
    """
    files = set(tracked())
    problems: list[str] = []
    represented: set[str] = set()
    seen: list[str] = []

    for r in ROWS:
        src, dst = r["path"], r["destination"]
        seen.append(src)
        candidates = [src] if dst == "RETAIN" else [src, dst]
        here = [c for c in candidates if c in files]
        if len(here) == 1:
            represented.add(here[0])
        elif not here:
            problems.append(
                f"{src}: present at neither its source nor {dst}")
        else:
            problems.append(
                f"{src}: present at both its source and {dst}; an "
                f"interrupted move left a copy behind")

    # Files that existed at the freeze, not every file that will ever
    # exist. The manifest records one migration; holding the live tree to its
    # 335 rows fails on the first file added afterwards.
    frozen_files = VALIDATOR.frozen_snapshot()
    extra = sorted((files & frozen_files) - represented)
    dupes = sorted({p for p in seen if seen.count(p) > 1})
    assert not problems, problems[:10]
    assert not extra, f"tracked at the freeze but in no manifest row: {extra[:10]}"
    assert not dupes, f"classified twice: {dupes}"


def test_coverage_and_the_validator_agree_about_a_completed_wave():
    """The falsification, and the reason the rewrite was needed.

    Run the same two checks over a synthetic tree with the bfo wave applied.
    The old coverage rule called that state 42-missing-and-42-extra while
    the validator called it valid; they must now agree, because they are
    checking the same property from the same manifest.
    """
    moved = {r["destination"] if r.get("wave") == "bfo" and
             r["destination"] != "RETAIN" else r["path"] for r in ROWS}

    assert VALIDATOR.completed_waves(ROWS, moved) == ["bfo"], (
        "the synthetic tree does not represent a completed bfo wave")
    assert VALIDATOR.validate(ROWS, moved, "bfo") == [], (
        "the validator rejects a correctly completed wave")

    problems = []
    represented = set()
    for r in ROWS:
        candidates = ([r["path"]] if r["destination"] == "RETAIN"
                      else [r["path"], r["destination"]])
        here = [c for c in candidates if c in moved]
        if len(here) != 1:
            problems.append(r["path"])
        else:
            represented.add(here[0])
    assert not problems, (
        f"{len(problems)} row(s) rejected on a state the validator accepts: "
        f"{problems[:6]}")
    assert not (moved - represented)


def test_nothing_is_unassigned():
    """The builder refuses to write these, so finding one means the file on
    disk is older than the rules that produced it."""
    unassigned = [r["path"] for r in ROWS if r["destination"] == "UNASSIGNED"]
    assert not unassigned, unassigned


# ======================================================================
# dispositions
# ======================================================================


def test_no_destination_collides():
    seen: dict[str, str] = {}
    clashes = []
    for r in MOVES:
        d = r["destination"]
        if d in seen:
            clashes.append(f"{r['path']} and {seen[d]} both land on {d}")
        seen[d] = r["path"]
    assert not clashes, clashes


def test_no_move_is_a_no_op():
    """A row whose destination equals its source is not a move.

    It also breaks the transition validator, whose rule is that exactly one
    of source and destination is tracked -- and here they are the same file.
    """
    same = [r["path"] for r in MOVES if r["destination"] == r["path"]]
    assert not same, same


def test_no_move_renames_or_changes_extension():
    """An undeclared rename inside a relocation is how content goes missing."""
    problems = []
    for r in MOVES:
        src, dst = posixpath.basename(r["path"]), posixpath.basename(r["destination"])
        if src != dst:
            problems.append(f"{r['path']} -> {r['destination']}")
    assert not problems, problems


def test_no_destination_escapes_the_repository():
    bad = [r["path"] for r in MOVES
           if posixpath.isabs(r["destination"])
           or ".." in r["destination"].split("/")]
    assert not bad, bad


# ======================================================================
# waves partition the moves
# ======================================================================


def test_every_move_belongs_to_exactly_one_wave():
    orphans = [r["path"] for r in MOVES if r.get("wave") not in WAVES]
    assert not orphans, f"moves outside every wave: {orphans[:10]}"


def test_no_retained_file_is_assigned_a_wave():
    """A wave on a RETAIN row would schedule a move that never happens."""
    strays = [r["path"] for r in ROWS
              if r["destination"] == "RETAIN" and r.get("wave")]
    assert not strays, strays


def test_the_waves_account_for_every_move():
    counted = sum(1 for r in ROWS if r.get("wave") in WAVES)
    assert counted == len(MOVES), f"{counted} in waves, {len(MOVES)} moves"


# ======================================================================
# provenance
# ======================================================================


@pytest.mark.parametrize("field,allowed",
                         [("origin", ORIGINS), ("maintenance", MAINTENANCE)])
def test_provenance_values_are_from_the_declared_vocabulary(field, allowed):
    bad = sorted({r[field] for r in ROWS} - allowed)
    assert not bad, bad


def test_no_upstream_file_moves():
    """The plan's rule, and the one with consequences outside this repository.

    The fork may reorganize what it wrote. Moving a file that came from
    upstream turns every subsequent merge into a conflict, and that conflict
    surfaces in someone else's work long after this commit.
    """
    moved = [r["path"] for r in MOVES if r["origin"] == "upstream-valuenet"]
    assert not moved, moved


def test_generated_files_say_what_generated_them():
    """`generated` is a claim about maintenance, so it needs a referent."""
    missing = [r["path"] for r in ROWS
               if r["maintenance"] == "generated" and not r.get("generated_from")]
    assert not missing, missing


def test_generated_sources_exist():
    """A `generated_from` names either a file on disk or a declared tool.

    The two are spelled differently: a tool reference is `tool:<slug>`
    while the component that resolves it is `tool.<slug>`. The colon is
    what distinguishes a tool from a path, so the separator cannot simply
    be unified; the mapping is done here, once, in the open.
    """
    absent = []
    for r in ROWS:
        src = r.get("generated_from")
        if not src:
            continue
        if src.startswith("tool:"):
            cid = "tool." + src.split(":", 1)[1]
            try:
                layout.component(cid).resolve()
            except layout.LayoutError as exc:
                absent.append(f"{r['path']} is generated by {src}, "
                              f"which resolves to nothing: {exc}")
        elif not (REPO / src).exists():
            absent.append(f"{r['path']} is generated from {src}, "
                          f"which is absent")
    assert not absent, absent


# ======================================================================
# the builder fails closed
# ======================================================================


def _builder():
    import importlib.util
    path = layout.component("tool.build-move-manifest").resolve()
    spec = importlib.util.spec_from_file_location("build_move_manifest", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_an_unknown_path_is_unassigned_rather_than_guessed():
    """The builder must not invent a destination for a file no rule covers.

    Guessing is what produced destinations like `/.ttl`: a prefix-stripping
    rule that matched something it was never meant to.
    """
    b = _builder()
    assert b.destination("some/unrecognized/thing.txt", "fork") == "UNASSIGNED"


def test_a_test_module_with_no_group_is_unassigned():
    """Placeholder destinations for tests were a real defect: every unmapped
    test module quietly landed in one bucket."""
    b = _builder()
    assert b.destination("tests/test_not_in_any_group.py", "fork") == "UNASSIGNED"


def test_conftest_and_support_are_retained_not_moved_in_place():
    b = _builder()
    for name in ("tests/conftest.py", "tests/_support.py"):
        assert b.destination(name, "fork") == "RETAIN", name


def test_malformed_destinations_are_rejected():
    """`validate` is what stands between a bad rule and a written manifest."""
    b = _builder()
    cases = [
        ({"path": "a/x.ttl", "destination": "b/x.owl"}, "extension changed"),
        ({"path": "a/x.ttl", "destination": "b/y.ttl"}, "undeclared rename"),
        ({"path": "a/x.ttl", "destination": "a/x.ttl"}, "destination equals source"),
        ({"path": "a/x.ttl", "destination": "/abs/x.ttl"}, "unsafe destination"),
        ({"path": "a/x.ttl", "destination": "../x.ttl"}, "unsafe destination"),
    ]
    for row, expected in cases:
        problems = b.validate([row])
        assert problems, f"{row['destination']} was accepted"
        assert any(expected in p for p in problems), (row, problems)


def test_two_rows_landing_on_one_destination_are_rejected():
    b = _builder()
    problems = b.validate([{"path": "a/x.ttl", "destination": "c/x.ttl"},
                           {"path": "b/x.ttl", "destination": "c/x.ttl"}])
    assert any("collides" in p for p in problems), problems


def test_a_destination_in_no_wave_is_named_not_ignored():
    b = _builder()
    assert b.wave_of("nowhere/x.ttl") == "UNASSIGNED-WAVE"
    assert b.wave_of("RETAIN") is None


# ======================================================================
# transition states
# ======================================================================


def test_the_transition_state_is_valid_now():
    """Called the way the freeze requires, in whatever state the tree is in.

    `main([])` was correct exactly until the tag existed, and then the
    validator began refusing to read the mutable manifest -- so this test
    failed in the state it is supposed to certify. It passed only because
    the gate that certified the freeze ran before the tag was created, which
    is the same defect as every other check in this repository that could
    not have failed when it ran.

    The wave is derived, not passed in. Asking the caller which wave has run
    would make the assertion depend on the answer it is verifying.
    """
    argv = []
    if VALIDATOR.frozen_exists():
        argv = ["--frozen-ref", VALIDATOR.FREEZE_TAG]
        wave = VALIDATOR.current_wave(ROWS, VALIDATOR.tracked())
        if wave:
            argv += ["--wave", wave]
    assert VALIDATOR.main(argv) == 0, argv


def test_the_manifest_being_checked_is_the_frozen_one():
    """Once the tag exists, nothing here reads the working copy."""
    if VALIDATOR.frozen_exists():
        assert MANIFEST_SOURCE.endswith("@" + VALIDATOR.FREEZE_TAG), MANIFEST_SOURCE
    else:
        assert "working copy" in MANIFEST_SOURCE, MANIFEST_SOURCE


def test_the_working_manifest_still_matches_the_frozen_one():
    """They may differ only if somebody edited a file that is frozen.

    The validator prints a note when they diverge; a note is not a gate, and
    the manifest is not supposed to change again.
    """
    if not VALIDATOR.frozen_exists():
        pytest.skip("nothing is frozen yet")
    working = (REPO / "config/move-manifest.yaml").read_text(encoding="utf-8")
    assert working.replace("\r\n", "\n") == MANIFEST_TEXT.replace("\r\n", "\n"), (
        "the working manifest differs from the frozen one; the freeze says "
        "this was the last generation")


# ======================================================================
# completed waves are read off the tree
# ======================================================================


SYNTH = [
    {"path": "a/one.ttl", "destination": "x/one.ttl", "wave": "bfo"},
    {"path": "a/two.ttl", "destination": "x/two.ttl", "wave": "bfo"},
    {"path": "b/three.ttl", "destination": "y/three.ttl", "wave": "marep"},
    {"path": "keep/four.ttl", "destination": "RETAIN", "wave": None},
]


def test_no_wave_is_complete_before_anything_moves():
    files = {"a/one.ttl", "a/two.ttl", "b/three.ttl", "keep/four.ttl"}
    assert VALIDATOR.completed_waves(SYNTH, files) == []
    assert VALIDATOR.current_wave(SYNTH, files) is None


def test_a_finished_wave_is_reported_complete():
    """The falsification: without this, completed_waves could always be []."""
    files = {"x/one.ttl", "x/two.ttl", "b/three.ttl", "keep/four.ttl"}
    assert VALIDATOR.completed_waves(SYNTH, files) == ["bfo"]
    assert VALIDATOR.current_wave(SYNTH, files) == "bfo"


def test_a_half_finished_wave_is_not_complete():
    """One file moved is not a wave, and must not read as one."""
    files = {"x/one.ttl", "a/two.ttl", "b/three.ttl", "keep/four.ttl"}
    assert VALIDATOR.completed_waves(SYNTH, files) == []


def test_a_partial_wave_stops_the_run():
    """A later wave cannot be complete while an earlier one is half done.

    Reporting `marep` as finished with `bfo` outstanding would let the
    lifecycle checks retire allowances for a move that has not happened.
    """
    files = {"x/one.ttl", "a/two.ttl", "y/three.ttl", "keep/four.ttl"}
    assert VALIDATOR.completed_waves(SYNTH, files) == []


def test_every_wave_complete_reports_every_wave():
    files = {"x/one.ttl", "x/two.ttl", "y/three.ttl", "keep/four.ttl"}
    assert VALIDATOR.completed_waves(SYNTH, files) == ["bfo", "marep"]


#: One row and the snapshot it was frozen from. Supplied explicitly:
#: `validate` otherwise measures a one-row manifest against the real
#: 335-file tag and returns 334 coverage complaints, which satisfies any
#: bare `assert problems` whatever the rule under test does.
ONE_ROW = [{"path": "src/a.ttl", "destination": "dst/a.ttl", "wave": "bfo"}]
ONE_SNAPSHOT = {"src/a.ttl"}


def test_a_move_completed_before_its_wave_is_a_violation():
    """Omitting --wave must mean zero moves completed, not skip the check."""
    problems = VALIDATOR.validate(ONE_ROW, files={"dst/a.ttl"},
                                  current_wave=None, frozen=ONE_SNAPSHOT)
    assert any("has not run" in p for p in problems), problems


def test_a_file_still_at_its_source_after_its_wave_is_a_violation():
    problems = VALIDATOR.validate(ONE_ROW, files={"src/a.ttl"},
                                  current_wave="bfo", frozen=ONE_SNAPSHOT)
    assert any("still at its" in p for p in problems), problems


def test_a_file_at_both_paths_is_a_violation():
    """The XOR rule: exactly one of source and destination is tracked.

    Asserted on the specific diagnostic. `assert problems` alone was
    satisfied by the coverage noise a one-row manifest generated against the
    real snapshot, and would have gone on passing with the XOR check deleted.
    """
    problems = VALIDATOR.validate(
        ONE_ROW, files={"src/a.ttl", "dst/a.ttl"},
        current_wave="bfo", frozen=ONE_SNAPSHOT)
    assert any("both" in p for p in problems), (
        "a file present at both paths was accepted: " + str(problems))


def test_the_clean_one_row_case_produces_no_problems():
    """The control. Without it the three above could all pass because every
    input produces complaints, which is how the XOR test became vacuous."""
    problems = VALIDATOR.validate(ONE_ROW, files={"dst/a.ttl"},
                                  current_wave="bfo", frozen=ONE_SNAPSHOT)
    assert problems == [], problems


# ======================================================================
# fail-closed generation, exercised rather than inspected
# ======================================================================


SENTINEL = b"# sentinel: this manifest must survive a refused run\n"


def _tiny_repo(tmp_path):
    """A git repository the builder can classify, plus one file it cannot."""
    import shutil

    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    (root / "out").mkdir()
    shutil.copy2(REPO / "config/repository-layout.yaml",
                 root / "config/repository-layout.yaml")
    tool = layout.component("tool.build-move-manifest").resolve()
    shutil.copy2(tool, root / "build_move_manifest.py")
    (root / "out/manifest.yaml").write_bytes(SENTINEL)

    def git(*args):
        r = subprocess.run(["git", *args], cwd=str(root),
                           capture_output=True, text=True)
        assert r.returncode == 0, (args, r.stderr)
        return r.stdout

    git("init", "-q")
    git("config", "user.email", "t@example.invalid")
    git("config", "user.name", "t")
    git("add", "-A")
    git("commit", "-qm", "seed")
    # Provenance is derived against upstream/main; without it the builder
    # refuses for the wrong reason and this test would prove nothing.
    #
    # The ref points at the seed commit, before the unclassifiable file
    # exists. Pointing it at a commit containing everything made every
    # file upstream-origin, and upstream files are RETAIN -- so the run
    # succeeded with 0 UNASSIGNED and the fixture proved nothing.
    git("update-ref", "refs/remotes/upstream/main", "HEAD")
    return root, git


def _add_unclassifiable(root, git):
    """A name no rule in the builder covers, added after the seed."""
    (root / "unclassifiable.xyz").write_text("x", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "add unclassifiable")


def test_the_builder_refuses_to_write_when_a_file_is_unassigned(tmp_path):
    """Fail-closed, exercised end to end.

    An earlier version of this builder wrote the manifest and then reported
    the failure, so a refused run still replaced a good file. Asserting that
    `validate()` returns problems does not catch that; only running it and
    looking at the bytes does.
    """
    root, git = _tiny_repo(tmp_path)
    _add_unclassifiable(root, git)
    r = subprocess.run([sys.executable, "build_move_manifest.py",
                        "-o", "out/manifest.yaml"],
                       cwd=str(root), capture_output=True, text=True)
    assert r.returncode != 0, (
        "the builder exited 0 with an unclassified file:\n" + r.stdout)
    assert "UNASSIGNED" in r.stdout, r.stdout
    assert (root / "out/manifest.yaml").read_bytes() == SENTINEL, (
        "a refused run replaced the existing manifest")


def test_the_builder_writes_when_everything_classifies(tmp_path):
    """The falsification: without it, a builder that always refused would
    pass the test above."""
    root, git = _tiny_repo(tmp_path)
    r = subprocess.run([sys.executable, "build_move_manifest.py",
                        "-o", "out/manifest.yaml"],
                       cwd=str(root), capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (root / "out/manifest.yaml").read_bytes() != SENTINEL, (
        "the builder reported success without writing")


# ======================================================================
# the freeze query works where there is no git
# ======================================================================


def _tree_without_git(tmp_path):
    """A tree the validator can import into, with no repository under it."""
    import shutil

    root = tmp_path / "nogit"
    (root / "config").mkdir(parents=True)
    (root / "probe").mkdir()
    shutil.copy2(REPO / "config/repository-layout.yaml",
                 root / "config/repository-layout.yaml")
    shutil.copytree(REPO / "marep", root / "marep",
                    ignore=shutil.ignore_patterns("__pycache__"))
    # Copied to a neutral name. Writing the tool's real path into the
    # probe below would put a literal that moves into this module and make
    # the coverage check demand an allowance for a string used only to
    # locate a temporary copy.
    shutil.copy2(layout.component("tool.validate-migration-state").resolve(),
                 root / "probe/validator_probe.py")
    return root


PROBE = (
    "import importlib.util;"
    "spec=importlib.util.spec_from_file_location("
    "'v','probe/validator_probe.py');"
    "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
    "print(m.in_git_work_tree(), m.frozen_exists(), "
    "m.frozen_text('config/repository-layout.yaml')[1])"
)


def test_the_freeze_query_answers_no_where_there_is_no_git(tmp_path):
    """A marker deselects tests; it does not stop a module being imported.

    `frozen_exists()` runs at import in three repository-marked modules. In
    a materialised copy there is no .git, `sh` failed loudly as it should on
    the command line, and the exception took the entire collection down
    before pytest could deselect anything -- so every wave reported "no
    tests ran" and the gate failed for a reason that had nothing to do with
    the move.

    Outside a repository the honest answer is that no tag exists, and the
    caller falls back to the working copy.
    """
    root = _tree_without_git(tmp_path)
    r = subprocess.run([sys.executable, "-c", PROBE], cwd=str(root),
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-600:]
    in_tree, frozen, source = r.stdout.split(None, 2)
    assert in_tree == "False", r.stdout
    assert frozen == "False", r.stdout
    assert "working copy" in source, r.stdout


def test_a_corrupt_repository_raises_rather_than_reading_as_unfrozen(tmp_path):
    """The falsification for the failure mode the first fix had.

    `in_git_work_tree` returned False for every non-zero exit, so a
    repository git could not read was indistinguishable from no repository
    at all: `frozen_exists()` answered no and `frozen_text()` quietly
    returned the mutable working manifest -- the one thing the freeze
    exists to stop anybody trusting.

    Both cases exit 128, and their messages differ only in wording, so the
    discriminator cannot be the message. It is whether the marker is there:
    a `.git` pointing at a directory that does not exist is a broken
    repository, and the only honest answer is to refuse.
    """
    root = _tree_without_git(tmp_path)
    (root / ".git").write_text("gitdir: /nonexistent/definitely/not/here" + chr(10),
                               encoding="utf-8")
    r = subprocess.run([sys.executable, "-c", PROBE], cwd=str(root),
                       capture_output=True, text=True)
    assert r.returncode != 0, (
        "a corrupt repository was accepted:" + chr(10) + r.stdout)
    combined = r.stdout + r.stderr
    assert "cannot read this repository" in combined, combined[-600:]
    assert "False" not in r.stdout, (
        "the probe answered rather than refusing: " + r.stdout)


def test_an_absent_marker_and_a_broken_one_are_told_apart(tmp_path):
    """Both git invocations exit 128. Only one of them means 'not frozen'."""
    clean = _tree_without_git(tmp_path / "a")
    broken = _tree_without_git(tmp_path / "b")
    (broken / ".git").write_text("gitdir: /nonexistent" + chr(10), encoding="utf-8")

    rc_clean = subprocess.run([sys.executable, "-c", PROBE], cwd=str(clean),
                              capture_output=True, text=True)
    rc_broken = subprocess.run([sys.executable, "-c", PROBE], cwd=str(broken),
                               capture_output=True, text=True)
    assert rc_clean.returncode == 0 and "False False" in rc_clean.stdout
    assert rc_broken.returncode != 0


def test_this_repository_is_a_work_tree_and_knows_it():
    """The falsification: in_git_work_tree() returning False everywhere
    would make the freeze silently optional."""
    assert VALIDATOR.in_git_work_tree() is True
    assert VALIDATOR.frozen_exists() is True, (
        "the freeze tag is not visible from this repository")


# ======================================================================
# coverage is about the migration, not about the repository forever
# ======================================================================

#: A frozen manifest small enough to reason about, with two moved rows
#: and one retained, so a coverage rule can be caught dropping either.
SNAPSHOT = {'src/one.ttl', 'src/two.ttl', 'keep/three.ttl'}
TINY = [
    {'path': 'src/one.ttl', 'destination': 'dst/one.ttl', 'wave': 'bfo'},
    {'path': 'src/two.ttl', 'destination': 'dst/two.ttl', 'wave': 'bfo'},
    {'path': 'keep/three.ttl', 'destination': 'RETAIN', 'wave': None},
]
MOVED = {'dst/one.ttl', 'dst/two.ttl', 'keep/three.ttl'}


def test_a_file_created_after_the_freeze_is_accepted():
    """The manifest records one migration, not the repository forever.

    Held to the live tree, the first file added after step 12 would fail
    a migration already signed off. Calls validate() rather than checking
    a set expression, so it still means something if the implementation
    changes underneath it."""
    live = MOVED | {'created/after/the/freeze.txt'}
    problems = VALIDATOR.validate(TINY, live, 'bfo', frozen=SNAPSHOT)
    assert problems == [], problems


def test_an_omitted_moved_row_is_caught():
    """The defect the earlier rule could not see.

    Intersecting live paths with the frozen snapshot dropped every
    completed move before comparing -- source gone from the tree,
    destination never in the snapshot -- so a moved row could be deleted
    from the manifest unnoticed. Row count is held constant by
    substituting a different row, so this cannot pass on a count check."""
    without_one = [r for r in TINY if r['path'] != 'src/one.ttl']
    without_one.append(
        {'path': 'keep/four.ttl', 'destination': 'RETAIN', 'wave': None})
    assert len(without_one) == len(TINY)
    problems = VALIDATOR.validate(
        without_one, MOVED | {'keep/four.ttl'}, 'bfo', frozen=SNAPSHOT)
    assert any('src/one.ttl' in p for p in problems), (
        'a moved row was dropped from the manifest and coverage did not '
        'notice: ' + str(problems))


def test_a_manifest_row_for_a_file_that_never_existed_is_caught():
    """The other direction: the manifest may not invent rows."""
    invented = TINY + [
        {'path': 'src/ghost.ttl', 'destination': 'dst/ghost.ttl',
         'wave': 'bfo'}]
    problems = VALIDATOR.validate(
        invented, MOVED | {'dst/ghost.ttl'}, 'bfo', frozen=SNAPSHOT)
    assert any('ghost' in p for p in problems), problems
