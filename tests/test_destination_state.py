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
    """The baseline must name every group, not a convenient subset."""
    baseline = json.loads(CHECKER.grouping_baseline())
    assert len(baseline) >= 7, f"only {len(baseline)} groups measured: {baseline}"
    assert not [g for g, n in baseline.items() if n == 0], baseline
    assert sum(baseline.values()) >= 160, (
        f"the baseline covers {sum(baseline.values())} files; the corpus is larger")


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
