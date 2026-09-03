# SPDX-License-Identifier: Apache-2.0
"""Every public JSON document has a schema, and every schema a document.

Exact coverage in both directions. A published document with no contract
is a shape consumers infer from one example, and a schema with no
document is a contract nothing is held to -- and the second is the one
that rots quietly, because nothing fails when it drifts.

The pairing is derived from the artifact rather than listed here, so
adding a generated JSON file to the build without giving it a schema
fails, which is the moment to decide whether it should be public at all.
"""

from __future__ import annotations

import importlib.util
import json

import pytest
from jsonschema import Draft7Validator

from marep import layout

REPO = layout.repository_root()
SCHEMA_SOURCE = layout.component("site.schemas").resolve()


@pytest.fixture(scope="module")
def artifact(tmp_path_factory):
    spec = importlib.util.spec_from_file_location(
        "schema_build_site", REPO / "tools/site/build_site.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    out = tmp_path_factory.mktemp("schemas") / "_site"
    assert build.main(["-o", str(out)]) == 0
    return out


def published_documents(artifact):
    """The generated JSON a consumer can fetch, excluding the schemas."""
    return sorted(p.relative_to(artifact).as_posix()
                  for p in (artifact / "data").glob("*.json"))


def published_schemas(artifact):
    return sorted(p.relative_to(artifact).as_posix()
                  for p in (artifact / "schemas").glob("*.json"))


def test_every_public_document_has_a_schema(artifact):
    documents = published_documents(artifact)
    assert documents, "no public JSON found, so this test checks nothing"
    missing = [d for d in documents
               if not (SCHEMA_SOURCE / (d.split("/")[-1].replace(
                   ".json", ".schema.json"))).is_file()]
    assert not missing, (
        "%s published with no schema. Give it one, or stop publishing it."
        % missing)


def test_every_schema_has_a_document(artifact):
    """The direction that rots quietly."""
    documents = {d.split("/")[-1] for d in published_documents(artifact)}
    orphans = []
    for schema in published_schemas(artifact):
        name = schema.split("/")[-1].replace(".schema.json", ".json")
        if name not in documents:
            orphans.append(schema)
    assert not orphans, (
        "%s describes nothing the build publishes" % orphans)


def test_the_pairing_is_exact(artifact):
    documents = {d.split("/")[-1].replace(".json", "")
                 for d in published_documents(artifact)}
    schemas = {s.split("/")[-1].replace(".schema.json", "")
               for s in published_schemas(artifact)}
    assert documents == schemas, sorted(documents ^ schemas)
    assert len(documents) == 3, sorted(documents)


def test_every_document_validates_against_its_schema(artifact):
    for relative in published_documents(artifact):
        name = relative.split("/")[-1]
        schema = json.loads(
            (SCHEMA_SOURCE / name.replace(".json", ".schema.json"))
            .read_text(encoding="utf-8"))
        document = json.loads((artifact / relative).read_text(encoding="utf-8"))
        errors = sorted(Draft7Validator(schema).iter_errors(document),
                        key=lambda e: list(e.path))
        assert not errors, "%s: %s" % (name, [
            ("/".join(str(x) for x in e.path) or "(root)", e.message[:100])
            for e in errors[:3]])


def test_every_schema_is_valid_draft_07(artifact):
    for relative in published_schemas(artifact):
        schema = json.loads((artifact / relative).read_text(encoding="utf-8"))
        Draft7Validator.check_schema(schema)
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"


def test_every_schema_is_published_at_the_id_it_claims(artifact):
    """A schema naming a URL the build does not serve is a dangling
    reference in the one document whose job is to say what the data must
    look like."""
    site = json.loads(
        (layout.component("site.content").resolve() / "site.json")
        .read_text(encoding="utf-8"))
    base = site["deployment"]["public_url"]
    for relative in published_schemas(artifact):
        schema = json.loads((artifact / relative).read_text(encoding="utf-8"))
        assert schema["$id"] == base + relative, (schema["$id"], base + relative)


def test_every_schema_closes_its_objects(artifact):
    """additionalProperties false, or a field can appear in a published
    document with nothing to say what it means."""
    open_objects = []

    def walk(node, path):
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                if node.get("additionalProperties") is not False:
                    open_objects.append(path)
            for key, value in node.items():
                walk(value, path + "/" + str(key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, "%s/%d" % (path, index))

    for relative in published_schemas(artifact):
        schema = json.loads((artifact / relative).read_text(encoding="utf-8"))
        walk(schema, relative)
    assert not open_objects, open_objects


def test_the_builders_validate_before_writing(artifact):
    """Validation in a test alone checks the shape where it is convenient
    rather than where it is produced: a broken generator would ship and
    be reported afterwards against an artifact already written."""
    index_source = (REPO / "tools/site/build_class_index.py").read_text(
        encoding="utf-8")
    downloads_source = (REPO / "tools/site/build_downloads.py").read_text(
        encoding="utf-8")
    assert "class-index.schema.json" in index_source
    assert 'validate(coverage, "coverage.schema.json")' in index_source
    assert "downloads.schema.json" in downloads_source
    assert "def validate(" in downloads_source
