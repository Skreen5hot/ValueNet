# SPDX-License-Identifier: Apache-2.0
"""Record what changed in the corpus since the transition matrix measured it.

    python tools/marep/build_remediation_record.py

The matrix compares three checkouts of one commit. Once the corpus moves,
re-running it would not repeat that experiment, it would replace it with a
different one wearing the same name. So the matrix stays frozen and this
artifact carries the difference, and the successor baseline may cite the
older matrix only while a record like this enumerates the gap.

AN ORDERED LEDGER, NOT ONE INTERVAL

The span from the matrix's input to HEAD can contain several unrelated
changes. It currently contains two: a source-data repair, and a pass that
annotated the ontology headers with licence and title metadata. A single
verdict over the whole span can only report the coarser of them, so a
record promising to say *why* the digest moved could only say "something
did".

Every commit in the span that touched Turtle is a boundary; consecutive
boundaries are the events. Boundaries come from git, so an event cannot
be omitted by forgetting to list one, and the chain is required to start
at the matrix input, end at HEAD, and cover exactly the files that differ
across the whole span.

WHAT MAKES A CLASSIFICATION CHECKABLE

`publication-metadata` means the ontology said the same things and only
its description of itself changed. Five conditions, all derived:

  * every changed ground triple has a subject the graph types
    `owl:Ontology` -- a changed class annotation is not header metadata;
  * every changed predicate is in HEADER_PREDICATES, which deliberately
    excludes `skos:definition`;
  * the named class inventory is identical;
  * the named subclass edges are identical; and
  * the blank-node fingerprint is identical.

The last was missing and is the one that matters most. A change confined
to an OWL restriction or a SHACL shape moves no ground triple, no named
class and no named-to-named edge, so the other four conditions cannot see
it at all and would have called it metadata.

Ground triples are what `merged_ground_sha256` measures; the fingerprint
is the baseline's own `_bnode_shape`, imported rather than reimplemented.
Between them they cover every triple, which is why the pair is the test
and either alone is not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

FORMAT_VERSION = 2
GENERATOR = "tools/marep/build_remediation_record.py"
DEFAULT_BEFORE = "eol-hardened-v1"
ARTIFACT = "config/remediation-record.json"
MATRIX = "config/eol-transition-matrix.json"

#: Permitted on an ontology header for a change to count as publication
#: metadata. `skos:definition` is absent on purpose: a changed class
#: definition changes what the ontology says.
HEADER_PREDICATES = {
    "http://purl.org/dc/terms/license",
    "http://purl.org/dc/terms/title",
    "http://purl.org/dc/terms/description",
    "http://www.w3.org/2000/01/rdf-schema#comment",
    "http://www.w3.org/2000/01/rdf-schema#label",
    "http://www.w3.org/2000/01/rdf-schema#seeAlso",
    "http://www.w3.org/2002/07/owl#versionInfo",
}

ARCHIVE = "ThatsAllFolks/MFRC_1k_ESWC.zip"
#: Reproduces every count this record stores -- affected members,
#: occurrences, and members carrying the misspelled property declaration.
#: An earlier version printed only the first, so two of the three recorded
#: numbers had no command a reader could run to check them.
DETECTION = (
    "python -c \"import zipfile,rdflib;"
    "z=zipfile.ZipFile('" + ARCHIVE + "');"
    "P=rdflib.URIRef('http://www.ontologydesignpatterns.org/ont/dul/"
    "DUL.owl#hasDataValue');"
    "m=o=d=0;"
    "\nfor n in z.namelist():"
    "\n    t=z.read(n).decode('utf-8','replace') "
    "if n.endswith('.ttl') and not n.startswith('__MACOSX') else None"
    "\n    if t is None or 'hasDataValue' not in t: continue"
    "\n    d+= 'owl:DataTypeProperty' in t"
    "\n    g=rdflib.Graph()"
    "\n    g.parse(data=t,format='turtle',"
    "publicID='https://probe.invalid/'+n)"
    "\n    c=sum(1 for _ in g.triples((None,P,None)))"
    "\n    m+=bool(c); o+=c"
    "\nprint('members_affected',m,'occurrences',o,"
    "'members_with_misdeclared_property',d)\"")


def git(*args, check=True) -> list[str]:
    r = subprocess.run(["git", *args], cwd=str(_root),
                       capture_output=True, text=True)
    if r.returncode and check:
        raise SystemExit("git " + " ".join(args) + " failed: "
                         + r.stderr.strip()[-400:])
    return r.stdout.splitlines()


def changed_turtle(before: str, after: str) -> tuple[list, list]:
    """Which Turtle files differ, and whether any moved.

    The document base is the repository-relative path, so the same bytes
    at a new path parse to different terms. A rename is a corpus change
    this record cannot express, so it is refused rather than absorbed.
    """
    changed, renamed = [], []
    for line in git("diff", "--name-status", "--find-renames", before, after,
                    "--", "*.ttl"):
        parts = line.split("\t")
        if parts[0].startswith("R"):
            renamed.append((parts[1], parts[2]))
        else:
            changed.append(parts[-1])
    return sorted(changed), renamed


def event_boundaries(before: str, after: str) -> list:
    """The (lo, hi) pairs the ledger must consist of.

    One function, used by the generator to build the ledger and by the
    consumer to check it, so the two cannot disagree about what the
    events should have been. A consumer that only replays the intervals a
    record hands it will accept a record that collapsed two events into
    one: the replay succeeds, and the distinction the ledger exists to
    preserve is gone.

    Every commit in the span that touched Turtle is a boundary. The final
    event runs through to `after` rather than stopping at the last such
    commit, because commits after it changed no Turtle and therefore no
    corpus -- a Turtle commit followed by a README commit would otherwise
    produce a chain that could not reach HEAD, and every later evidence
    cycle would hit it.
    """
    touching = git("rev-list", "--reverse", before + ".." + after,
                   "--", "*.ttl")
    if not touching:
        return []
    bounds = [before] + touching
    # Extend through the trailing non-Turtle commits. Sound because the
    # Turtle diff from the previous boundary to `after` is identical to
    # the diff to `touching[-1]`.
    bounds[-1] = after
    return list(zip(bounds, bounds[1:]))


def parse_at(rev: str | None, rel: str):
    """One version of one file, under its own stable document base."""
    import rdflib

    from marep import ontology_source as onto

    if rev is None:
        text = (_root / rel).read_text(encoding="utf-8")
    else:
        raw = subprocess.run(["git", "show", rev + ":" + rel], cwd=str(_root),
                             capture_output=True).stdout
        text = raw.decode("utf-8")
    g = rdflib.Graph()
    g.parse(data=text, format="turtle", publicID=onto.public_id(rel))
    return g


def ground(triples) -> set:
    """Triples with no blank node.

    A blank node is renamed by every parse, so a set difference reports
    every triple touching one as both added and removed -- on SHACL
    shapes that turns a fourteen-triple change into four hundred. These
    are exactly what `merged_ground_sha256` measures.
    """
    import rdflib

    return {t for t in triples
            if not any(isinstance(x, rdflib.BNode) for x in t)}


def logical_shape(triples) -> tuple[set, set]:
    """Named class inventory and named subclass edges."""
    import rdflib
    from rdflib.namespace import OWL, RDF, RDFS

    classes = {s for s, p, o in triples
               if p == RDF.type and o == OWL.Class
               and isinstance(s, rdflib.URIRef)}
    edges = {(s, o) for s, p, o in triples
             if p == RDFS.subClassOf
             and isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef)}
    return classes, edges


def ontology_subjects(triples) -> set:
    """Resources the graph itself types owl:Ontology."""
    import rdflib
    from rdflib.namespace import OWL, RDF

    return {str(s) for s, p, o in triples
            if p == RDF.type and o == OWL.Ontology
            and isinstance(s, rdflib.URIRef)}


def _baseline_module():
    import importlib.util

    path = _root / "tools/marep/build_semantic_baseline.py"
    spec = importlib.util.spec_from_file_location("bsb_for_shape", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bnode_shape_of(triples) -> dict:
    """The baseline's fingerprint over a triple set."""
    import rdflib

    g = rdflib.Graph()
    for t in triples:
        g.add(t)
    return _baseline_module()._bnode_shape(g)


def bnode_shape(graphs) -> dict:
    """The baseline's identity-invariant blank-node fingerprint.

    Imported rather than reimplemented, so this record and the digest it
    explains measure the same thing. Computed over the changed files
    only: a blank node never spans a Turtle document, so unchanged files
    contribute identical components to the corpus-wide value either way.
    """
    import rdflib

    merged = rdflib.Graph()
    for g in graphs:
        for t in g:
            merged.add(t)
    return _baseline_module()._bnode_shape(merged)


def classify_change(was_all: set, now_all: set, added: list,
                    removed: list) -> tuple[dict, dict, dict]:
    """Classify one change from its two graphs. No git, no filesystem.

    Pure so it can be falsified directly: a blank-node-only edit and a
    changed class definition are both constructible in four lines, and
    neither needs a commit to exist.

    Returns (classification, shape_before, shape_after).
    """
    cw, ew = logical_shape(was_all)
    cn, en = logical_shape(now_all)
    headers = ontology_subjects(was_all) | ontology_subjects(now_all)

    subjects = sorted({e["triple"].split(" ", 1)[0].strip("<>")
                       for e in added + removed})
    predicates = sorted({e["triple"].split(" ", 2)[1].strip("<>")
                         for e in added + removed})
    header_subjects_only = bool(subjects) and all(s in headers
                                                  for s in subjects)
    header_predicates_only = bool(predicates) and all(p in HEADER_PREDICATES
                                                      for p in predicates)

    shape_before = bnode_shape_of(was_all)
    shape_after = bnode_shape_of(now_all)
    shape_unchanged = shape_before == shape_after

    is_metadata = (header_subjects_only and header_predicates_only
                   and cw == cn and ew == en and shape_unchanged)

    return ({
        "change_class": ("publication-metadata" if is_metadata
                         else "content-change"),
        "header_subjects_only": header_subjects_only,
        "header_predicates_only": header_predicates_only,
        "named_classes_unchanged": cw == cn,
        "subclass_edges_unchanged": ew == en,
        "blank_node_shape_unchanged": shape_unchanged,
        "subjects_touched": subjects,
        "predicates_touched": predicates,
        "basis": "publication-metadata requires all five: every changed "
                 "ground triple on a subject the graph types owl:Ontology, "
                 "every changed predicate an approved header predicate, the "
                 "named class inventory and named subclass edges identical, "
                 "and the blank-node fingerprint identical. Ground triples "
                 "and the fingerprint between them cover every triple; "
                 "either alone leaves a change invisible.",
    }, shape_before, shape_after)


def build_event(lo: str, hi: str, files: list[str], head: str) -> dict:
    """One boundary-to-boundary change, derived and classified on its own."""
    was_all, now_all = set(), set()
    added, removed = [], []
    for rel in files:
        was = parse_at(lo, rel)
        now = parse_at(None if hi == head else hi, rel)
        was_all |= set(was)
        now_all |= set(now)
        gw, gn = ground(was), ground(now)
        for t in sorted(gw - gn, key=str):
            removed.append({"file": rel,
                            "triple": " ".join(x.n3() for x in t)})
        for t in sorted(gn - gw, key=str):
            added.append({"file": rel, "triple": " ".join(x.n3() for x in t)})

    classification, shape_before, shape_after = classify_change(
        was_all, now_all, added, removed)

    return {
        "before_commit": lo,
        "after_commit": hi,
        "files": files,
        "substitutions": {
            "added": added,
            "removed": removed,
            "count": len(added) + len(removed),
            "scope": "ground triples only -- those with no blank node. "
                     "Blank-node structure is compared by the fingerprint "
                     "below, because a blank node is renamed by every parse "
                     "and cannot be diffed by identity.",
        },
        "blank_node_shape": {
            "before": shape_before,
            "after": shape_after,
            "unchanged": shape_before == shape_after,
            "scope": "computed over this event's changed files only, which "
                     "is sound because a blank node never spans a Turtle "
                     "document",
        },
        "classification": classification,
    }


def archive_record() -> dict:
    """Opened here, at generation time, and never by a test."""
    import rdflib

    P = rdflib.URIRef("http://www.ontologydesignpatterns.org/ont/dul/"
                      "DUL.owl#hasDataValue")
    path = _root / ARCHIVE
    raw = path.read_bytes()
    members = occurrences = graphs = misdeclared = 0
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".ttl") or name.startswith("__MACOSX"):
                continue
            graphs += 1
            text = z.read(name).decode("utf-8", errors="replace")
            if "hasDataValue" not in text:
                continue
            if "owl:DataTypeProperty" in text:
                misdeclared += 1
            g = rdflib.Graph()
            try:
                g.parse(data=text, format="turtle",
                        publicID="https://probe.invalid/" + name)
            except Exception:
                continue
            n = sum(1 for _ in g.triples((None, P, None)))
            if n:
                members += 1
                occurrences += n
    return {
        "path": ARCHIVE,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "turtle_members": graphs,
        "members_affected": members,
        "occurrences": occurrences,
        "members_with_misdeclared_property": misdeclared,
        "defect": "dul:hasDataValue objects are relative IRI references "
                  "rather than literals, and the property is declared "
                  "owl:DataTypeProperty, which is not an OWL term. Both are "
                  "the FRED export's behaviour, not damage to this copy.",
        "excluded_from_live_corpus": True,
        "why_excluded": "discover() walks Turtle files in the working tree. "
                        "Archive members are not files in the working tree, "
                        "so no corpus measure has ever seen them.",
        "disposition": "permanent upstream debt; bytes preserved. Repacking "
                       "would fork an unaudited binary that nothing reads.",
        "detection": DETECTION,
        "note": "No runtime test opens this archive. Tests assert its "
                "sha256 over the bytes.",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=DEFAULT_BEFORE)
    ap.add_argument("-o", "--out", default=ARTIFACT)
    args = ap.parse_args(argv)

    dirty = "\n".join(git("status", "--porcelain"))
    unexpected = [l[3:].strip().strip('"') for l in dirty.splitlines()
                  if l[3:].strip().strip('"') != args.out]
    if unexpected:
        raise SystemExit(
            "the working tree has uncommitted changes, so this record would "
            "describe a state no commit contains: "
            + ", ".join(sorted(unexpected)[:6]))

    tag_commit = git("rev-parse", args.before + "^{commit}")[0]
    matrix = json.loads((_root / MATRIX).read_text(encoding="utf-8"))
    before = matrix["input_commit"]
    after = git("rev-parse", "HEAD")[0]

    # Citing the tag while diffing from its parent is honest only if the
    # two hold the same corpus, so that is checked rather than assumed.
    drift, drift_renames = changed_turtle(before, tag_commit)
    if drift or drift_renames:
        raise SystemExit(
            "%s and the commit its matrix measured (%s) hold different "
            "corpora: %s" % (args.before, before[:12],
                             (drift + [r[1] for r in drift_renames])[:4]))

    print("  matrix input %s  ->  HEAD %s" % (before[:12], after[:12]))

    events = []
    for lo, hi in event_boundaries(before, after):
        changed, renamed = changed_turtle(lo, hi)
        if renamed:
            raise SystemExit("Turtle renamed between %s and %s: %s"
                             % (lo[:12], hi[:12], renamed[:3]))
        if not changed:
            continue
        events.append(build_event(lo, hi, changed, after))

    if not events:
        raise SystemExit(
            "no Turtle changed between %s and HEAD, so the matrix still "
            "describes this corpus and needs no record." % args.before)

    span, _ = changed_turtle(before, after)
    covered = sorted({f for e in events for f in e["files"]})
    if covered != sorted(span):
        raise SystemExit(
            "the ledger covers %s but %s differ across the whole span; an "
            "intervening change is missing" % (covered[:4], sorted(span)[:4]))
    if events[0]["before_commit"] != before:
        raise SystemExit("the ledger starts at %s, not at the matrix input %s"
                         % (events[0]["before_commit"][:12], before[:12]))
    if events[-1]["after_commit"] != after:
        raise SystemExit("the ledger ends at %s, not at HEAD %s"
                         % (events[-1]["after_commit"][:12], after[:12]))

    for e in events:
        c = e["classification"]
        print("    %s..%s  %-22s %2d file(s)  +%d/-%d ground  bnode %s"
              % (e["before_commit"][:8], e["after_commit"][:8],
                 c["change_class"], len(e["files"]),
                 len(e["substitutions"]["added"]),
                 len(e["substitutions"]["removed"]),
                 "same" if c["blank_node_shape_unchanged"] else "MOVED"))

    doc = {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "before_tag": args.before,
        "before_tag_commit": tag_commit,
        "before_commit": before,
        "before_commit_is": "the commit the transition matrix measured. It "
                            "is the parent of " + args.before + ", which "
                            "carries the evidence generated from it. No "
                            "Turtle differs between the two; that was "
                            "checked, not assumed.",
        "after_commit": after,
        "working_tree_clean": not dirty,
        "why": "The matrix measured the corpus at " + args.before + " and is "
               "frozen: its content is a comparison of three checkouts of "
               "one commit, so re-running it against a later corpus would "
               "replace the experiment rather than repeat it. This ledger "
               "is what lets the successor baseline cite it without "
               "pretending the two describe the same corpus.",
        "corpus_files_changed": sorted(span),
        "events": events,
        "not_remediated": {"archive": archive_record()},
    }

    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    target = _root / args.out
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, target)
    print()
    print("  %d event(s); archive %s unchanged at %s"
          % (len(events), ARCHIVE,
             doc["not_remediated"]["archive"]["sha256"][:16]))
    print("  wrote %s (sha256 %s)"
          % (args.out, hashlib.sha256(text.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
