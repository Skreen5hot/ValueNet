"""Diagnose why ThatsAllFolks/folk_*.ttl does not parse. Read-only.

Applies nothing. It reports what is wrong, in what proportions, and what each
class of defect would cost to repair, so that the decision about *how* to fix
it — prefix header per file, a build step that concatenates fragments against a
parent, or a redesign — can be made on measurements rather than impressions.

The reason this exists as a script rather than a paragraph: the first
assumption about these files was that they shared one missing prefix. They do
not, and the only way that became clear was running the repair and seeing what
survived it.

    python ValueNet_code/diagnose_folk_fragments.py [--verbose]
"""

from __future__ import annotations

import argparse
import collections
import glob
import os
import sys

try:
    import rdflib
except ImportError:  # pragma: no cover
    sys.exit("needs rdflib: pip install rdflib")

#: The bindings the parent artifacts (folk.owl, taf.ttl) declare. Every prefix
#: the fragments use is drawn from here; none of them invent one.
HEADER = """@prefix folk: <http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#> .
@prefix vcvf: <http://www.ontologydesignpatterns.org/ont/values/valuecore_with_value_frames.owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix be:   <http://www.ontologydesignpatterns.org/ont/emotions/BasicEmotions.owl#> .
"""

TRIGGERS = rdflib.URIRef(
    "http://www.ontologydesignpatterns.org/ont/values/"
    "valuecore_with_value_frames.owl#triggers")


def defects(text: str) -> set[str]:
    """Content defects that survive a prefix header. Mutually exclusive here."""
    found = set()
    if any(line.strip() in ("data", "0") for line in text.splitlines()):
        found.add("export debris")
    if ">>" in text:
        found.add("malformed IRI")
    if text.count('"') % 2:
        found.add("unbalanced quote")
    return found


def repair(text: str) -> str:
    """The minimal mechanical repair for each defect class. Never written out."""
    text = "\n".join(l for l in text.splitlines() if l.strip() not in ("data", "0"))
    text = text.replace(">>", ">")
    if text.count('"') % 2:
        text = text.replace('"', "", 1)
    return text


def parses(text: str) -> tuple[bool, int, str]:
    g = rdflib.Graph()
    try:
        g.parse(data=text, format="turtle")
    except Exception as exc:
        return False, 0, " ".join(str(exc).split())[:110]
    return True, len(g), ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true", help="name every affected file")
    ap.add_argument("--dir", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ThatsAllFolks"))
    args = ap.parse_args(argv)

    files = sorted(glob.glob(os.path.join(args.dir, "folk_*.ttl")))
    if not files:
        return sys.exit(f"no folk_*.ttl under {args.dir}")

    stages = collections.Counter()
    by_defect: dict[str, list[str]] = collections.defaultdict(list)
    merged, recovered = rdflib.Graph(), 0

    for path in files:
        name = os.path.basename(path)
        raw = open(path, encoding="utf-8", errors="replace").read()

        as_is, _, _ = parses(raw)
        if as_is:
            stages["parses as committed"] += 1
            continue

        with_header, n, _ = parses(HEADER + raw)
        if with_header:
            stages["needs only a prefix header"] += 1
            recovered += n
            merged.parse(data=HEADER + raw, format="turtle")
            continue

        for d in defects(raw):
            by_defect[d].append(name)
        fixed, n, err = parses(HEADER + repair(raw))
        if fixed:
            stages["needs a header and content repair"] += 1
            recovered += n
            merged.parse(data=HEADER + repair(raw), format="turtle")
        else:
            stages["not recovered by either"] += 1
            by_defect["unrecovered: " + err[:60]].append(name)

    print(f"\n{len(files)} fragment files under {os.path.relpath(args.dir)}\n")
    for label in ("parses as committed", "needs only a prefix header",
                  "needs a header and content repair", "not recovered by either"):
        if stages[label]:
            print(f"  {stages[label]:4}  {label}")

    print("\ncontent defects, beyond the missing header:")
    for defect, names in sorted(by_defect.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(names):4}  {defect}")
        shown = names if args.verbose else names[:3]
        for n in shown:
            print(f"          {n}")
        if not args.verbose and len(names) > 3:
            print(f"          ... and {len(names) - 3} more (--verbose to list)")

    triggers = len(list(merged.triples((None, TRIGGERS, None))))
    print(f"\nrecoverable content:")
    print(f"  {len(merged):>8,}  distinct triples")
    print(f"  {triggers:>8,}  distinct vcvf:triggers statements")
    print("\nNothing was written. This script diagnoses only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
