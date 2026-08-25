"""Derive the reorganization move manifest from the repository, not by hand.

Hand-listing destinations missed six files in the first two plan drafts. Version
one of this script replaced the list with a derivation and then made four
execution mistakes of its own, all found by review:

* it wrote the manifest **before** returning failure, so a run with unassigned
  files could overwrite a good manifest and only then exit non-zero — the
  opposite of the "refuses to emit an incomplete manifest" property claimed for
  it;
* prefix-stripping produced destinations like
  `ontology/bfo/extensions/moral-epistemics/.ttl` — a hidden, extension-only
  filename — because a family prefix consumed the whole basename;
* every test received the placeholder `REORGANIZE-IN-PLACE`, so the manifest
  could not detect a test filed into the wrong group, which was most of the
  point of listing them; and
* git calls ignored their exit status, so a missing `upstream/main` would have
  produced confident, wrong provenance rather than an error.

All four are fixed here, and the validator below now refuses a manifest whose
destinations are malformed rather than trusting the mapping table to be right.

**Provenance is two orthogonal axes**, because "fork-authored", "generated" and
"vendored" are not mutually exclusive:

    origin      : upstream-valuenet | fork | external-bfo | external-cco
    maintenance : unchanged | locally-modified | generated

**Origin follows rename history**, with an explicit override where git cannot.

Under the settled rule, anything whose origin is `upstream-valuenet` is RETAINED
at its current path whatever its maintenance state, documentation assets
included. Only fork and external material moves.

    python ValueNet_code/build_move_manifest.py [-o config/move-manifest.yaml]
"""

from __future__ import annotations

import argparse
import os
import posixpath
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(*args: str) -> str:
    """Run git, failing loudly. Ignoring exit status here produced confident
    wrong provenance when a ref was missing."""
    r = subprocess.run(args, capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise SystemExit(f"git failed: {' '.join(args)}\n{r.stderr.strip()}")
    return r.stdout


def tracked() -> list[str]:
    """`git ls-files`, not `ls-tree HEAD`: the latter misses staged additions,
    which is how this script omitted itself and its own output."""
    return sorted(p for p in sh("git", "ls-files").split("\n") if p)


def upstream_paths() -> set[str]:
    try:
        sh("git", "rev-parse", "--verify", "upstream/main")
    except SystemExit:
        raise SystemExit(
            "upstream/main does not resolve. Provenance cannot be derived "
            "without it; run: git fetch upstream")
    return {p for p in sh("git", "ls-tree", "-r", "--name-only",
                          "upstream/main").split("\n") if p}


GENERATED = {
    "folk_aligned.ttl": "tool:generate-folk-aligned",
    "BFO/imports/cco-valuenet-extract.ttl": "tool:generate-cco-extract",
    "BFO/imports/cco-valuenet-extract.manifest.json": "tool:generate-cco-extract",
    "config/move-manifest.yaml": "tool:build-move-manifest",
}

#: Upstream descent git cannot detect, asserted with its reason. Rename
#: detection needs content similarity; these two edits exceeded the threshold.
KNOWN_UPSTREAM_DESCENT = {
    "ThatsAllFolks/folk.ttl":
        "converted from upstream ThatsAllFolks/folk.owl (RDF/XML to Turtle)",
    "ThatsAllFolks/folk_Religion.ttl":
        "renamed from upstream ThatsAllFolks/folk_Belief.ttl during retargeting",
}

#: Path-sensitive configuration, retained where it is. Invisible to a
#: .py/.ttl sweep, which is why .gitignore was missed twice.
RETAINED_CONFIG = {".gitignore", "pytest.ini", "README.md",
                   "pyproject.toml", "tox.ini", "setup.cfg",
                   "config/move-manifest.yaml", "config/repository-layout.yaml",
                   "config/reorganization-baseline.json",
                   "config/path-sensitive-inventory.md"}
RETAINED_CONFIG_DIRS = (".github/",)

#: Exact source -> destination. Explicit beats clever: the family-prefix
#: approach silently ate basenames. Every entry preserves its filename unless a
#: rename is deliberate, and the validator enforces that.
EXACT: dict[str, str] = {
    "BFO/bfo-core.ttl": "ontology/bfo/vendor/bfo/bfo-core.ttl",
    "BFO/valuenet-core.ttl": "ontology/bfo/core/valuenet-core.ttl",
    "BFO/valuenet-folk.ttl": "ontology/bfo/core/valuenet-folk.ttl",
    "BFO/valuenet-schwartz-values.ttl": "ontology/bfo/core/valuenet-schwartz-values.ttl",
    "BFO/valuenet-mappings.ttl": "ontology/bfo/core/valuenet-mappings.ttl",
    "BFO/valuenet-moral-foundations.ttl":
        "ontology/bfo/extensions/moral-foundations/valuenet-moral-foundations.ttl",
    "BFO/valuenet-moral-epistemics.ttl":
        "ontology/bfo/extensions/moral-epistemics/valuenet-moral-epistemics.ttl",
    "BFO/valuenet-moral-epistemics-scenario.ttl":
        "ontology/bfo/extensions/moral-epistemics/valuenet-moral-epistemics-scenario.ttl",
    "BFO/valuenet-moral-epistemics-CQ.md":
        "ontology/bfo/extensions/moral-epistemics/valuenet-moral-epistemics-CQ.md",
    "BFO/valuenet-moral-epistemics-shapes.ttl":
        "ontology/bfo/shapes/valuenet-moral-epistemics-shapes.ttl",
    "BFO/valuenet-core-shapes.ttl": "ontology/bfo/shapes/valuenet-core-shapes.ttl",
    "BFO/vcvf-triggers-shapes.ttl": "ontology/bfo/shapes/vcvf-triggers-shapes.ttl",
    "BFO/vcvf-triggers-semantics.ttl":
        "ontology/bfo/extensions/trigger-semantics/vcvf-triggers-semantics.ttl",
    "BFO/vcvf-triggers-review.md": "docs/bfo/guides/vcvf-triggers-review.md",
    "BFO/remediation/generate_cco_extract.py": "tools/bfo/generate_cco_extract.py",
    "BFO/remediation/check_bfo_consistency.py": "tools/bfo/check_bfo_consistency.py",
    "BFO/remediation/extract-manifest.schema.json":
        "tools/bfo/extract-manifest.schema.json",
    "ValueNet_code/report_run.py": "tools/marep/report_run.py",
    "ValueNet_code/build_move_manifest.py": "tools/marep/build_move_manifest.py",
    "REPO_REORGANIZATION_PLAN.md": "docs/architecture/REPO_REORGANIZATION_PLAN.md",
}

#: Test module -> group. Assigned by what a module exercises, not when it was
#: written. Listing them explicitly is what lets the manifest catch a test
#: filed into the wrong group.
TEST_GROUPS: dict[str, str] = {
    "test_runtime.py": "marep", "test_adjudicator.py": "marep",
    "test_agents.py": "marep", "test_ingest.py": "marep",
    "test_resume.py": "marep", "test_grounding_strength.py": "marep",
    "test_commitments.py": "marep/ontology",
    "test_constraint_metrics.py": "marep/ontology",
    "test_duplication_metrics.py": "marep/ontology",
    "test_reasoner_scope.py": "marep/ontology",
    "test_ontology_source.py": "marep/ontology",
    "test_ontology_artifacts.py": "original-valuenet",
    "test_folk_generation.py": "original-valuenet",
    "test_trigger_shapes.py": "original-valuenet",
    "test_bfo_alignment_remediation.py": "bfo",
    "test_bfo_cco_extract.py": "bfo",
    "test_bfo_core_definitions.py": "bfo",
    "test_bfo_external_closure.py": "bfo",
    "test_bfo_mapping_semantics.py": "bfo",
    "test_bfo_moral_epistemics_categories.py": "bfo",
    "test_competency_questions.py": "integration",
}

#: DIRECTORY prefixes: the matched part is a path segment and is replaced.
#: Applied only after EXACT and the test table. Ordered, specific first.
DIR_PREFIXES: list[tuple[str, str]] = [
    ("BFO/imports/", "ontology/bfo/vendor/cco/"),
    ("BFO/remediation/", "docs/bfo/remediation/"),
    ("BFO/", "docs/bfo/guides/"),
    ("ValueNet_code/", "tools/original-valuenet/"),
    ("examples/", "examples/marep/"),
]

#: NAME prefixes: the match is part of the FILENAME and must be preserved.
#: Treating these like directory prefixes stripped "MAREP_" off every document,
#: turning MAREP_v2.1.md into docs/marep/specifications/1.md. The validator
#: caught it, which is the whole reason it exists.
NAME_PREFIXES: list[tuple[str, str]] = [
    ("MAREP_v2.", "docs/marep/specifications/"),
    ("MAREP_RUN", "docs/marep/runs/"),
    ("MAREP_", "docs/marep/plans/"),
]


#: Migration waves. Steps 7 through 11 each move exactly one, and the waves must
#: partition the MOVE rows: no row omitted, no row in two waves. Derived from
#: the destination rather than stored by hand, so a new destination cannot
#: silently land outside every wave.
WAVE_RULES: list[tuple[tuple[str, ...], str]] = [
    (("ontology/bfo/", "tools/bfo/", "docs/bfo/"), "bfo"),
    (("docs/marep/", "tools/marep/", "examples/marep/"), "marep"),
    (("tools/original-valuenet/",), "original-valuenet"),
    (("docs/architecture/",), "architecture"),
    (("tests/",), "tests"),
]


def wave_of(destination: str) -> str | None:
    if destination in ("RETAIN", "UNASSIGNED"):
        return None
    for prefixes, name in WAVE_RULES:
        if destination.startswith(prefixes):
            return name
    return "UNASSIGNED-WAVE"


def destination(path: str, origin: str) -> str:
    if origin == "upstream-valuenet":
        return "RETAIN"
    if path in RETAINED_CONFIG or path.startswith(RETAINED_CONFIG_DIRS):
        return "RETAIN"
    if path in EXACT:
        return EXACT[path]
    if path.startswith("tests/"):
        name = posixpath.basename(path)
        if name == "conftest.py":
            return "tests/conftest.py"
        group = TEST_GROUPS.get(name)
        return f"tests/{group}/{name}" if group else "UNASSIGNED"
    if path.startswith("marep/"):
        # The framework implementation is not relocated by this plan.
        return "RETAIN"
    for prefix, dest in DIR_PREFIXES:
        if path.startswith(prefix):
            return dest + path[len(prefix):]
    for prefix, dest in NAME_PREFIXES:
        if path.startswith(prefix):
            return dest + posixpath.basename(path)
    return "UNASSIGNED"


def validate(rows: list[dict]) -> list[str]:
    """Refuse a manifest whose destinations are malformed."""
    problems: list[str] = []
    seen: dict[str, str] = {}
    for r in rows:
        d, p = r["destination"], r["path"]
        if d in ("RETAIN", "UNASSIGNED"):
            continue
        base = posixpath.basename(d)
        if not base:
            problems.append(f"{p}: destination has no filename ({d})")
        elif base.startswith("."):
            problems.append(f"{p}: destination is a hidden/extension-only name ({d})")
        elif posixpath.splitext(base)[1] != posixpath.splitext(posixpath.basename(p))[1]:
            problems.append(f"{p}: extension changed ({d})")
        elif base != posixpath.basename(p):
            problems.append(f"{p}: undeclared rename to {base}")
        if posixpath.isabs(d) or ".." in d.split("/"):
            problems.append(f"{p}: unsafe destination ({d})")
        if d in seen:
            problems.append(f"{p}: destination collides with {seen[d]} ({d})")
        seen[d] = p
    return problems


def classify(path: str, up: set[str]) -> tuple[str, str]:
    if path in up:
        changed = sh("git", "diff", "--stat", "upstream/main", "HEAD", "--", path)
        return "upstream-valuenet", ("locally-modified" if changed.strip() else "unchanged")
    if path.startswith("BFO/imports/"):
        return "external-cco", "generated"
    if path.endswith("bfo-core.ttl"):
        return "external-bfo", "unchanged"
    if path in KNOWN_UPSTREAM_DESCENT or _from_upstream(path, up):
        return "upstream-valuenet", "locally-modified"
    return "fork", ("generated" if path in GENERATED else "unchanged")


def _from_upstream(path: str, up: set[str]) -> bool:
    names = sh("git", "log", "--follow", "--name-only", "--format=", "--", path)
    return any(n.strip() in up for n in names.split("\n") if n.strip())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)

    up = upstream_paths()
    rows = []
    for path in tracked():
        origin, maintenance = classify(path, up)
        rows.append({
            "path": path, "origin": origin, "maintenance": maintenance,
            "generated_from": GENERATED.get(path),
            "destination": destination(path, origin),
            "wave": wave_of(destination(path, origin)),
        })

    unassigned = [r["path"] for r in rows if r["destination"] == "UNASSIGNED"]
    problems = validate(rows)
    # The waves must partition the moves. A destination outside every wave
    # would be moved by no step, which the plan forbids.
    problems += [f"{r['path']}: destination {r['destination']} belongs to no "
                 f"migration wave" for r in rows if r["wave"] == "UNASSIGNED-WAVE"]
    moves = sum(1 for r in rows if r["destination"] not in ("RETAIN", "UNASSIGNED"))

    print(f"  {len(rows)} tracked files")
    print(f"    {sum(1 for r in rows if r['destination'] == 'RETAIN'):>4}  RETAIN")
    print(f"    {moves:>4}  MOVE")
    print(f"    {len(unassigned):>4}  UNASSIGNED")
    waves = {}
    for r in rows:
        if r["wave"] and r["wave"] != "UNASSIGNED-WAVE":
            waves[r["wave"]] = waves.get(r["wave"], 0) + 1
    print("  waves: " + ", ".join(f"{k} {v}" for k, v in sorted(waves.items())))

    if unassigned:
        print("\n  UNASSIGNED — refusing to write:")
        for p in unassigned[:20]:
            print(f"      {p}")
    if problems:
        print(f"\n  {len(problems)} malformed destination(s) — refusing to write:")
        for p in problems[:20]:
            print(f"      {p}")
    if unassigned or problems:
        return 1

    if args.out:
        import yaml
        target = os.path.join(HERE, args.out)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        # Atomic: a partial or rejected run must never replace a good manifest.
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(target), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            yaml.safe_dump({"components": rows}, fh, sort_keys=False)
        os.replace(tmp, target)
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
