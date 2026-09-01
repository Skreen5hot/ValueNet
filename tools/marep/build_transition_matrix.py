# SPDX-License-Identifier: Apache-2.0
"""Measure the semantic-measurement hardening, and write down what it measured.

    python tools/marep/build_transition_matrix.py -o config/eol-transition-matrix.json

Two changes landed together: the document base stopped being the parsed
file's own location, and the working tree stopped being whatever
`core.autocrlf` produced. Read as one difference they invite one explanation,
so they are separated:

    A  CRLF checkout + filesystem base   the pre-hardening measurement
    B  CRLF checkout + stable base       the base change alone
    C  LF checkout   + stable base       the base change plus line endings

A and B are materialised with `core.autocrlf=true` supplied per command, so
the cell does not depend on the host's configuration, and never with
`git config`, which writes to the shared repository config rather than the
worktree -- doing that once turned autocrlf off for the whole repository and
produced three cells silently measuring one condition.

These cells are *not* the frozen baseline's conditions and are not described
as such. That tree was 155 CRLF-only, 8 mixed and 5 LF-only files, a state
produced by tools writing some files and checkout writing others, which no
checkout reproduces. What A reproduces is a plain CRLF checkout; the measured
distribution is recorded so the difference is visible rather than implied.

This is a tool, and its output an artifact, because its numbers are cited as
evidence. Anything cited should be re-runnable by somebody who doubts it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

FORMAT_VERSION = 2
GENERATOR = "tools/marep/build_transition_matrix.py"
TAG = "reorg-post-move-v1"

CELLS = (("A", False, False, "CRLF checkout, filesystem document base"),
         ("B", True, False, "CRLF checkout, stable document base"),
         ("C", True, True, "LF checkout, stable document base"))

MEASURE = r"""
import importlib.util, json, sys
from pathlib import Path
WT = Path(sys.argv[1]); sys.path.insert(0, str(WT))
spec = importlib.util.spec_from_file_location(
    "bsb", str(WT / "tools/marep/build_semantic_baseline.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def val(n):
    return n["value"] if isinstance(n, dict) and "value" in n else n
print(json.dumps({
    "corpus": {k: val(v) for k, v in m.corpus_measures(WT).items()},
    "reasoner": {k: val(v) for k, v in m.reasoner_measures(WT).items()},
}))
"""


def git(*args, cwd=None, check=True, config=()):
    """Run git, with any config supplied per invocation.

    `-c key=value` and never `git config`: run inside a worktree the latter
    writes to the shared repository config, which is how a stray
    `core.autocrlf false` once changed the setting for every tree at once.
    """
    cmd = ["git"]
    for kv in config:
        cmd += ["-c", kv]
    cmd += list(args)
    r = subprocess.run(cmd, cwd=str(cwd or _root), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit("git %s failed:%s%s"
                         % (" ".join(args), os.linesep, r.stderr.strip()))
    return r.stdout


def ttl_files(tree: Path) -> list[str]:
    # splitlines, not split: a tracked path containing a space is one file and
    # whitespace splitting turns it into two that do not exist.
    return [f for f in git("ls-files", "--", "*.ttl", cwd=tree).splitlines() if f]


def eol_map(tree: Path, files: list[str]) -> dict:
    """Per-file line-ending shape, plus one digest over the whole set.

    A count of "files containing CRLF" hides the difference between a file
    that is entirely CRLF and one that is mixed, and the mixed case is real:
    eight files in the frozen working tree were part CRLF and part LF.
    """
    kinds, h = {}, hashlib.sha256()
    for f in sorted(files):
        raw = (tree / f).read_bytes()
        crlf = raw.count(b"\r\n")
        lone_lf = raw.count(b"\n") - crlf
        kinds[f] = ("crlf" if crlf and not lone_lf
                    else "lf" if lone_lf and not crlf
                    else "mixed" if crlf and lone_lf else "none")
        h.update(f.encode("utf-8") + b"\0" + raw)
    tally = {}
    for v in kinds.values():
        tally[v] = tally.get(v, 0) + 1
    return {"per_file": kinds, "distribution": tally,
            "aggregate_sha256": h.hexdigest()}


def build_cell(stage: Path, name: str, hardened: bool, lf: bool) -> Path:
    tree = stage / name
    git("worktree", "prune")
    # autocrlf supplied here, so the cell is the same on any host.
    git("worktree", "add", "-q", "--detach", str(tree), TAG,
        config=("core.autocrlf=" + ("true" if not lf else "false"),))

    # Line endings first, then the code under test. `git checkout` restores
    # every path it is given, so installing the hardened tools before the
    # re-checkout lets git put the tag's versions back -- which happened, and
    # gave three runs of a cell measuring the parser it was the control for.
    if lf:
        (tree / ".gitattributes").write_text("*.ttl text eol=lf\n",
                                             encoding="utf-8", newline="\n")
        files = ttl_files(tree)
        for f in files:
            (tree / f).unlink()
        git("checkout", "--", *files, cwd=tree, config=("core.autocrlf=false",))

    if hardened:
        for sub in ("marep", "tools"):
            shutil.rmtree(tree / sub)
            shutil.copytree(_root / sub, tree / sub,
                            ignore=shutil.ignore_patterns("__pycache__"))

    installed = "def parse_source" in (
        tree / "marep/ontology_source.py").read_text(encoding="utf-8")
    if installed != hardened:
        raise SystemExit("cell %s claims hardened=%s but parse_source "
                         "present=%s" % (name, hardened, installed))
    return tree


def enumerate_literal_transition() -> dict:
    """Which triples change when line endings do, across the whole corpus.

    Every tracked Turtle file is examined and the affected set is derived.
    An earlier version iterated a list of four files, so a fifth could not
    have been found and "four files" was an assumption wearing the clothes
    of a measurement.

    Blank-node subjects are included. Excluding them would have made the
    annotation-only conclusion partly a consequence of what was counted.
    """
    import rdflib
    from marep import ontology_source as onto

    per_file, per_pred, examples = {}, {}, {}
    for path in sorted(onto.discover(_root)):
        rel = path.relative_to(_root).as_posix()
        lf = path.read_bytes()
        if b"\r\n" in lf:
            raise SystemExit("%s is not LF; run this after normalization" % rel)
        base = onto.public_id(rel)

        def literals(data: bytes) -> list:
            g = rdflib.Graph()
            try:
                g.parse(data=data.decode("utf-8"), format="turtle", publicID=base)
            except Exception:
                return []
            # Every triple whose object is a literal, blank-node subjects
            # included; a multiset, so a duplicated literal still counts twice.
            return sorted("%s %s" % (p.n3(), o.n3()) for _s, p, o in g
                          if isinstance(o, rdflib.Literal))

        was, now = literals(lf.replace(b"\n", b"\r\n")), literals(lf)
        if was == now:
            continue
        import collections
        delta = collections.Counter(was) - collections.Counter(now)
        n = sum(delta.values())
        if not n:
            continue
        per_file[rel] = n
        for entry, count in delta.items():
            pred = entry.split(" ", 1)[0].strip("<>")
            per_pred[pred] = per_pred.get(pred, 0) + count
        examples[rel] = sorted(delta)[0][:160]

    return {"files": per_file, "predicates": per_pred,
            "total": sum(per_file.values()), "examples": examples,
            "definition": "literal-object triples present when the file is "
                          "CRLF and absent when it is LF, over every tracked "
                          "Turtle file, blank-node subjects included, compared "
                          "as multisets"}


def relative_iri_inventory() -> dict:
    """Every IRI in the corpus that resolved against the document base."""
    import rdflib
    from marep import ontology_source as onto

    found: dict[str, list[str]] = {}
    for path in onto.discover(_root):
        rel = path.relative_to(_root).as_posix()
        fact = onto.measure_file(path, _root)
        if not fact.parses:
            continue
        for triple in onto.graph_for(_root, fact):
            for term in triple:
                if isinstance(term, rdflib.URIRef) and \
                        str(term).startswith(onto.SOURCE_BASE):
                    found.setdefault(rel, []).append(
                        str(term)[len(onto.SOURCE_BASE):])
    return {k: sorted(set(v)) for k, v in found.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--allow-dirty", action="store_true",
                    help="measure a tree with uncommitted changes. The output "
                         "records working_tree_clean=false and consumers "
                         "refuse it as evidence.")
    args = ap.parse_args(argv)

    dirty = bool(git("status", "--porcelain").strip())
    if dirty and not args.allow_dirty:
        raise SystemExit(
            "the working tree has uncommitted changes. Evidence has to name "
            "an input somebody else can check out; commit the measurement "
            "code first, or pass --allow-dirty for a diagnostic run.")
    head = git("rev-parse", "HEAD").strip()

    cells, made = {}, []
    stage = Path(tempfile.mkdtemp(prefix="transition-"))
    try:
        for name, hardened, lf, label in CELLS:
            tree = build_cell(stage, name, hardened, lf)
            made.append(tree)
            files = ttl_files(tree)
            out = measure(tree)
            out.update({"label": label, "hardened": hardened, "lf": lf,
                        "ttl_files": len(files), "eol": eol_map(tree, files)})
            cells[name] = out
            print("  %s  %-38s %s" % (name, label,
                                      out["corpus"]["merged_ground_sha256"]))
            print("     eol %s" % out["eol"]["distribution"])

        second = build_cell(stage, "A-at-another-path-entirely", False, False)
        made.append(second)
        a2 = measure(second)["corpus"]["merged_ground_sha256"]
        a1 = cells["A"]["corpus"]["merged_ground_sha256"]
        print("  A again at another path: %s" % a2)
    finally:
        for t in made:
            subprocess.run(["git", "worktree", "remove", "--force", str(t)],
                           cwd=str(_root), capture_output=True)
        shutil.rmtree(stage, ignore_errors=True)
        git("worktree", "prune", check=False)

    # Derived, not listed. The hand-written version omitted
    # class_declarations_summed -- present, equal in all three cells, and
    # silently outside an invariant called "corpus counts identical". A
    # list of field names does not grow when the measurement does, so the
    # invariant's name and its scope drift apart with nothing to say so.
    #
    # Every integer-valued corpus measure is a count; merged_ground_sha256
    # is a string and merged_bnode_shape a mapping, and both legitimately
    # differ between cells. The compared set is recorded beside the
    # verdict so its scope is readable rather than implied.
    counts = sorted(k for k, v in cells["A"]["corpus"].items()
                    if isinstance(v, int) and not isinstance(v, bool))
    doc = {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "input_commit": head,
        "working_tree_clean": not dirty,
        "measured_from_tag": TAG,
        "cells": cells,
        "path_dependence": {
            "A_first": a1, "A_second": a2, "differ": a1 != a2,
            "definition": "cell A measured twice at two different absolute "
                          "paths; a difference is the defect the stable base "
                          "removes",
        },
        "invariants": {
            "corpus_counts_identical_across_cells": all(
                cells["A"]["corpus"][k] == cells["B"]["corpus"][k]
                == cells["C"]["corpus"][k] for k in counts),
            "reasoner_identical_across_cells":
                cells["A"]["reasoner"] == cells["B"]["reasoner"]
                == cells["C"]["reasoner"],
            "A_and_B_are_byte_identical_checkouts":
                cells["A"]["eol"]["aggregate_sha256"]
                == cells["B"]["eol"]["aggregate_sha256"],
            "C_has_no_crlf": cells["C"]["eol"]["distribution"].get("crlf", 0) == 0
                and cells["C"]["eol"]["distribution"].get("mixed", 0) == 0,
        },
        # The scope of the invariant above, beside it rather than inside
        # it: `invariants` is booleans, and every one of them is asserted
        # to be true.
        "invariant_scope": {
            "corpus_counts_compared": counts,
            "definition": "every integer-valued corpus measure. "
                          "merged_ground_sha256 and merged_bnode_shape are "
                          "excluded because both legitimately differ between "
                          "cells -- that difference is the measurement.",
        },
        "line_ending_transition": enumerate_literal_transition(),
        "relative_iris": relative_iri_inventory(),
    }

    text = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    print()
    for k, v in doc["invariants"].items():
        print("  %-42s %s" % (k, v))
    print("  %-42s %d field(s)"
          % ("counts compared",
             len(doc["invariant_scope"]["corpus_counts_compared"])))
    print("  %-42s %s" % ("path dependence in A", doc["path_dependence"]["differ"]))
    print("  %-42s %d triple(s) in %d file(s)"
          % ("literal transition", doc["line_ending_transition"]["total"],
             len(doc["line_ending_transition"]["files"])))
    print("  %-42s %s" % ("relative IRIs",
                          list(doc["relative_iris"]) or "none"))

    if args.out:
        target = _root / args.out
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, target)
        print("%s  wrote %s (sha256 %s)"
              % (os.linesep, args.out,
                 hashlib.sha256(text.encode("utf-8")).hexdigest()))
    return 0


def measure(tree: Path) -> dict:
    r = subprocess.run([sys.executable, "-c", MEASURE, str(tree)],
                       capture_output=True, text=True, cwd=str(tree))
    if r.returncode != 0:
        raise SystemExit("measuring %s failed:%s%s"
                         % (tree.name, os.linesep, r.stderr[-1500:]))
    return json.loads(r.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
