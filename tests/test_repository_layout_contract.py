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
from pathlib import Path
from typing import NamedTuple

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

def _validator():
    import importlib.util
    path = layout.component("tool.validate-migration-state").resolve()
    spec = importlib.util.spec_from_file_location("validate_migration_state", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VALIDATOR = _validator()

#: The manifest is the frozen plan and comes from the tag. The contract is
#: living state -- allowances are removed as their waves complete -- so it is
#: read from the working tree, which is the thing being asserted about.
MANIFEST = yaml.safe_load(
    VALIDATOR.frozen_text("config/move-manifest.yaml")[0])["components"]
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


#: Any current path back to the frozen source path that names it. An
#: allowance is attached to a file, and the file moves; without a stable
#: identity the allowance stops matching the moment its own wave runs.
IDENTITY = {}
for _r in MANIFEST:
    IDENTITY[_r["path"]] = _r["path"]
    if _r["destination"] != "RETAIN":
        IDENTITY[_r["destination"]] = _r["path"]


def identity_of(rel: str) -> str:
    return IDENTITY.get(rel, rel)


def allowance_file(a: dict):
    """Where an allowance's file is now, or None if it is nowhere.

    Tried in frozen order: the source first, then the destination. A
    permanent allowance on a file that has moved is still live -- what it
    covers is the literal, not the location of the file holding it.
    """
    for cand in (a["file"], next((r["destination"] for r in MANIFEST
                                  if r["path"] == a["file"]
                                  and r["destination"] != "RETAIN"), None)):
        if cand and (REPO / cand).is_file():
            return REPO / cand
    return None


class Occurrence(NamedTuple):
    """One naming of a moving path, at one place in one file.

    `identity` is the containing file's frozen source path, so an occurrence
    keeps its name when the file holding it moves. `start`/`end` are
    character offsets, which is what lets a pattern allowance be judged
    against this occurrence rather than against the file.
    """

    identity: str
    literal: str
    start: int
    end: int
    line: int


def occurrences(suffixes=IN_SCOPE) -> list[Occurrence]:
    """Every naming of a moving path, individually.

    Collapsing these to a set of (file, path) pairs is what made per-file
    coverage look sufficient: two occurrences a hundred lines apart, one
    permitted and one not, were indistinguishable.
    """
    found: list[Occurrence] = []
    for f in tracked():
        ident = identity_of(f)
        if ident in EXEMPT or not f.endswith(suffixes):
            continue
        text = (REPO / f).read_text(encoding="utf-8", errors="replace")
        for m in MOVING:
            at = text.find(m)
            while at != -1:
                found.append(Occurrence(ident, m, at, at + len(m),
                                        text.count("\n", 0, at) + 1))
                at = text.find(m, at + 1)
    return found


def _pattern_spans(pattern: str, text: str) -> list[tuple[int, int]]:
    return [mt.span() for mt in re.finditer(pattern, text)]


def covered_by(a: dict, occ: Occurrence, text: str) -> bool:
    """Whether this allowance permits this occurrence.

    A literal allowance names the exact string, so it permits any occurrence
    of that string in its file: the permission is about what may be named,
    and five identical namings are one decision. A pattern allowance is
    judged against the occurrence's span, because a pattern says which
    *places* are permitted -- and a pattern accepted for matching elsewhere
    in the file permits everything in that file, which is the whole defect.
    """
    if a["file"] != occ.identity:
        return False
    if a.get("literal"):
        return a["literal"] == occ.literal
    return any(start < occ.end and occ.start < end
               for start, end in _pattern_spans(a["pattern"], text))


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


def ignored(rel: str) -> bool:
    """What git actually does with the path, not what the file says."""
    r = subprocess.run(["git", "check-ignore", "-q", "--no-index", rel],
                       cwd=str(REPO), capture_output=True, text=True)
    assert r.returncode in (0, 1), r.stderr
    return r.returncode == 0


def test_both_run_locations_are_ignored():
    """A gap on either side commits generated run state, 1,127,251 bytes of it.

    The old rule has to survive until the examples wave completes and the new
    one has to exist before it starts, so for a while both are correct.

    Asserted by running `git check-ignore`. The earlier form searched
    .gitignore for the two rule strings, which proves they were typed and not
    that they match anything: a pattern in the wrong section, negated later in
    the file, or shadowed by a rule above it reads exactly the same.
    """
    for rel in ("examples/_run/RUN1_STATE.yaml",
                "examples/nested/_run/RUN1_STATE.yaml"):
        assert ignored(rel), f"{rel} is not ignored by git"


def test_the_ignore_check_can_say_no():
    """The falsification. `git check-ignore` returning 0 for everything, or
    the helper swallowing its exit code, would make the test above vacuous."""
    # Both RETAIN. Naming a file that moves would put a literal path in
    # this module and make the coverage check demand an allowance for a
    # path used only to prove git says no.
    assert not ignored("marep/layout.py")
    assert not ignored("tests/conftest.py")


def test_no_run_state_is_tracked():
    leaked = [f for f in tracked() if "/_run/" in f or f.startswith("_run/")]
    assert not leaked, leaked


# ======================================================================
# allowances: shape
# ======================================================================


#: Looped rather than parametrized, and the reason is the migration itself.
#: One case per allowance meant four collected node ids per entry, so removing
#: the eight BFO allowances -- which the bfo wave requires -- would delete 32
#: node ids and break the frozen identity set the baseline exists to hold.
#: A test whose identity changes every time the plan proceeds cannot be the
#: thing that proves the plan changed nothing.
#:
#: The counts are deliberately not quoted here. An earlier version named
#: them and was already stale by the next capture, which is the same
#: failure in miniature: a number copied into prose stops tracking what it
#: was copied from. The baseline holds the numbers; this holds the reason.


def test_every_allowance_is_well_formed():
    problems = []
    for a in ALLOWANCES:
        i = a.get("id", "<no id>")
        if not a.get("file"):
            problems.append(f"{i}: no file")
        if not (a.get("literal") or a.get("pattern")):
            problems.append(f"{i}: neither a literal nor a pattern")
        if a.get("literal") and a.get("pattern"):
            problems.append(f"{i}: both a literal and a pattern, so neither decides")
        if not (a.get("justification") or "").strip():
            problems.append(f"{i}: an unexplained exception")
        if not a.get("category"):
            problems.append(f"{i}: no category")
        if not a.get("owner"):
            problems.append(f"{i}: no owner")
    assert not problems, problems


def test_every_allowance_declares_a_lifecycle():
    """Permanent, or expiring after a named wave. Never both, never neither."""
    problems = []
    for a in ALLOWANCES:
        perm, wave = a.get("permanent"), a.get("remove_after_wave")
        if perm is None:
            problems.append(f"{a['id']}: no 'permanent' field")
        elif bool(perm) == bool(wave):
            problems.append(
                f"{a['id']}: permanent={perm!r} remove_after_wave={wave!r}; "
                "an allowance is one or the other")
        if wave and wave not in WAVES:
            problems.append(f"{a['id']}: {wave!r} is not a migration wave")
        if wave and a.get("discharge") not in ("regenerate", "edit"):
            problems.append(
                f"{a['id']}: expires after {wave} but does not say whether it "
                "is discharged by regenerating or by editing")
    assert not problems, problems


def test_every_allowance_names_a_real_owner():
    ids = {c["id"] for c in COMPONENTS}
    bad = [f"{a['id']}: owner {a['owner']!r}" for a in ALLOWANCES
           if a["owner"] not in ids and a["owner"] != "unowned"]
    assert not bad, bad


def test_every_allowance_matches_something():
    """A zero-match allowance is an exception granted for nothing.

    It also reads as coverage, which is the harm: the list looks complete
    while an occurrence somewhere else has no entry at all.
    """
    problems = []
    for a in ALLOWANCES:
        path = allowance_file(a)
        if path is None:
            problems.append(
                f"{a['id']}: {a['file']} is at neither of its frozen paths")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        needle = a.get("literal")
        if needle and needle not in text:
            problems.append(f"{a['id']}: {needle!r} does not occur in {a['file']}")
        elif not needle and not re.search(a["pattern"], text):
            problems.append(
                f"{a['id']}: pattern {a['pattern']!r} matches nothing in {a['file']}")
    assert not problems, problems


def test_allowance_ids_are_unique():
    ids = [a["id"] for a in ALLOWANCES]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, dupes


# ======================================================================
# allowances: both directions of coverage
# ======================================================================


def test_every_occurrence_is_covered():
    """The other direction, and the one that actually catches breakage.

    Opens with the falsification for how coverage is judged, because every
    assertion below inherits it. A pattern allowance permits places, not
    files: given the same path written twice in one file -- once inside the
    quoted mapping table the pattern is written for, once in a bare usage
    line it is not -- only the first is covered. While a pattern was tested
    against the whole file, the table licensed the usage line twelve lines
    above it, and the inventory that should have demanded a fix reported
    full coverage instead.
    """
    # A synthetic path. Naming a real moving one would put a literal in
    # this file and make the inventory below demand an allowance for a
    # string that exists only to demonstrate the rule.
    lit = "OldDir/some_tool.py"
    synthetic = (f'    "{lit}": "tools/marep/build_move_manifest.py",\n'
                 f'    python {lit}\n')
    table_at = synthetic.index(lit)
    usage_at = synthetic.index(lit, synthetic.index("python"))
    probe = {"file": "probe", "pattern": '"(OldDir|NewDir)/'}
    table = Occurrence("probe", lit, table_at, table_at + len(lit), 1)
    usage = Occurrence("probe", lit, usage_at, usage_at + len(lit), 2)

    assert covered_by(probe, table, synthetic), (
        "the pattern no longer covers the occurrence it exists for")
    assert not covered_by(probe, usage, synthetic), (
        "a pattern matching the table certified a usage line it does not "
        "match; coverage has gone back to being per file")

    uncovered = []
    for occ in sorted(occurrences()):
        holder = allowance_file({"file": occ.identity})
        if holder is None:
            continue
        text = holder.read_text(encoding="utf-8", errors="replace")
        if not any(covered_by(a, occ, text) for a in ALLOWANCES):
            uncovered.append(
                f"{occ.identity}:{occ.line} names {occ.literal} "
                f"({MOVING[occ.literal]['wave']} wave) with no allowance")
    assert not uncovered, (
        f"{len(uncovered)} literal path occurrence(s) nobody has accounted "
        "for:\n" + "\n".join("  " + u for u in uncovered))


def test_no_two_allowances_cover_the_same_occurrence():
    """Overlap means neither entry's lifecycle governs the occurrence.

    Removing one after its wave leaves the other still granting it, so the
    path survives a move that should have rewritten it.
    """
    overlaps = []
    for occ in sorted(occurrences()):
        holder = allowance_file({"file": occ.identity})
        if holder is None:
            continue
        text = holder.read_text(encoding="utf-8", errors="replace")
        hits = [a["id"] for a in ALLOWANCES if covered_by(a, occ, text)]
        if len(hits) > 1:
            overlaps.append(
                f"{occ.identity}:{occ.line} / {occ.literal} is covered by {hits}")
    assert not overlaps, overlaps


def test_prose_occurrences_are_out_of_scope_and_counted():
    """The exclusion is stated as a number so it cannot quietly grow.

    Markdown review documents describe what was true when they were written.
    Rewriting their paths would falsify the record, so they are excluded here
    and their links are checked in the final documentation pass.
    """
    prose = {(o.identity, o.literal) for o in occurrences((".md",))}
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


def completed_waves() -> list[str]:
    """Read off the repository, not assumed.

    `expired([])` was the whole lifecycle check, and `[]` says "no wave has
    run" whatever the tree looks like. It was true when written and would
    have stayed green through every wave, letting a stale allowance in a
    retained file survive indefinitely -- retained files do not move, so
    nothing else would have noticed either.
    """
    return VALIDATOR.completed_waves(MANIFEST, VALIDATOR.tracked())


def test_no_expired_allowance_survives_its_wave():
    """The real gate. Empty today because no wave has run, and it says so."""
    done = completed_waves()
    overdue = expired(done)
    assert not overdue, (
        f"waves {done} have completed, so these allowances should have been "
        f"removed with them: {overdue}")


def test_the_lifecycle_check_knows_which_waves_have_run():
    """Guards the failure where `done` is empty for the wrong reason.

    If wave derivation broke, the check above would pass by measuring
    nothing -- which is exactly how it passed before.
    """
    done = completed_waves()
    moved = [r for r in MANIFEST
             if r["destination"] != "RETAIN" and r["destination"] in set(VALIDATOR.tracked())]
    if moved:
        assert done, (
            f"{len(moved)} file(s) are at their destinations but no wave is "
            "reported complete; the lifecycle check is measuring nothing")
    else:
        assert done == [], done


def test_an_allowance_expires_after_its_wave():
    """The falsification, against a synthetic completed-wave list.

    Without it `expired` could return [] for every input and every lifecycle
    assertion above would pass.
    """
    have_waves = {a.get("remove_after_wave") for a in ALLOWANCES} - {None}
    if not have_waves:
        pytest.skip("every allowance is permanent; nothing can expire")
    for w in sorted(have_waves):
        assert expired([w]), f"nothing expires after the {w} wave"


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

def test_no_test_here_is_parametrized_over_the_allowance_list():
    """Node ids must not depend on how many exceptions exist.

    Four parametrized tests produced four node ids per allowance, so the
    eight removals the bfo wave requires would have deleted 32 ids and
    broken the frozen identity set the baseline exists to hold. A check
    whose identity changes whenever the plan advances cannot be the thing
    that proves the plan changed nothing.
    """
    src = Path(__file__).read_text(encoding='utf-8')
    # Built by concatenation so this line is not itself a match.
    needle = "ALLOWANCES," + " ids="
    assert needle not in src, (
        "an allowance-parametrized test is back; loop inside one test "
        "instead, so the collected identity survives the migration")
