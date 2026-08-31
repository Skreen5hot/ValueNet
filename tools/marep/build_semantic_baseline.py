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

    python tools/marep/build_semantic_baseline.py [-o config/reorganization-baseline.json]
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
#:   5  every measurement parse resolves against a stable document base
#:      instead of the file's own location, and the corpus is measured
#:      from an LF working tree. A version-4 digest describes the machine
#:      and checkout that produced it; a version-5 digest describes the
#:      corpus. The two are not comparable and the version says so.
TOOL_VERSION = 5


def canonical_digest(path: Path) -> str:
    """SHA-256 over sorted N-Triples of the canonicalized graph.

    Canonicalization makes blank-node identity irrelevant, which is what lets
    the folk source and its generated view compare equal despite different
    serializations.
    """
    import rdflib
    from rdflib.compare import to_canonical_graph
    g = rdflib.Graph()
    # The same stable base the corpus measurements use. An artifact
    # canonicalized against its own filesystem path would carry the
    # checkout directory into its digest.
    from marep import ontology_source as _onto
    _onto.parse_source(g, path, layout.repository_root())
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
        from marep import ontology_source as _onto
        _onto.parse_source(g, p, layout.repository_root())
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


#: Where the measured half of the transition record comes from.
#:
#: It is loaded, never typed. Every number in it was produced by
#: tools/marep/build_transition_matrix.py and is re-derivable by running
#: that tool; the baseline records the artifact's path and digest so a
#: reader can tell which run they are looking at. An earlier version of
#: this file carried the same numbers as Python literals, and one of them
#: was a digest transcribed from an abbreviated log -- correct in its
#: first ten characters and invented in the remaining fifty-four.
MATRIX_ARTIFACT = "config/eol-transition-matrix.json"

#: The half that is a policy statement rather than a measurement. These
#: are decisions and their reasons, and they are not derivable from any
#: run.
TRANSITION_POLICY = {
    "supersedes": {
        "baseline": "config/reorganization-baseline.json",
        "tag": "reorg-pre-move-v1",
        "tool_version": 4,
    },
    "document_base": {
        "before": "the parsed file's own absolute filesystem path",
        "after": "https://valuenet.invalid/source/v1/<repo-relative-path>",
        "why": (
            "ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl writes "
            "ns7:hasDataValue <1>, a relative IRI reference. Resolved "
            "against the file's location it became a file: IRI holding "
            "the checkout directory, so the corpus digest was a function "
            "of where the repository sat on disk. The frozen value is "
            "reproducible only at the original path; see the matrix "
            "artifact's path_dependence section for the measurement."),
    },
    "line_endings": {
        "before": "whatever core.autocrlf produced; CRLF on Windows",
        "after": "LF, pinned by *.ttl text eol=lf in .gitattributes",
        "why": (
            "Committed content was always LF; the checkout converted it, "
            "so byte digests recorded the platform. A CRLF inside a "
            "multi-line literal is part of that literal's value, so the "
            "conversion also changes annotation triples -- enumerated in "
            "the matrix artifact, not summarised here."),
    },
    "known_exceptions": {
        "relative_iri": {
            "file": "ThatsAllFolks/MFRC_1k_graphs/357_GRAPH.ttl",
            "term": "ns7:hasDataValue <1>",
            "status": "unremediated upstream source-data debt",
            "note": (
                "A stable base makes the measurement reproducible. It "
                "does not make the term correct, and the intended range "
                "of hasDataValue has not been established. Remediation "
                "is a separate task."),
        },
    },
}


MATRIX_FORMAT_VERSION = 2
MATRIX_GENERATOR = "tools/marep/build_transition_matrix.py"
EVIDENCE_ORCHESTRATOR = "tools/marep/build_evidence.py"
REMEDIATION_ARTIFACT = "config/remediation-record.json"
REMEDIATION_GENERATOR = "tools/marep/build_remediation_record.py"
REMEDIATION_FORMAT_VERSION = 1
MATRIX_TAG = "reorg-post-move-v1"
EXPECTED_CELLS = {"A": (False, False), "B": (True, False),
                  "C": (True, True)}


def load_remediation(root: Path, matrix_commit: str,
                     head: str) -> dict | None:
    """The only way a matrix may describe an earlier corpus.

    The transition matrix compares three checkouts of one commit. Once
    the corpus is repaired, re-running it would not repeat that
    experiment, it would replace it with a different one wearing the
    same name -- so the matrix is frozen and the gap is recorded
    instead.

    A record asserting the gap would be worth nothing on its own, so
    the list of changed Turtle files is re-derived here, from git, and
    compared against what the record claims. A stale record, a
    hand-edited one, or one describing a different pair of commits is
    refused. Renames are refused outright: the document base is the
    repository-relative path, so the same bytes at a new path are
    different terms.
    """
    import hashlib

    path = root / REMEDIATION_ARTIFACT
    if not path.is_file():
        return None
    raw = path.read_bytes()
    doc = json.loads(raw.decode("utf-8"))

    def bad(why):
        raise SystemExit(
            "refusing the remediation record: " + why + ". It is the "
            "only thing permitting a transition matrix measured at a "
            "different commit, so it is not accepted on its word. "
            "Regenerate it with " + REMEDIATION_GENERATOR + ".")

    if doc.get("format_version") != REMEDIATION_FORMAT_VERSION:
        bad("format version %r" % doc.get("format_version"))
    if doc.get("generated_by") != REMEDIATION_GENERATOR:
        bad("produced by %r" % doc.get("generated_by"))
    if doc.get("working_tree_clean") is not True:
        bad("it was produced from a tree with uncommitted changes")
    if doc.get("before_commit") != matrix_commit:
        bad("it describes a repair from %s, but the matrix was measured "
            "at %s" % (str(doc.get("before_commit"))[:12],
                       matrix_commit[:12]))
    if doc.get("after_commit") != head:
        bad("it describes a repair landing at %s, not %s"
            % (str(doc.get("after_commit"))[:12], head[:12]))

    # Asked of git, not read from the record.
    out = subprocess.run(
        ["git", "diff", "--name-status", "--find-renames",
         matrix_commit, head, "--", "*.ttl"],
        capture_output=True, text=True, cwd=str(root))
    if out.returncode:
        bad("git could not compare %s with %s"
            % (matrix_commit[:12], head[:12]))
    actual, renamed = [], []
    for line in out.stdout.splitlines():
        parts = line.split("	")
        (renamed if parts[0].startswith("R") else actual).append(parts[-1])
    if renamed:
        bad("Turtle files were renamed between the two commits (%s); a "
            "rename changes the document base and therefore the terms, "
            "which this record cannot express" % renamed[:2])
    if sorted(doc.get("corpus_files_changed") or []) != sorted(actual):
        bad("it lists %s as changed, git says %s"
            % (sorted(doc.get("corpus_files_changed") or [])[:4],
               sorted(actual)[:4]))

    subs = doc.get("substitutions") or {}
    if not subs.get("removed") or not subs.get("added"):
        bad("it enumerates no triples, so it documents nothing")

    archive = (doc.get("not_remediated") or {}).get("archive") or {}
    if len(str(archive.get("sha256", ""))) != 64:
        bad("it records no digest for the archive it declines to repair")

    return {
        "artifact": REMEDIATION_ARTIFACT,
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "before_tag": doc.get("before_tag"),
        "before_commit": doc["before_commit"],
        "after_commit": doc["after_commit"],
        "corpus_files_changed": doc["corpus_files_changed"],
        "substitutions": subs,
        "not_remediated": doc["not_remediated"],
        "verified": "the changed-file list was re-derived from git by "
                    "this baseline rather than taken from the record",
    }


def load_transition(root: Path, expected_commit: str) -> dict:
    """The policy statement, plus measurements that survive checking.

    Key presence is not validation. A matrix produced with --allow-dirty,
    or produced from a different commit, or missing a cell, satisfies a
    check that only asks whether the fields exist -- and would then be
    cited in this baseline as though it described this commit.
    """
    import hashlib

    path = root / MATRIX_ARTIFACT
    if not path.is_file():
        raise SystemExit(
            "no transition matrix at " + MATRIX_ARTIFACT + ". Generate "
            "both artifacts with python " + EVIDENCE_ORCHESTRATOR + " from "
            "a clean checkout of this commit; this baseline cites the "
            "matrix's measurements and will not invent them.")
    raw = path.read_bytes()
    doc = json.loads(raw.decode("utf-8"))

    def bad(why):
        # Both artifacts, not just this one. Regenerating the matrix
        # alone leaves the reader to notice that the baseline has to
        # follow, which is the same half-instruction the published
        # `reproduce` field carried until it was corrected.
        raise SystemExit("refusing the transition matrix: " + why
                         + ". Regenerate both artifacts with python "
                         + EVIDENCE_ORCHESTRATOR + " from a clean checkout "
                         "of this commit.")

    if doc.get("format_version") != MATRIX_FORMAT_VERSION:
        bad("format version %r, expected %r"
            % (doc.get("format_version"), MATRIX_FORMAT_VERSION))
    if doc.get("generated_by") != MATRIX_GENERATOR:
        bad("produced by %r" % doc.get("generated_by"))
    if doc.get("measured_from_tag") != MATRIX_TAG:
        bad("measured from %r, expected %r"
            % (doc.get("measured_from_tag"), MATRIX_TAG))
    if doc.get("working_tree_clean") is not True:
        bad("it was produced from a tree with uncommitted changes, so it "
            "is a diagnostic and not evidence")
    remediation = None
    if doc.get("input_commit") != expected_commit:
        # Not automatically wrong: a source-data repair moves the corpus
        # forward while the experiment stays where it was measured. But
        # it is wrong unless the gap is enumerated and the enumeration
        # survives being checked against git.
        remediation = load_remediation(
            root, str(doc.get("input_commit")), expected_commit)
        if remediation is None:
            bad("it measured %s but this baseline describes %s, and no "
                "%s enumerates the difference"
                % (str(doc.get("input_commit"))[:12], expected_commit[:12],
                   REMEDIATION_ARTIFACT))

    cells = doc.get("cells") or {}
    if set(cells) != set(EXPECTED_CELLS):
        bad("cells %s, expected %s"
            % (sorted(cells), sorted(EXPECTED_CELLS)))
    for name, (hardened, lf) in EXPECTED_CELLS.items():
        cell = cells[name]
        if (cell.get("hardened"), cell.get("lf")) != (hardened, lf):
            bad("cell %s declares hardened=%r lf=%r, expected %r/%r"
                % (name, cell.get("hardened"), cell.get("lf"), hardened, lf))
        digest = cell.get("corpus", {}).get("merged_ground_sha256", "")
        if len(digest) != 64 or any(
                c not in "0123456789abcdef" for c in digest):
            bad("cell %s has no usable ground digest" % name)

    nonbool = sorted(k for k, v in (doc.get("invariants") or {}).items()
                     if not isinstance(v, bool))
    if nonbool:
        bad("invariants must be booleans; %s are not, and a consumer that "
            "checks them for truth would pass on any non-empty value"
            % nonbool)

    for key in ("path_dependence", "line_ending_transition", "invariants",
                "invariant_scope", "relative_iris"):
        if key not in doc:
            bad("missing %r" % key)

    measured = {
        "artifact": MATRIX_ARTIFACT,
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "format_version": doc["format_version"],
        "input_commit": doc["input_commit"],
        "working_tree_clean": doc["working_tree_clean"],
        "cells": {k: {"label": v["label"], "hardened": v["hardened"],
                      "lf": v["lf"],
                      "ground": v["corpus"]["merged_ground_sha256"],
                      "eol_distribution": v["eol"]["distribution"],
                      "eol_aggregate_sha256": v["eol"]["aggregate_sha256"]}
                  for k, v in cells.items()},
        "path_dependence": doc["path_dependence"],
        "line_ending_transition": doc["line_ending_transition"],
        "invariants": doc["invariants"],
        "invariant_scope": doc["invariant_scope"],
        "relative_iris": doc["relative_iris"],
    }
    if remediation is not None:
        measured["describes_corpus_at"] = doc["input_commit"]
        measured["corpus_repaired_since"] = remediation
    return dict(TRANSITION_POLICY, measured=measured)

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)

    from marep import ontology_source as onto
    root = layout.repository_root()
    rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                         text=True, cwd=str(root))
    if rev.returncode != 0:
        raise SystemExit("git rev-parse HEAD failed; the baseline must record "
                         "the commit it describes.\n" + rev.stderr.strip())
    head = rev.stdout.strip()

    # The commit this describes must be one somebody else can check out.
    # Measuring a dirty tree and recording HEAD attributes the result to a
    # commit that does not contain what was measured.
    #
    # One exception, by path and no wider: the matrix artifact is written
    # immediately before this runs, so it is untracked at exactly this
    # moment. A blanket override would have let any uncommitted change
    # through while producing a file indistinguishable from a clean
    # measurement.
    PERMITTED_UNTRACKED = {MATRIX_ARTIFACT}
    status = subprocess.run(["git", "status", "--porcelain"],
                            capture_output=True, text=True, cwd=str(root))
    unexpected = []
    for line in status.stdout.splitlines():
        rel = line[3:].strip().strip('"')
        if rel not in PERMITTED_UNTRACKED:
            unexpected.append(rel)
    if unexpected:
        raise SystemExit(
            "the working tree has changes beyond the matrix artifact, so "
            "this baseline would describe a state no commit contains: "
            + ", ".join(sorted(unexpected)[:6])
            + ". Commit the measurement code and policies first.")
    tree_state = ("clean apart from the matrix artifact"
                  if status.stdout.strip() else "clean")
    baseline = {
        "tool_version": TOOL_VERSION,
        # The commit measured, not the commit this file will land in.
        "input_commit": head,
        "input_tree_state": tree_state,
        # Naming this builder alone was false. It cites the matrix and
        # refuses one measured at any commit but its own, so run on its
        # own at a later commit it exits 1 -- which is the refusal working
        # and the instruction wrong. The two artifacts are produced
        # together or not at all.
        "reproduce": {
            "command": "python " + EVIDENCE_ORCHESTRATOR,
            "from": "a clean checkout of input_commit",
            "why": "this baseline cites " + MATRIX_ARTIFACT + " and refuses "
                   "a matrix measured at any other commit, so the two are "
                   "generated together. The commit they are committed in is "
                   "necessarily later than the one they describe.",
            "expect": "the same values in every field except input_commit, "
                      "the matrix digest cited here, and cell A -- which is "
                      "the unhardened parser and is path-dependent by "
                      "definition.",
        },
        "policy": {
            "document_base": onto.SOURCE_BASE,
            "line_endings": "lf",
            "measured_from": "the working tree, which .gitattributes pins to LF",
        },
        "transition": load_transition(root, head),
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
