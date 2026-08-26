"""Capture the semantic fingerprints the migration gate compares against.

Counts alone are not invariants: two different graphs can have identical triple
and class counts. So every measure here records its **definition** and the
**command** that reproduces it, and the graph-level measures are canonical RDF
digests rather than sizes.

The reason this exists at all, from the record: `reasoner_metrics` silently
dropped from 306 classes to 275 when the CCO extract landed in a directory its
hardcoded file list did not know about. HermiT stayed consistent. Every test
stayed green. A move that changes *what gets loaded* looks exactly like a move
that changed nothing, and only a fingerprint captured beforehand can tell them
apart.

One measure is deliberately not an invariant. `folk_aligned.ttl`'s byte hash
**must** change when its generator moves, because the generated header records
the generator's path. Its canonical RDF digest must not. Both are recorded, with
the byte hash marked as an expected transition rather than a violation.

    python ValueNet_code/build_semantic_baseline.py [-o config/reorganization-baseline.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from marep import layout  # noqa: E402

#: Bumped when the schema or any digest definition changes, so a baseline
#: cannot be compared against one computed a different way. Version 2 replaced
#: the merged-corpus canonical digest with a ground digest plus blank-node
#: fingerprint, and replaced that fingerprint's predicate-frequency hash with
#: flattened-triple and node-signature digests.
TOOL_VERSION = 2


def canonical_digest(path: Path) -> str:
    """SHA-256 over sorted N-Triples of the canonicalized graph.

    Canonicalization makes blank-node identity irrelevant, which is what lets
    the folk source and its generated view compare equal despite different
    serializations.
    """
    import rdflib
    from rdflib.compare import to_canonical_graph
    g = rdflib.Graph()
    g.parse(str(path))
    lines = sorted(to_canonical_graph(g).serialize(format="nt").splitlines())
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def byte_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_measures(root: Path) -> dict:
    import rdflib
    from rdflib.namespace import OWL, RDF
    from marep import ontology_source as onto

    onto.clear_graph_cache()
    facts = [onto.measure_file(p, root) for p in onto.discover(root)]
    parsing = [f for f in facts if f.parses]
    g = onto.merged_graph(root, parsing)
    named = {c for c in g.subjects(RDF.type, OWL.Class)
             if isinstance(c, rdflib.URIRef)}
    triggers = rdflib.URIRef(
        "http://www.ontologydesignpatterns.org/ont/values/"
        "valuecore_with_value_frames.owl#triggers")
    trig = list(g.triples((None, triggers, None)))
    return {
        "files_discovered": {
            "value": len(facts),
            "definition": "ontology_source.discover over the repository",
        },
        "files_parsing": {
            "value": len(parsing),
            "definition": "measure_file(...).parses is True",
        },
        "distinct_triples": {
            "value": len(g),
            "definition": "len of the merged graph over all parsing files",
        },
        "named_classes": {
            "value": len(named),
            "definition": "owl:Class subjects that are rdflib.URIRef; blank-node "
                          "restrictions excluded. Counting them gave 3,703 "
                          "against a true 2,889.",
        },
        "class_declarations_summed": {
            "value": sum(f.classes for f in parsing),
            "definition": "sum of per-file class counts; double-counts a class "
                          "declared in two files, by design",
        },
        "trigger_statements": {
            "value": len(trig),
            "definition": "vcvf:triggers statements in the merged graph",
        },
        "distinct_trigger_objects": {
            "value": len({o for _, _, o in trig}),
            "definition": "distinct objects of vcvf:triggers",
        },
        # The counts above cannot detect a semantic change that preserves
        # them — a renamed class, a re-pointed subClassOf, a swapped literal.
        # That is precisely the failure this baseline exists to catch.
        "merged_ground_sha256": {
            "value": _ground_digest(g),
            "definition": "SHA-256 over sorted N-Triples of every triple with "
                          "no blank node. Catches a renamed class, a re-pointed "
                          "subClassOf, a swapped literal — changes the counts "
                          "cannot see.",
        },
        "merged_bnode_shape": {
            "value": _bnode_shape(g),
            "definition": "identity-invariant digest over the blank-node "
                          "subgraph: flattened triples with blank nodes as a "
                          "constant token, plus per-node degree and predicate "
                          "signatures. Catches changed neighbours and changed "
                          "topology; ignores relabelling. Full canonicalization "
                          "of 104,763 triples measured at about 29 minutes, "
                          "which no per-commit gate would survive.",
        },
    }


def _graph_digest(graph) -> str:
    """Full canonicalization. Affordable only for small graphs: 330 triples
    take 0.12s and 5,910 take 23s, and the cost grows worse than linearly."""
    from rdflib.compare import to_canonical_graph
    lines = sorted(to_canonical_graph(graph).serialize(format="nt").splitlines())
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def _ground_digest(graph) -> str:
    import rdflib
    lines = sorted(
        f"{s.n3()} {p.n3()} {o.n3()} ."
        for s, p, o in graph
        if not any(isinstance(t, rdflib.BNode) for t in (s, p, o)))
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def _bnode_shape(graph) -> dict:
    """Identity-invariant digest over the blank-node subgraph.

    An earlier version hashed only blank-node counts, touching-triple counts
    and predicate frequencies. That is not semantically protective: rewriting

        _:x owl:onProperty ex:p ; owl:someValuesFrom ex:A .

    to different property and class IRIs leaves every one of those numbers
    unchanged, because the predicates are still `owl:onProperty` and
    `owl:someValuesFrom` — only the objects moved. It lost term values and
    topology, not merely blank-node identity.

    Two digests instead, both linear, because full canonicalization costs about
    29 minutes over this corpus and roughly 7s per folk fragment:

    *Flattened triples.* Every blank-node-touching triple with blank nodes
    replaced by the constant token `_:B`, sorted and hashed. Named terms and
    literals survive verbatim, so the rewrite above changes the digest. Which
    blank node is which does not survive, which is the point.

    *Node signatures.* Per blank node, its in-degree, out-degree, and sorted
    predicate signature, as a multiset. Catches topology change — a triple
    moved from one blank node to another — that flattening alone would miss.
    """
    import collections
    import rdflib

    def term(t):
        return "_:B" if isinstance(t, rdflib.BNode) else t.n3()

    flattened, sigs = [], []
    out_p = collections.defaultdict(list)
    in_p = collections.defaultdict(list)
    bnodes, touching = set(), 0

    for s, p, o in graph:
        hit = [t for t in (s, o) if isinstance(t, rdflib.BNode)]
        if not hit:
            continue
        touching += 1
        bnodes.update(hit)
        flattened.append(f"{term(s)} {p.n3()} {term(o)} .")
        if isinstance(s, rdflib.BNode):
            out_p[s].append(str(p))
        if isinstance(o, rdflib.BNode):
            in_p[o].append(str(p))

    for b in bnodes:
        sigs.append("|".join([
            str(len(in_p[b])), str(len(out_p[b])),
            ",".join(sorted(out_p[b])), ",".join(sorted(in_p[b]))]))

    return {
        "blank_nodes": len(bnodes),
        "triples_touching": touching,
        "flattened_sha256": hashlib.sha256(
            "\n".join(sorted(flattened)).encode()).hexdigest(),
        "node_signature_sha256": hashlib.sha256(
            "\n".join(sorted(sigs)).encode()).hexdigest(),
    }


def reasoner_measures(root: Path) -> dict:
    from marep import ontology_source as onto
    metrics = {m.check: m for m in onto.reasoner_metrics(root)}
    return {
        "bfo_layer_classes": {
            "value": int(metrics["unsatisfiable_classes"].detail.split()[1].replace(",", ""))
            if "of" in metrics["unsatisfiable_classes"].detail else None,
            "definition": "named classes in the HermiT scope, including the "
                          "configured CCO extract",
        },
        "bfo_layer_files": {
            "value": int(metrics["reasoner_files"].value),
            "definition": "files loaded into the HermiT scope",
        },
        "bfo_layer_imports_unresolved": {
            "value": int(metrics["reasoner_imports_unresolved"].value),
            "definition": "imports naming an ontology no loaded file provides",
        },
        "bfo_layer_consistent": {
            "value": int(metrics["reasoner_consistent"].value),
            "definition": "HermiT consistency over the BFO layer",
        },
        "bfo_layer_unsatisfiable": {
            "value": int(metrics["unsatisfiable_classes"].value),
            "definition": "unsatisfiable named classes",
        },
        # The scope is the thing that silently shrank once already. A digest
        # over exactly what HermiT loads catches a scope change that leaves
        # the class count intact.
        "bfo_scope_canonical_sha256": {
            "value": _scope_digest(),
            "definition": "SHA-256 over sorted N-Triples of the canonicalized "
                          "union of layout.reasoner_scope()",
        },
        "bfo_scope_files": {
            "value": len(layout.reasoner_scope()),
            "definition": "files the layout contract declares as the HermiT scope",
        },
    }


def _scope_digest() -> str:
    import rdflib
    g = rdflib.Graph()
    for p in layout.reasoner_scope():
        g.parse(str(p))
    return _graph_digest(g)


def artifact_digests(root: Path) -> dict:
    out = {}
    pairs = [
        ("folk_source", layout.path("original-valuenet.folk-source")),
        ("folk_aligned", layout.path("original-valuenet.folk-aligned")),
        ("cco_extract", layout.path("bfo.vendor-cco") / "cco-valuenet-extract.ttl"),
    ]
    for name, p in pairs:
        entry = {
            "path": layout.relative(p),
            "canonical_sha256": canonical_digest(p),
            "canonical_is_invariant": True,
        }
        if name == "folk_aligned":
            entry["byte_sha256"] = byte_digest(p)
            entry["byte_is_invariant"] = False
            entry["byte_transition_note"] = (
                "The generated header embeds the generator's path, so this "
                "changes when the generator moves in wave 9. The canonical "
                "digest must not.")
        else:
            entry["byte_sha256"] = byte_digest(p)
            entry["byte_is_invariant"] = True
        out[name] = entry
    return out


def test_baseline(root: Path) -> dict:
    """Collected node ids, canonicalized so a directory move does not change them.

    The canonical id is the module basename plus the remainder of the pytest
    node id. A move from tests/ to tests/marep/ leaves it untouched; a renamed
    or lost test does not.
    """
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "-m", "slow or not slow"],
        capture_output=True, text=True, cwd=str(root))
    if r.returncode != 0:
        # A collection error still prints the node ids gathered before it
        # failed. Accepting that partial list would write a smaller baseline
        # and call it the truth.
        raise SystemExit("pytest collection failed; refusing to write a "
                         "baseline from a partial list.\n"
                         + r.stderr.strip()[:2000])
    ids = [ln.strip() for ln in r.stdout.splitlines()
           if "::" in ln and not ln.startswith(" ")]
    canonical = sorted(os.path.basename(i) for i in ids)
    collisions = [c for c in set(canonical) if canonical.count(c) > 1]
    return {
        "collected": len(canonical),
        "canonical_id_sha256": hashlib.sha256(
            "\n".join(canonical).encode()).hexdigest(),
        "canonical_id_collisions": sorted(collisions),
        "definition": "pytest --collect-only -q -m 'slow or not slow'; each id "
                      "reduced to basename plus node path so directory moves "
                      "do not perturb it",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)

    root = layout.repository_root()
    rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                         text=True, cwd=str(root))
    if rev.returncode != 0:
        raise SystemExit("git rev-parse HEAD failed; the baseline must record "
                         "the commit it describes.\n" + rev.stderr.strip())
    head = rev.stdout.strip()

    baseline = {
        "tool_version": TOOL_VERSION,
        "captured_at_commit": head,
        "reproduce": "python ValueNet_code/build_semantic_baseline.py",
        "corpus": corpus_measures(root),
        "reasoner": reasoner_measures(root),
        "artifacts": artifact_digests(root),
        "tests": test_baseline(root),
    }

    print(f"  commit {head[:12]}")
    for section in ("corpus", "reasoner"):
        for k, v in baseline[section].items():
            print(f"    {k:<32} {v['value']}")
    print(f"    {'tests collected':<32} {baseline['tests']['collected']}")
    print(f"    {'canonical id digest':<32} "
          f"{baseline['tests']['canonical_id_sha256'][:16]}…")
    if baseline["tests"]["canonical_id_collisions"]:
        print("\n  canonical id collisions — refusing to write:")
        for c in baseline["tests"]["canonical_id_collisions"][:10]:
            print(f"      {c}")
        return 1

    if args.out:
        target = root / args.out
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(baseline, fh, indent=2, sort_keys=False)
            fh.write("\n")
        os.replace(tmp, target)
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
