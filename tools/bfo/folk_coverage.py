# SPDX-License-Identifier: Apache-2.0
"""How much of the folk corpus the BFO folk module actually carries. Read-only.

Applies nothing. It reports coverage in both directions, by kind, and says
which rule matched each pairing, so a decision about the gap can be made on
measurements rather than on the word "comprehensive".

    python tools/bfo/folk_coverage.py
    python tools/bfo/folk_coverage.py --check      # exit 1 on a finding
    python tools/bfo/folk_coverage.py --json OUT

WHY THIS EXISTS

Somebody demonstrating the site searched for "frugal" and found nothing.
`folk:Frugality` is in the corpus -- it is in ThatsAllFolks/folk.ttl, it is in
the generated alignment view, and the ThatsAllFolks README names it explicitly
as an example of what the module contributes. What it was not in is
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

COVERAGE IS REPORTED BY KIND (D-014)

Every folk value is one of four kinds, and the kinds are not added together,
because they are different claims:

  exact           a BFO class is the value. Paired by rdfs:seeAlso into a folk
                  namespace, or by rdfs:label less its " Disposition" or
                  " Role" suffix.
  synonym         a BFO class carries the value's word as skos:altLabel, and
                  the class is not that value's exact class. D-014's
                  substitution test decides which words may be labels.
  correspondence  a mapping assertion relates a BFO entity to the value's
                  corpus IRI. The value evokes or indicates the class without
                  naming it; annotation can reach the class, search by the
                  value's name cannot.
  excluded        recorded in config/folk-membership.json as not a
                  value-related realizable entity. The only kind no triple
                  carries, so the only one read from a record.

The first two together are how many corpus values the ontology names. A value
of no kind is pending, which is a finding, and so is a value of two kinds:
D-014 gives each value one.

A BFO class that pairs exactly with no value is reported as unmatched rather
than as wrong. It may be a deliberate addition drawn from Schwartz or from
somewhere else, and D-014's Table B records which; this tool does not guess.
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

VN_CORE = "https://fandaws.com/ontology/bfo/valuenet-core#"

#: The project's mapping annotation properties. A correspondence is any of
#: them pointing at a corpus value's IRI.
MAPPING_PREDICATES = tuple(VN_CORE + name for name in (
    "hasRelatedConceptualMatch", "historicallyCorrespondsTo",
    "hasBroaderConceptualMatch"))

SKOS_ALT_LABEL = "http://www.w3.org/2004/02/skos/core#altLabel"

SUFFIX = re.compile(r"(Disposition|Role)$")
LABEL_SUFFIX = re.compile(r"\s+(Disposition|Role)$")

SOURCE = "original-valuenet.folk-source"
FRAGMENTS = "original-valuenet.folk-fragments"
BFO_FOLK = "bfo.module.folk"
MAPPINGS = "bfo.module.mappings"
MEMBERSHIP = "config.folk-membership"

KINDS = ("exact", "synonym", "correspondence", "excluded")


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
        for obj in graph.objects(subject, rdflib.URIRef(SKOS_ALT_LABEL)):
            candidates.append(("altLabel", str(obj), None))
        for obj in graph.objects(subject, rdflib.RDFS.label):
            candidates.append(("label", LABEL_SUFFIX.sub("", str(obj)), None))
        out[str(subject)] = candidates
    return out


def recorded_exclusions(path=None) -> list[dict]:
    """The exclusions D-014 records, as rows with at least a `value`."""
    path = path if path is not None else component(MEMBERSHIP).resolve()
    with open(str(path), encoding="utf-8") as stream:
        return json.load(stream)["excluded"]


#: Every rule `measure` may use. Named here so the report can say which
#: ones never fired, rather than leaving a reader to infer it from a
#: number that happens to add up.
RULES = ("seeAlso", "altLabel", "label")
EXACT_RULES = ("seeAlso", "label")


def measure(source_graph=None, fragments_dir=None, bfo_graph=None,
            mapping_graph=None, excluded=None) -> dict:
    declared, fragments = source_values(source_graph, fragments_dir)
    universe = dict(declared)
    universe.update(fragments)
    if bfo_graph is None:
        bfo_graph = rdflib.Graph()
        bfo_graph.parse(str(component(BFO_FOLK).resolve()), format="turtle")
    classes = bfo_classes(bfo_graph)
    if mapping_graph is None:
        mapping_graph = rdflib.Graph()
        mapping_graph.parse(str(component(MAPPINGS).resolve()), format="turtle")
    if excluded is None:
        excluded = recorded_exclusions()

    exact, synonym, unmatched, dangling = {}, {}, [], []
    for iri, candidates in sorted(classes.items()):
        hit = None
        for rule, name, raw in candidates:
            if rule not in EXACT_RULES:
                continue
            key = normalise(name)
            if key in universe:
                hit = (rule, key)
                break
            if rule == "seeAlso":
                dangling.append({"class": iri, "seeAlso": raw,
                                 "names_no_folk_value": name})
        if hit:
            exact.setdefault(hit[1], []).append(
                {"class": iri, "rule": hit[0], "value": universe[hit[1]]})
        else:
            unmatched.append({"class": iri,
                              "tried": [c[1] for c in candidates]})
        # A class's alternative labels usually repeat its own value's word;
        # only a label naming a *different* corpus value is a synonym.
        own = hit[1] if hit else None
        for rule, name, _raw in candidates:
            key = normalise(name)
            if rule == "altLabel" and key in universe and key != own:
                synonym.setdefault(key, []).append(
                    {"class": iri, "rule": rule, "value": universe[key],
                     "label": name})

    correspondence, unknown_targets = {}, []
    for graph in (mapping_graph, bfo_graph):
        for predicate in MAPPING_PREDICATES:
            for subject, obj in graph.subject_objects(rdflib.URIRef(predicate)):
                text = str(obj)
                if not text.startswith(ODP):
                    continue
                key = normalise(text[len(ODP):])
                if key not in universe:
                    unknown_targets.append(text)
                    continue
                row = {"class": str(subject), "value": universe[key],
                       "predicate": predicate[len(VN_CORE):], "target": text}
                if row not in correspondence.get(key, []):
                    correspondence.setdefault(key, []).append(row)

    exclusion, unknown_exclusions = {}, []
    for row in excluded:
        key = normalise(row["value"])
        if key in universe:
            exclusion[key] = row
        else:
            unknown_exclusions.append(row["value"])

    tables = {"exact": exact, "synonym": synonym,
              "correspondence": correspondence, "excluded": exclusion}
    by_kind = {kind: 0 for kind in KINDS}
    pending, overlapping = [], []
    for key in sorted(universe):
        kinds = [kind for kind in KINDS if key in tables[kind]]
        if not kinds:
            pending.append(universe[key])
        elif len(kinds) > 1:
            overlapping.append({"value": universe[key], "kinds": kinds})
        else:
            by_kind[kinds[0]] += 1

    rules = {}
    for table in (exact, synonym):
        for rows in table.values():
            for row in rows:
                rules[row["rule"]] = rules.get(row["rule"], 0) + 1

    return {
        "generated_by": relative(_here),
        "source": {
            "declared_in_folk_ttl": len(declared),
            "trigger_fragments": len(fragments),
            "union": len(universe),
            "fragment_without_a_class": sorted(
                fragments[k] for k in set(fragments) - set(declared)),
        },
        "bfo_layer": {
            "classes": len(classes),
            "matched_a_folk_value": sum(len(v) for v in exact.values()),
            "matched_by_rule": rules,
            # A rule that never fires is indistinguishable from a rule
            # that does not work. On this corpus no pairing comes from
            # rdfs:label, so that rule rests entirely on its test.
            "rules_that_never_fired": [r for r in RULES if r not in rules],
            "unmatched": unmatched,
        },
        "coverage": {
            "by_kind": by_kind,
            "pending": pending,
            "named_by_the_ontology": by_kind["exact"] + by_kind["synonym"],
            "in_more_than_one_kind": overlapping,
            "synonyms": sorted(
                ({"value": r["value"], "class": r["class"], "label": r["label"]}
                 for rows in synonym.values() for r in rows),
                key=lambda r: (r["value"], r["class"])),
            "correspondences": sorted(
                (r for rows in correspondence.values() for r in rows),
                key=lambda r: (r["value"], r["class"])),
            "excluded": sorted(r["value"] for r in exclusion.values()),
            "not_a_folk_value": {
                "correspondence_targets": sorted(set(unknown_targets)),
                "exclusions": sorted(unknown_exclusions),
            },
        },
        "dangling_see_also": dangling,
        "not_covered_by_this_tool": [
            "Whether an unmatched BFO class is a deliberate addition or an "
            "accident. D-014's Table B records the decision for each; this "
            "tool does not guess.",
            "Whether a covered value is modelled *correctly* -- only that a "
            "class, label, mapping or exclusion claiming it exists. Whether a "
            "word should be a label or a correspondence is D-014's "
            "substitution test, which a string comparison cannot apply.",
            "The moral-foundations, Schwartz and core modules, except as the "
            "subjects of correspondences. This compares the folk layer and "
            "the mapping layer against the folk corpus and nothing else.",
            "Any pairing only rdfs:label would have found. That rule fires on "
            "nothing in this corpus, so exact coverage rests on rdfs:seeAlso.",
        ],
    }


def findings(record: dict) -> list[str]:
    out = []
    coverage = record["coverage"]
    if coverage["pending"]:
        total = record["source"]["union"]
        out.append(
            "%d of %d folk values are of no kind -- no class, alternative "
            "label, correspondence or recorded exclusion -- so D-014's "
            "coverage is incomplete. e.g. %s"
            % (len(coverage["pending"]), total,
               ", ".join(coverage["pending"][:6])))
    if coverage["in_more_than_one_kind"]:
        out.append(
            "%d folk value(s) are recorded as more than one kind, and D-014 "
            "gives each value one: %s"
            % (len(coverage["in_more_than_one_kind"]),
               ", ".join("%s (%s)" % (row["value"], " and ".join(row["kinds"]))
                         for row in coverage["in_more_than_one_kind"][:6])))
    unknown = coverage["not_a_folk_value"]
    if unknown["correspondence_targets"] or unknown["exclusions"]:
        out.append(
            "a correspondence or exclusion names something the folk corpus "
            "does not have: %s"
            % ", ".join(unknown["correspondence_targets"][:3]
                        + unknown["exclusions"][:3]))
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
                    choices=("pending", "synonyms", "correspondences",
                             "excluded", "unmatched", "dangling"))
    args = ap.parse_args(argv)

    record = measure()
    source, layer, coverage = (record["source"], record["bfo_layer"],
                               record["coverage"])

    if args.list:
        rows = {"pending": coverage["pending"],
                "synonyms": ["%s -> %s" % (r["value"], r["class"])
                             for r in coverage["synonyms"]],
                "correspondences": ["%s -> %s" % (r["value"], r["class"])
                                    for r in coverage["correspondences"]],
                "excluded": coverage["excluded"],
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
    print("    %4d matched a folk value exactly" % layer["matched_a_folk_value"])
    print("    %4d matched none exactly" % len(layer["unmatched"]))
    print()
    print("  coverage of %d folk values, by kind (D-014)" % source["union"])
    for kind in KINDS:
        print("    %4d %s" % (coverage["by_kind"][kind], kind))
    print("    %4d pending" % len(coverage["pending"]))
    print("  the ontology names %d of them (exact and synonym); "
          "correspondences are what annotation can reach, not names"
          % coverage["named_by_the_ontology"])
    if layer["rules_that_never_fired"]:
        print("    (%s fired on nothing here and rest%s on %s test%s)"
              % (", ".join(layer["rules_that_never_fired"]),
                 "" if len(layer["rules_that_never_fired"]) > 1 else "s",
                 "their" if len(layer["rules_that_never_fired"]) > 1 else "its",
                 "s" if len(layer["rules_that_never_fired"]) > 1 else ""))

    problems = findings(record)
    if problems:
        print()
        for problem in problems:
            print("  FINDING: %s" % problem)
        print()
        print("  --list pending | synonyms | correspondences | excluded | "
              "unmatched | dangling  for the full sets")

    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, indent=2, sort_keys=True,
                      ensure_ascii=False)
            stream.write("\n")
        print("  wrote %s" % args.json)

    return 1 if (args.check and problems) else 0


if __name__ == "__main__":
    raise SystemExit(main())
