"""Validate the working tree against the frozen move manifest.

Run after every move commit. From step 7 onward the manifest is **read, never
regenerated**: reclassifying a half-moved tree would turn completed
destinations into new sources and destroy the audit trail, so the manifest is
the fixed reference and the tree is what gets checked against it.

The central rule is an exclusive or. For every `MOVE` row exactly one of source
and destination is tracked — before its wave the source, after it the
destination, never both and never neither. Both means a copy rather than a
move; neither means the file was lost.

    python ValueNet_code/validate_migration_state.py [--wave bfo]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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


def validate(rows: list[dict], files: set[str], current_wave: str | None) -> list[str]:
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
        if True:
            if dest_here and wave not in done:
                problems.append(
                    f"{src}: moved to {dest} but wave {wave!r} has not run "
                    f"(current: {current_wave or 'none'})")
            if src_here and wave in done:
                problems.append(
                    f"{src}: wave {wave!r} has run but the file is still at its "
                    f"source path")

    for f in sorted(files - represented):
        problems.append(f"tracked but absent from the manifest: {f}")
    return problems


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

    problems = validate(rows, files, args.wave)
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
