"""Retarget the two trigger objects that name no declared value.

Both are errors rather than modelling gaps, and neither should be declared as a
value — declaring them would make the mistake permanent and give one value two
identities.

**Repayment -> Recognition.** `folk:Repayment` receives 106 trigger statements
and is declared nowhere. All 106 live in `ThatsAllFolks/folk_Recognition.ttl`,
which is headed `## folk:Recognition`, while the properly declared
`folk:Recognition` receives zero. The decisive evidence is the corpus-wide
convention: of 127 fragment files, 126 use exactly their own filename as the
trigger object, and `folk_Recognition.ttl` is the only exception. The file's
object was wrong throughout — including under its `# Repayment frame` heading,
where FrameNet material about repayment is being offered as a trigger source
for Recognition, which is what that section is for.

**Strenght -> Strength.** A spelling defect, Run 1's NAME-001. `folk:Strength`
is declared and receives zero triggers; the misspelled `folk:Strenght` receives
all 205 statement lines. Here the file follows the convention correctly — the
filename and the object agree — so both are renamed together.

Idempotent: files already carrying the corrected IRI are left alone, so this
can be re-run and serves as the record of exactly what changed.

    python ValueNet_code/retarget_bad_trigger_objects.py [--check]
"""

from __future__ import annotations

import argparse
import os
import sys

# Root by upward search for the layout contract, not by counting
# directories. This script moves under tools/, at which point two
# dirname calls resolve to repo/tools -- a path that exists, so the
# failure is silent.
_here = os.path.abspath(__file__)
HERE = _here
while not os.path.isfile(os.path.join(HERE, "config", "repository-layout.yaml")):
    _up = os.path.dirname(HERE)
    if _up == HERE:
        raise SystemExit("no config/repository-layout.yaml above " + _here)
    HERE = _up

#: (wrong IRI token, right IRI token, files to rewrite, file to rename or None)
RETARGETS = [
    ("folk:Repayment", "folk:Recognition",
     ["ThatsAllFolks/folk_Recognition.ttl", "ThatsAllFolks/taf.ttl"],
     None),
    ("folk:Strenght", "folk:Strength",
     ["ThatsAllFolks/folk_Strenght.ttl", "ThatsAllFolks/taf.ttl"],
     ("ThatsAllFolks/folk_Strenght.ttl", "ThatsAllFolks/folk_Strength.ttl")),
]


def rewrite(path: str, wrong: str, right: str, check: bool) -> int:
    full = os.path.join(HERE, path)
    if not os.path.exists(full):
        print(f"    missing: {path}")
        return 0
    with open(full, encoding="utf-8", newline="") as fh:
        text = fh.read()
    n = text.count(wrong)
    if not n:
        return 0
    if not check:
        with open(full, "w", encoding="utf-8", newline="") as fh:
            fh.write(text.replace(wrong, right))
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args(argv)

    total = 0
    for wrong, right, paths, rename in RETARGETS:
        print(f"\n{wrong} -> {right}")
        for p in paths:
            n = rewrite(p, wrong, right, args.check)
            total += n
            if n:
                print(f"    {'would rewrite' if args.check else 'rewrote':<14} "
                      f"{n:>4} occurrence(s) in {p}")
        if rename:
            src, dst = (os.path.join(HERE, x) for x in rename)
            if os.path.exists(src):
                if args.check:
                    print(f"    would rename   {rename[0]} -> {rename[1]}")
                else:
                    os.replace(src, dst)
                    print(f"    renamed        {rename[0]} -> {rename[1]}")

    if not total:
        print("\nNothing to do; the corpus already carries the corrected IRIs.")
    else:
        print(f"\n{total} occurrence(s) "
              f"{'would be' if args.check else ''} retargeted.")
    print("Neither erroneous IRI is declared as a value; both are retired.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
