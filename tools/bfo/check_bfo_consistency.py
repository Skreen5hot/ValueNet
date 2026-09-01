# SPDX-License-Identifier: Apache-2.0
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


# Root by upward search for the layout contract, and each artifact by
# name through it. `parents[2]` happens to stay correct from tools/bfo/
# because that sits at the same depth as BFO/remediation/, but the
# literal `ROOT / "BFO"` below it does not: the bfo wave turns BFO/ into
# ontology/bfo/ and every path here would resolve to nothing.
_here = Path(__file__).resolve()
ROOT = next((d for d in _here.parents
             if (d / "config" / "repository-layout.yaml").is_file()), None)
if ROOT is None:  # pragma: no cover - a tree without the contract
    raise SystemExit(f"no config/repository-layout.yaml above {_here}")
sys.path.insert(0, str(ROOT))

from marep.layout import bfo_artifact  # noqa: E402

#: The T-box HermiT loads. Deliberately NOT layout.reasoner_scope(): that
#: set also carries valuenet-mappings.ttl, and which files enter the
#: consistency check decides what "consistent" means here. Only the
#: resolution changed; the membership is left as its author set it.
TBOX_FILES = tuple(bfo_artifact(n) for n in (
    "bfo-core.ttl",
    "cco-valuenet-extract.ttl",
    "valuenet-core.ttl",
    "valuenet-schwartz-values.ttl",
    "valuenet-moral-foundations.ttl",
    "valuenet-folk.ttl",
    "valuenet-moral-epistemics.ttl",
))


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
        paths.append(bfo_artifact("valuenet-moral-epistemics-scenario.ttl"))

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
