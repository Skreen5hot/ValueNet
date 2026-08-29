"""Repository invariants for the ontology artifacts themselves.

These are not tests of `marep`. They are tests of the files in this repository,
and they exist because of a specific failure: 127 `ThatsAllFolks/folk_*.ttl`
files declared none of the prefixes they used. They were written to be read
alongside a parent that supplied the bindings, which put correctness in the
reader rather than in the artifact — a file that only loads if you already know
the convention is not a document, it is a fragment of one.

The invariant encoded here is that a `.ttl` file in this repository is a valid
Turtle document on its own, with no header injection, no format guessing, and
no knowledge of where it sits in a directory tree. Anything a loader has to
know in order to read the file belongs in the file.

The same principle produced a second invariant. Eight files carried a `.owl`
extension; seven of them held Turtle, and a loader that believed the suffix
reported six perfectly good ontologies as broken. The repository now states its
serialization in the extension and `test_extensions_state_the_serialization`
holds it there, so no reader needs private knowledge of which files lie.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

# The repository root comes from the layout contract, not from counting
# parents. This file moves one level deeper in the tests wave, at which
# point parents[1] resolves to tests/ and every path below it is wrong
# without raising anything.
from marep.layout import repository_root  # noqa: E402

REPO = repository_root()
SKIP_DIRS = {".git", "_run", "__pycache__", "node_modules"}

#: The fragment corpus was 38,949 triples when the prefix headers were added.
#: A floor rather than an equality: content may legitimately grow, and the
#: failure this guards against is the opposite one — making files parse by
#: deleting what would not parse.
FRAGMENT_TRIPLE_FLOOR = 38_000

_PREFIX_DECL = re.compile(r"@prefix\s+([A-Za-z0-9_-]*):", re.I)
_PREFIX_USE = re.compile(r"(?<![<\w:/#-])([A-Za-z][A-Za-z0-9_-]*):(?![/\w]*//)")
_TRIPLE_QUOTED = re.compile(r'"""[\s\S]*?"""')
_QUOTED = re.compile(r'"(?:[^"\\\n]|\\.)*"')
_COMMENT = re.compile(r"(?m)#.*$")
_BUILTIN = frozenset({"http", "https", "file", "urn", "mailto", "doi", "tag"})


def ttl_files(*subpaths: str) -> list[Path]:
    roots = [REPO / s for s in subpaths] if subpaths else [REPO]
    out: list[Path] = []
    for root in roots:
        out.extend(p for p in root.rglob("*.ttl")
                   if not SKIP_DIRS & set(p.parts))
    return sorted(out)


def undeclared_prefixes(text: str) -> list[str]:
    """Prefixes used outside literals and comments but never declared."""
    body = _COMMENT.sub("", _QUOTED.sub('""', _TRIPLE_QUOTED.sub('""', text)))
    declared = set(_PREFIX_DECL.findall(text))
    used = {u for u in _PREFIX_USE.findall(body) if u not in _BUILTIN}
    return sorted(used - declared)


FRAGMENTS = sorted((REPO / "ThatsAllFolks").glob("folk_*.ttl"))


@pytest.mark.parametrize("path", FRAGMENTS, ids=lambda p: p.name)
def test_every_fragment_is_self_contained(path: Path):
    """Every prefix a fragment uses is declared in that fragment.

    Checked separately from parsing because the failure message matters: a
    bare parse error names a line number, while this names the prefix that is
    missing, which is what a person needs in order to fix it.
    """
    missing = undeclared_prefixes(path.read_text(encoding="utf-8", errors="replace"))
    assert not missing, (
        f"{path.name} uses {missing} without declaring them. A .ttl file must "
        "carry its own bindings; relying on a parent to supply them puts "
        "correctness in the reader rather than the artifact.")


@pytest.mark.parametrize("path", FRAGMENTS, ids=lambda p: p.name)
def test_every_fragment_parses_standalone(path: Path):
    """No header injection, no format guessing, no directory context."""
    graph = rdflib.Graph()
    try:
        graph.parse(str(path), format="turtle")
    except Exception as exc:
        pytest.fail(f"{path.name} is not a valid Turtle document on its own: "
                    f"{' '.join(str(exc).split())[:160]}")
    assert len(graph) > 0, f"{path.name} parses but carries no statements"


def test_the_fragment_corpus_has_not_been_emptied():
    """Guards the repair that makes a file parse by deleting its content."""
    total = 0
    for path in FRAGMENTS:
        g = rdflib.Graph()
        g.parse(str(path), format="turtle")
        total += len(g)
    assert total >= FRAGMENT_TRIPLE_FLOOR, (
        f"the fragment corpus holds {total:,} triples, below the "
        f"{FRAGMENT_TRIPLE_FLOOR:,} floor — a file was probably made to parse "
        "by removing what would not parse")


#: rdflib's name for the serialization a given extension promises. A file whose
#: suffix is absent here is not an ontology artifact and is not checked.
EXTENSION_FORMAT = {".ttl": "turtle", ".owl": "xml", ".rdf": "xml",
                    ".nt": "nt", ".n3": "n3", ".jsonld": "json-ld"}


def ontology_files() -> list[Path]:
    return sorted(p for p in REPO.rglob("*")
                  if p.suffix.lower() in EXTENSION_FORMAT
                  and not SKIP_DIRS & set(p.parts))


@pytest.mark.slow
def test_extensions_state_the_serialization():
    """A file's extension is a fact about the file, not a hint.

    The counterexample: `.owl` files holding Turtle. Nothing was wrong with
    their content, but every reader had to be told which ones lied, which is
    exactly the knowledge that should not live in the reader.
    """
    liars = []
    for path in ontology_files():
        promised = EXTENSION_FORMAT[path.suffix.lower()]
        try:
            rdflib.Graph().parse(str(path), format=promised)
        except Exception:
            actual = next((f for f in ("turtle", "xml", "n3", "nt", "json-ld")
                           if f != promised and _parses_as(path, f)), None)
            liars.append(f"{path.relative_to(REPO)}: named {promised}, "
                         + (f"is {actual}" if actual else "parses as nothing"))
    joined = "\n".join(f"  {x}" for x in liars)
    assert not liars, ("these files do not hold the format their extension "
                       "promises:\n" + joined)


def _parses_as(path: Path, fmt: str) -> bool:
    try:
        rdflib.Graph().parse(str(path), format=fmt)
        return True
    except Exception:
        return False


@pytest.mark.slow
def test_every_ttl_in_the_repository_parses_standalone():
    """The invariant generalised past the fragments.

    Marked slow because it parses the whole corpus, including files of a
    megabyte and more. Run it with `-m slow`, or let CI run the full suite.
    """
    failures = []
    for path in ttl_files():
        try:
            rdflib.Graph().parse(str(path), format="turtle")
        except Exception as exc:
            failures.append(f"{path.relative_to(REPO)}: "
                            f"{' '.join(str(exc).split())[:90]}")
    assert not failures, "these .ttl files are not valid Turtle on their own:\n" + \
        "\n".join(f"  {f}" for f in failures)
