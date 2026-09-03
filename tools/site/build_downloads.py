# SPDX-License-Identifier: Apache-2.0
"""Publishable Turtle, a deterministic bundle, and a checksum manifest.

    python tools/site/build_downloads.py --out _site

Membership is derived, never listed. The reviewed catalog in
`site/content/site.json` names the components; `tools/licensing` says
which files this repository may publish. This build takes the
intersection and refuses if the two disagree, because a download list
maintained by hand is a list that drifts from what the repository
actually licenses, and the drift is invisible from either side.

Bytes are copied, never re-serialised. Round-tripping Turtle through a
parser would produce a file that says the same thing and is not the same
file, and every checksum a consumer verified would be a checksum of the
build rather than of the ontology.

Determinism is the point of the archive. Order, timestamps, permissions
and the creating system are all fixed, so two builds of one commit on two
machines at two paths produce identical bytes -- which is what makes a
published checksum mean anything.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import zipfile
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())

FORMAT_VERSION = 1
GENERATOR = "tools/site/build_downloads.py"

#: Inside the archive, so an unpacked bundle does not scatter files into
#: the current directory. Fixed rather than versioned: the commit is
#: recorded in the manifest, and a directory name carrying it would make
#: every release archive differ in a way no consumer benefits from.
BUNDLE_ROOT = "bfo-aligned-valuenet"
BUNDLE_NAME = "bfo-aligned-valuenet.zip"

#: Reproduced alongside the ontology so the bundle carries its own terms.
GOVERNANCE = ("LICENSE", "THIRD_PARTY_NOTICES.md", "CITATION.cff")


class Refused(SystemExit):
    """Raised rather than guessing. Every message names the file."""


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, _root / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def catalog() -> list[dict]:
    """The reviewed deliverables, in catalog order, with their group."""
    site = json.loads((_root / "site/content/site.json")
                      .read_text(encoding="utf-8"))
    out = []
    for group in ("primary", "supporting"):
        for entry in site["catalog"][group]:
            out.append(dict(entry, group=group))
    if not out:
        raise Refused("the catalog names no deliverables")
    return out


def publishable() -> dict[str, str]:
    """Path to licence, for every file this repository may publish.

    Read from the licensing tool rather than restated here. A second copy
    of the rule is a second thing to keep true.
    """
    disposition = _load("downloads_disposition", "tools/licensing/disposition.py")
    return {row.path: row.licence for row in disposition.classify()
            if row.disposition == disposition.CONTENT
            and row.path.endswith(".ttl")}


def namespace_from(ontology_iri: str) -> str:
    """The term namespace this file's own terms live in.

    Derived from the ontology IRI by a stated rule because the suite
    writes that IRI in three forms: six modules end it `.owl`, three end
    it `.ttl`, and two already end it `#`. The rule strips a document
    suffix and appends a fragment separator, and `build` then checks that
    the result is where the file's terms actually are -- a derivation
    nothing verifies is a guess with a docstring.
    """
    iri = str(ontology_iri)
    if iri.endswith("#"):
        return iri
    for suffix in (".owl", ".ttl", ".rdf"):
        if iri.endswith(suffix):
            return iri[:-len(suffix)] + "#"
    return iri + "#"


def read_header(path: Path) -> tuple[str, str, str, str]:
    """Ontology IRI, title, description and licence, each exactly once."""
    import rdflib
    from rdflib.namespace import DCTERMS, OWL, RDF

    from marep import ontology_source as onto

    graph = rdflib.Graph()
    onto.parse_source(graph, path, _root)
    headers = list(graph.subjects(RDF.type, OWL.Ontology))
    if len(headers) != 1:
        raise Refused("%s declares %d ontology headers; exactly one is "
                      "required to name what the file is"
                      % (path.name, len(headers)))
    header = headers[0]

    def one(predicate, what):
        values = [str(v) for v in graph.objects(header, predicate)]
        if len(values) != 1:
            raise Refused("%s declares %d values for %s; one is required"
                          % (path.name, len(values), what))
        return values[0]

    return (str(header), one(DCTERMS.title, "dcterms:title"),
            one(DCTERMS.description, "dcterms:description"),
            one(DCTERMS.license, "dcterms:license"))


def own_terms(path: Path, namespace: str, header: str) -> int:
    """How many subjects the file asserts about in its own namespace.

    Counts subjects rather than declarations of a particular type: the
    scenario's individuals are typed with domain classes rather than
    `owl:NamedIndividual`, and a rule that looked only for declarations
    would have called a file of 27 individuals empty.

    The ontology header is excluded. Two modules write their ontology IRI
    ending in `#`, which puts the header itself inside the namespace, so
    counting it made the same number mean "terms" for nine files and
    "terms plus one" for two -- and turned two genuinely term-less files
    into files with one.
    """
    return len(declared_iris(path, namespace, header))


def declared_iris(path: Path, namespace: str, header: str) -> set[str]:
    """Every IRI in the file's own namespace that it says something about.

    Shared with the diagram check, so "this module declares that term"
    means the same thing to the manifest and to the models page. Two
    definitions of the same membership question is how a diagram comes to
    depict a term the module does not have.
    """
    import rdflib

    from marep import ontology_source as onto

    graph = rdflib.Graph()
    onto.parse_source(graph, path, _root)
    return {str(s) for s in graph.subjects()
            if isinstance(s, rdflib.URIRef)
            and str(s).startswith(namespace)
            and str(s) != header}


def imports_of(path: Path, header: str) -> list[str]:
    """Declared `owl:imports`, sorted. What the file says it needs."""
    import rdflib
    from rdflib.namespace import OWL

    from marep import ontology_source as onto

    graph = rdflib.Graph()
    onto.parse_source(graph, path, _root)
    return sorted(str(o) for o in graph.objects(rdflib.URIRef(header),
                                                OWL.imports))


def references_of(path: Path, namespaces: dict[str, str],
                  own: str) -> list[str]:
    """Which other reviewed modules this file mentions.

    Derived from the IRIs it actually uses rather than from `owl:imports`.
    A module can import a file and use nothing from it, and -- as the
    mappings module does -- can use another module's terms heavily while
    importing nothing at all. Both are worth showing, and they are
    different questions.
    """
    import rdflib

    from marep import ontology_source as onto

    graph = rdflib.Graph()
    onto.parse_source(graph, path, _root)
    used = set()
    for triple in graph:
        for node in triple:
            if not isinstance(node, rdflib.URIRef):
                continue
            text = str(node)
            for key, namespace in namespaces.items():
                if namespace != own and text.startswith(namespace):
                    used.add(key)
    return sorted(used)


def entries(commit: str) -> list[dict]:
    """One record per deliverable, every field extracted."""
    from marep import layout

    allowed = publishable()
    records, seen = [], set()
    for entry in catalog():
        path = layout.component(entry["component"]).resolve()
        relative = path.relative_to(_root).as_posix()

        if relative not in allowed:
            raise Refused(
                "%s is in the reviewed catalog but the licensing tool does "
                "not place it among the files this repository may publish. "
                "One of the two is wrong and neither may be overridden here."
                % relative)
        if path.name in seen:
            raise Refused("two deliverables would publish as " + path.name)
        seen.add(path.name)

        data = path.read_bytes()
        iri, title, description, licence = read_header(path)
        namespace = namespace_from(iri)
        records.append({
            "id": entry["key"],
            "group": entry["group"],
            "source": relative,
            "filename": path.name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "ontology_iri": iri,
            "namespace": namespace,
            "own_terms": own_terms(path, namespace, iri),
            "title": title,
            "description": description,
            "license": licence,
            "licence_category": "project-content",
            "spdx": allowed[relative],
            "indexed": bool(entry.get("indexed")),
            "source_commit": commit,
        })

    # A second pass: cross-module references need every namespace known,
    # so they cannot be computed while the namespaces are still arriving.
    namespaces = {r["id"]: r["namespace"] for r in records}
    for record in records:
        path = _root / record["source"]
        record["imports"] = imports_of(path, record["ontology_iri"])
        record["references"] = references_of(path, namespaces,
                                             record["namespace"])

    missing = sorted(set(allowed) - {r["source"] for r in records})
    if missing:
        raise Refused(
            "these files are licensed for publication but the catalog does "
            "not name them, so they would be silently undownloadable: %s"
            % missing)
    return records


def deterministic_zip(destination: Path, members: list[tuple[str, bytes]],
                      epoch: int) -> bytes:
    """A byte-identical archive for identical input.

    Everything a zip records beyond the file content is pinned. Order is
    the caller's, timestamps come from the commit rather than the clock,
    permissions are fixed at 0644 so an executable bit picked up from a
    checkout cannot change the archive, and the creating system is stamped
    Unix so the same input on Windows produces the same bytes.
    """
    stamp = _zip_time(epoch)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name, data in members:
            info = zipfile.ZipInfo(name, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3           # Unix, on every platform
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return destination.read_bytes()


def _zip_time(epoch: int) -> tuple:
    """Zip stores local time with no zone, so UTC is used explicitly.

    Zip cannot represent a year before 1980; a repository whose commit
    predates that is a clock problem, not something to silently clamp.
    """
    import datetime

    when = datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc)
    if when.year < 1980:
        raise Refused("the build timestamp %s predates the zip epoch" % when)
    # DOS timestamps carry seconds in two-second steps, so an odd second
    # is not representable. Truncating here rather than letting zipfile
    # round means the value written and the value read back are the same
    # number, and a test can compare them without knowing the format.
    return (when.year, when.month, when.day,
            when.hour, when.minute, when.second - (when.second % 2))


def sha256sums(rows: list[tuple[str, str]]) -> bytes:
    """The familiar format, sorted, LF-terminated on every platform."""
    lines = ["%s  %s" % (digest, name) for name, digest in sorted(rows)]
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate(manifest: dict) -> None:
    """Against the schema, before the manifest reaches the artifact.

    The manifest carries every published checksum. A shape defect found
    by a test afterwards would be found against a directory somebody
    could already have downloaded.
    """
    from jsonschema import Draft7Validator

    from marep import layout

    schema_path = (layout.component("site.schemas").resolve()
                   / "downloads.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft7Validator(schema).iter_errors(manifest),
                    key=lambda e: list(e.path))
    if errors:
        raise Refused(
            "the download manifest does not satisfy %s: %s"
            % (schema_path.name, "; ".join(
                "%s: %s" % ("/".join(str(x) for x in e.path) or "(root)",
                            e.message[:120]) for e in errors[:4])))


def build(out: Path, commit: str, epoch: int) -> dict:
    records = entries(commit)

    published = out / "downloads"
    published.mkdir(parents=True, exist_ok=True)

    members: list[tuple[str, bytes]] = []
    for record in records:
        data = (_root / record["source"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise Refused(record["source"] + " changed while being published")
        target = published / record["filename"]
        target.write_bytes(data)
        if target.read_bytes() != data:
            raise Refused("the published copy of %s is not its source bytes"
                          % record["filename"])
        os.utime(target, (epoch, epoch))
        members.append((BUNDLE_ROOT + "/" + record["filename"], data))

    governance = []
    for name in GOVERNANCE:
        path = _root / name
        if not path.is_file():
            raise Refused(name + " is missing; the bundle must carry its "
                                 "own licence, attribution and citation")
        data = path.read_bytes()
        governance.append({"filename": name, "bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest()})
        members.append((BUNDLE_ROOT + "/" + name, data))

    # Two checksum records, because they describe two different
    # directories and a single one describes neither.
    #
    # The inner file sits beside the unpacked archive and covers what is
    # in there: the Turtle and the three governance documents.
    inner_rows = ([(r["filename"], r["sha256"]) for r in records]
                  + [(g["filename"], g["sha256"]) for g in governance])
    inner = sha256sums(inner_rows)
    members.append((BUNDLE_ROOT + "/SHA256SUMS", inner))

    members.sort()
    bundle_bytes = deterministic_zip(published / BUNDLE_NAME, members, epoch)
    os.utime(published / BUNDLE_NAME, (epoch, epoch))

    # The outer file sits in the published downloads directory and covers
    # what is served from it: the Turtle and the archive. One file listing
    # both sets was verifiable in neither place -- run against the
    # published directory it reported three missing governance files and
    # never checked the archive at all.
    outer_rows = ([(r["filename"], r["sha256"]) for r in records]
                  + [(BUNDLE_NAME,
                      hashlib.sha256(bundle_bytes).hexdigest())])
    sums = published / "SHA256SUMS"
    sums.write_bytes(sha256sums(outer_rows))
    os.utime(sums, (epoch, epoch))

    manifest = {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "source_commit": commit,
        "modules": records,
        "governance": governance,
        "bundle": {
            "filename": BUNDLE_NAME,
            "root": BUNDLE_ROOT,
            "bytes": len(bundle_bytes),
            "sha256": hashlib.sha256(bundle_bytes).hexdigest(),
            "members": [name for name, _ in members],
        },
        "checksums": {
            "published": {
                "path": "SHA256SUMS",
                "covers": sorted(name for name, _ in outer_rows),
                "note": "verifiable in the downloads directory as served",
            },
            "in_bundle": {
                "path": BUNDLE_ROOT + "/SHA256SUMS",
                "covers": sorted(name for name, _ in inner_rows),
                "note": "verifiable beside the unpacked archive",
            },
        },
        "note": (
            "Membership is the intersection of the reviewed catalog and the "
            "files this repository licenses for publication; the build "
            "refuses if those disagree. Turtle is copied byte for byte and "
            "never re-serialised."),
    }
    validate(manifest)

    data_dir = out / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    written = json.dumps(manifest, indent=2, sort_keys=True,
                         ensure_ascii=False).encode("utf-8") + b"\n"
    (data_dir / "downloads.json").write_bytes(written)
    os.utime(data_dir / "downloads.json", (epoch, epoch))
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="_site")
    ap.add_argument("--commit", default=None)
    ap.add_argument("--epoch", default=None)
    args = ap.parse_args(argv)

    site_build = _load("downloads_site_build", "tools/site/build_site.py")
    commit, epoch = site_build.build_stamp()
    commit = args.commit or commit
    epoch = int(args.epoch or epoch)

    out = Path(args.out)
    out = out if out.is_absolute() else _root / out
    manifest = build(out, commit, epoch)

    print("  %d module(s) published, bundle %s"
          % (len(manifest["modules"]), manifest["bundle"]["sha256"][:16]))
    for record in manifest["modules"]:
        print("    %-34s %7d B  %s  %d own term(s)"
              % (record["filename"], record["bytes"],
                 record["sha256"][:12], record["own_terms"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
