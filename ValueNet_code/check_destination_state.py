"""Evaluate every consumer against the post-move tree, without moving anything.

Step 4 passed its gate on a tree where nothing had moved, and that gate could
not have failed: every literal path it exercised still existed. Review found
five surfaces that would break the moment a wave ran — the gate tools losing
their own package, four MAREP loaders reading an empty `BFO/`, seven tests
appending `BFO/...` to a correctly-resolved root, six tools deriving their root
from their current depth, and a fallback that treated a malformed contract as
an absent one.

Every one of those is invisible until the move happens, which is the worst
possible time to discover it. So this materialises the destination tree in a
temporary directory, points the resolver at it, and asks each consumer whether
it can still find what it needs.

It moves nothing in the real repository. It copies.

    python ValueNet_code/check_destination_state.py [--wave bfo]
"""

from __future__ import annotations

import argparse
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

WAVE_ORDER = ["bfo", "marep", "original-valuenet", "architecture", "tests"]


def materialise(rows: list[dict], through_wave: str | None, dest: Path) -> int:
    """Copy the repository into `dest` with the given waves applied."""
    import yaml  # noqa: F401  (import proves the environment before copying)

    done = (WAVE_ORDER[:WAVE_ORDER.index(through_wave) + 1]
            if through_wave else WAVE_ORDER)
    moved = 0
    for r in rows:
        src = _root / r["path"]
        if not src.exists():
            continue
        target = r["destination"]
        if target != "RETAIN" and r.get("wave") in done:
            out = dest / target
            moved += 1
        else:
            out = dest / r["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
    return moved


#: Every tool, loaded from wherever it now lives, must still compute the
#: repository root correctly. Added after three tools were found resolving
#: their root by counting directories: from tools/marep/ two dirname calls
#: give repo/tools, which exists, so build_move_manifest.py would have run
#: `git ls-files` from there and written a manifest listing only the tools
#: directory. The checker had not been looking at the tools at all -- it
#: tested the contract's consumers and not the programs that move.
#:
#: Two rules, because the first draft had neither and flagged three
#: innocents. A tool that takes every path from a required CLI argument
#: has no root to get wrong, so absence of a root constant is not a
#: finding. And `is_v_emo_overlaps.py` fails on import against hardcoded
#: paths from its original author's machine -- broken before the move and
#: not by it, so import failures are judged against a pre-move baseline
#: and only new ones count.
_TOOL_ROOTS = '''import json, pathlib
root = pathlib.Path.cwd().resolve()
known_bad = set(json.loads('TOOL_IMPORT_BASELINE'))
bad = []
for d in ('tools', 'ValueNet_code'):
    if not (root / d).is_dir():
        continue
    for q in sorted((root / d).rglob('*.py')):
        failed = []
        m = _load(q, failed)
        if m is None:
            if q.name not in known_bad:
                bad.append(q.name + ': newly fails on import')
            continue
        # Any module-level constant naming the repository root must name
        # this tree's root. HERE, ROOT and REPO are the three spellings
        # in use; a tool using none of them resolves paths from argv.
        for attr in ('HERE', 'ROOT', 'REPO'):
            v = getattr(m, attr, None)
            if v is None or not isinstance(v, (str, pathlib.Path)):
                continue
            if pathlib.Path(v).resolve() != root:
                bad.append(str(q.relative_to(root)) + ': ' + attr + '='
                           + str(v) + ' is not the repository root')
assert not bad, bad
'''

CONSUMERS = [
    ("layout resolves the BFO tree",
     "from marep import layout; "
     "assert layout.path('bfo.ontology-tree').exists()"),
    ("reasoner scope is complete",
     "from marep import layout; n=len(layout.reasoner_scope()); "
     "assert n == 8, f'{n} files, expected 8'"),
    ("shape files are found",
     "from marep import layout; n=len(layout.shape_files()); "
     "assert n == 3, f'{n} shape sets, expected 3'"),
    ("bfo modules resolve",
     "from marep import layout; "
     "n=len(layout.bfo_modules('valuenet-core','valuenet-folk','valuenet-mappings')); "
     "assert n == 3, f'{n} modules, expected 3'"),
    ("corpus grouping is unchanged",
     # The whole map, not two groups of it. Asserting only bfo-layer and
     # bfo-vendored let the other 155 files fall into any bucket at all and
     # still printed OK -- the narrow assertion could not have failed for
     # them. The baseline is measured on the real tree and injected, so this
     # states the actual invariant: the move does not reclassify anything.
     "from marep import layout, ontology_source as onto; "
     "import collections, json; root=layout.repository_root(); "
     "got=dict(collections.Counter(onto.measure_file(p,root).group "
     "for p in onto.discover(root))); want=json.loads('GROUPING_BASELINE'); "
     "assert got == want, "
     "f'moved: {want} -> {got}'"),
    ("query documents resolve",
     "from marep import competency; d=competency.query_docs(); "
     "assert len(d) == 2, d"),
    ("competency queries still answer",
     "from marep import competency, layout; "
     "root=layout.repository_root(); "
     "rs=[r for doc in competency.query_docs() "
     "for r in competency.run_document(root, root/doc)]; "
     "bad=[r.query.ref for r in rs if not r.passed]; assert not bad, bad"),
    # Every tool, loaded from wherever it now lives, must still compute the
    # repository root correctly. This consumer was added after three tools
    # were found resolving their root by counting directories: from
    # tools/marep/ two dirname calls give repo/tools, which exists, so
    # build_move_manifest.py would have run `git ls-files` from there and
    # written a manifest listing only the tools directory. The checker had
    # not been looking at the tools at all -- it tested the consumers of the
    # contract and not the programs that move.
    ("every tool computes the repository root from its destination",
     _TOOL_ROOTS),
    ("folk generator finds its source and target",
     "import runpy, sys; sys.argv=['g','--check']; "
     "runpy.run_path('TOOL_GENERATE_FOLK', run_name='__main__')"),
]


#: Prelude injected into consumer snippets that need to import a tool by
#: path without running it. Tools act only under `if __name__ ==
#: "__main__"`, so exec_module is safe; a tool that raises on import is
#: itself the finding.
_LOAD_PRELUDE = '''import importlib.util as _il
def _load(q, bad):
    sp = _il.spec_from_file_location('t_' + q.stem, q)
    m = _il.module_from_spec(sp)
    try:
        sp.loader.exec_module(m)
    except BaseException as e:
        bad.append(q.name + ': ' + type(e).__name__ + ' on import: '
                   + str(e)[:70])
        return None
    return m
'''


def tool_import_baseline() -> str:
    """Tools that already fail on import, before anything moves.

    Measured, not listed. `is_v_emo_overlaps.py` reads four absolute paths
    under /Users/sdg/Desktop at import time -- an upstream file, RETAIN,
    broken on any machine but its author's. Hardcoding its name here would
    have made the exemption permanent and silent; measuring it means the
    day it is fixed, the exemption disappears on its own.
    """
    import json

    failures: list[str] = []
    ns: dict = {}
    exec(_LOAD_PRELUDE, ns)
    for d in ('tools', 'ValueNet_code'):
        if not (_root / d).is_dir():
            continue
        for q in sorted((_root / d).rglob('*.py')):
            ns['_load'](q, failures)
    return json.dumps(sorted({f.split(':')[0] for f in failures}))


#: What a completed wave owes, beyond moving files.
#:
#: The contract declares path allowances with `remove_after_wave`: a
#: literal path that is correct until a wave runs and must be regenerated
#: afterwards. That is part of executing the wave, not an optional
#: follow-up, so a check that materialises the wave without it is checking
#: a state the plan never intends to be in.
#:
#: Mapped explicitly rather than inferred. `generate_cco_extract.py` takes
#: four required arguments including a source digest, so it cannot be run
#: bare; that entry is reported instead of silently skipped, because a
#: regeneration nobody performs and nobody mentions is how the header in
#: folk_aligned.ttl came to name a generator that had moved.
REGENERATORS = {
    "folk-aligned-generated-header-generator":
        ("tool.generate-folk-aligned", []),
    "cco-manifest-generator-path": None,
}


def owed_regenerations(through_wave: str | None) -> list[dict]:
    """Allowances whose `remove_after_wave` has run."""
    from marep import layout
    done = (WAVE_ORDER[:WAVE_ORDER.index(through_wave) + 1]
            if through_wave else WAVE_ORDER)
    return [a for a in layout.path_allowances()
            if a.get("remove_after_wave") in done]


def regenerate(dest: Path, through_wave: str | None) -> list[str]:
    """Run what the wave owes. Returns what could not be run."""
    from marep import layout
    unperformed = []
    for a in owed_regenerations(through_wave):
        spec = REGENERATORS.get(a.get("id"), None)
        if spec is None:
            unperformed.append(f"{a.get('id')}: {a.get('file')} must be "
                               f"regenerated by hand after the "
                               f"{a.get('remove_after_wave')} wave")
            continue
        component_id, extra = spec
        tool = layout.component(component_id).resolve(dest)
        r = subprocess.run([sys.executable, str(tool), *extra],
                           capture_output=True, text=True, cwd=str(dest))
        rel = os.path.relpath(tool, dest).replace(os.sep, '/')
        print(f"    regenerated {a.get('file')} via {rel}"
              if r.returncode == 0 else
              f"    FAILED to regenerate {a.get('file')}: "
              + (r.stderr.strip()[-120:] or r.stdout.strip()[-120:]))
        if r.returncode != 0:
            unperformed.append(f"{a.get('id')}: regeneration failed")
    return unperformed

def grouping_baseline() -> str:
    """How the current tree groups its corpus, as JSON, for injection.

    Measured rather than hardcoded so the assertion reads "the move changes
    no file's group" instead of "the counts are these seven numbers", and so
    it stays true when the corpus legitimately grows.
    """
    import collections
    import json

    from marep import layout, ontology_source as onto
    root = layout.repository_root()
    counts = collections.Counter(onto.measure_file(p, root).group
                                 for p in onto.discover(root))
    return json.dumps(dict(counts))


def check_prefix_groups_are_stable(rows: list[dict]) -> list[str]:
    """Prefix-based corpus groups must not have moving members.

    Four groups -- MFTriggers, MoralMolecules, ThatsAllFolks, vale2024 --
    are matched by path prefix. They survive the move only because every
    one of their files is RETAIN, which is a fact about this manifest and
    not a property of the resolver. The moment a later wave moves one of
    those directories, the prefix stops matching and 130 files change group
    with nothing raising. The BFO groups already avoid this by declaring
    exact `members_after`; these four have no `group_prefixes_after` at all.

    So the invariant is stated here rather than assumed: a prefix-grouped
    file either does not move, or its component declares where the prefix
    goes.
    """
    from marep import layout
    prefixes = layout.corpus_groups()
    moving = {r["path"]: r["destination"] for r in rows
              if r["destination"] != "RETAIN"}
    # By corpus_group, not by component id. `group` below is a group name
    # such as 'thats-all-folks'; collecting ids compared two different
    # vocabularies and could never match, so a component that did declare
    # group_prefixes_after would still have been reported as not having.
    declared = {c.corpus_group for c in layout.components()
                if c.group_prefixes_after}

    out = []
    for path, dest in sorted(moving.items()):
        for prefix, group in prefixes.items():
            if path.startswith(prefix) and group not in declared:
                out.append(
                    f"prefix-grouped file moves with no group_prefixes_after: "
                    f"{path} -> {dest} (group {group!r} is matched by the "
                    f"prefix {prefix!r}, which will stop matching)")
                break
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pytest", action="store_true",
                    help="also run the suite inside the materialised "
                         "tree; slower, and the only check that "
                         "exercises the tests themselves rather than "
                         "a listed consumer")
    ap.add_argument("--wave", default=None, choices=WAVE_ORDER,
                    help="apply waves up to and including this one; "
                         "omit to apply all of them")
    args = ap.parse_args(argv)

    import yaml
    rows = yaml.safe_load(
        (_root / "config/move-manifest.yaml").read_text(encoding="utf-8"))["components"]

    structural = check_prefix_groups_are_stable(rows)
    baseline = grouping_baseline()
    tool_baseline = tool_import_baseline()

    with tempfile.TemporaryDirectory(prefix="destcheck-") as td:
        dest = Path(td) / "repo"
        moved = materialise(rows, args.wave, dest)
        label = args.wave or "all waves"
        print(f"  materialised {label}: {moved} file(s) at their destinations")

        # Executing a wave includes what the contract says it owes.
        manual = regenerate(dest, args.wave)
        for m in manual:
            print(f"    note: {m}")

        # Through the contract, against the materialised tree. Two literal
        # candidates tried in order worked, but encoded the same move the
        # contract already states -- and would have gone quietly stale the
        # day the generator was routed somewhere else.
        from marep import layout
        # Relative to `dest`, not via layout.relative(), which measures
        # against the real repository root and raises on a path under a
        # temporary tree.
        gen = os.path.relpath(
            layout.component("tool.generate-folk-aligned").resolve(dest),
            dest).replace(os.sep, "/")

        failures = list(structural)
        for f in structural:
            print(f"    FAIL {f}")
        for name, snippet in CONSUMERS:
            code = (snippet.replace("TOOL_GENERATE_FOLK", gen)
                           .replace("GROUPING_BASELINE", baseline)
                           .replace("TOOL_IMPORT_BASELINE", tool_baseline))
            if "_load(" in code:
                code = _LOAD_PRELUDE + code
            r = subprocess.run([sys.executable, "-c", code],
                               capture_output=True, text=True, cwd=str(dest))
            ok = r.returncode == 0
            print(f"    {'OK  ' if ok else 'FAIL'} {name}")
            if not ok:
                tail = (r.stderr.strip().splitlines() or ["(no output)"])[-1]
                failures.append(f"{name}: {tail[:140]}")

        if args.pytest:
            # The consumers are a list somebody maintains, so they cover
            # what that person thought of. Running the suite covers what
            # the suite covers -- and the suite is where the literal
            # BFO/ path in test_trigger_shapes.py was found by reading,
            # because no consumer had ever looked at it.
            print("    running the suite inside the materialised tree ...")
            r = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                               capture_output=True, text=True, cwd=str(dest))
            tail = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
            summary = tail[-1] if tail else "(no output)"
            ok = r.returncode == 0
            print("    " + ("OK  " if ok else "FAIL") + " pytest: " + summary)
            if not ok:
                for ln in tail:
                    if "FAILED" in ln or "ERROR" in ln:
                        print("        " + ln[:150])
                failures.append("pytest in the moved tree: " + summary)

        if failures:
            print(f"\n  {len(failures)} consumer(s) break after {label}:")
            for f in failures:
                print(f"      {f}")
            return 1
    print(f"  every consumer resolves after {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
