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

    python tools/marep/check_destination_state.py [--wave bfo]
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


class MaterialiseError(RuntimeError):
    """The working tree is not in any state the manifest describes."""


def materialise(rows: list[dict], through_wave: str | None, dest: Path,
                source_root: Path | None = None) -> int:
    """Copy the repository into `dest` with the given waves applied.

    Reads each row from whichever of its two paths actually holds the
    file. The first version read only the source and skipped the row when
    it was absent, which is fine on a pristine tree and useless on a real
    one: after the BFO wave those 42 sources are gone, their destinations
    exist, and the checker would have silently omitted all 42 and reported
    the remaining 288 as a complete tree.

    So exactly one of the two must exist. Both means an interrupted move
    left a copy behind; neither means the file is lost. Either is a state
    the manifest does not describe, and copying on regardless would
    produce a verdict about a tree nobody has.
    """
    import yaml  # noqa: F401  (import proves the environment before copying)

    # A caller may hand us a tree other than this repository -- a fixture
    # standing in for a half-run migration. Without that the partial-move
    # path could only be tested by half-running a migration.
    base = Path(source_root) if source_root is not None else _root
    done = (WAVE_ORDER[:WAVE_ORDER.index(through_wave) + 1]
            if through_wave else WAVE_ORDER)
    moved = 0
    copied = 0
    problems: list[str] = []
    for r in rows:
        target = r["destination"]
        src = base / r["path"]
        dst = (base / target) if target != "RETAIN" else None
        src_here = src.is_file()
        dst_here = bool(dst and dst.is_file())

        if src_here and dst_here:
            problems.append(
                r["path"] + " exists at both its source and its "
                "destination " + str(target) + "; an interrupted move "
                "left a copy behind, and there is no way to tell which "
                "of the two the repository means")
            continue
        if not src_here and not dst_here:
            problems.append(
                r["path"] + " exists at neither its source nor its "
                "destination " + str(target))
            continue
        origin = src if src_here else dst
        if target != "RETAIN" and r.get("wave") in done:
            out = dest / target
            moved += 1
        else:
            out = dest / r["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, out)
        copied += 1

    if problems:
        raise MaterialiseError(
            f"{len(problems)} row(s) are not in a state the manifest "
            f"describes:" + chr(10) + chr(10).join("      " + x for x in problems[:20]))
    if copied != len(rows):
        raise MaterialiseError(
            f"materialised {copied} of {len(rows)} manifest rows; a row that "
            f"reaches the destination tree by no path is a file the check "
            f"never looked at")
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

#: Compared per file against the pre-move map, keyed by manifest identity.
#: Aggregate counts were the earlier form and could not fail for a
#: balanced swap: two files exchanging groups leaves every total intact.
_GROUPING = '''import json, pathlib, yaml
from marep import layout, ontology_source as onto
root = layout.repository_root()
rows = yaml.safe_load(
    (root / 'config/move-manifest.yaml').read_text(encoding='utf-8'))['components']
ident = identity_map(rows)
got = {}
for path in onto.discover(root):
    rel = path.relative_to(root).as_posix()
    got[ident.get(rel, rel)] = onto.measure_file(path, root).group
want = json.loads('GROUPING_BASELINE')
changed = grouping_delta(want, got)
assert not changed, str(len(changed)) + ' file(s) changed group: ' + str(changed[:8])
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
    ("corpus grouping is unchanged", _GROUPING),
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
#: Mapped explicitly rather than inferred. Rebuilding the CCO extract
#: needs the pinned upstream release, which is not in this repository --
#: but the obligation is not about the extract. Moving the script changes
#: only where the manifest says the extract came from, so
#: --refresh-provenance discharges it after checking the extract's digest
#: still matches.
#:
#: An entry of None means nobody can discharge it here, and that is a
#: failure, not a note. Printing it and returning success is how the
#: header in folk_aligned.ttl came to name a generator that had moved:
#: the obligation was recorded, reported, and never carried out.
REGENERATORS = {
    "folk-aligned-generated-header-generator":
        ("tool.generate-folk-aligned", []),
    "cco-manifest-generator-path":
        ("tool.generate-cco-extract", ["--refresh-provenance"]),
    # cross-ref-folk-aligned-...-review-md was here. It became a
    # permanent historical record once its source literal turned out
    # to be a prov:wasAttributedTo triple rather than a comment, so
    # there is no longer a regeneration that discharges it.
}


def _expired(through_wave: str | None) -> list[dict]:
    from marep import layout
    done = (WAVE_ORDER[:WAVE_ORDER.index(through_wave) + 1]
            if through_wave else WAVE_ORDER)
    return [a for a in layout.path_allowances()
            if a.get("remove_after_wave") in done]


def owed_regenerations(through_wave: str | None) -> list[dict]:
    """Expired allowances a program can discharge.

    Only `discharge: regenerate`. The other kind is a source edit -- a usage
    line in a docstring, a cross-reference in a comment -- which no program
    rebuilds and which belongs to the move commit. Treating the two as one
    obligation demanded an automated remedy for 28 that have none, leaving
    only "fail forever" or "print a note beside a green verdict".
    """
    return [a for a in _expired(through_wave)
            if a.get("discharge") == "regenerate"]


def pending_edits(through_wave: str | None) -> list[dict]:
    """Expired allowances whose remedy is an edit in the move commit.

    Listed, not performed: this materialises a file move, and the plan's move
    commits carry the link updates with them. What proves these were done is
    the lifecycle check against the real tree after the wave -- the literal
    has to be gone -- not anything observable in a copy.
    """
    return [a for a in _expired(through_wave)
            if a.get("discharge") == "edit"]


def regenerate(dest: Path, through_wave: str | None) -> list[str]:
    """Run what the wave owes. Returns what could not be run."""
    from marep import layout
    unperformed = []
    ran: set = set()
    for a in owed_regenerations(through_wave):
        spec = REGENERATORS.get(a.get("id"), None)
        key = None if spec is None else (spec[0], tuple(spec[1]))
        if key is not None and key in ran:
            continue
        if spec is None:
            unperformed.append(
                f"{a.get('id')}: {a.get('file')} must be brought up to "
                f"date after the {a.get('remove_after_wave')} wave, and "
                f"no automated way to do so is recorded")
            continue
        component_id, extra = spec
        tool = layout.component(component_id).resolve(dest)
        r = subprocess.run([sys.executable, str(tool), *extra],
                           capture_output=True, text=True, cwd=str(dest))
        ran.add(key)
        rel = os.path.relpath(tool, dest).replace(os.sep, '/')
        print(f"    regenerated {a.get('file')} via {rel}"
              if r.returncode == 0 else
              f"    FAILED to regenerate {a.get('file')}: "
              + (r.stderr.strip()[-120:] or r.stdout.strip()[-120:]))
        if r.returncode != 0:
            unperformed.append(f"{a.get('id')}: regeneration failed")
    return unperformed

#: Which files changed group, computed identically in this process and
#: inside the materialised tree. Defined once as source so the check and
#: its falsification test cannot drift apart.
_DELTA_SRC = '''def grouping_delta(want, got):
    out = []
    for k in sorted(set(want) | set(got)):
        a, b = want.get(k), got.get(k)
        if a != b:
            out.append(str(k) + ': ' + str(a) + ' -> ' + str(b))
    return out
'''

exec(_DELTA_SRC, globals())


#: Manifest identity for a path: the row's source path, whichever of its
#: two locations the file currently occupies. Counting group totals could
#: not see a file move between groups as long as another moved back, so
#: the comparison is per file and the key has to survive the move.
_IDENTITY_SRC = '''def identity_map(rows):
    out = {}
    for r in rows:
        out[r['path']] = r['path']
        if r['destination'] != 'RETAIN':
            out[r['destination']] = r['path']
    return out
'''

exec(_IDENTITY_SRC, globals())

def grouping_baseline() -> str:
    """Every ontology file's group, keyed by manifest identity, as JSON.

    Measured rather than hardcoded, so the assertion reads "the move
    reclassifies no file" and stays true when the corpus grows.

    Per file, not per group. The first version compared
    `Counter(group)`, which two files swapping groups leaves completely
    unchanged -- a check that cannot see the thing it is named after.
    """
    import json

    import yaml
    from marep import layout, ontology_source as onto
    root = layout.repository_root()
    rows = yaml.safe_load(
        (root / "config/move-manifest.yaml").read_text(encoding="utf-8"))["components"]
    ident = identity_map(rows)
    out = {}
    for path in onto.discover(root):
        rel = path.relative_to(root).as_posix()
        out[ident.get(rel, rel)] = onto.measure_file(path, root).group
    return json.dumps(out, sort_keys=True)

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

        # Executing a wave includes what the contract says it owes. An
        # obligation the wave has expired and nobody discharged leaves the
        # tree in a state the contract calls invalid, so it fails the
        # check rather than printing as a note beside a green verdict.
        unperformed = regenerate(dest, args.wave)
        for m in unperformed:
            print(f"    FAIL {m}")
        edits = pending_edits(args.wave)
        if edits:
            waves = sorted({a["remove_after_wave"] for a in edits})
            print(f"    {len(edits)} link edit(s) belong to the "
                  f"{', '.join(waves)} move commit(s); the lifecycle check "
                  f"against the real tree is what proves they were made")

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

        failures = list(structural) + list(unperformed)
        for f in structural:
            print(f"    FAIL {f}")
        for name, snippet in CONSUMERS:
            code = (snippet.replace("TOOL_GENERATE_FOLK", gen)
                           .replace("GROUPING_BASELINE", baseline)
                           .replace("TOOL_IMPORT_BASELINE", tool_baseline))
            if "identity_map(" in code:
                code = _IDENTITY_SRC + _DELTA_SRC + code
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
            # `not repository` as well as the configured `not slow`: a
            # command-line -m replaces addopts rather than adding to it.
            # The repository-marked modules assert what git tracks and
            # where the manifest says it is, which a copy cannot answer.
            r = subprocess.run([sys.executable, "-m", "pytest", "-q",
                                "-m", "not slow and not repository"],
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
