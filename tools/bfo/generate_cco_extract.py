"""Generate the pinned CCO subset required by the ValueNet BFO layer.

The generator copies complete descriptions of the requested CCO entities,
recursively follows named CCO entities used by logical axioms, includes inverse
property descriptions, closes blank-node expressions, and adds declarations
for referenced entities. It intentionally omits owl:imports so validation is
offline and reproducible against the project's supplied BFO core.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

import sys

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.compare import to_canonical_graph
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD


CCO = Namespace("https://www.commoncoreontologies.org/")
EXTRACT_IRI = URIRef("https://fandaws.com/ontology/imports/cco-valuenet-extract")
EXTRACT_VERSION_IRI = URIRef(
    "https://fandaws.com/ontology/imports/cco-valuenet-extract/2.2-2026-08-25-phase6"
)
CCO_RELEASE_URL = URIRef(
    "https://github.com/CommonCoreOntology/CommonCoreOntologies/releases/tag/v2.2"
)
CCO_LICENSE_URL = URIRef(
    "https://github.com/CommonCoreOntology/CommonCoreOntologies/blob/v2.2/LICENSE"
)
SOURCE_ARTIFACT_URL = (
    "https://raw.githubusercontent.com/CommonCoreOntology/"
    "CommonCoreOntologies/v2.2/src/cco-merged/CommonCoreOntologiesMerged.ttl"
)
SOURCE_COMMIT = "0bc7d33e1bc09fd4693366119ab4e03cb0340042"
SOURCE_RELEASE = "v2.2"
# Root by upward search for the layout contract, so this script can ask
# where it lives rather than asserting it. The manifest it writes records
# its own path, and that value was written literally: after the bfo wave
# it named BFO/remediation/, a directory that no longer exists, and
# regenerating re-emitted the same stale string.
_here = Path(__file__).resolve()
_root = next((d for d in _here.parents
             if (d / "config" / "repository-layout.yaml").is_file()), None)
if _root is None:  # pragma: no cover - a tree without the contract
    raise SystemExit(f"no config/repository-layout.yaml above {_here}")
sys.path.insert(0, str(_root))

from marep.layout import component, relative  # noqa: E402


def script_path() -> str:
    """This script's repository-relative path, from the contract."""
    return relative(component("tool.generate-cco-extract").resolve())


SCRIPT_VERSION = "4"

ROOT_TERMS = (
    URIRef(CCO.ont00000037),  # Act of Observation
    URIRef(CCO.ont00000253),  # Information Bearing Entity
    URIRef(CCO.ont00000636),  # Act of Appraisal
    URIRef(CCO.ont00000853),  # Descriptive Information Content Entity
    URIRef(CCO.ont00000958),  # Information Content Entity
    URIRef(CCO.ont00000965),  # Prescriptive Information Content Entity
    URIRef(CCO.ont00001017),  # Agent
    URIRef(CCO.ont00001921),  # has input
    URIRef(CCO.ont00001986),  # has output
)

DECLARATION_TYPES = {
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.AnnotationProperty,
    OWL.NamedIndividual,
}

LOGICAL_REFERENCE_PREDICATES = {
    RDFS.subClassOf,
    RDFS.subPropertyOf,
    RDFS.domain,
    RDFS.range,
    OWL.equivalentClass,
    OWL.equivalentProperty,
    OWL.disjointWith,
    OWL.inverseOf,
    OWL.onProperty,
    OWL.someValuesFrom,
    OWL.allValuesFrom,
    OWL.hasValue,
    OWL.onClass,
    OWL.onDataRange,
    OWL.unionOf,
    OWL.intersectionOf,
    OWL.complementOf,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_blank_node_closure(source: Graph, target: Graph, node: BNode) -> None:
    pending = [node]
    seen: set[BNode] = set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        for triple in source.triples((current, None, None)):
            target.add(triple)
            if isinstance(triple[2], BNode):
                pending.append(triple[2])


def add_entity_description(source: Graph, target: Graph, entity: URIRef) -> None:
    triples = list(source.triples((entity, None, None)))
    if not triples:
        raise ValueError(f"Selected entity is not described in source: {entity}")
    for triple in triples:
        target.add(triple)
        if isinstance(triple[2], BNode):
            add_blank_node_closure(source, target, triple[2])


def cco_logical_dependencies(graph: Graph) -> set[URIRef]:
    dependencies: set[URIRef] = set()
    for _, predicate, obj in graph:
        if predicate not in LOGICAL_REFERENCE_PREDICATES:
            continue
        if isinstance(obj, URIRef) and str(obj).startswith(str(CCO)):
            dependencies.add(obj)
    return dependencies


def add_inverse_descriptions(source: Graph, target: Graph, roots: set[URIRef]) -> set[URIRef]:
    inverses: set[URIRef] = set()
    for root in roots:
        for subject in source.subjects(OWL.inverseOf, root):
            if isinstance(subject, URIRef) and str(subject).startswith(str(CCO)):
                add_entity_description(source, target, subject)
                inverses.add(subject)
        for obj in source.objects(root, OWL.inverseOf):
            if isinstance(obj, URIRef) and str(obj).startswith(str(CCO)):
                add_entity_description(source, target, obj)
                inverses.add(obj)
    return inverses


def add_referenced_declarations(source: Graph, target: Graph) -> None:
    referenced: set[URIRef] = set()
    for subject, predicate, obj in list(target):
        if isinstance(subject, URIRef):
            referenced.add(subject)
        if isinstance(predicate, URIRef):
            referenced.add(predicate)
        if isinstance(obj, URIRef):
            referenced.add(obj)

    for entity in referenced:
        for declaration_type in DECLARATION_TYPES:
            if (entity, RDF.type, declaration_type) in source:
                target.add((entity, RDF.type, declaration_type))


def build_extract(source: Graph) -> Graph:
    extract = Graph()
    selected: set[URIRef] = set(ROOT_TERMS)

    for root in ROOT_TERMS:
        add_entity_description(source, extract, root)
    selected.update(add_inverse_descriptions(source, extract, selected))

    while True:
        new_dependencies = cco_logical_dependencies(extract) - selected
        if not new_dependencies:
            break
        for dependency in sorted(new_dependencies, key=str):
            add_entity_description(source, extract, dependency)
        selected.update(new_dependencies)
        selected.update(add_inverse_descriptions(source, extract, new_dependencies))

    add_referenced_declarations(source, extract)

    extract.add((EXTRACT_IRI, RDF.type, OWL.Ontology))
    extract.add((EXTRACT_IRI, OWL.versionIRI, EXTRACT_VERSION_IRI))
    extract.add(
        (
            EXTRACT_IRI,
            OWL.versionInfo,
            Literal("CCO 2.2 ValueNet extract, Phase 6 revision 2026-08-25", lang="en"),
        )
    )
    extract.add((EXTRACT_IRI, DCTERMS.source, CCO_RELEASE_URL))
    extract.add((EXTRACT_IRI, DCTERMS.license, CCO_LICENSE_URL))
    extract.add((EXTRACT_IRI, DCTERMS.created, Literal(date(2026, 8, 25), datatype=XSD.date)))
    extract.add((DCTERMS.source, RDF.type, OWL.AnnotationProperty))
    extract.add((DCTERMS.license, RDF.type, OWL.AnnotationProperty))
    extract.add((DCTERMS.created, RDF.type, OWL.AnnotationProperty))

    canonical = Graph()
    for triple in to_canonical_graph(extract):
        canonical.add(triple)
    return canonical


def write_manifest(output: Path, manifest_path: Path, source_path: Path) -> None:
    manifest = {
        "extract_id": "cco-valuenet-v2.2-2026-08-25-phase6",
        "source_project": "CCO",
        "source_release": SOURCE_RELEASE,
        "source_commit": SOURCE_COMMIT,
        "source_artifact_url": SOURCE_ARTIFACT_URL,
        "source_sha256": sha256(source_path),
        "retrieved_on": "2026-08-24",
        "license": {
            "spdx": "BSD-3-Clause",
            "url": str(CCO_LICENSE_URL),
            "attribution_required": True,
        },
        "root_terms": [str(term) for term in ROOT_TERMS],
        "closure_policy": {
            "declarations": True,
            "annotations": True,
            "logical_axioms": True,
            "referenced_entities": "recursive",
            "import_declarations": "omit-documented",
        },
        "generated_by": {
            "script": script_path(),
            "version": SCRIPT_VERSION,
        },
        "extract_sha256": sha256(output),
        "modifications": [
            "Selected complete root-entity descriptions from the CCO 2.2 merged release.",
            "Expanded the roots with the Phase 5 CCO superclass alignments for moral epistemics.",
            "Expanded the roots with CCO Act of Observation for the Phase 6 behavioral-observation alignment.",
            "Included inverse-property descriptions and recursive named CCO logical dependencies.",
            "Included recursive blank-node OWL expression closure and referenced entity declarations.",
            "Omitted upstream owl:imports; ValueNet supplies its pinned BFO core separately.",
            "Canonicalized blank nodes and serialized as Turtle.",
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh-provenance", action="store_true",
        help="rewrite only the contract-derived fields of the existing "
             "manifest, after verifying the extract it describes is "
             "byte-identical. Rebuilding the extract needs the pinned "
             "upstream CCO release, which is not in this repository; "
             "moving this script does not change the extract, only where "
             "the manifest says the extract came from")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--expected-source-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if not args.refresh_provenance:
        missing = [n for n in (
            "source", "expected_source_sha256", "output", "manifest")
            if getattr(args, n) is None]
        if missing:
            parser.error("required unless --refresh-provenance: "
                         + ", ".join("--" + m.replace("_", "-")
                                     for m in missing))
    return args


def refresh_provenance() -> None:
    """Bring `generated_by.script` back in line with the contract.

    The layout contract declares an allowance for this literal with
    `remove_after_wave: bfo`, meaning it must be corrected once that wave
    runs. Before this existed the only declared remedy was to regenerate,
    which re-emitted the identical stale string -- an obligation that
    could be recorded, reported and never discharged.

    The extract's digest is checked first. Rewriting provenance onto an
    extract this manifest no longer describes would produce a file that
    is internally consistent and wrong."""
    from marep.layout import bfo_artifact

    manifest_path = bfo_artifact("cco-valuenet-extract.manifest.json")
    extract_path = bfo_artifact("cco-valuenet-extract.ttl")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    recorded, actual = data.get("extract_sha256"), sha256(extract_path)
    if recorded != actual:
        raise SystemExit(
            f"refusing to refresh provenance: {extract_path.name} has "
            f"digest {actual}, but the manifest describes {recorded}. "
            f"Regenerate the extract instead.")

    want = script_path()
    have = data.get("generated_by", {}).get("script")
    if have == want:
        print(f"provenance already current: {want}")
        return
    data["generated_by"]["script"] = want
    manifest_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"refreshed generated_by.script: {have} -> {want}")


def main() -> None:
    args = parse_args()
    if args.refresh_provenance:
        refresh_provenance()
        return
    actual_source_sha256 = sha256(args.source)
    if actual_source_sha256.lower() != args.expected_source_sha256.lower():
        raise SystemExit(
            "Source checksum mismatch: "
            f"expected {args.expected_source_sha256.lower()}, got {actual_source_sha256}"
        )

    source = Graph()
    source.parse(args.source, format="turtle")
    extract = build_extract(source)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(extract.serialize(format="turtle"), encoding="utf-8")
    write_manifest(args.output, args.manifest, args.source)

    print(f"wrote {len(extract)} triples to {args.output}")
    print(f"wrote manifest to {args.manifest}")


if __name__ == "__main__":
    main()
