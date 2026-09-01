# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")
jsonschema = pytest.importorskip("jsonschema")

from jsonschema.validators import Draft202012Validator
from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS


# The repository root comes from the layout contract, not from counting
# parents. This file moves one level deeper in the tests wave, at which
# point parents[1] resolves to tests/ and every path below it is wrong
# without raising anything.
from marep.layout import (bfo_artifact, component,
                          repository_root)  # noqa: E402

ROOT = repository_root()
EXTRACT = bfo_artifact("cco-valuenet-extract.ttl")
MANIFEST = bfo_artifact("cco-valuenet-extract.manifest.json")
SCHEMA = bfo_artifact("extract-manifest.schema.json")

CCO_AGENT = URIRef("https://www.commoncoreontologies.org/ont00001017")
CCO_AGENT_CAPABILITY = URIRef("https://www.commoncoreontologies.org/ont00001379")
CCO_INFORMATION_BEARING_ENTITY = URIRef(
    "https://www.commoncoreontologies.org/ont00000253"
)
CCO_INFORMATION_CONTENT_ENTITY = URIRef(
    "https://www.commoncoreontologies.org/ont00000958"
)
CCO_ACT_OF_OBSERVATION = URIRef("https://www.commoncoreontologies.org/ont00000037")
CCO_ACT_OF_APPRAISAL = URIRef("https://www.commoncoreontologies.org/ont00000636")
CCO_DESCRIPTIVE_ICE = URIRef("https://www.commoncoreontologies.org/ont00000853")
CCO_PRESCRIPTIVE_ICE = URIRef("https://www.commoncoreontologies.org/ont00000965")
CCO_HAS_INPUT = URIRef("https://www.commoncoreontologies.org/ont00001921")
CCO_HAS_OUTPUT = URIRef("https://www.commoncoreontologies.org/ont00001986")
CCO_INPUT_OF = URIRef("https://www.commoncoreontologies.org/ont00001841")
CCO_OUTPUT_OF = URIRef("https://www.commoncoreontologies.org/ont00001816")
BFO_MATERIAL_ENTITY = URIRef("http://purl.obolibrary.org/obo/BFO_0000040")
BFO_REALIZABLE_ENTITY = URIRef("http://purl.obolibrary.org/obo/BFO_0000017")
BFO_PROCESS = URIRef("http://purl.obolibrary.org/obo/BFO_0000015")
BFO_HAS_PARTICIPANT = URIRef("http://purl.obolibrary.org/obo/BFO_0000057")
RO_HAS_INPUT = URIRef("http://purl.obolibrary.org/obo/RO_0002233")
RO_HAS_OUTPUT = URIRef("http://purl.obolibrary.org/obo/RO_0002234")


@pytest.fixture(scope="module")
def extract_graph():
    graph = Graph()
    graph.parse(EXTRACT, format="turtle")
    return graph


def test_extract_manifest_validates_and_matches_artifact():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(
        manifest
    )
    assert hashlib.sha256(EXTRACT.read_bytes()).hexdigest() == manifest["extract_sha256"]


def test_extract_contains_canonical_cco_dependencies(extract_graph):
    assert (CCO_AGENT, RDF.type, OWL.Class) in extract_graph
    assert (CCO_INFORMATION_BEARING_ENTITY, RDF.type, OWL.Class) in extract_graph
    assert (CCO_INFORMATION_CONTENT_ENTITY, RDF.type, OWL.Class) in extract_graph
    assert (CCO_ACT_OF_OBSERVATION, RDF.type, OWL.Class) in extract_graph
    assert (CCO_ACT_OF_APPRAISAL, RDF.type, OWL.Class) in extract_graph
    assert (CCO_DESCRIPTIVE_ICE, RDF.type, OWL.Class) in extract_graph
    assert (CCO_PRESCRIPTIVE_ICE, RDF.type, OWL.Class) in extract_graph
    assert (CCO_DESCRIPTIVE_ICE, OWL.disjointWith, CCO_PRESCRIPTIVE_ICE) in extract_graph
    assert (CCO_DESCRIPTIVE_ICE, RDFS.subClassOf, CCO_INFORMATION_CONTENT_ENTITY) in extract_graph
    assert (CCO_PRESCRIPTIVE_ICE, RDFS.subClassOf, CCO_INFORMATION_CONTENT_ENTITY) in extract_graph
    assert (CCO_AGENT, RDFS.subClassOf, BFO_MATERIAL_ENTITY) in extract_graph
    assert (CCO_AGENT_CAPABILITY, RDFS.subClassOf, BFO_REALIZABLE_ENTITY) in extract_graph
    assert (CCO_HAS_INPUT, RDFS.subPropertyOf, BFO_HAS_PARTICIPANT) in extract_graph
    assert (CCO_HAS_INPUT, RDFS.domain, BFO_PROCESS) in extract_graph
    assert (CCO_HAS_OUTPUT, RDFS.subPropertyOf, BFO_HAS_PARTICIPANT) in extract_graph
    assert (CCO_HAS_OUTPUT, RDFS.domain, BFO_PROCESS) in extract_graph
    assert (CCO_INPUT_OF, OWL.inverseOf, CCO_HAS_INPUT) in extract_graph
    assert (CCO_OUTPUT_OF, OWL.inverseOf, CCO_HAS_OUTPUT) in extract_graph
    for term in (CCO_AGENT, CCO_AGENT_CAPABILITY, CCO_HAS_INPUT, CCO_HAS_OUTPUT):
        assert not list(extract_graph.objects(term, OWL.deprecated))


def test_agent_equivalence_and_relation_ranges_are_not_truncated(extract_graph):
    agent_equivalences = list(extract_graph.objects(CCO_AGENT, OWL.equivalentClass))
    assert agent_equivalences and all(isinstance(node, BNode) for node in agent_equivalences)
    assert list(extract_graph.objects(CCO_HAS_INPUT, RDFS.range))
    assert list(extract_graph.objects(CCO_HAS_OUTPUT, RDFS.range))
    for node in agent_equivalences + list(extract_graph.objects(CCO_HAS_INPUT, RDFS.range)):
        assert list(extract_graph.triples((node, None, None)))


def test_superseded_ro_terms_are_absent(extract_graph):
    assert not list(extract_graph.triples((RO_HAS_INPUT, None, None)))
    assert not list(extract_graph.triples((RO_HAS_OUTPUT, None, None)))


# ======================================================================
# the canonical anchor may not certify itself
#
# `extract_canonical_sha256` is the guard that decides whether provenance
# may be rewritten onto this extract. On the single run that introduces
# the field there is no previous value to compare against, so a generator
# that initialised it by hashing the file in front of it would let a
# modified extract vouch for itself -- and would do so silently, once,
# with no artifact left behind saying that is what happened.
#
# The refusals below were confirmed by hand when the anchor was written.
# A refusal nobody re-runs is a claim about the past, so they are encoded
# here: each one deletes the field in a throwaway tree and requires the
# generator to refuse rather than initialise.
# ======================================================================


#: Resolved once, while the real root is still in force. The module is
#: loaded from the repository rather than from the sandbox copy so that its
#: own `_root` -- and therefore the `git show` that reads the freeze --
#: still points at a checkout that has the tag.
GENERATOR = component("tool.generate-cco-extract").resolve()


def _generator():
    import importlib.util

    spec = importlib.util.spec_from_file_location("gen_cco_probe", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """A throwaway tree the layout resolver treats as the repository.

    The generator refuses by raising before it writes, so a passing test
    proves nothing unless the write would have been real. This gives it a
    tree it may genuinely modify. The generator is copied in as well:
    `script_path()` reads it through the contract, and a contract that
    resolves to nothing raises before the guard under test is reached."""
    import shutil

    from marep import layout

    root = (tmp_path / "repo").resolve()
    (root / "config").mkdir(parents=True)
    shutil.copy2(ROOT / "config/repository-layout.yaml", root / "config")
    for src in (EXTRACT, MANIFEST, GENERATOR):
        dest = root / src.resolve().relative_to(ROOT.resolve())
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    layout.clear_cache()
    monkeypatch.setattr(layout, "repository_root", lambda start=None: root)
    try:
        yield root
    finally:
        layout._load.cache_clear()


def _sandbox_manifest(root):
    return root / MANIFEST.resolve().relative_to(ROOT.resolve())


def _sandbox_extract(root):
    return root / EXTRACT.resolve().relative_to(ROOT.resolve())


def _drop_the_anchor(root):
    """The state the initialisation branch exists to handle."""
    path = _sandbox_manifest(root)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("extract_canonical_sha256", None)
    path.write_text(json.dumps(data, indent=2) + chr(10),
                    encoding="utf-8", newline=chr(10))
    return path


def test_the_canonical_anchor_comes_from_the_freeze():
    """Not from the extract in front of us.

    The anchor is an independent value: written by a different tool, at a
    different time, under the previous document-base rule."""
    import json as _json
    import subprocess as _sp
    import unittest.mock

    gen = _generator()

    # The anchor is read out of git. That read used `text=True`, which
    # decodes with the locale codec -- cp1252 on Windows -- so a frozen
    # baseline holding a non-ASCII definition would decode to different
    # characters and the anchor would silently fail to match. Fed bytes
    # here so the property holds on any platform, not only one whose
    # locale happens to be UTF-8.
    payload_obj = {"artifacts": {"cco_extract": {
        "canonical_is_invariant": True,
        "canonical_sha256": "a" * 64,
        "note": "curly quote \u2019 and em dash \u2014"}}}
    text = _json.dumps(payload_obj, ensure_ascii=False)
    payload = text.encode("utf-8")
    assert len(payload) > len(text), (
        "the probe payload contains no multi-byte sequence, so it cannot "
        "distinguish the two decodings")

    seen = {}

    def _bytes_only(cmd, **kw):
        seen.update(kw)
        return _sp.CompletedProcess(cmd, 0, stdout=payload, stderr=b"")

    with unittest.mock.patch.object(_sp, "run", _bytes_only):
        probed = gen.frozen_canonical_anchor()
    assert seen.get("text") is not True, (
        "frozen_canonical_anchor asked for locale-decoded text")
    assert probed == "a" * 64, (
        "the anchor did not survive a UTF-8 payload: %r" % probed)

    anchor = gen.frozen_canonical_anchor()
    assert anchor is not None, (
        "no canonical digest for this artifact at " + gen.FROZEN_TAG)
    assert len(anchor) == 64
    assert set(anchor) <= set("0123456789abcdef")


def test_the_anchor_agrees_with_the_manifest_on_disk():
    """Two independently produced values agreeing is a fact worth
    checking rather than assuming: it holds only because this extract
    contains no relative IRI, so the document base cannot move it."""
    gen = _generator()
    recorded = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert recorded["extract_canonical_sha256"] == gen.frozen_canonical_anchor()


def test_initialisation_is_refused_when_the_freeze_has_no_record(
        sandbox, monkeypatch):
    """With nothing to anchor to, the only remaining source for the value
    is the extract itself, which is the case that must not proceed."""
    gen = _generator()
    monkeypatch.setattr(gen, "frozen_canonical_anchor", lambda: None)
    path = _drop_the_anchor(sandbox)

    with pytest.raises(SystemExit) as exc:
        gen.refresh_provenance()
    assert "its own evidence" in str(exc.value)
    assert "extract_canonical_sha256" not in json.loads(
        path.read_text(encoding="utf-8")), (
        "the field was written despite the refusal")


def test_initialisation_is_refused_for_an_extract_the_freeze_disowns(sandbox):
    """A changed extract with the field deleted is exactly the shape of
    the attack: no previous value to contradict it, and a fresh hash that
    would describe it perfectly."""
    gen = _generator()
    path = _drop_the_anchor(sandbox)
    extract = _sandbox_extract(sandbox)
    extract.write_text(
        extract.read_text(encoding="utf-8")
        + chr(10)
        + "<https://valuenet.invalid/probe/s> "
          "<https://valuenet.invalid/probe/p> "
          '"a triple the freeze never saw" .' + chr(10),
        encoding="utf-8", newline=chr(10))

    with pytest.raises(SystemExit) as exc:
        gen.refresh_provenance()
    assert "different extract" in str(exc.value)
    assert "extract_canonical_sha256" not in json.loads(
        path.read_text(encoding="utf-8"))


def test_refresh_is_refused_when_the_recorded_anchor_disagrees(sandbox):
    """The same guard on the ordinary path, where a value does exist.

    Rewriting provenance onto an extract the manifest no longer describes
    would produce a file that is internally consistent and wrong."""
    gen = _generator()
    extract = _sandbox_extract(sandbox)
    extract.write_text(
        extract.read_text(encoding="utf-8")
        + chr(10)
        + "<https://valuenet.invalid/probe/s> "
          "<https://valuenet.invalid/probe/p> "
          '"a triple the manifest never described" .' + chr(10),
        encoding="utf-8", newline=chr(10))

    before = _sandbox_manifest(sandbox).read_bytes()
    with pytest.raises(SystemExit) as exc:
        gen.refresh_provenance()
    assert "regenerate it instead" in str(exc.value)
    assert _sandbox_manifest(sandbox).read_bytes() == before


def test_initialisation_writes_the_frozen_value_when_they_agree(sandbox):
    """The permitted case, asserted on the value rather than on success.

    A generator that hashed the extract would pass a test that only
    checked the field came back populated. What makes this the safe path
    is that the value written is the frozen one."""
    gen = _generator()
    path = _drop_the_anchor(sandbox)

    gen.refresh_provenance()

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["extract_canonical_sha256"] == gen.frozen_canonical_anchor()
