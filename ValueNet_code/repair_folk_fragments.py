"""Make every ThatsAllFolks/folk_*.ttl a valid, independently loadable document.

The fragments were written to be read alongside a parent that declares their
prefixes. That put correctness in the tooling rather than in the artifact: the
file on disk was not a Turtle document, and only a reader who knew the
convention could load it. This script moves the correctness into the files.

What it does, and nothing else:

* prepends the six prefix declarations the parent artifacts already use, taking
  the bindings verbatim from `folk.owl` and `taf.ttl` rather than inventing any;
* removes stray export debris — lines that are just `data` or `0`, evidently
  spreadsheet residue (12 files);
* repairs a doubled IRI terminator, `>>` to `>` (2 files);
* removes a lone `"` on its own line (1 file).

Deliberately out of scope: the 126 files containing U+00A0 non-breaking spaces,
which sit inside comments and break nothing; duplicate triples; and the
file-per-value structure itself, which the diagnosis gave no reason to revisit.

Idempotent. Files already carrying the header are left untouched, so it can be
re-run safely and serves as the record of exactly what was changed.

    python ValueNet_code/repair_folk_fragments.py [--check] [--dir PATH]
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

#: Verbatim from folk.owl and taf.ttl. All six go into every file: a uniform
#: header keeps the corpus editable without each file having a different
#: preamble, and unused prefix declarations are inert in Turtle.
PREFIXES = [
    ("owl", "http://www.w3.org/2002/07/owl#"),
    ("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
    ("skos", "http://www.w3.org/2004/02/skos/core#"),
    ("be", "http://www.ontologydesignpatterns.org/ont/emotions/BasicEmotions.owl#"),
    ("folk", "http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#"),
    ("vcvf", "http://www.ontologydesignpatterns.org/ont/values/"
             "valuecore_with_value_frames.owl#"),
]

MARKER = "@prefix folk:"

#: Lines removed entirely when they are the whole line, stripped.
DEBRIS_LINES = ("data", "0", '"')


def header(eol: str) -> str:
    lines = [f"@prefix {p}: <{u}> ." for p, u in PREFIXES]
    return eol.join(lines) + eol + eol


def dominant_eol(text: str) -> str:
    return "\r\n" if text.count("\r\n") >= text.count("\n") - text.count("\r\n") else "\n"


def repair(text: str) -> tuple[str, list[str]]:
    """Return repaired text and the list of repairs applied."""
    applied: list[str] = []

    lines = text.split("\n")
    kept = [l for l in lines if l.strip().rstrip("\r").strip() not in DEBRIS_LINES]
    removed = len(lines) - len(kept)
    if removed:
        dropped = {l.strip().rstrip("\r").strip() for l in lines if l not in kept}
        applied.append(f"removed {removed} stray line(s): {sorted(dropped)}")
        text = "\n".join(kept)

    if ">>" in text:
        applied.append(f"repaired {text.count('>>')} doubled IRI terminator(s)")
        text = text.replace(">>", ">")

    return text, applied


def process(path: str, check_only: bool) -> tuple[str, list[str]]:
    with open(path, encoding="utf-8", newline="") as fh:
        original = fh.read()

    if MARKER in original:
        return "already has header", []

    eol = dominant_eol(original)
    body, applied = repair(original)
    new = header(eol) + body

    if not check_only:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
    return ("would repair" if check_only else "repaired"), applied


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    ap.add_argument("--dir", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ThatsAllFolks"))
    args = ap.parse_args(argv)

    files = sorted(glob.glob(os.path.join(args.dir, "folk_*.ttl")))
    if not files:
        sys.exit(f"no folk_*.ttl under {args.dir}")

    counts = {"repaired": 0, "would repair": 0, "already has header": 0}
    content_repairs = 0
    for path in files:
        status, applied = process(path, args.check)
        counts[status] = counts.get(status, 0) + 1
        if applied:
            content_repairs += 1
            print(f"  {os.path.basename(path)}")
            for a in applied:
                print(f"      {a}")

    print(f"\n{len(files)} fragment files")
    for k, v in counts.items():
        if v:
            print(f"  {v:4}  {k}")
    print(f"  {content_repairs:4}  needed a content repair beyond the header")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
