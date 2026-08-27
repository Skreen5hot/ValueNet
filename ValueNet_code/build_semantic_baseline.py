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
import collections
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

from marep import layout  # noqa: E402

#: Bumped when the schema or any digest definition changes, so a baseline
#: cannot be compared against one computed a different way.
#:
#:   1  merged-corpus canonical digest
#:   2  ground digest plus a flattened/node-signature blank-node fingerprint
#:   3  that fingerprint replaced by connected-component canonicalization,
#:      after the version-2 form was shown to collide on non-isomorphic graphs
#:   4  the test baseline records the default-run selection as well as the
#:      all-markers total, after a silent deselection left the total intact
TOOL_VERSION = 4


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
                          "subgraph: blank nodes partitioned into connected "
                          "components, every triple touching a component "
                          "collected with its named and literal anchors, each "
                          "component canonicalized independently, sorted "
                          "component digests hashed. Complete rather than "
                          "heuristic. Affordable because components are OWL "
                          "restrictions of a few triples each; the whole "
                          "corpus canonicalized at once measured about 29 "
                          "minutes.",
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

    Two earlier attempts were unsound, and the second failed in a way worth
    recording because it looked convincing.

    Hashing predicate frequencies missed a changed object: rewriting
    `owl:onProperty ex:p` to `ex:q` leaves the predicate multiset identical.

    Flattening every blank node to one token then also missed which neighbours
    belonged to which node. These two graphs are not isomorphic, and produced
    identical digests under both the flattened and the signature hash:

        _:a ex:p ex:X ; ex:q ex:Y .      _:a ex:p ex:X ; ex:q ex:V .
        _:b ex:p ex:U ; ex:q ex:V .      _:b ex:p ex:U ; ex:q ex:Y .

    Degree and predicate signatures cannot restore an association that
    flattening destroyed.

    So: partition the blank nodes into connected components, take every triple
    touching each component — named and literal anchors included —
    canonicalize each component independently, and hash the sorted component
    digests. Canonicalization is complete, and it is affordable here because
    the components are small: the whole corpus canonicalized at once was
    measured at about 29 minutes, while its components are OWL restrictions
    and list cells of a few triples each.
    """
    import collections
    import rdflib
    from rdflib.compare import to_canonical_graph

    # Union-find over blank nodes sharing a triple.
    parent: dict = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    touching_triples = []
    bnodes = set()
    for s, p, o in graph:
        hit = [t for t in (s, o) if isinstance(t, rdflib.BNode)]
        if not hit:
            continue
        touching_triples.append((s, p, o))
        bnodes.update(hit)
        for b in hit:
            find(b)
        if len(hit) == 2:
            union(hit[0], hit[1])

    members = collections.defaultdict(set)
    for b in bnodes:
        members[find(b)].add(b)

    by_component = collections.defaultdict(list)
    for s, p, o in touching_triples:
        anchor = find(s) if isinstance(s, rdflib.BNode) else find(o)
        by_component[anchor].append((s, p, o))

    digests = []
    for root_node, triples in by_component.items():
        sub = rdflib.Graph()
        for t in triples:
            sub.add(t)
        lines = sorted(to_canonical_graph(sub).serialize(format="nt").splitlines())
        digests.append(hashlib.sha256("\n".join(lines).encode()).hexdigest())

    sizes = collections.Counter(len(v) for v in members.values())
    return {
        "blank_nodes": len(bnodes),
        "triples_touching": len(touching_triples),
        "components": len(by_component),
        "largest_component_nodes": max(sizes) if sizes else 0,
        "component_digest_sha256": hashlib.sha256(
            "\n".join(sorted(digests)).encode()).hexdigest(),
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
            "byte_sha256": byte_digest(p),
            "byte_is_invariant": name != "folk_aligned",
        }
        if name == "folk_aligned":
            entry["byte_transition_note"] = (
                "The generated header embeds the generator's path, so this "
                "changes when the generator moves in the original-valuenet "
                "wave. The canonical digest must not.")
        out[name] = entry
    return out


def _collect(root: Path, marker: str | None) -> list[str]:
    """Canonical node ids under a marker expression, or a named failure.

    The canonical id is the module basename plus the remainder of the pytest
    node id. A move from tests/ to tests/marep/ leaves it untouched; a renamed
    or lost test does not.
    """
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    if marker is not None:
        cmd += ["-m", marker]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root))
    if r.returncode != 0:
        # A collection error still prints the node ids gathered before it
        # failed. Accepting that partial list would write a smaller baseline
        # and call it the truth.
        raise SystemExit("pytest collection failed; refusing to write a "
                         "baseline from a partial list.\n"
                         + r.stderr.strip()[:2000])
    ids = [ln.strip() for ln in r.stdout.splitlines()
           if "::" in ln and not ln.startswith(" ")]
    return sorted(os.path.basename(i) for i in ids)


def test_baseline(root: Path) -> dict:
    """Both totals, because either one alone can hold still while it lies.

    Version 3 recorded only the count under `-m 'slow or not slow'` -- every
    test, selected or not. That number cannot move when a test is silently
    deselected, and one was: after the competency scopes became component ids
    the literal `"BFO/"` in CHEAP_SCOPES matched nothing, eight tests left the
    default run, and the collected total stayed 539 with a green suite.

    So the split is recorded too. A test moving from selected to deselected
    changes `default_selected` and its hash while `collected` holds steady,
    which is exactly the shape of that regression.

    The two counts are easy to confuse, and comparing the wrong pair reads
    as agreement: version 3 stored a single `collected`, so a reader
    checking it against version 4's `default_selected` is comparing an
    all-markers total against a default-run selection. They are different
    measurements and there is no reason for them to match.
    """
    every = _collect(root, "slow or not slow")
    default = _collect(root, None)
    collisions = [c for c in set(every) if every.count(c) > 1]
    deselected = sorted((collections.Counter(every)
                         - collections.Counter(default)).elements())
    return {
        "collected": len(every),
        "default_selected": len(default),
        "default_deselected": len(deselected),
        "canonical_id_sha256": hashlib.sha256(
            "\n".join(every).encode()).hexdigest(),
        "default_selected_sha256": hashlib.sha256(
            "\n".join(default).encode()).hexdigest(),
        "deselected_ids": deselected,
        "canonical_id_collisions": sorted(collisions),
        "definition": "pytest --collect-only -q, run twice: once with "
                      "-m 'slow or not slow' for `collected` and once with the "
                      "configured default for `default_selected`. Each id is "
                      "reduced to its basename plus node path so directory "
                      "moves do not perturb it. Both are recorded because a "
                      "silent deselection leaves `collected` unchanged.",
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
