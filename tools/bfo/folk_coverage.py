# SPDX-License-Identifier: Apache-2.0
"""How much of the folk corpus the BFO folk module actually carries. Read-only.

Applies nothing. It reports coverage in both directions and says which rule
matched each pairing, so a decision about the gap can be made on measurements
rather than on the word "comprehensive".

    python tools/bfo/folk_coverage.py
    python tools/bfo/folk_coverage.py --check      # exit 1 on a finding
    python tools/bfo/folk_coverage.py --json OUT

WHY THIS EXISTS

Somebody demonstrating the site searched for "frugal" and found nothing.
`folk:Frugality` is in the corpus -- it is in ThatsAllFolks/folk.ttl, it is in
the generated alignment view, and the ThatsAllFolks README names it explicitly
as an example of what the module contributes. What it is not in is
ontology/bfo/core/valuenet-folk.ttl, and the site's class index is built from
the BFO modules, so the explorer can only ever find what that layer carries.

Nothing compared the two. The folk layer was authored, tested for internal
consistency, and documented as "comprehensive in its coverage" -- and the one
question nobody asked was whether the values in it are the values the corpus
has. That is the shape of defect this repository keeps finding: a check that
reports on something adjacent to what it claims, here by being absent
altogether while a sentence in a guide stood in for it.

WHAT COUNTS AS A FOLK VALUE

The union of two populations, because neither is complete on its own:

  folk.ttl classes    241 owl:Class in the FolkValues.owl namespace.
  trigger fragments   127 ThatsAllFolks/folk_<Name>.ttl files, of which 37
                      name a value folk.ttl does not declare.

That 37 is a finding in its own right and is reported below: a value with a
trigger fragment and no class is a value the annotation pipeline can evoke and
the ontology cannot express.

HOW A PAIRING IS ESTABLISHED

Three rules, tried in order, and the report says which one fired. They are
listed rather than blended because a coverage number produced by an unstated
matching rule is not a measurement:

  seeAlso   the BFO class carries rdfs:seeAlso into a folk namespace; the
            local name, less a Disposition or Role suffix, is the value name.
  altLabel  the BFO class carries skos:altLabel, which is where this module
            keeps the bare value word.
  label     rdfs:label with a trailing " Disposition" or " Role" removed.

A BFO class that matches under none of them is reported as unmatched rather
than as wrong. It may be a deliberate addition drawn from Schwartz or from
somewhere else; nothing in the repository records the decision either way, and
this tool is not the place to guess.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

# Root by upward search for the layout contract, not by counting directories.
# A tool that counts parents resolves to a path that exists when it moves, so
# the failure is silent -- three tools here had already done it.
_here = os.path.abspath(__file__)
HERE = _here
while not os.path.isfile(os.path.join(HERE, "config", "repository-layout.yaml")):
    _up = os.path.dirname(HERE)
    if _up == HERE:
        raise SystemExit("no config/repository-layout.yaml above " + _here)
    HERE = _up
sys.path.insert(0, HERE)

try:
    import rdflib
except ImportError:  # pragma: no cover
    sys.exit("needs rdflib: pip install rdflib")

from marep.layout import component, relative  # noqa: E402

#: The namespace the authored folk source actually uses. The BFO layer points
#: its back-links at a w3id namespace instead, which is why `seeAlso` matching
#: strips the namespace and compares local names rather than IRIs.
ODP = "http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#"

#: Namespaces a back-link may use to mean "the folk value of this name".
FOLK_NAMESPACES = (ODP, "https://w3id.org/valuenet/folk#",
                   "http://w3id.org/valuenet/folk#")

SUFFIX = re.compile(r"(Disposition|Role)$")
LABEL_SUFFIX = re.compile(r"\s+(Disposition|Role)$")

SOURCE = "original-valuenet.folk-source"
FRAGMENTS = "original-valuenet.folk-fragments"
BFO_FOLK = "bfo.module.folk"


def normalise(name: str) -> str:
    """Compare on letters only.

    `Affective_autonomy` and `AffectiveAutonomy` are the same value spelled by
    two different generations of the corpus, and a comparison that treats them
    as different reports a gap that is not there.
    """
    return re.sub(r"[^a-z0-9]", "", name.lower())


def source_values(graph=None, folder=None) -> tuple[dict, dict]:
    """Folk value names, and where each one came from.

    Takes its inputs so a test can hand it a graph. The alternative is a
    function that can only be exercised against the whole corpus, which
    means the matching rules below get tested by whether the total looks
    plausible.
    """
    if graph is None:
        graph = rdflib.Graph()
        graph.parse(str(component(SOURCE).resolve()), format="turtle")
    declared = {}
    for subject in graph.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        text = str(subject)
        if text.startswith(ODP):
            name = text[len(ODP):].lstrip(":")
            if name:
                declared[normalise(name)] = name

    fragments = {}
    folder = folder if folder is not None else component(FRAGMENTS).resolve()
    for found in sorted(glob.glob(os.path.join(str(folder), "folk_*.ttl"))):
        name = os.path.basename(found)[len("folk_"):-len(".ttl")]
        fragments[normalise(name)] = name
    return declared, fragments


def bfo_classes(graph=None) -> dict:
    """Each BFO folk class, with every name it offers for matching."""
    if graph is None:
        graph = rdflib.Graph()
        graph.parse(str(component(BFO_FOLK).resolve()), format="turtle")
    out = {}
    for subject in graph.subjects(rdflib.RDF.type, rdflib.OWL.Class):
        candidates = []
        for obj in graph.objects(subject, rdflib.RDFS.seeAlso):
            text = str(obj)
            for namespace in FOLK_NAMESPACES:
                if text.startswith(namespace):
                    candidates.append(
                        ("seeAlso", SUFFIX.sub("", text[len(namespace):]), text))
        for obj in graph.objects(
                subject, rdflib.URIRef(
                    "http://www.w3.org/2004/02/skos/core#altLabel")):
            candidates.append(("altLabel", str(obj), None))
        for obj in graph.objects(subject, rdflib.RDFS.label):
            candidates.append(("label", LABEL_SUFFIX.sub("", str(obj)), None))
        out[str(subject)] = candidates
    return out


#: Every rule `measure` may use. Named here so the report can say which
#: ones never fired, rather than leaving a reader to infer it from a
#: number that happens to add up.
RULES = ("seeAlso", "altLabel", "label")


def measure(source_graph=None, fragments_dir=None, bfo_graph=None) -> dict:
    declared, fragments = source_values(source_graph, fragments_dir)
    universe = dict(declared)
    universe.update(fragments)
    classes = bfo_classes(bfo_graph)

    matched, unmatched, dangling = {}, [], []
    for iri, candidates in sorted(classes.items()):
        hit = None
        for rule, name, raw in candidates:
            key = normalise(name)
            if key in universe:
                hit = (rule, universe[key])
                break
            if rule == "seeAlso":
                dangling.append({"class": iri, "seeAlso": raw,
                                 "names_no_folk_value": name})
        if hit:
            matched.setdefault(normalise(hit[1]), []).append(
                {"class": iri, "rule": hit[0], "value": hit[1]})
        else:
            unmatched.append({"class": iri,
                              "tried": [c[1] for c in candidates]})

    uncovered = sorted(universe[k] for k in set(universe) - set(matched))
    fragment_only = sorted(fragments[k]
                           for k in set(fragments) - set(declared))

    rules = {}
    for rows in matched.values():
        for row in rows:
            rules[row["rule"]] = rules.get(row["rule"], 0) + 1

    return {
        "generated_by": relative(_here),
        "source": {
            "declared_in_folk_ttl": len(declared),
            "trigger_fragments": len(fragments),
            "union": len(universe),
            "fragment_without_a_class": fragment_only,
        },
        "bfo_layer": {
            "classes": len(classes),
            "matched_a_folk_value": sum(len(v) for v in matched.values()),
            "matched_by_rule": rules,
            # A rule that never fires is indistinguishable from a rule
            # that does not work. On this corpus every pairing comes from
            # seeAlso, so the other two rest entirely on their tests.
            "rules_that_never_fired": [r for r in RULES if r not in rules],
            "unmatched": unmatched,
        },
        "coverage": {
            "folk_values_covered": len(matched),
            "folk_values_uncovered": len(uncovered),
            "uncovered": uncovered,
        },
        "dangling_see_also": dangling,
        "not_covered_by_this_tool": [
            "Whether an unmatched BFO class is a deliberate addition or an "
            "accident. Nothing in the repository records the decision, and "
            "this tool does not guess.",
            "Whether a covered value is modelled *correctly* -- only that a "
            "class claiming that name exists.",
            "The moral-foundations, Schwartz and core modules. This compares "
            "the folk layer against the folk corpus and nothing else.",
            "Any pairing that only altLabel or label would have found. Both "
            "rules fire on nothing in this corpus, so the coverage figure "
            "rests entirely on rdfs:seeAlso.",
        ],
    }


def findings(record: dict) -> list[str]:
    out = []
    coverage = record["coverage"]
    if coverage["folk_values_uncovered"]:
        total = coverage["folk_values_covered"] + coverage["folk_values_uncovered"]
        out.append(
            "%d of %d folk values have no class in the BFO folk module, so "
            "nothing built from that module -- the site class index included "
            "-- can find them. e.g. %s"
            % (coverage["folk_values_uncovered"], total,
               ", ".join(coverage["uncovered"][:6])))
    if record["dangling_see_also"]:
        out.append(
            "%d rdfs:seeAlso back-link(s) name a folk value that does not "
            "exist in the corpus. A link that reads as provenance and "
            "resolves to nothing is worse than no link. e.g. %s"
            % (len(record["dangling_see_also"]),
               record["dangling_see_also"][0]["seeAlso"]))
    if record["source"]["fragment_without_a_class"]:
        out.append(
            "%d value(s) have a trigger fragment and no class in folk.ttl, so "
            "the annotation pipeline can evoke a value the ontology cannot "
            "express: %s"
            % (len(record["source"]["fragment_without_a_class"]),
               ", ".join(record["source"]["fragment_without_a_class"][:6])))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if there is a finding")
    ap.add_argument("--json", default=None, metavar="OUT")
    ap.add_argument("--list", default=None,
                    choices=("uncovered", "unmatched", "dangling"))
    args = ap.parse_args(argv)

    record = measure()
    source, layer, coverage = (record["source"], record["bfo_layer"],
                               record["coverage"])

    if args.list:
        rows = {"uncovered": coverage["uncovered"],
                "unmatched": [r["class"] for r in layer["unmatched"]],
                "dangling": [r["seeAlso"]
                             for r in record["dangling_see_also"]]}[args.list]
        for row in rows:
            print(row)
        return 0

    print("  folk corpus")
    print("    %4d value(s) declared in folk.ttl" % source["declared_in_folk_ttl"])
    print("    %4d trigger fragment(s), %d of them naming no class"
          % (source["trigger_fragments"],
             len(source["fragment_without_a_class"])))
    print("    %4d distinct value name(s) in total" % source["union"])
    print()
    print("  BFO folk module")
    print("    %4d class(es)" % layer["classes"])
    print("    %4d matched a folk value  (%s)"
          % (layer["matched_a_folk_value"],
             ", ".join("%s %d" % (k, v)
                       for k, v in sorted(layer["matched_by_rule"].items()))
             or "none"))
    print("    %4d matched none" % len(layer["unmatched"]))
    print()
    print("  coverage: %d of %d folk values (%.0f%%)"
          % (coverage["folk_values_covered"], source["union"],
             100.0 * coverage["folk_values_covered"] / max(source["union"], 1)))
    if layer["rules_that_never_fired"]:
        print("    (every pairing came from one rule; %s fired on nothing "
              "here and rest on their tests)"
              % ", ".join(layer["rules_that_never_fired"]))

    problems = findings(record)
    if problems:
        print()
        for problem in problems:
            print("  FINDING: %s" % problem)
        print()
        print("  --list uncovered | unmatched | dangling  for the full sets")

    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, indent=2, sort_keys=True,
                      ensure_ascii=False)
            stream.write("\n")
        print("  wrote %s" % args.json)

    return 1 if (args.check and problems) else 0


if __name__ == "__main__":
    raise SystemExit(main())
