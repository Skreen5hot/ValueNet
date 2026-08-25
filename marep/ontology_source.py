"""Ontology facts as substrate records (MAREP v2.2 §7).

`ingest.py` builds a substrate from git history, which grounds a retrospective
about *work done*. It cannot ground one about *the state of an artifact*: "127
files do not parse" is a fact about no commit, so under the git source alone
such a finding has no admissible evidence and can never leave `proposed`.

This module closes that gap the same way the git source closed the first one.
It runs the validation battery and emits each result as a citable record, so an
agent's claim about the ontology resolves to something checkable rather than
standing on the agent's word.

Two properties carried over from `ingest.py`, for the same reasons:

**Determinism.** Timestamps come from git, never from the clock — a document is
stamped with the commit that last touched it, a metric with the HEAD commit it
describes. A check that stamped itself with `now()` would make the substrate
differ on every run and break the stable-identifier guarantee that lets earlier
evidence keep resolving.

**Honest gaps.** A check that cannot run says so as a record, rather than being
absent. A metric that is missing because a tool was unavailable looks exactly
like a metric that is missing because the defect is not there, and only one of
those is a reason for confidence.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

#: Files that are vendored upstream rather than authored here. Still measured —
#: they are part of what a load has to parse — but flagged so a finding about
#: them is not mistaken for a finding about this repository's own work.
VENDORED = ("bfo-core.ttl",)

ONTOLOGY_SUFFIXES = (".ttl", ".owl")

#: Directories whose contents form a coherent group for group-level metrics.
GROUPS: tuple[tuple[str, str], ...] = (
    ("BFO/valuenet-", "bfo-layer"),
    ("BFO/", "bfo-vendored"),
    ("ThatsAllFolks/", "thats-all-folks"),
    ("MFTriggers/", "mf-triggers"),
    ("MoralMolecules/", "moral-molecules"),
    ("vale2024/", "vale2024"),
)

#: Formats to try, in order. Kept as a fallback for foreign input, but no
#: longer load-bearing here: every ontology file in this repository is now a
#: .ttl containing Turtle, and a test asserts that the extension tells the
#: truth. This list once mattered because six .owl files held Turtle and
#: trusting the suffix reported them as unparseable.
PARSE_FORMATS = ("turtle", "xml", "n3", "nt")

_PREFIX_DECL = re.compile(r"@prefix\s+([A-Za-z0-9_-]*):", re.I)
_PREFIX_USE = re.compile(r"(?<![<\w:/#-])([A-Za-z][A-Za-z0-9_-]*):(?![/\w]*//)")
_BUILTIN = frozenset({"http", "https", "file", "urn", "mailto", "doi", "tag"})


def group_of(rel: str) -> str:
    rel = rel.replace("\\", "/")
    for prefix, name in GROUPS:
        if rel.startswith(prefix):
            return name
    return "repository-root"


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class FileFacts:
    """Everything measurable about one ontology file."""

    rel: str
    group: str
    checksum: str
    bytes: int
    parses: bool
    parse_error: str = ""
    triples: int = 0
    classes: int = 0
    imports: list[str] = None
    undeclared_prefixes: list[str] = None
    vendored: bool = False
    parsed_as: str = ""
    #: Class IRIs declared in this file. Kept out of the emitted record — a
    #: payload listing thousands of IRIs helps nobody — but needed to count
    #: how much of the corpus a scoped check leaves unmeasured.
    class_iris: frozenset = frozenset()

    def summary(self) -> str:
        if not self.parses:
            return f"{self.rel} does not parse: {self.parse_error}"
        return (f"{self.rel} parses as {self.parsed_as}: {self.triples} triples, "
                f"{self.classes} classes, {len(self.imports or [])} imports")


#: Upper ontologies a class can root in. "Not rooted in BFO" and "not rooted
#: at all" are different findings, and a check that only knows about BFO
#: reports the DUL layer as ungrounded when it is grounded elsewhere.
UPPER_ONTOLOGIES: tuple[tuple[str, str], ...] = (
    ("bfo", "http://purl.obolibrary.org/obo/BFO_"),
    ("dul", "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#"),
    ("dolce", "http://www.loa-cnr.it/ontologies/DOLCE"),
    ("skos", "http://www.w3.org/2004/02/skos/core#"),
    ("sumo", "http://www.adampease.org/OP/SUMO.owl#"),
)


_TRIPLE_QUOTED = re.compile(r'"""[\s\S]*?"""')
_QUOTED = re.compile(r'"(?:[^"\\\n]|\\.)*"')
_COMMENT = re.compile(r"(?m)#.*$")


def undeclared_prefixes(text: str) -> list[str]:
    """Prefixes used but never declared.

    A cheap textual check that happens to be the whole ThatsAllFolks story: a
    file using `folk:` and `vcvf:` with no `@prefix` line is not a Turtle
    document, whatever its extension says.

    String literals and comments are stripped first. Without that, prose inside
    an rdfs:comment — "compare OBI:has specified input" — reads as a prefix use
    and the check reports undeclared prefixes in files that declare everything.
    A metric that cries wolf is worse than no metric, because a finding built on
    it looks grounded.
    """
    body = _COMMENT.sub("", _QUOTED.sub('""', _TRIPLE_QUOTED.sub('""', text)))
    declared = set(_PREFIX_DECL.findall(text))
    used = {u for u in _PREFIX_USE.findall(body) if u not in _BUILTIN}
    return sorted(used - declared)


def measure_file(path: Path, repo: Path) -> FileFacts:
    import rdflib
    from rdflib.namespace import OWL, RDF

    rel = str(path.relative_to(repo)).replace("\\", "/")
    text = path.read_text(encoding="utf-8", errors="replace")
    facts = FileFacts(
        rel=rel, group=group_of(rel), checksum=sha256(path), bytes=path.stat().st_size,
        parses=False, imports=[], undeclared_prefixes=[],
        vendored=path.name in VENDORED,
    )
    g = None
    first_error = ""
    for fmt in PARSE_FORMATS:
        candidate = rdflib.Graph()
        try:
            candidate.parse(str(path), format=fmt)
            g = candidate
            facts.parsed_as = fmt
            break
        except Exception as exc:
            if not first_error:
                first_error = " ".join(str(exc).split())[:140]
    if g is None:
        facts.parse_error = first_error
        facts.undeclared_prefixes = undeclared_prefixes(text)
        return facts
    facts.parses = True
    # The prefix check is a Turtle rule and only means anything for Turtle. Run
    # against RDF/XML it reads English prose inside text nodes as prefix uses
    # and reports "Justice", "cohabitation" and "have" as undeclared. Files
    # that fail to parse keep the check — an unparseable file is exactly where
    # a missing prefix is worth naming.
    if facts.parsed_as != "xml":
        facts.undeclared_prefixes = undeclared_prefixes(text)
    facts.triples = len(g)
    iris = {str(x) for x in g.subjects(RDF.type, OWL.Class) if isinstance(x, rdflib.URIRef)}
    facts.class_iris = frozenset(iris)
    facts.classes = len(iris)
    facts.imports = sorted(str(o) for o in g.objects(None, OWL.imports))
    return facts


def discover(repo: Path, scopes: Iterable[str] | None = None) -> list[Path]:
    """Ontology files under `repo`, optionally limited to given subpaths."""
    roots = [repo / s for s in scopes] if scopes else [repo]
    found: set[Path] = set()
    for root in roots:
        if root.is_file():
            found.add(root)
            continue
        for suffix in ONTOLOGY_SUFFIXES:
            found.update(p for p in root.rglob(f"*{suffix}")
                         if ".git" not in p.parts and "_run" not in p.parts)
    return sorted(found)


# ----------------------------------------------------------------------
# metrics
# ----------------------------------------------------------------------

@dataclass
class Metric:
    check: str
    scope: str
    value: float
    detail: str = ""
    tool: str = "rdflib"

    @property
    def ref(self) -> str:
        return f"{self.check}:{self.scope}"

    def summary(self) -> str:
        v = int(self.value) if float(self.value).is_integer() else round(self.value, 4)
        return f"{self.check} for {self.scope}: {v}" + (f" ({self.detail})" if self.detail else "")


def group_metrics(facts: list[FileFacts]) -> list[Metric]:
    """Per-group aggregates. The numbers a corpus-level finding would cite."""
    out: list[Metric] = []
    by_group: dict[str, list[FileFacts]] = {}
    for f in facts:
        by_group.setdefault(f.group, []).append(f)

    for group, fs in sorted(by_group.items()):
        ok = [f for f in fs if f.parses]
        bad = [f for f in fs if not f.parses]
        out.append(Metric("files_total", group, len(fs)))
        out.append(Metric("files_parsing", group, len(ok)))
        out.append(Metric("files_not_parsing", group, len(bad),
                          detail=", ".join(f.rel for f in bad[:4]) + ("…" if len(bad) > 4 else "")))
        # Named as sums, not totals. They add per-file counts, so any module
        # stored in two files contributes twice. That was routine when every
        # BFO module was kept as both .ttl and .owl; the repository now keeps
        # one serialization each, but the name still says what it does, since
        # the next duplicate pair should not be able to hide inside a "total".
        out.append(Metric("triples_sum_over_files", group, sum(f.triples for f in ok),
                          detail="sum across files; a module stored twice is counted twice"))
        out.append(Metric("classes_sum_over_files", group, sum(f.classes for f in ok),
                          detail="sum across files; a module stored twice is counted twice"))
        noprefix = [f for f in fs if f.undeclared_prefixes]
        out.append(Metric("files_with_undeclared_prefixes", group, len(noprefix),
                          detail=", ".join(sorted({p for f in noprefix
                                                   for p in f.undeclared_prefixes})[:6])))
    return out


#: Parsed graphs, keyed by content checksum. `measure_file` parses every file
#: once, and then `duplication_metrics`, `constraint_metrics` and
#: `shape_coverage_metrics` each parsed them all again — five passes over
#: 162,446 triples to answer questions that could share one. Keyed on the
#: checksum rather than the path so that a file edited between calls is
#: re-read rather than served stale, which matters because these run inside a
#: substrate build that must describe the tree as it is at HEAD.
_GRAPH_CACHE: dict[str, Any] = {}


def graph_for(repo: Path, fact: FileFacts):
    """The parsed graph for one file, parsed at most once per content."""
    import rdflib
    cached = _GRAPH_CACHE.get(fact.checksum)
    if cached is not None:
        return cached
    g = rdflib.Graph()
    try:
        g.parse(str(repo / fact.rel), format=fact.parsed_as or None)
    except Exception:
        g = rdflib.Graph()
    _GRAPH_CACHE[fact.checksum] = g
    return g


def merged_graph(repo: Path, facts: Iterable[FileFacts]):
    """One graph over several files, built from the per-file cache."""
    import rdflib
    out = rdflib.Graph()
    for f in facts:
        if f.parses:
            for triple in graph_for(repo, f):
                out.add(triple)
    return out


def clear_graph_cache() -> None:
    """Drop the cache. Called by tests that write files in a tmp_path."""
    _GRAPH_CACHE.clear()


def duplication_metrics(repo: Path, facts: list[FileFacts]) -> list[Metric]:
    """How much of each group's bulk is the same triple stated again.

    Every count in `group_metrics` is a sum over files, which is honest about
    what it does but says nothing about how much distinct content a group
    holds. The gap is not small: `mf-triggers` sums to 24,684 triples and
    merges to 12,364, and `thats-all-folks` sums to 83,497 and merges to
    44,934. Just under half of each is restatement.

    That matters beyond tidiness, because a corpus-size figure is exactly the
    sort of number a finding leans on. An agent has already read two equal
    triple counts as evidence that `folk.owl` and `folk_aligned.ttl` were the
    same file, when they are not isomorphic. Emitting the merged count next to
    the summed one removes the inference rather than arguing with it.

    Listed in MAREP_VALUENET_PLAN §2 as one of three checks still missing.
    """
    import rdflib

    out: list[Metric] = []
    by_group: dict[str, list[FileFacts]] = {}
    for f in facts:
        if f.parses:
            by_group.setdefault(f.group, []).append(f)

    for group, fs in sorted(by_group.items()):
        merged = merged_graph(repo, fs)
        summed = sum(f.triples for f in fs)
        distinct = len(merged)
        out.append(Metric("triples_distinct_in_group", group, distinct,
                          detail=f"{summed:,} summed over {len(fs)} files"))
        if summed:
            out.append(Metric("duplicate_triple_ratio", group,
                              round((summed - distinct) / summed, 4),
                              detail=f"{summed - distinct:,} of {summed:,} triples "
                                     "are the same statement made in another file"))
    return out


def constraint_metrics(repo: Path, facts: list[FileFacts]) -> list[Metric]:
    """What each group asserts about its own terms, and what it leaves open.

    Run 1 could ask whether the corpus loads and whether it contradicts itself.
    Neither question reaches the one Run 2 is scoped to: what does this corpus
    treat as true without ever saying so. A finding of that kind — "sibling
    dispositions under `MoralValueDisposition` are never declared disjoint" —
    has no admissible evidence under the existing records, because absence of
    an axiom is a fact about no file, no commit and no metric. It would sit in
    `proposed` forever, exactly as findings about unparseable files did before
    this module existed.

    So each check here counts a population and the subset of it that carries a
    given axiom. A bare "37 properties have no domain" invites the reading that
    37 domains are missing, which is false: some properties are deliberately
    polymorphic, and `vcvf:triggers` relating almost anything to almost
    anything may well be correct. The denominator and the names travel with the
    count so a finding has to argue rather than point.

    Nothing here proposes a constraint. These records say what is and is not
    asserted; deciding whether an absence is a gap or a considered choice is
    the judgement Run 2 exists to make, and it is not one a count can settle.
    """
    import rdflib
    from rdflib.namespace import OWL, RDF, RDFS

    out: list[Metric] = []
    by_group: dict[str, list[FileFacts]] = {}
    for f in facts:
        if f.parses:
            by_group.setdefault(f.group, []).append(f)

    def names(iris, n=5):
        """Sample the set, and say plainly that it is a sample.

        This printed the first five alphabetically followed by a bare ellipsis.
        An agent then read a list that did not contain
        `hasPositiveCounterpart` and concluded the property lacked an inverse,
        which is false -- it is declared both ways and so never entered the
        set at all. A second agent overturned the finding by noticing that the
        list included a later-sorting name, which is a lot of work to ask of a
        reader in order to not be misled. Absence from a truncated list is not
        evidence of anything, so the truncation now names itself.
        """
        ordered = sorted(iris)
        short = [str(i).split("#")[-1].split("/")[-1] for i in ordered[:n]]
        if len(ordered) <= n:
            return ", ".join(short) if short else "none"
        return (", ".join(short)
                + f" (first {n} of {len(ordered)} alphabetically; the rest are "
                  f"not shown and absence from this list means nothing)")

    # Every property declared anywhere in the corpus, gathered before the group
    # loop so that "used but not declared" means what it says.
    declared_anywhere: set = set()
    for f in facts:
        if not f.parses:
            continue
        cg = graph_for(repo, f)
        for kind in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty,
                     RDF.Property):
            declared_anywhere |= {s for s in cg.subjects(RDF.type, kind)
                                  if isinstance(s, rdflib.URIRef)}

    for group, fs in sorted(by_group.items()):
        g = merged_graph(repo, fs)

        # Only terms this group declares. Counting imported BFO properties as
        # lacking a domain would report the upstream ontology's choices as this
        # repository's omissions.
        obj_props = {s for s in g.subjects(RDF.type, OWL.ObjectProperty)
                     if isinstance(s, rdflib.URIRef)}
        data_props = {s for s in g.subjects(RDF.type, OWL.DatatypeProperty)
                      if isinstance(s, rdflib.URIRef)}
        props = obj_props | data_props
        if props:
            no_domain = {p for p in props if (p, RDFS.domain, None) not in g}
            no_range = {p for p in props if (p, RDFS.range, None) not in g}
            out.append(Metric("properties_declared", group, len(props),
                              detail=f"{len(obj_props)} object, {len(data_props)} datatype"))
            out.append(Metric("properties_without_domain", group, len(no_domain),
                              detail=f"of {len(props)} declared: {names(no_domain)}"))
            out.append(Metric("properties_without_range", group, len(no_range),
                              detail=f"of {len(props)} declared: {names(no_range)}"))
            characterised = set()
            for c in (OWL.FunctionalProperty, OWL.InverseFunctionalProperty,
                      OWL.TransitiveProperty, OWL.SymmetricProperty,
                      OWL.AsymmetricProperty, OWL.ReflexiveProperty,
                      OWL.IrreflexiveProperty):
                characterised |= set(g.subjects(RDF.type, c))
            characterised |= {s for s, _, _ in g.triples((None, OWL.inverseOf, None))}
            characterised |= {o for _, _, o in g.triples((None, OWL.inverseOf, None))}
            plain = props - characterised
            out.append(Metric("properties_without_characteristics", group, len(plain),
                              detail=f"of {len(props)} declared, no functionality, "
                                     f"transitivity, symmetry or inverse: {names(plain)}"))

        # What logical machinery the group has at all, per group and without a
        # reasoner. HermiT runs only over the BFO layer inside a substrate
        # build, because `repository-root` alone costs 23 minutes, so the
        # survey's central fact — four groups holding 143,717 triples in which
        # nothing can contradict anything — would otherwise be uncitable, and a
        # finding resting on it could never leave `proposed`. These two are
        # pure functions of the graph and cost nothing. Named apart from the
        # `reasoner_*` records so the two never collide on a ref, which is a
        # bug Run 1 already found once when `classes_total:bfo-layer` was
        # emitted twice with different values.
        capacity = _contradiction_axioms(g)
        out.append(Metric("contradiction_capacity", group, capacity,
                          detail="axioms by which a reasoner could find this group "
                                 "inconsistent" + ("; none, so a consistency "
                                 "verdict over it is guaranteed" if not capacity else "")))
        out.append(Metric("individuals_declared", group, _individuals(g),
                          detail="instances available to a SHACL shape or an ABox check"))

        # Predicates the group asserts with but never declares. `mf-triggers`
        # is the case that makes this worth a check: it declares no class and
        # no property at all, so every other check here skips it silently,
        # while it states `vcvf:triggers` thousands of times. A group can be
        # invisible to a constraint audit precisely because it constrains
        # nothing — which is the finding, not a reason to omit it.
        used = {p for _, p, _ in g if isinstance(p, rdflib.URIRef)}
        used -= {p for p in used if str(p).startswith(
            ("http://www.w3.org/1999/02/22-rdf-syntax-ns#",
             "http://www.w3.org/2000/01/rdf-schema#",
             "http://www.w3.org/2002/07/owl#",
             "http://www.w3.org/2004/02/skos/core#",
             "http://purl.org/dc/", "http://www.w3.org/ns/shacl#"))}
        # Declaration is looked for corpus-wide, not group-wide. The BFO layer
        # uses BFO_0000055 and three siblings without declaring them, but the
        # vendored bfo-core.ttl does declare them and merely sits in another
        # group. Scoping the lookup to the group reported four properties as
        # undeclared when the corpus declares all four — the same false gap as
        # matching imports on ontology IRI alone, arrived at from a different
        # direction. A group boundary is a fact about this module's filing, not
        # about the ontology.
        # Emitted even when the count is zero. An absent metric is
        # indistinguishable from a check that did not run, and this module's
        # standing rule is that a gap says so as a record.
        undeclared = used - declared_anywhere
        out.append(Metric("predicates_used_but_not_declared", group, len(undeclared),
                          detail=f"of {len(used)} non-builtin predicates in use; "
                                 f"declaration looked for across the whole "
                                 f"corpus, not just this group: {names(undeclared)}"))

        # Sibling sets: a named parent with two or more named direct children.
        # Whether siblings should be disjoint is a domain question — folk value
        # vocabularies are meant to overlap — so this reports the population
        # and how much of it is decided either way, not a shortfall.
        children: dict[Any, set] = {}
        for s, _, o in g.triples((None, RDFS.subClassOf, None)):
            if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef):
                children.setdefault(o, set()).add(s)
        sibling_sets = {p: c for p, c in children.items() if len(c) > 1}
        if sibling_sets:
            disjoint_pairs = set()
            for a, _, b in g.triples((None, OWL.disjointWith, None)):
                disjoint_pairs.add(frozenset((a, b)))
            for node in g.subjects(RDF.type, OWL.AllDisjointClasses):
                for lst in g.objects(node, OWL.members):
                    members = list(rdflib.collection.Collection(g, lst))
                    for i, a in enumerate(members):
                        for b in members[i + 1:]:
                            disjoint_pairs.add(frozenset((a, b)))
            decided = {p for p, kids in sibling_sets.items()
                       if any(frozenset((a, b)) in disjoint_pairs
                              for a in kids for b in kids if a != b)}
            undecided = set(sibling_sets) - decided
            out.append(Metric("sibling_sets", group, len(sibling_sets),
                              detail="named parents with two or more named direct "
                                     "subclasses"))
            out.append(Metric("sibling_sets_without_disjointness", group, len(undecided),
                              detail=f"of {len(sibling_sets)}; whether siblings should "
                                     f"be disjoint is a domain question, not a "
                                     f"shortfall: {names(undecided)}"))

        # Classes whose only assertion is where they sit. No equivalent class,
        # no restriction, nothing that constrains an instance of them.
        declared = {s for s in g.subjects(RDF.type, OWL.Class)
                    if isinstance(s, rdflib.URIRef)}
        if declared:
            constrained = {s for s, _, _ in g.triples((None, OWL.equivalentClass, None))}
            constrained |= {s for s, _, o in g.triples((None, RDFS.subClassOf, None))
                            if isinstance(o, rdflib.BNode)}
            bare = declared - constrained
            out.append(Metric("classes_without_necessary_conditions", group, len(bare),
                              detail=f"of {len(declared)}; placed in a hierarchy but "
                                     f"carrying no restriction or equivalence: "
                                     f"{names(bare)}"))
    return out


def shape_coverage_metrics(repo: Path, facts: list[FileFacts]) -> list[Metric]:
    """Classes that have instances but no SHACL shape targeting them.

    The complement of `shacl_focus_nodes`, and the record a SHACL-side finding
    needs. Fourteen focus nodes across a 162,446-triple corpus says the shapes
    reach almost nothing; this says what they are failing to reach, which is
    the part a proposal has to name.
    """
    import rdflib
    from rdflib.namespace import RDF

    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    shape_files = sorted((repo / "BFO").glob("*-shapes.ttl")) if (repo / "BFO").exists() else []
    targeted = set()
    for sf in shape_files:
        try:
            sg = rdflib.Graph(); sg.parse(str(sf))
        except Exception:
            continue
        targeted |= {str(o) for o in sg.objects(None, SH.targetClass)}

    out: list[Metric] = []
    by_group: dict[str, list[FileFacts]] = {}
    for f in facts:
        if f.parses:
            by_group.setdefault(f.group, []).append(f)

    for group, fs in sorted(by_group.items()):
        g = merged_graph(repo, fs)
        populated: dict[str, int] = {}
        for _, _, o in g.triples((None, RDF.type, None)):
            if isinstance(o, rdflib.URIRef) and str(o).startswith(
                    ("http://www.ontologydesignpatterns.org", "https://fandaws.com",
                     "http://purl.obolibrary.org", "https://www.commoncoreontologies.org")):
                populated[str(o)] = populated.get(str(o), 0) + 1
        if not populated:
            continue
        uncovered = {c: n for c, n in populated.items() if c not in targeted}
        top = sorted(uncovered.items(), key=lambda kv: -kv[1])[:4]
        out.append(Metric("populated_classes", group, len(populated),
                          detail="classes with at least one instance in this group"))
        out.append(Metric("populated_classes_without_a_shape", group, len(uncovered),
                          detail=f"of {len(populated)}; largest: " + ", ".join(
                              f"{c.split('#')[-1].split('/')[-1]} ({n})" for c, n in top)))
    return out


def suite_metrics(repo: Path, facts: list[FileFacts]) -> list[Metric]:
    """Checks specific to the BFO-aligned suite, where a namespace is known."""
    import rdflib
    from rdflib.namespace import OWL, RDF, RDFS, SKOS

    NS = "https://fandaws.com/ontology/bfo/"
    BFO = "http://purl.obolibrary.org/obo/BFO_"
    # A distinct scope from the file-group name. These measure the merged
    # import closure, not the directory, and sharing "bfo-layer" made two
    # different numbers answer to one reference.
    SCOPE = "bfo-suite-merged"
    out: list[Metric] = []

    modules = [repo / "BFO" / f"{n}.ttl" for n in (
        "valuenet-core", "valuenet-schwartz-values", "valuenet-moral-foundations",
        "valuenet-folk", "valuenet-moral-epistemics", "valuenet-mappings")]
    modules = [m for m in modules if m.exists()]
    if not modules:
        return out

    merged = rdflib.Graph()
    for m in modules:
        try:
            merged.parse(str(m))
        except Exception:
            return out

    declared = {str(s) for s in set(merged.subjects(RDF.type, None))
                if str(s).startswith(NS) and "#" in str(s)}
    referenced = {str(t) for s, p, o in merged for t in (s, p, o)
                  if isinstance(t, rdflib.URIRef) and str(t).startswith(NS) and "#" in str(t)}
    out.append(Metric("dangling_iris", SCOPE, len(referenced - declared),
                      detail=", ".join(sorted(referenced - declared)[:3])))

    parents: dict[Any, set] = {}
    for a, b in merged.subject_objects(RDFS.subClassOf):
        if isinstance(b, rdflib.URIRef):
            parents.setdefault(a, set()).add(b)

    def ancestors(n, seen=None):
        seen = seen or set()
        for q in parents.get(n, ()):
            if q not in seen:
                seen.add(q)
                ancestors(q, seen)
        return seen

    classes = [c for c in set(merged.subjects(RDF.type, OWL.Class))
               if isinstance(c, rdflib.URIRef) and str(c).startswith(NS)]
    grounded = [c for c in classes
                if any(str(a).startswith(BFO) for a in ancestors(c))]
    out.append(Metric("classes_total", SCOPE, len(classes)))
    out.append(Metric("classes_reaching_bfo_root", SCOPE, len(grounded)))
    out.append(Metric("classes_missing_label", SCOPE,
                      sum(1 for c in classes if not list(merged.objects(c, RDFS.label)))))
    out.append(Metric("classes_missing_definition", SCOPE,
                      sum(1 for c in classes if not list(merged.objects(c, SKOS.definition)))))

    # How much of the corpus this check does not see. Three agents in a live
    # run independently read `classes_reaching_bfo_root: 179 / 179` as "the
    # ontology is grounded", which it does not say: the check is scoped to one
    # layer. The scope was in the record's ref all along and that was not
    # enough — an absence has to be measured to be citable, not merely implied
    # by the presence of something narrower.
    corpus_classes = set()
    for f in facts:
        corpus_classes |= f.class_iris
    measured = {str(c) for c in classes}
    out.append(Metric("classes_distinct_in_corpus", "corpus", len(corpus_classes),
                      detail="distinct class IRIs across every parsing file"))
    out.append(Metric("classes_measured_for_grounding", "corpus", len(measured),
                      detail="the population classes_reaching_bfo_root is computed over"))
    out.append(Metric("classes_unmeasured_for_grounding", "corpus",
                      len(corpus_classes - measured),
                      detail="declared in the corpus but outside the grounding check's scope"))

    # A ttl_owl_isomorphic metric used to live here, checking that each module's
    # two serializations agreed. The repository now keeps one serialization per
    # module, so there is nothing to compare and the whole class of drift it
    # guarded against cannot occur.
    return out


def rooting_metrics(repo: Path, facts: list[FileFacts]) -> list[Metric]:
    """Where each group's classes bottom out, across the whole corpus.

    Run 1 reported that hygiene metrics covered 179 of ~2,900 classes, which
    was true. Widening the BFO check alone would have swapped one distortion
    for another: the DUL layer is not ungrounded, it is grounded in DOLCE, and
    a BFO-only check would have called it broken. So the question asked here is
    "what does this class root in", not "does it root in BFO".
    """
    import rdflib
    from rdflib.namespace import RDFS

    merged = rdflib.Graph()
    for path in discover(repo):
        for fmt in PARSE_FORMATS:
            try:
                merged.parse(str(path), format=fmt)
                break
            except Exception:
                continue

    parents: dict[Any, set] = {}
    for a, b in merged.subject_objects(RDFS.subClassOf):
        if isinstance(b, rdflib.URIRef):
            parents.setdefault(a, set()).add(b)

    def roots(node) -> set[str]:
        seen, stack, hit = set(), [node], set()
        while stack:
            cur = stack.pop()
            for parent in parents.get(cur, ()):
                if parent in seen:
                    continue
                seen.add(parent)
                text = str(parent)
                for name, prefix in UPPER_ONTOLOGIES:
                    if text.startswith(prefix):
                        hit.add(name)
                stack.append(parent)
        return hit

    out: list[Metric] = []
    by_group: dict[str, set[str]] = {}
    for f in facts:
        by_group.setdefault(f.group, set()).update(f.class_iris)

    for group, iris in sorted(by_group.items()):
        counts: dict[str, int] = {name: 0 for name, _ in UPPER_ONTOLOGIES}
        unrooted = 0
        for iri in iris:
            hit = roots(rdflib.URIRef(iri))
            if not hit:
                unrooted += 1
            for name in hit:
                counts[name] += 1
        out.append(Metric("classes_declared", group, len(iris),
                          detail="distinct class IRIs in this group"))
        for name, _ in UPPER_ONTOLOGIES:
            if counts[name]:
                out.append(Metric(f"classes_rooted_in_{name}", group, counts[name]))
        out.append(Metric("classes_with_no_upper_root", group, unrooted,
                          detail="reach no known upper ontology by rdfs:subClassOf"))
    return out


def shacl_metrics(repo: Path) -> list[Metric]:
    """SHACL results, or an honest record that the check could not run."""
    out: list[Metric] = []
    shapes = sorted((repo / "BFO").glob("*-shapes.ttl")) if (repo / "BFO").exists() else []
    if not shapes:
        return out
    try:
        import pyshacl
        import rdflib
        from rdflib.namespace import RDF
        SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    except ImportError:
        return [Metric("shacl_available", "bfo-layer", 0, detail="pyshacl not installed",
                       tool="pyshacl")]

    data = rdflib.Graph()
    loaded = 0
    # The trigger shapes target predicates, not classes, so their data graph is
    # the trigger corpus rather than the BFO layer. Loading ThatsAllFolks here
    # is what takes shacl_focus_nodes from 14 to the tens of thousands: three
    # of seven groups declare no individuals at all, and a class-targeted shape
    # could never have reached them.
    for n in ("valuenet-core", "valuenet-schwartz-values", "valuenet-moral-foundations",
              "valuenet-folk", "valuenet-moral-epistemics", "valuenet-moral-epistemics-scenario"):
        p = repo / "BFO" / f"{n}.ttl"
        if p.exists():
            try:
                data.parse(str(p))
                loaded += 1
            except Exception:
                pass
    # What the shape check does not see. A live agent read `shacl_violations: 0`
    # and pointed out it is largely an artifact of 127 files never being
    # loadable: a file that cannot be parsed cannot violate a shape. Same
    # scope-blindness as the grounding metric, so it gets the same treatment.
    # How many nodes the shapes actually reached. "Zero violations" over a
    # graph nothing targets is vacuous, and Run 1 caught exactly that: the
    # result was read as a clean bill of health for a corpus 127 of whose
    # files never entered the data graph. A denominator makes the difference
    # between "checked and clean" and "not checked" visible.
    focus = 0
    for shape_graph_file in shapes:
        try:
            sg = rdflib.Graph(); sg.parse(str(shape_graph_file))
        except Exception:
            continue
        for cls in sg.objects(None, SH.targetClass):
            focus += sum(1 for _ in data.subjects(RDF.type, cls))
        for prop in sg.objects(None, SH.targetSubjectsOf):
            focus += len({s for s in data.subjects(prop, None)})

    in_repo = len(discover(repo))
    out.append(Metric("shacl_files_validated", "corpus", loaded,
                      detail=f"of {in_repo} ontology files in the repository; the "
                             "data graph is the BFO layer plus the scenario, "
                             "nothing else", tool="pyshacl"))
    out.append(Metric("shacl_focus_nodes", "corpus", focus,
                      detail="nodes the shapes actually targeted; zero violations over "
                             "zero focus nodes says nothing", tool="pyshacl"))

    # The denominator travels with every verdict, not just in a record beside
    # it. A finding cites one metric, and `shacl_violations: 0` on its own is
    # the same over-readable shape as `reasoner_consistent: 1` was.
    reach = (f"over {focus} focus node(s) in {loaded} of {in_repo} files"
             + ("; nothing was checked" if not focus else ""))

    for shape_file in shapes:
        try:
            sg = rdflib.Graph(); sg.parse(str(shape_file))
            _c, rg, _t = pyshacl.validate(data, shacl_graph=sg, advanced=True, inference="none")
            results = list(rg.subjects(RDF.type, SH.ValidationResult))
            sev = [str(rg.value(r, SH.resultSeverity)).split("#")[-1] for r in results]
            out.append(Metric("shacl_violations", shape_file.stem,
                              sum(1 for s in sev if s == "Violation"),
                              detail=reach, tool="pyshacl"))
            out.append(Metric("shacl_warnings", shape_file.stem,
                              sum(1 for s in sev if s == "Warning"), tool="pyshacl"))
        except Exception as exc:
            out.append(Metric("shacl_error", shape_file.stem, 1,
                              detail=" ".join(str(exc).split())[:90], tool="pyshacl"))
    return out


#: Axiom forms that can make a class unsatisfiable or a KB inconsistent. A
#: reasoner run over a graph containing none of these cannot fail, so the count
#: is reported next to the verdict: `reasoner_consistent: 1` is a claim about
#: the ontology only in proportion to how much of this machinery was present.
def _contradiction_axioms(graph) -> int:
    from rdflib.namespace import OWL, RDF
    n = 0
    for p in (OWL.disjointWith, OWL.complementOf, OWL.disjointUnionOf,
              OWL.propertyDisjointWith, OWL.maxCardinality,
              OWL.maxQualifiedCardinality, OWL.cardinality,
              OWL.qualifiedCardinality, OWL.differentFrom):
        n += len(list(graph.triples((None, p, None))))
    for c in (OWL.AllDisjointClasses, OWL.AllDisjointProperties, OWL.AllDifferent):
        n += len(list(graph.subjects(RDF.type, c)))
    for c in (OWL.FunctionalProperty, OWL.InverseFunctionalProperty,
              OWL.IrreflexiveProperty, OWL.AsymmetricProperty):
        n += len(list(graph.subjects(RDF.type, c)))
    return n


def _unresolved_imports(graph) -> set:
    """Imports that nothing in the graph answers to, under either of its names.

    A file answers to two IRIs: its ontology IRI and its `owl:versionIRI`. Both
    have to count. `valuenet-core` imports BFO by *version* IRI
    (`obo/bfo/2020/bfo-core.ttl`) while the vendored copy declares itself as
    `obo/bfo.owl` and carries that version IRI. Matching on ontology IRI alone
    reported BFO 2020 as missing, and the verdict then said upstream axioms
    were absent while all 1,014 triples of them were loaded — a false gap, the
    same failure this module was rewritten to stop making, reintroduced by the
    rewrite meant to prevent it.
    """
    from rdflib.namespace import OWL, RDF
    answers_to = {str(s) for s in graph.subjects(RDF.type, OWL.Ontology)}
    answers_to |= {str(o) for _, _, o in graph.triples((None, OWL.versionIRI, None))}
    requested = {str(o) for _, _, o in graph.triples((None, OWL.imports, None))}
    return requested - answers_to


def _individuals(graph) -> int:
    """ABox size: subjects typed by something that is not an OWL/RDFS builtin."""
    import rdflib
    from rdflib.namespace import OWL, RDF, RDFS
    builtin = {OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
               OWL.AnnotationProperty, OWL.Ontology, OWL.Restriction,
               OWL.AllDisjointClasses, OWL.AllDisjointProperties,
               OWL.AllDifferent, OWL.NamedIndividual, OWL.FunctionalProperty,
               OWL.InverseFunctionalProperty, OWL.TransitiveProperty,
               OWL.SymmetricProperty, OWL.AsymmetricProperty,
               OWL.ReflexiveProperty, OWL.IrreflexiveProperty,
               RDFS.Class, RDFS.Datatype, RDF.Property}
    return len({s for s, _, o in graph.triples((None, RDF.type, None))
                if o not in builtin and isinstance(s, rdflib.URIRef)})


def reasoner_metrics(repo: Path, scope: str = "bfo-layer") -> list[Metric]:
    """HermiT consistency, reported together with the reach of the check.

    Opt-in: needs a JRE and takes seconds, not milliseconds.

    A bare `reasoner_consistent: 1` is the most over-readable number this
    module produces. It was true of the BFO layer while that layer held no
    individuals at all, declared 31 axioms capable of causing a contradiction
    against 277 `subClassOf`, and had its `owl:imports` stripped before
    loading — so BFO's and CCO's own axioms were absent and a class asserted to
    be both a continuant and an occurrent would have passed. None of that was
    visible in the metric, which is the same defect as the four false facts
    this module was fixed for once already: an accurate number that invites a
    conclusion it does not support.

    So the verdict now travels with its denominators. `reasoner_individuals`,
    `reasoner_contradiction_axioms`, and `reasoner_imports_unresolved` are
    emitted as their own records, and the verdict's `detail` says plainly when
    the check was one nothing could have failed.
    """
    try:
        import owlready2  # noqa: F401
    except ImportError:
        return [Metric("reasoner_available", scope, 0,
                       detail="owlready2 not installed", tool="hermit")]
    import tempfile

    import rdflib
    from rdflib.namespace import OWL, RDF

    if scope == "bfo-layer":
        names = ["bfo-core", "valuenet-core", "valuenet-schwartz-values",
                 "valuenet-moral-foundations", "valuenet-folk",
                 "valuenet-moral-epistemics", "valuenet-mappings"]
        paths = [repo / "BFO" / f"{n}.ttl" for n in names]
        # Everything the layer imports and supplies locally, not just the
        # modules. The hardcoded list above missed the pinned CCO extract when
        # the alignment remediation added it, so HermiT was checking a layer
        # whose imported Agent, Act of Appraisal and Act of Observation axioms
        # were absent — and reporting the import unresolved while the file sat
        # in the tree. A hardcoded list ages badly; the glob does not.
        paths += sorted((repo / "BFO" / "imports").glob("*.ttl"))
        paths = [p for p in paths if p.exists()]
    else:
        paths = [repo / f.rel for f in
                 (measure_file(p, repo) for p in discover(repo))
                 if f.group == scope and f.parses]

    merged = rdflib.Graph()
    loaded = 0
    for p in paths:
        try:
            merged.parse(str(p))
            loaded += 1
        except Exception:
            return [Metric("reasoner_error", scope, 1,
                           detail=f"{p.name} did not parse", tool="hermit")]

    if loaded == 0:
        return [Metric("reasoner_available", scope, 0,
                       detail="no parseable files in scope", tool="hermit")]

    unresolved = _unresolved_imports(merged)
    individuals = _individuals(merged)
    contradiction = _contradiction_axioms(merged)

    for t in list(merged.triples((None, OWL.imports, None))):
        merged.remove(t)
    for s in list(merged.subjects(RDF.type, OWL.Ontology)):
        merged.remove((s, RDF.type, OWL.Ontology))
    merged.add((rdflib.URIRef("http://example.org/marep-check"), RDF.type, OWL.Ontology))

    classes = len(set(merged.subjects(RDF.type, OWL.Class)))
    reach = [
        Metric("reasoner_files", scope, loaded, tool="hermit"),
        Metric("reasoner_triples", scope, len(merged), tool="hermit"),
        Metric("reasoner_individuals", scope, individuals, tool="hermit",
               detail="" if individuals else
                      "no ABox: this is a TBox satisfiability check only"),
        Metric("reasoner_contradiction_axioms", scope, contradiction, tool="hermit",
               detail="disjointness, complement, cardinality, functional and "
                      "difference axioms: the only ways a run can fail"),
        Metric("reasoner_imports_unresolved", scope, len(unresolved), tool="hermit",
               detail=("none: every import is declared by a file in scope"
                      if not unresolved else ", ".join(sorted(unresolved)[:3]))),
    ]

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "merged.owl"
        merged.serialize(destination=str(path), format="xml")
        try:
            from owlready2 import default_world, get_ontology, sync_reasoner_hermit
            onto = get_ontology("file://" + str(path.resolve())).load()
            with onto:
                sync_reasoner_hermit(infer_property_values=False, debug=0)
            unsat = list(default_world.inconsistent_classes())
            return reach + [
                Metric("reasoner_consistent", scope, 1, tool="hermit",
                       detail=_verdict_caveat(individuals, contradiction, unresolved)),
                Metric("unsatisfiable_classes", scope, len(unsat), tool="hermit",
                       detail=(", ".join(c.name for c in unsat[:5]) if unsat
                               else f"of {classes} classes; "
                                    f"{contradiction} axioms could have made one fail")),
            ]
        except Exception as exc:
            name = type(exc).__name__
            consistent = 0 if "Inconsistent" in name else 1
            return reach + [Metric("reasoner_consistent", scope, consistent,
                                   detail=f"{name}: {' '.join(str(exc).split())[:80]}",
                                   tool="hermit")]


def _verdict_caveat(individuals: int, contradiction: int, unresolved: set) -> str:
    """State what a passing run did not check. Empty when it checked plenty.

    The zero case is called vacuous rather than weak, and deliberately leads.
    A graph with no disjointness, no cardinality, no functionality and no
    complement cannot be made inconsistent by any reasoner, so "consistent, 0
    unsatisfiable" over it is a restatement of the input, not a result. Four of
    this repository's seven groups are in that position, covering 143,717 of
    its triples: mf-triggers, moral-molecules, thats-all-folks and vale2024 are
    flat taxonomies, and every second HermiT spent on them bought nothing.
    Saying "only 0 axioms could have produced a failure" is true but reads as a
    quantitative caveat on a real finding; it is not one.
    """
    parts = []
    if contradiction == 0:
        parts.append("VACUOUS: no axiom in scope can produce a contradiction, "
                     "so this verdict was guaranteed before the reasoner ran")
    elif contradiction < 50:
        parts.append(f"only {contradiction} axioms could have produced a failure")
    if individuals == 0:
        parts.append("no individuals in scope, so no ABox was checked")
    if unresolved:
        parts.append(f"{len(unresolved)} import(s) name an ontology no file "
                     "in scope provides, so those axioms were absent")
    return "; ".join(parts)
