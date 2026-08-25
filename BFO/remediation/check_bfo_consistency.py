"""Run an offline HermiT consistency check over the ValueNet BFO modules."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import OWL, RDF

try:
    from owlready2 import OwlReadyInconsistentOntologyError, World, sync_reasoner
except ImportError as error:  # pragma: no cover - environment guidance
    raise SystemExit("owlready2 is required for the HermiT consistency check") from error


ROOT = Path(__file__).resolve().parents[2]
BFO_DIR = ROOT / "BFO"

TBOX_FILES = (
    BFO_DIR / "bfo-core.ttl",
    BFO_DIR / "imports" / "cco-valuenet-extract.ttl",
    BFO_DIR / "valuenet-core.ttl",
    BFO_DIR / "valuenet-schwartz-values.ttl",
    BFO_DIR / "valuenet-moral-foundations.ttl",
    BFO_DIR / "valuenet-folk.ttl",
    BFO_DIR / "valuenet-moral-epistemics.ttl",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-scenario",
        action="store_true",
        help="include valuenet-moral-epistemics-scenario.ttl",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = list(TBOX_FILES)
    if args.include_scenario:
        paths.append(BFO_DIR / "valuenet-moral-epistemics-scenario.ttl")

    graph = Graph()
    for path in paths:
        graph.parse(path, format="turtle")

    # The imported content is already merged explicitly. Removing import triples
    # prevents network access and makes this validation byte-source reproducible.
    for triple in list(graph.triples((None, OWL.imports, None))):
        graph.remove(triple)

    class_count = len(set(graph.subjects(RDF.type, OWL.Class)))

    with tempfile.TemporaryDirectory(prefix="valuenet-bfo-hermit-") as temp_dir:
        merged_path = Path(temp_dir) / "merged.owl"
        graph.serialize(merged_path, format="xml")

        world = World()
        with merged_path.open("rb") as merged_stream:
            ontology = world.get_ontology(
                "https://fandaws.com/ontology/remediation/merged-bfo-check"
            ).load(fileobj=merged_stream)
        try:
            sync_reasoner([ontology], debug=0)
        except OwlReadyInconsistentOntologyError:
            print("HermiT result: inconsistent", file=sys.stderr)
            raise SystemExit(1)

        unsatisfiable = [
            cls
            for cls in world.inconsistent_classes()
            if str(getattr(cls, "iri", cls)) != str(OWL.Nothing)
        ]

    print(f"scope: {'TBox + scenario' if args.include_scenario else 'TBox'}")
    print(f"files: {len(paths)}")
    print(f"triples: {len(graph)}")
    print(f"declared classes: {class_count}")
    print("HermiT result: consistent")
    print(f"unsatisfiable named classes: {len(unsatisfiable)}")
    if unsatisfiable:
        for cls in sorted(unsatisfiable, key=str):
            print(f"  {cls}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
