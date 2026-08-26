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
    """The contract is missing, malformed, or asked for an unknown id."""


@lru_cache(maxsize=1)
def repository_root(start: Path | None = None) -> Path:
    """Walk up until the layout contract is found."""
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONTRACT).is_file():
            return candidate
    raise LayoutError(
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


def clear_cache() -> None:
    """Tests that write a contract into a tmp_path need this."""
    repository_root.cache_clear()
    _load.cache_clear()
