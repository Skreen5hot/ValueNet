"""The move is evaluated before it happens.

Step 4 passed a gate that could not have failed. Nothing had moved, so every
literal path the gate exercised still existed, and five surfaces that would
break on the first wave went unrecorded until review found them by reading.

`check_destination_state.py` closes that by materialising the destination tree
in a temporary directory and asking each consumer whether it still resolves.
These tests guard the checker itself, because a checker that cannot fail is the
same defect one level up -- and the first version of it had exactly that
problem in miniature: the grouping consumer asserted two of seven groups, so
the other 155 files could have landed anywhere and it would still have printed
OK.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from marep.layout import component, repository_root  # noqa: E402

REPO = repository_root()


def _checker():
    # Through the contract, not by literal path. `ValueNet_code/...` here
    # would break on the marep wave, which is precisely the failure this
    # file's subject was written to detect -- and it would have failed
    # silently, because a test that cannot import its subject looks like a
    # collection error rather than a migration defect.
    path = component("tool.check-destination-state").resolve()
    spec = importlib.util.spec_from_file_location("check_destination_state", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CHECKER = _checker()
ROWS = yaml.safe_load(
    (REPO / "config/move-manifest.yaml").read_text(encoding="utf-8"))["components"]


def test_the_prefix_guard_is_clean_on_the_real_manifest():
    """Every prefix-grouped file is RETAIN today, so nothing should fire."""
    complaints = CHECKER.check_prefix_groups_are_stable(ROWS)
    assert not complaints, "\n".join(complaints)


def test_the_prefix_guard_fires_when_a_prefix_grouped_file_moves():
    """The falsification. Without this the guard above proves nothing.

    `ThatsAllFolks/` groups 130 files by path prefix and declares no
    `group_prefixes_after`. If a later wave moves it, the prefix stops
    matching and every one of those files silently changes group.
    """
    moved = [{"path": "ThatsAllFolks/folk_Honesty.ttl",
              "destination": "ontology/original-valuenet/ThatsAllFolks/folk_Honesty.ttl"}]
    complaints = CHECKER.check_prefix_groups_are_stable(moved)
    assert complaints, (
        "moving a prefix-grouped file raised nothing; the guard is inert")
    assert "thats-all-folks" in complaints[0]


def test_the_grouping_baseline_covers_the_whole_corpus():
    """Every ontology file, and every group still represented.

    The shape changed when the check moved from group totals to a
    per-file map, but the property has not: a baseline naming a
    convenient subset can only prove things about that subset.
    """
    baseline = json.loads(CHECKER.grouping_baseline())
    assert len(baseline) >= 160, f"only {len(baseline)} files measured"
    groups = set(baseline.values())
    assert len(groups) >= 7, f"only {len(groups)} groups: {sorted(groups)}"
    assert not [k for k, v in baseline.items() if not v], (
        "a file with no group is a file the grouping rule did not reach")

def test_every_consumer_snippet_has_its_placeholders_substituted():
    """A placeholder left in the code becomes a NameError the runner counts
    as a broken consumer -- a false alarm, which erodes the check faster than
    a missing one."""
    tokens = ("TOOL_GENERATE_FOLK", "GROUPING_BASELINE",
              "TOOL_IMPORT_BASELINE")
    gen = "ValueNet_code/generate_folk_aligned.py"
    baseline = CHECKER.grouping_baseline()
    tool_baseline = CHECKER.tool_import_baseline()
    for name, snippet in CHECKER.CONSUMERS:
        code = (snippet.replace(tokens[0], gen)
                       .replace(tokens[1], baseline)
                       .replace(tokens[2], tool_baseline))
        left = [t for t in tokens if t in code]
        assert not left, f"{name} still holds {left} after substitution"
        compile(code, f"<{name}>", "exec")


def test_there_are_consumers_to_run():
    assert len(CHECKER.CONSUMERS) >= 8, (
        f"only {len(CHECKER.CONSUMERS)} consumers; the checker is thinning out")


@pytest.mark.slow
@pytest.mark.parametrize("wave", CHECKER.WAVE_ORDER)
def test_every_consumer_resolves_after_each_wave(wave):
    """The check itself, wave by wave. Slow: each run copies the repository
    and parses the BFO tree eight times over."""
    assert CHECKER.main(["--wave", wave]) == 0, (
        f"a consumer breaks once the {wave} wave has run")

def _run_tool_root_consumer(tree: Path) -> subprocess.CompletedProcess:
    """The tool-root consumer alone, against an arbitrary tree."""
    snippet = dict(CHECKER.CONSUMERS)[
        "every tool computes the repository root from its destination"]
    code = CHECKER._LOAD_PRELUDE + snippet.replace(
        "TOOL_IMPORT_BASELINE", "[]")
    return subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True, cwd=str(tree))


def test_the_tool_root_consumer_accepts_a_correct_root(tmp_path: Path):
    (tmp_path / 'config').mkdir()
    (tmp_path / 'config/repository-layout.yaml').write_text('components: []',
                                                            encoding='utf-8')
    (tmp_path / 'tools').mkdir()
    (tmp_path / 'tools/good.py').write_text(
        "import pathlib" + chr(10) +
        "HERE = str(pathlib.Path(__file__).resolve().parents[1])" + chr(10),
        encoding='utf-8')
    r = _run_tool_root_consumer(tmp_path)
    assert r.returncode == 0, r.stderr[-400:]


def test_the_tool_root_consumer_catches_a_wrong_root(tmp_path: Path):
    """The falsification. A tool whose HERE points one level short
    of the root -- the exact defect found in build_move_manifest.py, where
    two dirname calls from tools/marep/ gave repo/tools, a path that
    exists and so fails silently."""
    (tmp_path / 'config').mkdir()
    (tmp_path / 'config/repository-layout.yaml').write_text('components: []',
                                                            encoding='utf-8')
    (tmp_path / 'tools').mkdir()
    (tmp_path / 'tools/bad.py').write_text(
        "import pathlib" + chr(10) +
        "HERE = str(pathlib.Path(__file__).resolve().parents[0])" + chr(10),
        encoding='utf-8')
    r = _run_tool_root_consumer(tmp_path)
    assert r.returncode != 0, 'a wrong HERE raised nothing'
    assert 'bad.py' in r.stderr and 'not the repository root' in r.stderr


def test_the_import_baseline_measures_rather_than_lists():
    """It must name the one genuinely broken tool, and only from
    measurement -- hardcoding the exemption would outlive the defect."""
    baseline = json.loads(CHECKER.tool_import_baseline())
    assert baseline == ['is_v_emo_overlaps.py'], baseline

def test_every_declared_regeneration_is_handled():
    """The guard that keeps the wave honest.

    An allowance with `remove_after_wave` is work the wave owes. If a new
    one is added and REGENERATORS is not updated, the checker would
    materialise a state the plan never intends and report it green --
    which is exactly how folk_aligned.ttl came to carry a header naming a
    generator that had moved. Unhandled is allowed; unnoticed is not, so
    an entry mapped to None still has to be written down."""
    from marep import layout
    owed = {a.get('id') for a in layout.path_allowances()
            if a.get('remove_after_wave')}
    missing = sorted(owed - set(CHECKER.REGENERATORS))
    assert not missing, (
        f'these allowances declare remove_after_wave but no REGENERATORS '
        f'entry says how, or that it is manual: {missing}')


def test_owed_regenerations_track_the_wave():
    """Nothing is owed before its wave; both are owed at the end."""
    assert CHECKER.owed_regenerations('bfo') != []
    early = {a.get('id') for a in CHECKER.owed_regenerations('bfo')}
    assert 'folk-aligned-generated-header-generator' not in early, (
        'the folk header is owed only after the original-valuenet wave')
    late = {a.get('id') for a in CHECKER.owed_regenerations(None)}
    assert 'folk-aligned-generated-header-generator' in late
    assert 'cco-manifest-generator-path' in late


# ======================================================================
# materialising a tree that has already been partly moved
# ======================================================================

MOVED_ROW = {"path": "src/moved.ttl", "destination": "dst/moved.ttl",
             "wave": "tests"}
RETAINED_ROW = {"path": "keep/stays.ttl", "destination": "RETAIN",
                "wave": None}


def _tree(root: Path, *rel: str) -> Path:
    for r in rel:
        f = root / r
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("# " + r + "\n", encoding="utf-8")
    return root


def test_a_completed_move_is_read_from_its_destination(tmp_path: Path):
    """The blocking defect: after a real wave the source is gone.

    The first version read only the manifest's source path and skipped the
    row when it was absent. On a pristine tree that is invisible. After the
    BFO wave it would have silently omitted all 42 moved files and called
    the remaining 288 a complete tree.
    """
    src = _tree(tmp_path / "repo", "dst/moved.ttl", "keep/stays.ttl")
    out = tmp_path / "out"
    moved = CHECKER.materialise([MOVED_ROW, RETAINED_ROW], "tests", out,
                                source_root=src)
    assert moved == 1
    assert (out / "dst/moved.ttl").is_file(), "the moved file was skipped"
    assert (out / "keep/stays.ttl").is_file()


def test_an_unrun_wave_places_a_moved_file_back_at_its_source(tmp_path: Path):
    """Content comes from wherever it is; position comes from the wave."""
    src = _tree(tmp_path / "repo", "dst/moved.ttl", "keep/stays.ttl")
    out = tmp_path / "out"
    moved = CHECKER.materialise([MOVED_ROW, RETAINED_ROW], "bfo", out,
                                source_root=src)
    assert moved == 0
    assert (out / "src/moved.ttl").is_file()
    assert not (out / "dst/moved.ttl").exists()


def test_a_row_present_at_both_paths_is_refused(tmp_path: Path):
    """An interrupted move left a copy; neither path is authoritative."""
    src = _tree(tmp_path / "repo", "src/moved.ttl", "dst/moved.ttl",
                "keep/stays.ttl")
    with pytest.raises(CHECKER.MaterialiseError) as exc:
        CHECKER.materialise([MOVED_ROW, RETAINED_ROW], "tests",
                            tmp_path / "out", source_root=src)
    assert "both" in str(exc.value)


def test_a_row_present_at_neither_path_is_refused(tmp_path: Path):
    """The count assertion: a row that reaches the tree by no path is a
    file the check never looked at."""
    src = _tree(tmp_path / "repo", "keep/stays.ttl")
    with pytest.raises(CHECKER.MaterialiseError) as exc:
        CHECKER.materialise([MOVED_ROW, RETAINED_ROW], "tests",
                            tmp_path / "out", source_root=src)
    assert "neither" in str(exc.value)


def test_the_real_tree_materialises_every_manifest_row(tmp_path: Path):
    """330 rows in, 330 files out, with nothing quietly dropped."""
    out = tmp_path / "out"
    CHECKER.materialise(ROWS, None, out)
    written = sum(1 for f in out.rglob("*") if f.is_file())
    assert written == len(ROWS), f"{written} files for {len(ROWS)} rows"


# ======================================================================
# grouping, per file rather than per group
# ======================================================================


def test_a_balanced_swap_changes_no_count_and_is_still_caught():
    """The blocking defect: a Counter of group totals cannot see this.

    Two files exchanging groups leaves every total identical, so the
    aggregate comparison passes while two files have been reclassified.
    """
    import collections

    want = {"a.ttl": "bfo-layer", "b.ttl": "thats-all-folks"}
    got = {"a.ttl": "thats-all-folks", "b.ttl": "bfo-layer"}
    assert (collections.Counter(want.values())
            == collections.Counter(got.values())), (
        "the premise of this test is that the counts agree")
    changed = CHECKER.grouping_delta(want, got)
    assert len(changed) == 2, changed


def test_the_grouping_baseline_is_keyed_per_file():
    baseline = json.loads(CHECKER.grouping_baseline())
    assert len(baseline) >= 160, f"{len(baseline)} files measured"
    assert all(isinstance(v, str) for v in baseline.values())
    assert "BFO/bfo-core.ttl" in baseline, sorted(baseline)[:5]


def test_identity_survives_the_move():
    """A file keeps one key either side of the move, or the two maps
    cannot be compared at all."""
    ident = CHECKER.identity_map(ROWS)
    moved = [r for r in ROWS if r["destination"] != "RETAIN"]
    assert moved
    for r in moved[:20]:
        assert ident[r["path"]] == ident[r["destination"]] == r["path"]


# ======================================================================
# obligations a completed wave owes
# ======================================================================


def test_an_undischargeable_obligation_fails_rather_than_notes(tmp_path: Path,
                                                               monkeypatch):
    """The blocking defect: printed as a note beside a green verdict.

    An expired obligation nobody discharged leaves the tree in a state the
    contract itself calls invalid. Reporting success there is how the CCO
    manifest kept naming a generator that had moved.
    """
    owed = CHECKER.owed_regenerations(None)
    assert owed, "nothing is owed, so this proves nothing"
    # Every obligation, not just the first: leaving the others live made
    # this test resolve a generator under an empty tmp_path and fail on
    # the resolver instead of on the property under test.
    for a in owed:
        monkeypatch.setitem(CHECKER.REGENERATORS, a["id"], None)
    unperformed = CHECKER.regenerate(tmp_path, None)
    assert unperformed, "an undischargeable obligation returned nothing"
    assert owed[0]["id"] in unperformed[0]


def test_the_cco_obligation_is_dischargeable():
    """Not None. Rebuilding the extract needs the pinned upstream release,
    but the obligation is only about provenance."""
    spec = CHECKER.REGENERATORS["cco-manifest-generator-path"]
    assert spec is not None, (
        "the declared remedy was inert: regenerating re-emitted the same "
        "stale path, so the obligation could never be discharged")
    assert "--refresh-provenance" in spec[1]

def test_the_real_tree_round_trips_through_a_partly_moved_state(tmp_path: Path):
    """The scenario the checker exists for, on the actual manifest.

    Stage one is this repository with the BFO wave applied: 42 sources
    gone, 42 destinations present. Stage two materialises *from* that,
    which is what the checker will have to do the morning after the wave
    actually runs. Every row must still be found, from whichever of its
    two paths now holds it."""
    stage1 = tmp_path / 'after-bfo'
    CHECKER.materialise(ROWS, 'bfo', stage1)
    assert not (stage1 / 'BFO/valuenet-core.ttl').exists()
    assert (stage1 / 'ontology/bfo/core/valuenet-core.ttl').is_file()

    # Read back from the moved tree, at the same wave and at the last one.
    for wave in ('bfo', None):
        out = tmp_path / ('from-partial-' + str(wave))
        CHECKER.materialise(ROWS, wave, out, source_root=stage1)
        written = sum(1 for f in out.rglob('*') if f.is_file())
        assert written == len(ROWS), (
            f'{written} of {len(ROWS)} rows survived a read from a '
            f'partly moved tree at wave {wave!r}')
