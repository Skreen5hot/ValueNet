# SPDX-License-Identifier: Apache-2.0
"""Resolve repository paths from the layout contract, not from source location.

Layout was hardcoded in three independent modules and twenty files. A move
therefore meant editing twenty files under a half-broken tree, which is why the
plan puts this step before any relocation.

Two properties matter more than convenience.

**Self-locating.** The repository root is found by walking up for
`config/repository-layout.yaml`, not by counting `parents[N]` from a module's
own file. The eight example programs each compute their root as
`Path(__file__).resolve().parents[1]`, which silently becomes `examples/`
rather than the repository once they move one level deeper — a wrong root that
raises nothing and simply reads the wrong tree.

**Migration-tolerant.** A component declares where it is and where it is going.
`resolve` returns whichever exists, preferring the destination once it appears.
So a consumer never needs to know which wave has run, and a half-moved tree
resolves correctly at every intermediate commit. That is what allows the plan's
per-commit gate to mean anything: the gate can run between waves without the
tooling reporting failures that are really just relocation in progress.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

CONTRACT = "config/repository-layout.yaml"


class LayoutError(RuntimeError):
    """The contract is malformed, or was asked for an unknown id.

    Distinct from `LayoutMissing` on purpose. A consumer may reasonably fall
    back to a hardcoded rule when there is no contract at all — a checkout of
    one file, a vendored copy. It may not fall back because the contract is
    broken: catching every exception turned malformed YAML, an unknown
    component id, and a bug in this module into the same silent "use the legacy
    path" outcome, which is how a resolver failure becomes invisible.
    """


class LayoutMissing(LayoutError):
    """No contract exists above the starting point. The only fallback case."""


@lru_cache(maxsize=1)
def repository_root(start: Path | None = None) -> Path:
    """Walk up until the layout contract is found."""
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONTRACT).is_file():
            return candidate
    raise LayoutMissing(
        f"no {CONTRACT} found above {here}. The layout contract locates the "
        "repository root; without it paths cannot be resolved.")


@dataclass(frozen=True)
class Component:
    id: str
    path: str
    moves_to: str | None
    role: str
    corpus_group: str | None = None
    generated_from: str | None = None
    generator: str | None = None
    pattern: str | None = None
    expect: str | None = None
    group_prefixes: list | None = None
    group_prefixes_after: list | None = None
    members: list | None = None
    members_after: list | None = None
    plus_directory: str | None = None
    description: str = ""

    def resolve(self, root: Path | None = None) -> Path:
        """The path that exists now, preferring the post-move location.

        Preference order matters. During a wave the destination appears before
        anything removes the source, and returning the destination first means
        a consumer reads the moved component rather than a stale copy.
        """
        base = root or repository_root()
        if self.moves_to:
            moved = base / self.moves_to
            if moved.exists():
                return moved
        current = base / self.path
        if current.exists():
            return current
        raise LayoutError(
            f"component {self.id!r} resolves to neither {self.path!r} nor "
            f"{self.moves_to!r} under {base}")


@lru_cache(maxsize=1)
def _load() -> dict[str, Component]:
    import yaml
    root = repository_root()
    doc = yaml.safe_load((root / CONTRACT).read_text(encoding="utf-8"))
    if not doc or "components" not in doc:
        raise LayoutError(f"{CONTRACT} declares no components")
    out: dict[str, Component] = {}
    for raw in doc["components"]:
        try:
            c = Component(**raw)
        except TypeError as exc:
            raise LayoutError(f"malformed component {raw.get('id')!r}: {exc}")
        if c.id in out:
            raise LayoutError(f"duplicate component id {c.id!r}")
        out[c.id] = c
    return out


def component(component_id: str) -> Component:
    known = _load()
    if component_id not in known:
        raise LayoutError(
            f"unknown component {component_id!r}. Declared: "
            + ", ".join(sorted(known)))
    return known[component_id]


def path(component_id: str) -> Path:
    return component(component_id).resolve()


def components(role: str | None = None) -> list[Component]:
    return [c for c in _load().values() if role is None or c.role == role]


def corpus_groups() -> dict[str, str]:
    """Path prefix -> group name, for the MAREP corpus source.

    Prefix-based, not directory-based, because the hardcoded rule it replaces
    is `BFO/valuenet-` -> bfo-layer and `BFO/` -> bfo-vendored. Deriving the
    prefix from a component's directory reclassified the CCO extract and both
    vcvf-triggers files out of bfo-vendored the moment the contract was
    adopted — three files silently regrouped by a change meant to move nothing.

    A component declares the prefixes selecting the same logical files before
    and after the move, and both sets are emitted: during migration some files
    sit at each, and a prefix matching nothing costs nothing.
    """
    out: dict[str, str] = {}
    for c in _load().values():
        if not c.corpus_group or c.members:
            continue
        befores = c.group_prefixes or [c.path.rstrip("/") + "/"]
        afters = c.group_prefixes_after or ([c.moves_to.rstrip("/") + "/"]
                                            if c.moves_to else [])
        for prefix in list(befores) + list(afters):
            out[prefix] = c.corpus_group
    return dict(sorted(out.items(), key=lambda kv: -len(kv[0])))


def corpus_group_members() -> dict[str, str]:
    """Exact path -> group, checked before any prefix.

    The BFO groups cannot be expressed as destination prefixes. Membership
    follows the FILENAME today — "BFO/valuenet-" is bfo-layer — while the
    destinations sort by ROLE, so the two valuenet SHACL files land under
    shapes/ beside the vendored vcvf-triggers-shapes.ttl. No prefix separates
    them. The prefix version reported zero group changes against the unmoved
    tree and silently reclassified three files the moment they moved.
    """
    out: dict[str, str] = {}
    for c in _load().values():
        if not (c.corpus_group and c.members):
            continue
        for p in list(c.members) + list(c.members_after or []):
            out[p] = c.corpus_group
    return out


def group_for(rel_path: str) -> str:
    """The corpus group of a repository-relative path, exact members first."""
    members = corpus_group_members()
    if rel_path in members:
        return members[rel_path]
    for prefix, group in corpus_groups().items():
        if rel_path.startswith(prefix):
            return group
    return "repository-root"


def reasoner_scope() -> list[Path]:
    """Exactly the files HermiT loads, listed rather than globbed.

    The hardcoded list omitted `BFO/imports/` and the reasoner silently dropped
    from 306 classes to 275 while every test stayed green.
    """
    root = repository_root()
    c = component("bfo.reasoner-scope")
    out: list[Path] = []
    for before, after in zip(c.members or [], c.members_after or []):
        for candidate in ((root / after), (root / before)):
            if candidate.exists():
                out.append(candidate)
                break
    if c.plus_directory:
        d = component(c.plus_directory).resolve(root)
        out.extend(sorted(d.glob("*.ttl")))
    return out


def bfo_module(name: str, root: Path | None = None) -> Path | None:
    """A BFO module by stem, wherever it currently lives.

    `repo / "BFO" / f"{n}.ttl"` is correct today and empty after the BFO wave,
    and an empty module list produces a metric of zero rather than an error —
    the exact silent-shrink failure that took the reasoner from 306 classes to
    275. The contract carries every module's before and after path, so this
    finds it either side of the move.
    """
    real = repository_root()
    if root is not None and Path(root).resolve() != real:
        # A synthetic tree gets its own files. Resolving this repository's
        # modules for a caller measuring a fixture reported 187 classes for a
        # two-file tmp tree, and the reconciliation check caught it.
        hits = sorted(Path(root).rglob(name + ".ttl"))
        return hits[0] if hits else None
    for group in ("bfo.core", "bfo.vendored"):
        c = component(group)
        for candidate in list(c.members_after or []) + list(c.members or []):
            if Path(candidate).stem == name:
                p = real / candidate
                if p.exists():
                    return p
    return None


def bfo_modules(*names: str, root: Path | None = None) -> list[Path]:
    """Only those that exist, in the order asked for."""
    return [p for p in (bfo_module(n, root) for n in names) if p is not None]


def shape_files(root: Path | None = None) -> list[Path]:
    """Every SHACL shape set, wherever it lives.

    Globbing `BFO/*-shapes.ttl` finds three files today and none after the
    wave, when they sit under ontology/bfo/shapes/.

    `root` matters. A caller measuring a synthetic tree — a test fixture in a
    tmp_path — must get that tree's shapes, not this repository's. Ignoring the
    argument made two fixture tests read the real BFO shapes and report a
    coverage number about the wrong corpus.
    """
    real = repository_root()
    if root is not None and Path(root).resolve() != real:
        return sorted(Path(root).rglob("*-shapes.ttl"))
    root = real
    found: list[Path] = []
    for group in ("bfo.core", "bfo.vendored"):
        c = component(group)
        for candidate in list(c.members_after or []) + list(c.members or []):
            p = root / candidate
            if p.exists() and p.name.endswith("-shapes.ttl") and p not in found:
                found.append(p)
    tree = component("bfo.ontology-tree").resolve(root)
    for p in sorted(tree.rglob("*-shapes.ttl")):
        if p not in found:
            found.append(p)
    return sorted(set(found))


def bfo_artifact(filename: str) -> Path:
    """Any file under the BFO tree, by name, before or after the move.

    Tests resolved the repository root correctly and then appended
    `BFO/<name>`, which is right today and gone after the BFO wave. The root
    was never the hard part; the artifact is.
    """
    root = repository_root()
    for group in ("bfo.core", "bfo.vendored", "bfo.reasoner-scope"):
        c = component(group)
        for candidate in list(c.members_after or []) + list(c.members or []):
            if Path(candidate).name == filename:
                p = root / candidate
                if p.exists():
                    return p
    tree = component("bfo.ontology-tree").resolve(root)
    for p in tree.rglob(filename):
        return p
    for extra in ("docs/bfo/guides", "docs/bfo/remediation", "tools/bfo",
                  "BFO/remediation"):
        p = root / extra / filename
        if p.exists():
            return p
    raise LayoutError(f"no BFO artifact named {filename!r} under {root}")


def path_allowances() -> list[dict]:
    """Occurrences that are correct as literal paths, each with its reason.

    Two dispositions that look alike and are not: `regenerate` means the value
    asserts where something IS, so a stale value is false; `preserve` means it
    records where something WAS, so rewriting it would falsify a record.
    """
    import yaml
    doc = yaml.safe_load((repository_root() / CONTRACT).read_text(encoding="utf-8"))
    return list(doc.get("path_allowances") or [])


def query_documents() -> list[Component]:
    """Executable query documents, addressed by id.

    `# scope: component:bfo.query-suite.competency` in a query survives the
    move; `# scope: BFO/` does not, and would have left the competency checks
    loading nothing for three commits.
    """
    return [c for c in _load().values() if c.role == "executable-queries"]


def run_artifacts_dir() -> Path:
    """Where an example writes its run state. Never committed."""
    c = component("marep.run-artifacts")
    base = repository_root()
    return base / (c.moves_to if (base / c.moves_to).parent.exists() else c.path)


def relative(p: Path | str) -> str:
    """A repository-relative POSIX path, for reporting and manifests."""
    return Path(p).resolve().relative_to(repository_root()).as_posix()


#: The bootstrap every moving script needs, duplicated rather than imported.
#: A script cannot import this module to discover the path that makes this
#: module importable, so the four lines below are the one place the contract
#: cannot be its own authority. Copy them verbatim:
#:
#:     _here = Path(__file__).resolve()
#:     _root = next(p for p in (_here, *_here.parents)
#:                  if (p / "config/repository-layout.yaml").is_file())
#:     sys.path.insert(0, str(_root))
#:
#: Counting parents instead breaks the moment the script changes depth, and
#: breaks silently: parents[1] from tools/marep/ is tools/, which exists.
BOOTSTRAP_DOC = __doc__


def clear_cache() -> None:
    """Tests that write a contract into a tmp_path need this."""
    repository_root.cache_clear()
    _load.cache_clear()
