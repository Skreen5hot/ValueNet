"""Produce the transition matrix and the successor baseline in one run.

    python tools/marep/build_evidence.py

The two artifacts have a bootstrap relationship: the baseline cites the
matrix, so the matrix must exist first -- and writing it makes the tree
dirty, which the baseline refuses, because a baseline measured from a dirty
tree names a commit that does not contain what it measured.

Resolving that with a blanket "allow dirty" switch would produce an evidence
file indistinguishable from a clean measurement, which is the failure the
refusal exists to prevent. So the sequence is run as one step from a clean
commit: matrix first, then baseline, with the baseline permitting exactly the
matrix path and nothing else, and recording that it did.

Both outputs name the same input commit, and that commit is neither of the
commits they will land in.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())

MATRIX = "config/eol-transition-matrix.json"
BASELINE = "config/semantic-baseline.json"


def run(*cmd) -> int:
    print("  $ " + " ".join(str(c) for c in cmd[1:]))
    return subprocess.run([str(c) for c in cmd], cwd=str(_root)).returncode


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", default=MATRIX)
    ap.add_argument("--baseline", default=BASELINE)
    args = ap.parse_args(argv)

    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(_root),
                            capture_output=True, text=True).stdout.strip()
    if status:
        raise SystemExit(
            "the working tree has uncommitted changes. Evidence is generated "
            "from a commit, so that the input it names is one somebody else "
            "can check out:" + os.linesep
            + os.linesep.join("      " + l for l in status.splitlines()[:8]))

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(_root),
                          capture_output=True, text=True).stdout.strip()
    print("  input commit %s" % head)
    print()

    rc = run(sys.executable, "tools/marep/build_transition_matrix.py",
             "-o", args.matrix)
    if rc:
        return rc
    print()
    rc = run(sys.executable, "tools/marep/build_semantic_baseline.py",
             "-o", args.baseline)
    if rc:
        return rc

    # Both must name the commit they were generated from, and each other.
    matrix = json.loads((_root / args.matrix).read_text(encoding="utf-8"))
    baseline = json.loads((_root / args.baseline).read_text(encoding="utf-8"))
    problems = []
    if matrix["input_commit"] != head:
        problems.append("the matrix names %s" % matrix["input_commit"][:12])
    if baseline["input_commit"] != head:
        problems.append("the baseline names %s" % baseline["input_commit"][:12])
    if baseline["transition"]["measured"]["input_commit"] != head:
        problems.append("the baseline cites a matrix from another commit")
    if problems:
        raise SystemExit("the two artifacts disagree about their input: "
                         + "; ".join(problems))

    print()
    print("  both artifacts describe %s" % head[:12])
    print("  matrix   %s" % args.matrix)
    print("  baseline %s" % args.baseline)
    print()
    print("  commit these two files together; the commit they land in is not")
    print("  the commit they describe, and neither claims to be it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
