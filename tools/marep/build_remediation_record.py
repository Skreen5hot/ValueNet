# SPDX-License-Identifier: Apache-2.0
"""Record exactly what a source-data repair changed, and what it did not.

    python tools/marep/build_remediation_record.py

The transition matrix measured the corpus as it stood at eol-hardened-v1.
Repairing the corpus does not make that measurement wrong, and
regenerating it would be worse than useless: the experiment's whole
content is a comparison of three checkouts of one commit, and re-running
it against a later corpus would quietly replace the thing it proved.

So the matrix stays frozen and this artifact carries the difference. The
successor baseline may then cite a matrix from an earlier commit -- but
only while a record like this one enumerates the gap, and only while the
enumeration survives being checked against git.

WHAT MAKES THIS NOT A LOOPHOLE

A record saying "nothing else changed" is worth nothing if the only
evidence for it is the record. Two things make it checkable:

  * The set of Turtle files that differ between the two commits is asked
    of git, not declared here. Unchanged blob at an unchanged path means
    unchanged triples -- the document base is derived from the path, so
    both inputs to the parse are identical. Renames are therefore
    disqualifying and are refused rather than absorbed.

  * The triples are diffed by parsing both versions, not by reading the
    text diff. `<1>` and `1` differ by two characters and by everything
    that matters.

`build_semantic_baseline.py` re-derives the changed-file set itself
before accepting this record, so a hand-edited or stale copy is caught by
the consumer rather than trusted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

FORMAT_VERSION = 1
GENERATOR = "tools/marep/build_remediation_record.py"
DEFAULT_BEFORE = "eol-hardened-v1"
ARTIFACT = "config/remediation-record.json"

#: Not remediated, deliberately. The archive is inert: nothing in the
#: repository opens it, no corpus measurement discovers it, and it is
#: upstream's bytes. Repacking it would fork a binary nobody reads.
ARCHIVE = "ThatsAllFolks/MFRC_1k_ESWC.zip"
DETECTION = (
    "python -c \"import zipfile,rdflib,collections;"
    "z=zipfile.ZipFile('" + ARCHIVE + "');"
    "P=rdflib.URIRef('http://www.ontologydesignpatterns.org/ont/dul/"
    "DUL.owl#hasDataValue');"
    "c=collections.Counter();"
    "[c.update({n:sum(1 for _ in rdflib.Graph().parse("
    "data=z.read(n).decode('utf-8'),format='turtle',"
    "publicID='https://probe.invalid/'+n).triples((None,P,None)))}) "
    "for n in z.namelist() if n.endswith('.ttl') "
    "and not n.startswith('__MACOSX')];"
    "print(sum(1 for v in c.values() if v),sum(c.values()))\"")


def git(*args, **kw):
    r = subprocess.run(["git", *args], cwd=str(_root),
                       capture_output=True, text=True, **kw)
    if r.returncode:
        raise SystemExit("git " + " ".join(args) + " failed: " + r.stderr[-400:])
    return r.stdout


def changed_turtle(before: str, after: str) -> tuple[list, list]:
    """Which Turtle files differ, and whether any of them moved.

    Asked of git rather than declared, and the rename check matters: the
    document base is the repository-relative path, so the same bytes at a
    new path parse to different terms. A rename is a corpus change this
    record has no way to express, so it is refused.
    """
    out = git("diff", "--name-status", "--find-renames", before, after,
              "--", "*.ttl")
    changed, renamed = [], []
    for line in out.splitlines():
        parts = line.split("\t")
        if parts[0].startswith("R"):
            renamed.append((parts[1], parts[2]))
        else:
            changed.append(parts[-1])
    return sorted(changed), renamed


def triples_at(rev: str | None, rel: str) -> set:
    """Parse one version of one file under its own stable document base."""
    import rdflib

    from marep import ontology_source as onto

    if rev is None:
        text = (_root / rel).read_text(encoding="utf-8")
    else:
        text = git("show", rev + ":" + rel)
    g = rdflib.Graph()
    g.parse(data=text, format="turtle", publicID=onto.public_id(rel))
    return set(g)


def archive_record() -> dict:
    """Opened here, at generation time, and never by a test.

    Counting the members means reading the archive; asserting the count
    later does not. A test that opened it would make an inert artifact
    into a corpus, which is the thing this record exists to say it is
    not.
    """
    import rdflib

    P = rdflib.URIRef("http://www.ontologydesignpatterns.org/ont/dul/"
                      "DUL.owl#hasDataValue")
    path = _root / ARCHIVE
    raw = path.read_bytes()
    members = occurrences = graphs = 0
    misdeclared = 0
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
                  "(<1>, <22>, <4200>) rather than literals, and the "
                  "property is declared owl:DataTypeProperty, which is not "
                  "an OWL term. Both are the FRED export's behaviour, not "
                  "damage to this copy.",
        "excluded_from_live_corpus": True,
        "why_excluded": "marep.ontology_source.discover() walks Turtle "
                        "files in the working tree. Archive members are "
                        "not files in the working tree, so no corpus "
                        "measure, digest or reasoner run has ever seen "
                        "them. The one member extracted into "
                        "ThatsAllFolks/MFRC_1k_graphs/ is measured; the "
                        "other members are not.",
        "disposition": "permanent upstream debt; bytes preserved. "
                       "Repacking would fork an unaudited binary that "
                       "nothing reads and no check measures, and would "
                       "diverge from upstream for no observable effect.",
        "detection": DETECTION,
        "note": "No runtime test opens this archive. Tests assert its "
                "sha256 over the bytes, which is how 'unchanged' is "
                "checked without treating it as a corpus.",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=DEFAULT_BEFORE,
                    help="the state this repair is measured against")
    ap.add_argument("-o", "--out", default=ARTIFACT)
    args = ap.parse_args(argv)

    dirty = git("status", "--porcelain").strip()
    permitted = {args.out}
    unexpected = [l[3:].strip().strip('"') for l in dirty.splitlines()
                  if l[3:].strip().strip('"') not in permitted]
    if unexpected:
        raise SystemExit(
            "the working tree has uncommitted changes, so this record would "
            "describe a state no commit contains: "
            + ", ".join(sorted(unexpected)[:6]))

    # The tag is what a reader should be told; the matrix's own input
    # commit is what the diff must start from. Those are not the same
    # commit: evidence is committed after the input it describes, so the
    # matrix inside eol-hardened-v1 names that tag's parent.
    #
    # Citing the tag while diffing from the parent is only honest if the
    # two hold the same corpus, so that is checked rather than assumed.
    tag_commit = git("rev-parse", args.before + "^{commit}").strip()
    matrix = json.loads(
        (_root / "config/eol-transition-matrix.json").read_text(
            encoding="utf-8"))
    before = matrix["input_commit"]
    after = git("rev-parse", "HEAD").strip()
    if before == after:
        raise SystemExit(
            "before and after are the same commit; there is nothing to "
            "record and a matrix from this commit needs no exemption.")
    drift, drift_renames = changed_turtle(before, tag_commit)
    if drift or drift_renames:
        raise SystemExit(
            "%s and the commit its matrix measured (%s) hold different "
            "corpora: %s. Citing the tag as the before-state would then be "
            "wrong, because the matrix never measured what the tag "
            "contains." % (args.before, before[:12],
                           (drift + [r[1] for r in drift_renames])[:4]))

    changed, renamed = changed_turtle(before, after)
    if renamed:
        raise SystemExit(
            "Turtle files were renamed between %s and %s: %s. The document "
            "base is the repository-relative path, so a rename changes the "
            "terms without changing the bytes. This record cannot express "
            "that." % (before[:12], after[:12], renamed[:3]))
    if not changed:
        raise SystemExit(
            "no Turtle file differs between %s and HEAD, so the matrix from "
            "%s still describes this corpus and needs no record."
            % (args.before, args.before))

    print("  before %s (matrix input; %s is %s)  after %s"
          % (before[:12], args.before, tag_commit[:12], after[:12]))
    print("  %d Turtle file(s) differ" % len(changed))

    removed, added = [], []
    for rel in changed:
        was, now = triples_at(before, rel), triples_at(None, rel)
        for t in sorted(was - now, key=str):
            removed.append({"file": rel,
                            "triple": " ".join(x.n3() for x in t)})
        for t in sorted(now - was, key=str):
            added.append({"file": rel,
                          "triple": " ".join(x.n3() for x in t)})
        print("    %-52s %+d triple(s), %d removed, %d added"
              % (rel, len(now) - len(was), len(was - now), len(now - was)))

    doc = {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "before_tag": args.before,
        "before_tag_commit": tag_commit,
        "before_commit": before,
        "before_commit_is": "the commit the transition matrix measured. "
                            "It is the parent of " + args.before + ", which "
                            "carries the evidence generated from it. No "
                            "Turtle file differs between the two, so citing "
                            "the tag as the before-state is accurate; that "
                            "was checked, not assumed.",
        "after_commit": after,
        "working_tree_clean": not dirty,
        "why": "The transition matrix measured the corpus at "
               + args.before + ". This repair changed the corpus after "
               "that measurement. The matrix is left frozen because its "
               "content is a comparison of three checkouts of one commit; "
               "re-running it against a later corpus would replace the "
               "experiment rather than repeat it. This record is what "
               "lets the successor baseline cite the older matrix without "
               "pretending the two describe the same corpus.",
        "corpus_files_changed": changed,
        "substitutions": {
            "removed": removed,
            "added": added,
            "count": len(removed),
        },
        "not_remediated": {"archive": archive_record()},
    }
    if len(removed) != len(added):
        doc["substitutions"]["note"] = (
            "removed and added counts differ, so this is not a pure "
            "substitution: %d removed against %d added"
            % (len(removed), len(added)))

    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    target = _root / args.out
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, target)

    print()
    print("  %d triple(s) removed, %d added" % (len(removed), len(added)))
    print("  archive %s unchanged at %s"
          % (ARCHIVE, doc["not_remediated"]["archive"]["sha256"][:16]))
    print("  wrote %s (sha256 %s)"
          % (args.out, hashlib.sha256(text.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
