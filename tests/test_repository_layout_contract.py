"""The layout contract has to be true about this repository.

`config/repository-layout.yaml` is the single place that says where things
are, where they are going, and which literal paths are allowed to survive the
move. Every consumer trusts it. Nothing checked it.

The allowance list is the part that most needs checking, because it is a list
of exceptions and a list of exceptions decays in two directions at once. An
entry that no longer matches anything is an exception granted for nothing, and
it reads as coverage. An occurrence nobody wrote an entry for is a path that
will break in a wave with no record saying who owns the fix. The first kind is
silent; the second is worse, because the check passes and the file breaks
anyway.

So both directions are asserted: every allowance matches a real occurrence,
and every real occurrence has exactly one allowance.

**Scope.** Executable and generated files -- `.py`, `.json`, `.yaml`, `.ttl`
and the config extensions. Prose documents are excluded and counted instead,
because a sentence in a review document describing where a file was is a
statement about the past, and rewriting it would falsify the record. Step 12
of the plan checks documentation links. The count is asserted so the exclusion
cannot quietly grow.
"""

from __future__ import annotations

import re
import subprocess

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
CONTRACT = yaml.safe_load(
    (REPO / "config/repository-layout.yaml").read_text(encoding="utf-8"))
COMPONENTS = CONTRACT["components"]
ALLOWANCES = CONTRACT["path_allowances"]

MANIFEST = yaml.safe_load(
    (REPO / "config/move-manifest.yaml").read_text(encoding="utf-8"))["components"]
MOVING = {r["path"]: r for r in MANIFEST if r["destination"] != "RETAIN"}

WAVES = ["bfo", "marep", "original-valuenet", "architecture", "tests"]

#: The resolver, the contract and the generated manifest name paths because
#: that is their job. Everything else has to justify it.
EXEMPT = {"config/repository-layout.yaml", "config/move-manifest.yaml",
          "marep/layout.py"}
IN_SCOPE = (".py", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".ttl")


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=str(REPO),
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    # Split on newlines, not whitespace. `BFOizing ValueNet.md` has a
    # space in it, and .split() turned one tracked file into two paths,
    # neither of which exists.
    return [p for p in out.stdout.splitlines() if p]


def occurrences(suffixes=IN_SCOPE) -> set[tuple[str, str]]:
    """Every (file, moving-path) pair, for files of the given kinds."""
    found = set()
    for f in tracked():
        if f in EXEMPT or not f.endswith(suffixes):
            continue
        text = (REPO / f).read_text(encoding="utf-8", errors="replace")
        for m in MOVING:
            if m in text:
                found.add((f, m))
    return found


def covered_by(a: dict, f: str, m: str, text: str) -> bool:
    if a["file"] != f:
        return False
    if a.get("literal"):
        return a["literal"] == m
    return bool(re.search(a["pattern"], text))


# ======================================================================
# components
# ======================================================================


def test_every_component_resolves():
    for c in COMPONENTS:
        layout.component(c["id"]).resolve()


def test_component_ids_are_unique():
    ids = [c["id"] for c in COMPONENTS]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, dupes


def test_no_two_components_move_to_the_same_place():
    """Two files sharing a destination lose one of them in the move."""
    seen: dict[str, str] = {}
    clashes = []
    for c in COMPONENTS:
        d = c.get("moves_to")
        # Directory destinations are shared on purpose: bfo.ontology-tree and
        # bfo.reasoner-scope are two views of the same tree, not two files
        # landing on one name. Only a file can clobber a file.
        if not d or "." not in d.rsplit("/", 1)[-1]:
            continue
        if d in seen:
            clashes.append(f"{c['id']} and {seen[d]} both move to {d}")
        seen[d] = c["id"]
    assert not clashes, clashes


def test_declared_destinations_agree_with_the_manifest():
    """The contract and the manifest must not disagree about a destination."""
    by_path = {r["path"]: r["destination"] for r in MANIFEST}
    disagreements = []
    for c in COMPONENTS:
        d, p = c.get("moves_to"), c.get("path")
        if not d or p not in by_path:
            continue
        if by_path[p] != d:
            disagreements.append(f"{c['id']}: contract {d}, manifest {by_path[p]}")
    assert not disagreements, disagreements


# ======================================================================
# ignore rules
# ======================================================================


def test_both_run_locations_are_ignored():
    """A gap on either side commits generated run state.

    The old rule has to survive until the examples wave completes and the new
    one has to exist before it starts, so for a while both are correct.
    """
    text = (REPO / ".gitignore").read_text(encoding="utf-8")
    for rule in ("examples/_run/", "examples/**/_run/"):
        assert rule in text, f"{rule} is not ignored"


def test_no_run_state_is_tracked():
    leaked = [f for f in tracked() if "/_run/" in f or f.startswith("_run/")]
    assert not leaked, leaked


# ======================================================================
# allowances: shape
# ======================================================================


@pytest.mark.parametrize("a", ALLOWANCES, ids=lambda a: a["id"])
def test_each_allowance_is_well_formed(a):
    assert a.get("file"), a
    assert a.get("literal") or a.get("pattern"), "neither a literal nor a pattern"
    assert not (a.get("literal") and a.get("pattern")), "both, so neither is decisive"
    assert (a.get("justification") or "").strip(), "an unexplained exception"
    assert a.get("category"), a
    assert a.get("owner"), a


@pytest.mark.parametrize("a", ALLOWANCES, ids=lambda a: a["id"])
def test_each_allowance_declares_a_lifecycle(a):
    """Permanent, or expiring after a named wave. Never both, never neither."""
    perm, wave = a.get("permanent"), a.get("remove_after_wave")
    assert perm is not None, "no 'permanent' field"
    assert bool(perm) != bool(wave), (
        "an allowance is permanent or it expires after a wave; "
        f"got permanent={perm!r} remove_after_wave={wave!r}")
    if wave:
        assert wave in WAVES, f"{wave!r} is not a migration wave"


@pytest.mark.parametrize("a", ALLOWANCES, ids=lambda a: a["id"])
def test_each_allowance_names_a_real_owner(a):
    ids = {c["id"] for c in COMPONENTS}
    assert a["owner"] in ids or a["owner"] == "unowned", a["owner"]


def test_allowance_ids_are_unique():
    ids = [a["id"] for a in ALLOWANCES]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, dupes


# ======================================================================
# allowances: both directions of coverage
# ======================================================================


@pytest.mark.parametrize("a", ALLOWANCES, ids=lambda a: a["id"])
def test_each_allowance_matches_something(a):
    """A zero-match allowance is an exception granted for nothing.

    It also reads as coverage, which is the harm: the list looks complete
    while an occurrence somewhere else has no entry at all.
    """
    path = REPO / a["file"]
    assert path.exists(), f"{a['file']} does not exist"
    text = path.read_text(encoding="utf-8", errors="replace")
    needle = a.get("literal")
    if needle:
        assert needle in text, f"{needle!r} does not occur in {a['file']}"
    else:
        assert re.search(a["pattern"], text), (
            f"pattern {a['pattern']!r} matches nothing in {a['file']}")


def test_every_occurrence_is_covered():
    """The other direction, and the one that actually catches breakage."""
    uncovered = []
    for f, m in sorted(occurrences()):
        text = (REPO / f).read_text(encoding="utf-8", errors="replace")
        if not any(covered_by(a, f, m, text) for a in ALLOWANCES):
            uncovered.append(f"{f} names {m} ({MOVING[m]['wave']} wave) "
                             f"with no allowance")
    assert not uncovered, (
        f"{len(uncovered)} literal path occurrence(s) nobody has accounted "
        "for:\n" + "\n".join("  " + u for u in uncovered))


def test_no_two_allowances_cover_the_same_occurrence():
    """Overlap means neither entry's lifecycle governs the occurrence.

    Removing one after its wave leaves the other still granting it, so the
    path survives a move that should have rewritten it.
    """
    overlaps = []
    for f, m in sorted(occurrences()):
        text = (REPO / f).read_text(encoding="utf-8", errors="replace")
        hits = [a["id"] for a in ALLOWANCES if covered_by(a, f, m, text)]
        if len(hits) > 1:
            overlaps.append(f"{f} / {m} is covered by {hits}")
    assert not overlaps, overlaps


def test_prose_occurrences_are_out_of_scope_and_counted():
    """The exclusion is stated as a number so it cannot quietly grow.

    Markdown review documents describe what was true when they were written.
    Rewriting their paths would falsify the record, so they are excluded here
    and their links are checked in the final documentation pass.
    """
    prose = occurrences((".md",))
    assert len(prose) <= 90, (
        f"{len(prose)} prose occurrences, up from the 77 recorded when the "
        "exclusion was justified; if documentation has grown this much the "
        "exclusion needs re-arguing rather than widening")


# ======================================================================
# allowances: lifecycle
# ======================================================================


def expired(completed: list[str]) -> list[str]:
    """Allowances whose removal wave has run and which are still here."""
    return [a["id"] for a in ALLOWANCES
            if a.get("remove_after_wave") in completed]


def test_nothing_has_expired_yet():
    """No wave has run, so no allowance can be overdue."""
    assert expired([]) == []


def test_an_allowance_expires_after_its_wave():
    """The falsification: without this, `expired` could always return []."""
    have_waves = {a.get("remove_after_wave") for a in ALLOWANCES} - {None}
    assert have_waves, "no allowance declares a removal wave"
    for w in sorted(have_waves):
        overdue = expired([w])
        assert overdue, f"nothing expires after the {w} wave, which cannot be right"


def test_every_temporary_allowance_names_a_wave_that_moves_its_referent():
    """An allowance must expire when the path it names actually moves.

    Naming a later wave lets the reference sit broken for one or more
    commits with the check still green; naming an earlier one demands a fix
    before the file has moved.
    """
    wrong = []
    for a in ALLOWANCES:
        w = a.get("remove_after_wave")
        lit = a.get("literal")
        if not w or not lit or lit not in MOVING:
            continue
        actual = MOVING[lit]["wave"]
        if actual != w:
            wrong.append(f"{a['id']}: expires after {w}, but {lit} moves in {actual}")
    assert not wrong, wrong
