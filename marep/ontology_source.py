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
    """State what a passing run did not check. Empty when it checked plenty."""
    parts = []
    if individuals == 0:
        parts.append("no individuals in scope, so no ABox was checked")
    if contradiction < 50:
        parts.append(f"only {contradiction} axioms could have produced a failure")
    if unresolved:
        parts.append(f"{len(unresolved)} import(s) name an ontology no file "
                     "in scope provides, so those axioms were absent")
    return "; ".join(parts)
