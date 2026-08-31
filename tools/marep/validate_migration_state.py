"""Validate the working tree against the frozen move manifest.

Run after every move commit. From step 7 onward the manifest is **read, never
regenerated**: reclassifying a half-moved tree would turn completed
destinations into new sources and destroy the audit trail, so the manifest is
the fixed reference and the tree is what gets checked against it.

The central rule is an exclusive or. For every `MOVE` row exactly one of source
and destination is tracked — before its wave the source, after it the
destination, never both and never neither. Both means a copy rather than a
move; neither means the file was lost.

    python tools/marep/validate_migration_state.py [--wave bfo]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

from marep import layout  # noqa: E402

WAVE_ORDER = ["bfo", "marep", "original-valuenet", "architecture", "tests"]

#: The one ref the frozen manifest may come from. `--frozen-ref` exists so the
#: tag name is not hardcoded at call sites, not so a caller can choose a
#: different manifest: passing HEAD would have validated the mutable working
#: commit and defeated the freeze entirely.
FREEZE_TAG = "reorg-pre-move-v1"


def sh(*args: str) -> str:
    r = subprocess.run(args, capture_output=True, text=True,
                       cwd=str(layout.repository_root()))
    if r.returncode != 0:
        raise SystemExit(f"git failed: {' '.join(args)}\n{r.stderr.strip()}")
    return r.stdout


def tracked() -> set[str]:
    return {p for p in sh("git", "ls-files").split("\n") if p}


def _norm(text: str) -> str:
    """Line-ending agnostic comparison. This repository is CRLF in the working
    tree and LF in the index, so a raw comparison always reports a difference."""
    return text.replace("\r\n", "\n")


def validate(rows: list[dict], files: set[str], current_wave: str | None,
             frozen: set | None = None) -> list[str]:
    """Problems with the tree, given the frozen manifest.

    `frozen` is the set of files tracked when the plan was frozen. Passed
    in rather than read from git, so this function can be exercised
    against any state a caller can describe -- including states no
    repository is currently in, which is where the interesting failures
    live. Defaults to reading the tag.
    """
    problems: list[str] = []
    represented: set[str] = set()
    destinations: dict[str, str] = {}

    # An unknown wave used to fall through to an empty completed list, which
    # silently disabled ordering enforcement — the check most likely to be
    # skipped by a typo was the one that reported nothing when skipped. The CLI
    # now constrains the value, so reaching here with an unknown one is a bug.
    if current_wave is not None and current_wave not in WAVE_ORDER:
        raise ValueError(f"unknown wave {current_wave!r}; expected one of "
                         + ", ".join(WAVE_ORDER))
    done = (WAVE_ORDER[:WAVE_ORDER.index(current_wave) + 1]
            if current_wave else [])

    for r in rows:
        src, dest, wave = r["path"], r["destination"], r.get("wave")

        if dest == "RETAIN":
            if src not in files:
                problems.append(f"RETAIN row missing from the tree: {src}")
            else:
                represented.add(src)
            continue

        src_here, dest_here = src in files, dest in files
        if src_here and dest_here:
            problems.append(
                f"{src}: both source and destination are tracked — a copy, "
                f"not a move ({dest})")
        elif not src_here and not dest_here:
            problems.append(
                f"{src}: neither source nor destination is tracked; the file "
                f"was lost in transit (expected at {dest})")
        represented |= {p for p in (src, dest) if p in files}

        if dest in destinations:
            problems.append(f"{dest}: two rows resolve here — {destinations[dest]} "
                            f"and {src}")
        destinations[dest] = src

        # Wave ordering: a completed move must belong to a wave already run.
        # With no wave given this still applies, and `done` is empty — so any
        # completed move is a violation. Omitting --wave must mean zero moves
        # completed, not "skip the check".
        if dest_here and wave not in done:
            problems.append(
                f"{src}: moved to {dest} but wave {wave!r} has not run "
                f"(current: {current_wave or 'none'})")
        if src_here and wave in done:
            problems.append(
                f"{src}: wave {wave!r} has run but the file is still at its "
                f"source path")

    # Only files that existed when the plan was frozen. The manifest is a
    # record of one migration; a file created afterwards was never part of
    # it and its absence from the rows is not a defect. Comparing against
    # the live tree instead made the closed 335-row world permanent, so the
    # first file added after step 12 would have failed a completed
    # migration's validator.
    # Against the frozen snapshot, not the live paths. Intersecting with
    # `files` first dropped every completed move -- its source is gone --
    # so an omitted moved row could not be detected: nothing would look
    # for its destination and nothing would miss its source.
    snapshot = frozen_snapshot() if frozen is None else frozen
    sources = {r["path"] for r in rows}
    for f in sorted(snapshot - sources):
        problems.append(f"tracked at the freeze but absent from the manifest: {f}")
    for f in sorted(sources - snapshot):
        problems.append(f"in the manifest but not tracked at the freeze: {f}")
    return problems



def frozen_snapshot() -> set:
    """The files tracked at the freeze, read from the tag itself."""
    if not frozen_exists():
        return tracked()
    out = sh("git", "ls-tree", "-r", "--name-only", FREEZE_TAG)
    return {line for line in out.splitlines() if line}


def completed_waves(rows: list[dict], files: set[str]) -> list[str]:
    """Which waves have actually run, read off the tree rather than asserted.

    A wave is complete when every one of its rows sits at its destination and
    none is still at its source. Taking the caller's word for it makes the
    check depend on the answer it exists to verify, which is how a lifecycle
    rule ends up green forever: `expired([])` says "nothing has run", and
    nothing had, because nobody ever asked the repository.

    The waves are ordered, so a partial wave ends the run. Continuing past one
    would report a later wave as complete while an earlier one is half done --
    a state the plan forbids and the validator would otherwise not see.
    """
    done: list[str] = []
    for wave in WAVE_ORDER:
        rows_here = [r for r in rows if r.get("wave") == wave]
        if not rows_here:
            continue
        at_destination = sum(1 for r in rows_here if r["destination"] in files)
        at_source = sum(1 for r in rows_here if r["path"] in files)
        if at_destination == len(rows_here) and at_source == 0:
            done.append(wave)
        else:
            break
    return done


def current_wave(rows: list[dict], files: set[str]) -> str | None:
    """The most recent completed wave, or None before any move."""
    done = completed_waves(rows, files)
    return done[-1] if done else None


def in_git_work_tree() -> bool:
    """Whether a readable repository governs the layout contract's root.

    False only when the repository marker is absent. A `.git` that exists
    and cannot be read is a broken repository, not an unfrozen one, and
    raises.

    The previous version returned False for every non-zero exit -- a
    permissions failure, a corrupt gitdir pointer, a half-finished clone --
    so any of them silently retired the freeze and `frozen_text` fell back
    to the mutable working copy, which is precisely what the freeze exists
    to prevent. The docstring beneath it claimed other failures propagated.
    The prose was the intent and the code was the behaviour, and only the
    behaviour runs.

    The contract's directory is the repository root by construction, so
    `root/.git` is the marker to ask about; no upward search, because a
    contract root with no marker of its own is not a repository whatever
    sits above it.
    """
    root = layout.repository_root()
    marker = root / ".git"
    if not marker.exists():
        return False

    r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                       capture_output=True, text=True, cwd=str(root))
    if r.returncode != 0:
        raise SystemExit(
            f"{marker} exists but git cannot read this repository, so whether "
            f"anything is frozen cannot be determined. Refusing to treat a "
            f"broken repository as an unfrozen one.\n"
            + (r.stderr.strip() or f"git exited {r.returncode}"))

    answer = r.stdout.strip()
    if answer != "true":
        raise SystemExit(
            f"git rev-parse --is-inside-work-tree returned {answer!r} with a "
            f"{marker} present. That is neither a work tree nor a failure, "
            f"and guessing which would decide whether the freeze applies.")
    return True


def frozen_exists() -> bool:
    """Whether the freeze tag exists. False where there is no git.

    Not the same as swallowing a git failure. A materialised copy has no
    .git at all, and 'does the tag exist here' has a correct answer there
    -- no -- while `sh` fails loudly, which is right for the command line
    and wrong for a query. The three repository-marked test modules call
    this at import, and a marker deselects tests without preventing the
    module from being imported, so the crash took the whole collection
    down before anything could be deselected.

    Any other git failure raises, and now actually does: `in_git_work_tree`
    swallowed every non-zero exit while this sentence claimed otherwise."""
    if not in_git_work_tree():
        return False
    return bool(sh("git", "tag", "-l", FREEZE_TAG).strip())


def frozen_text(rel: str) -> tuple[str, str]:
    """A tracked file as the freeze recorded it, and where that came from.

    Before the tag there is nothing to read but the working copy. After it,
    the working copy is exactly what a check must not trust: an edit to the
    manifest or the baseline could make a broken tree look valid, which is
    the whole reason the freeze exists.
    """
    if frozen_exists():
        return sh("git", "show", f"{FREEZE_TAG}:{rel}"), f"{rel}@{FREEZE_TAG}"
    root = layout.repository_root()
    return (root / rel).read_text(encoding="utf-8"), f"{rel} (working copy)"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", default=None, choices=WAVE_ORDER,
                    help="the most recent wave completed; omit before any move, "
                         "which asserts that no move has completed")
    ap.add_argument("--frozen-ref", default=None,
                    help="git ref for the frozen manifest. Must resolve to the "
                         "same commit as " + FREEZE_TAG + "; any other ref is "
                         "refused.")
    ap.add_argument("--manifest", default="config/move-manifest.yaml")
    args = ap.parse_args(argv)

    import yaml
    root = layout.repository_root()

    # From step 7 the manifest is read, never regenerated. Reading the mutable
    # working copy would let an edit to the manifest make a broken tree look
    # valid, which is the failure this whole freeze exists to prevent.
    frozen_exists = bool(sh("git", "tag", "-l", FREEZE_TAG).strip())
    ref = args.frozen_ref

    if ref is not None:
        # Resolve both to commits and require equality. Accepting the ref as
        # given would let --frozen-ref HEAD validate against whatever is
        # currently checked out, which is exactly what the freeze prevents.
        supplied = sh("git", "rev-parse", f"{ref}^{{commit}}").strip()
        if not frozen_exists:
            raise SystemExit(f"--frozen-ref given but {FREEZE_TAG} does not "
                             f"exist yet; the manifest is not frozen.")
        frozen = sh("git", "rev-parse", f"{FREEZE_TAG}^{{commit}}").strip()
        if supplied != frozen:
            raise SystemExit(
                f"--frozen-ref {ref} resolves to {supplied[:12]}, but "
                f"{FREEZE_TAG} is {frozen[:12]}. Only the frozen manifest may "
                f"be validated against.")
    elif frozen_exists:
        raise SystemExit(
            f"{FREEZE_TAG} exists; pass --frozen-ref {FREEZE_TAG} so validation "
            f"reads the frozen manifest rather than the working copy.")

    if ref is None:
        text = (root / args.manifest).read_text(encoding="utf-8")
        source = f"{args.manifest} (working copy; no freeze tag yet)"
    else:
        text = sh("git", "show", f"{ref}:{args.manifest}")
        working = (root / args.manifest).read_text(encoding="utf-8")
        if _norm(working) != _norm(text):
            print(f"  note: working manifest differs from {ref}; "
                  f"validating against {ref}")
        source = f"{args.manifest}@{ref}"

    doc = yaml.safe_load(text)
    rows = doc["components"]
    files = tracked()
    print(f"  manifest source: {source}")

    problems = validate(rows, files, args.wave, frozen_snapshot())
    moves = [r for r in rows if r["destination"] != "RETAIN"]
    pending = [r for r in moves if r["path"] in files]

    print(f"  manifest {len(rows)} rows, tree {len(files)} tracked files")
    print(f"  {len(moves) - len(pending)} of {len(moves)} moves completed"
          + (f", wave {args.wave!r}" if args.wave else ", no wave run yet"))

    if problems:
        print(f"\n  {len(problems)} problem(s):")
        for p in problems[:25]:
            print(f"      {p}")
        if len(problems) > 25:
            print(f"      … and {len(problems) - 25} more")
        return 1
    print("  transition state is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
