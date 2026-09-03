# SPDX-License-Identifier: Apache-2.0
"""Extract the class index from the authored ontology modules.

    python tools/site/build_class_index.py

Six authored inputs, three roles:

  * five class-producing modules, which supply the records;
  * valuenet-mappings.ttl, an overlay contributing mapping annotations to
    classes declared elsewhere and no classes of its own; and
  * the vendored BFO core and CCO extract, classification support only --
    they resolve parents and carry the category roots, and none of their
    classes becomes a record.

WHAT THIS REFUSES TO DO

Choose. Where the ontology is ambiguous the build fails instead of
picking: two labels on a class, two definitions, a parent that resolves
nowhere, a class reaching two different category roots. Each of those is
a question for whoever wrote the ontology, and answering it here would
put a value on the public site that nothing in the RDF asserts.

Invent. A class with no `skos:definition` fails rather than borrowing its
label. There is no allowlist; all 187 authored classes carry one today
and the gate is what keeps that true.

Infer. `category` comes from transitive closure over named
`rdfs:subClassOf` edges to four declared roots. Never from an IRI suffix,
a label, or a filename -- a rule keyed on names ending in "Disposition"
would be right until the day it was not, and would never say so.

Translate. Mapping predicates are published exactly as asserted. The four
ValueNet annotation properties are not SKOS relations, and rewriting them
into `skos:exactMatch` would silently strengthen a claim of historical
correspondence into one of logical equivalence.

DETERMINISM

Graph iteration order is not stable, so nothing here depends on it: every
collection is sorted before it is written, classes by normalised label
then IRI, and each array field by its own value. Two builds of one commit
produce identical bytes, from any checkout path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

FORMAT_VERSION = 1
GENERATOR = "tools/site/build_class_index.py"
OUT_INDEX = "_site/data/class-index.json"
OUT_COVERAGE = "_site/data/coverage.json"

VN_CORE = "https://fandaws.com/ontology/bfo/valuenet-core#"

#: The four ValueNet mapping annotation properties, published as asserted.
MAPPING_PREDICATES = tuple(VN_CORE + n for n in (
    "hasBroaderConceptualMatch",
    "hasRelatedConceptualMatch",
    "historicallyCorrespondsTo",
    "ontologyEntityMapping",
))

#: Category roots. Exact IRIs, and the only way a category is decided.
CATEGORY_ROOTS = {
    "http://purl.obolibrary.org/obo/BFO_0000016": "disposition",
    "http://purl.obolibrary.org/obo/BFO_0000023": "role",
    "http://purl.obolibrary.org/obo/BFO_0000015": "process",
    "https://www.commoncoreontologies.org/ont00000958": "information",
}

#: Classes that reach no category root, reviewed and expected.
#: ValueRelatedRealizableEntity subclasses BFO realizable entity and is the
#: common superclass of ValueDisposition and ValueRole, so it sits above
#: the split by design. A new member fails pending review rather than
#: quietly joining a catch-all.
REVIEWED_OTHER = {VN_CORE + "ValueRelatedRealizableEntity"}

#: Contributes mappings, not classes.
OVERLAY_COMPONENT = "bfo.module.mappings"

#: Classification support. Their classes never become records.
SUPPORT_COMPONENTS = ("bfo.vendor-bfo", "bfo.vendor-cco")


class Refused(SystemExit):
    """A question for whoever wrote the ontology, not for this build."""


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(_root),
                       capture_output=True, text=True)
    if r.returncode:
        raise Refused("git " + " ".join(args) + " failed: "
                      + r.stderr.strip()[-300:])
    return r.stdout.strip()


def catalog():
    """The indexed modules and the overlay, from curated configuration."""
    from marep import layout

    site = json.loads(
        (layout.component("site.content").resolve() / "site.json")
        .read_text(encoding="utf-8"))
    primary = site["catalog"]["primary"]
    indexed = [e for e in primary if e["indexed"]]
    if not indexed:
        raise Refused("no module is marked for indexing")
    return indexed


def load(component_id):
    """One module, parsed under the stable document base.

    Never a filesystem base: rdflib would otherwise resolve a relative
    IRI against the absolute path of the checkout, and the index would
    describe the machine that built it.
    """
    import rdflib

    from marep import layout
    from marep import ontology_source as onto

    path = layout.component(component_id).resolve()
    graph = rdflib.Graph()
    if path.is_dir():
        # Some components name a directory -- the CCO extract is one.
        # Sorted, so a build does not depend on directory order.
        members = sorted(path.rglob("*.ttl"), key=lambda q: q.as_posix())
        if not members:
            raise Refused(component_id + " names a directory with no Turtle")
        for member in members:
            onto.parse_source(graph, member, _root)
        return graph, path.relative_to(_root).as_posix()
    onto.parse_source(graph, path, _root)
    return graph, path.relative_to(_root).as_posix()


def one(graph, subject, predicate, what, iri, kind="literal"):
    """Exactly one value of the expected RDF term type, or a refusal.

    `kind` is checked, not assumed. A label that is a blank node or an
    IRI stringifies to something that looks like text -- "N3c8f2..." or
    a URL -- and would be published as the class's name. Requiring the
    term type means an authoring mistake fails here instead of appearing
    on the site as a plausible-looking label.
    """
    import rdflib

    values = list(graph.objects(subject, predicate))
    wrong = [v for v in values
             if (kind == "literal" and not isinstance(v, rdflib.Literal))
             or (kind == "iri" and not isinstance(v, rdflib.URIRef))]
    if wrong:
        raise Refused(
            "%s has a %s that is not %s: %r. Stringifying it would publish "
            "something the ontology does not say."
            % (iri, what, "a literal" if kind == "literal" else "an IRI",
               [str(w)[:60] for w in wrong]))
    if not values:
        raise Refused(
            "%s has no %s. The index publishes what the ontology asserts; "
            "there is no fallback and no allowlist." % (iri, what))
    if len(values) > 1:
        raise Refused(
            "%s has %d values for %s: %s. Which one is published would "
            "otherwise depend on traversal order, so this is a question "
            "for the ontology rather than for the build."
            % (iri, len(values), what,
               sorted(str(v)[:40] for v in values)))
    return str(values[0])


def sole_ontology(graph, source):
    """The one ontology header, or a refusal.

    `next(...)` would take whichever the graph yielded first, so a module
    with two headers would publish one title and silently drop the other
    -- and which one it published could change between runs.
    """
    import rdflib
    from rdflib.namespace import OWL, RDF

    # Counted before filtering. Filtering blank nodes out first meant a
    # module with a named header and a blank-node header counted one and
    # passed, so a second ontology description could sit in the file
    # unread.
    headers = list(graph.subjects(RDF.type, OWL.Ontology))
    if len(headers) != 1:
        raise Refused(
            "%s declares %d owl:Ontology resources (%s). Extraction needs "
            "exactly one; choosing would make the module's identity depend "
            "on traversal order."
            % (source, len(headers), sorted(str(h)[:60] for h in headers)[:3]))
    header = headers[0]
    if not isinstance(header, rdflib.URIRef):
        raise Refused(
            "%s declares its ontology on a blank node. A module has to be "
            "nameable to be cited, linked or downloaded." % source)
    return header


def namespace_of(class_iris, source):
    """The one namespace the module's classes share, derived not guessed.

    The previous version built this by replacing ".owl" in the ontology
    IRI with "#", which invents a string: it happens to match today and
    asserts nothing about the classes. Taken from the class IRIs
    themselves, a module whose classes straddle two namespaces fails
    rather than being described by one of them.
    """
    spaces = set()
    for iri in class_iris:
        if "#" in iri:
            spaces.add(iri.rsplit("#", 1)[0] + "#")
        else:
            spaces.add(iri.rsplit("/", 1)[0] + "/")
    if len(spaces) != 1:
        raise Refused(
            "%s declares classes in %d namespaces (%s); a module card can "
            "name one." % (source, len(spaces), sorted(spaces)[:3]))
    return spaces.pop()


def category_of(iri, parents_of):
    """Transitive closure to a declared root, including the class itself."""
    seen, stack, found = set(), [iri], set()
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        if cur in CATEGORY_ROOTS:
            found.add(CATEGORY_ROOTS[cur])
        stack.extend(parents_of.get(cur, ()))
    if len(found) > 1:
        raise Refused(
            "%s reaches %s. A class in two categories is an ontology "
            "question; picking one here would hide it."
            % (iri, sorted(found)))
    return found.pop() if found else "other"


def module_token(key: str) -> str:
    """A short stable prefix for the compact identifier."""
    return key[len("valuenet-"):] if key.startswith("valuenet-") else key


def build() -> tuple[dict, dict]:
    import rdflib
    from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS

    indexed = catalog()

    # Records come only from these. Parsed separately so every class is
    # attributable to the module that declares it.
    per_module, module_rows = {}, []
    for entry in indexed:
        graph, source = load(entry["component"])
        per_module[entry["key"]] = (graph, source, entry)

    # Annotations: the class modules plus the mappings overlay, which
    # carries assertions about classes declared elsewhere.
    annotations = rdflib.Graph()
    for graph, _s, _e in per_module.values():
        annotations += graph
    overlay, overlay_source = load(OVERLAY_COMPONENT)
    overlay_classes = sorted(
        str(c) for c in overlay.subjects(RDF.type, OWL.Class)
        if isinstance(c, rdflib.URIRef))
    if overlay_classes:
        raise Refused(
            "%s declares %d class(es) (%s). It is loaded as a mapping "
            "overlay and its classes are not indexed, so declaring one here "
            "would drop it from the catalog silently. Either move the class "
            "to a class-producing module or mark this one indexed."
            % (overlay_source, len(overlay_classes), overlay_classes[:3]))
    annotations += overlay

    # Closure: annotations plus classification support. Support classes
    # never become records; they resolve parents and hold the roots.
    closure = rdflib.Graph()
    closure += annotations
    for cid in SUPPORT_COMPONENTS:
        support, _s = load(cid)
        closure += support

    parents_of: dict[str, set] = {}
    for s, o in closure.subject_objects(RDFS.subClassOf):
        if isinstance(s, rdflib.URIRef) and isinstance(o, rdflib.URIRef):
            parents_of.setdefault(str(s), set()).add(str(o))

    # A parent resolves if something declares it a class. The previous
    # version accepted any IRI that appeared as a subject of any triple,
    # so a typo'd parent carrying one stray annotation counted as
    # resolved -- which is most of the ways a dangling parent actually
    # arises.
    declared_classes = {str(s) for s in closure.subjects(RDF.type, OWL.Class)
                        if isinstance(s, rdflib.URIRef)}
    resolvable = declared_classes | set(CATEGORY_ROOTS)

    records, seen_ids, seen_iris, others = [], {}, {}, set()
    for key, (graph, source, entry) in sorted(per_module.items()):
        token = module_token(key)
        ont = sole_ontology(graph, source)
        classes = sorted(
            (str(c) for c in graph.subjects(RDF.type, OWL.Class)
             if isinstance(c, rdflib.URIRef)))
        for iri in classes:
            node = rdflib.URIRef(iri)

            if iri in seen_iris:
                raise Refused(
                    "%s is declared by both %s and %s. Two modules claiming "
                    "one class would otherwise produce two records with "
                    "different compact identifiers and different module "
                    "attributions." % (iri, seen_iris[iri], key))
            seen_iris[iri] = key

            label = one(annotations, node, RDFS.label, "rdfs:label", iri)
            definition = one(annotations, node, SKOS.definition,
                             "skos:definition", iri)

            parents = sorted(
                str(p) for p in annotations.objects(node, RDFS.subClassOf)
                if isinstance(p, rdflib.URIRef))
            if not parents:
                raise Refused(
                    "%s has no named parent. An unattached class cannot be "
                    "categorised and would sit outside the hierarchy the "
                    "site presents." % iri)
            unresolved = [p for p in parents if p not in resolvable]
            if unresolved:
                raise Refused(
                    "%s names parent(s) nothing declares to be a class: %s. "
                    "The site would render a link to a term that does not "
                    "exist." % (iri, unresolved))

            category = category_of(iri, parents_of)
            if category == "other":
                others.add(iri)

            mappings = []
            for predicate in MAPPING_PREDICATES:
                for target in annotations.objects(node,
                                                  rdflib.URIRef(predicate)):
                    if not isinstance(target, rdflib.URIRef):
                        raise Refused(
                            "%s maps to a non-IRI target via %s: %r. "
                            "Dropping it would publish a class as unmapped "
                            "when the ontology says otherwise."
                            % (iri, predicate.rsplit("#", 1)[-1],
                               str(target)[:60]))
                    mappings.append({"predicate": predicate,
                                     "target": str(target)})
            mappings.sort(key=lambda m: (m["predicate"], m["target"]))

            synonym_values = list(annotations.objects(node, SKOS.altLabel))
            non_literal = [v for v in synonym_values
                           if not isinstance(v, rdflib.Literal)]
            if non_literal:
                raise Refused(
                    "%s has a skos:altLabel that is not a literal: %r"
                    % (iri, [str(v)[:50] for v in non_literal]))
            synonyms = sorted({str(v) for v in synonym_values})

            local = iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
            cid = token + ":" + local
            if cid in seen_ids:
                raise Refused(
                    "compact identifier %s is claimed by both %s and %s"
                    % (cid, seen_ids[cid], iri))
            seen_ids[cid] = iri

            records.append({
                "id": cid, "iri": iri, "label": label,
                "definition": definition, "module": key, "source": source,
                "category": category, "parents": parents,
                "mappings": mappings, "synonyms": synonyms,
            })

        module_rows.append({
            "key": key,
            "component": entry["component"],
            "source": source,
            "namespace": namespace_of(classes, source),
            "title": one(graph, ont, DCTERMS.title, "dcterms:title", source),
            "description": one(graph, ont, DCTERMS.description,
                               "dcterms:description", source),
            "license": one(graph, ont, DCTERMS.license, "dcterms:license",
                           source, kind="iri"),
            "classes": len(classes),
        })

    # Mappings are emitted by walking outward from each indexed class, so
    # an assertion whose subject is not indexed -- a misspelled IRI, a
    # class that moved -- is never visited and vanishes without trace.
    #
    # Scanned here in the other direction: every assertion using an
    # approved predicate anywhere in the authored modules or the overlay
    # must have an indexed subject and an IRI target, and the set must
    # equal what the records carry.
    declared_properties = {
        str(s) for kind in (OWL.ObjectProperty, OWL.DatatypeProperty,
                            OWL.AnnotationProperty)
        for s in closure.subjects(RDF.type, kind)
        if isinstance(s, rdflib.URIRef)}

    asserted, property_mappings = set(), []
    for predicate in MAPPING_PREDICATES:
        for subj, obj in annotations.subject_objects(rdflib.URIRef(predicate)):
            if not isinstance(subj, rdflib.URIRef):
                raise Refused(
                    "a %s assertion has a blank-node subject; it cannot be "
                    "attributed to a class"
                    % predicate.rsplit("#", 1)[-1])
            if not isinstance(obj, rdflib.URIRef):
                raise Refused(
                    "%s maps to a non-IRI target via %s: %r"
                    % (str(subj), predicate.rsplit("#", 1)[-1], str(obj)[:60]))
            if str(subj) in seen_iris:
                asserted.add((str(subj), predicate, str(obj)))
                continue
            # Properties carry correspondences too, and legitimately: two
            # do here. They are outside a *class* index, but recording
            # them is the difference between out of scope and lost.
            if str(subj) in declared_properties:
                property_mappings.append({"subject": str(subj),
                                          "predicate": predicate,
                                          "target": str(obj)})
                continue
            raise Refused(
                "%s carries %s and is neither an indexed class nor a "
                "declared property. Walking outward from the index would "
                "drop this assertion without trace, which is exactly what a "
                "misspelled subject looks like."
                % (str(subj), predicate.rsplit("#", 1)[-1]))

    property_mappings.sort(
        key=lambda m: (m["subject"], m["predicate"], m["target"]))

    emitted = {(r["iri"], m["predicate"], m["target"])
               for r in records for m in r["mappings"]}
    if emitted != asserted:
        raise Refused(
            "the index carries %d mapping(s) and the modules assert %d; "
            "missing from the index: %s; not asserted anywhere: %s"
            % (len(emitted), len(asserted),
               sorted(asserted - emitted)[:3], sorted(emitted - asserted)[:3]))

    if others != REVIEWED_OTHER:
        raise Refused(
            "the uncategorised set is %s, reviewed as %s. `other` is not a "
            "catch-all: a new member means either a class outside the four "
            "roots or a support graph that failed to load."
            % (sorted(others), sorted(REVIEWED_OTHER)))

    # Sorted by normalised label then IRI. Graph iteration order is not
    # stable and nothing here may depend on it.
    records.sort(key=lambda r: (r["label"].casefold(), r["iri"]))

    index = {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "source_commit": git("rev-parse", "HEAD"),
        "modules": sorted(module_rows, key=lambda m: m["key"]),
        "classes": records,
    }

    by_category: dict[str, int] = {}
    for r in records:
        by_category[r["category"]] = by_category.get(r["category"], 0) + 1

    # Per module, not only globally. A global figure of "187 of 187" stays
    # at 100% while one module quietly loses every definition and another
    # gains classes, so it cannot show where a gap is.
    per_module_coverage = {}
    for m in index["modules"]:
        rows = [r for r in records if r["module"] == m["key"]]
        per_module_coverage[m["key"]] = {
            "classes": len(rows),
            "with_label": sum(1 for r in rows if r["label"].strip()),
            "with_definition": sum(1 for r in rows if r["definition"].strip()),
            "with_named_parent": sum(1 for r in rows if r["parents"]),
            "with_mapping": sum(1 for r in rows if r["mappings"]),
            "with_synonym": sum(1 for r in rows if r["synonyms"]),
        }

    coverage = {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "source_commit": index["source_commit"],
        "classes": len(records),
        "modules": per_module_coverage,
        "categories": dict(sorted(by_category.items())),
        "with_definition": sum(1 for r in records if r["definition"]),
        "with_mapping": sum(1 for r in records if r["mappings"]),
        "with_synonym": sum(1 for r in records if r["synonyms"]),
        "uncategorised": sorted(others),
        "mappings_on_properties": property_mappings,
        "mappings_on_properties_note":
            "Approved mapping predicates asserted on properties rather than "
            "classes. They are outside a class index and are listed here so "
            "that being out of scope is visible rather than being a silent "
            "omission -- the index is built by walking outward from each "
            "class, which cannot see them.",
        "note": "Coverage is complete by construction: a class missing a "
                "label, a definition or a named parent fails the build "
                "rather than appearing here as a gap. The figures are "
                "published per module so the completeness is visible and "
                "locatable, not so it can be waived.",
    }
    return index, coverage


def validate(index: dict, schema_name: str = "class-index.schema.json") -> None:
    """Against the schema, in the build, before anything is written.

    Validating only in the test suite means the shape is checked where it
    is convenient rather than where it is produced: a generator change
    that broke the contract would ship, and the tests would report it
    afterwards on a artifact already written.
    """
    from jsonschema import Draft7Validator

    from marep import layout

    schema_path = layout.component("site.schemas").resolve() / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft7Validator(schema).iter_errors(index),
                    key=lambda e: list(e.path))
    if errors:
        raise Refused(
            "the generated document does not satisfy %s: %s"
            % (schema_path.name, "; ".join(
                "%s: %s" % ("/".join(str(x) for x in e.path) or "(root)",
                            e.message[:120]) for e in errors[:4])))

def write(path: Path, doc: dict) -> str:
    text = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=OUT_INDEX)
    ap.add_argument("--coverage", default=OUT_COVERAGE)
    args = ap.parse_args(argv)

    index, coverage = build()
    # Both public documents, both validated here rather than in a test:
    # a generator change that broke the contract would otherwise ship and
    # be reported afterwards against an artifact already written.
    validate(coverage, "coverage.schema.json")
    validate(index)

    def target(value):
        p = Path(value)
        return p if p.is_absolute() else _root / p

    i_digest = write(target(args.index), index)
    c_digest = write(target(args.coverage), coverage)

    print("  %d class(es) from %d module(s), commit %s"
          % (len(index["classes"]), len(index["modules"]),
             index["source_commit"][:12]))
    print("    %-30s %5s %5s %5s %5s %5s"
          % ("module", "cls", "lbl", "defn", "par", "map"))
    for key, c in coverage["modules"].items():
        print("    %-30s %5d %5d %5d %5d %5d"
              % (key, c["classes"], c["with_label"], c["with_definition"],
                 c["with_named_parent"], c["with_mapping"]))
    print("  categories %s" % coverage["categories"])
    print("  with mapping %d, with synonym %d"
          % (coverage["with_mapping"], coverage["with_synonym"]))
    print("  %s  sha256 %s" % (args.index, i_digest[:16]))
    print("  %s  sha256 %s" % (args.coverage, c_digest[:16]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
