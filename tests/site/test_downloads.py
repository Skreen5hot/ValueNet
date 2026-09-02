# SPDX-License-Identifier: Apache-2.0
"""What is published, that it is the same bytes, and that it is stable.

Three questions, and the third is the one that makes the first two worth
anything. A checksum published beside a file only means something if
rebuilding produces the same file, so most of this module is about the
archive's metadata rather than its contents.

The membership question is answered twice on purpose. `test_catalog`
already asserts that the reviewed catalog and the licensed set are equal;
here the builder is required to refuse when they are not, because a
control that lives only in a test is a control the build does not have.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile

import pytest

from marep import layout

REPO = layout.repository_root()
NEWLINE = chr(10)


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = _load("build_downloads", "tools/site/build_downloads.py")
SITE = _load("downloads_site", "tools/site/build_site.py")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("dl")
    commit, epoch = SITE.build_stamp()
    manifest = B.build(out, commit, int(epoch))
    return out, manifest


# ================================================================== what


def test_membership_is_the_catalog_and_the_licence_agreeing(built):
    """Never a hand-kept list. Both sides are derived, and the build
    refuses if they disagree rather than preferring one."""
    _out, manifest = built
    published = {r["source"] for r in manifest["modules"]}
    licensed = set(B.publishable())
    assert published == licensed, sorted(published ^ licensed)
    assert len(published) == 11


def test_a_catalogued_file_that_is_not_licensed_is_refused(monkeypatch,
                                                           tmp_path):
    """The failure that matters: something reaches the catalog that this
    repository has no right to publish. Dropping it silently would be the
    worst outcome, and publishing it would be worse than that."""
    real = B.publishable()
    victim = sorted(real)[0]
    monkeypatch.setattr(B, "publishable",
                        lambda: {k: v for k, v in real.items()
                                 if k != victim})
    with pytest.raises(SystemExit) as exc:
        B.entries("0" * 40)
    assert victim in str(exc.value)


def test_a_licensed_file_the_catalog_omits_is_refused(monkeypatch):
    """The other direction. A file nobody lists is a file nobody can
    download, and it would never be noticed from the page."""
    real = B.catalog()
    monkeypatch.setattr(B, "catalog", lambda: real[:-1])
    with pytest.raises(SystemExit) as exc:
        B.entries("0" * 40)
    assert "the catalog does not name them" in str(exc.value)


def test_the_bundle_excludes_everything_it_should(built):
    """Vendored dependencies, tests, tooling and run artifacts."""
    _out, manifest = built
    members = manifest["bundle"]["members"]
    for member in members:
        assert "/vendor/" not in member, member
        for forbidden in ("tests/", "tools/", "marep/", "_site/", "config/"):
            assert forbidden not in member, member
    assert not [m for m in members if m.endswith(".py")]


# ============================================================== the bytes


def test_every_published_file_is_its_source_bytes(built):
    """Copied, never re-serialised. A round trip through a parser would
    produce a file that says the same thing and hashes differently."""
    out, manifest = built
    for record in manifest["modules"]:
        source = (REPO / record["source"]).read_bytes()
        published = (out / "downloads" / record["filename"]).read_bytes()
        assert published == source, record["filename"]
        assert hashlib.sha256(source).hexdigest() == record["sha256"]
        assert len(source) == record["bytes"]


def test_the_archived_copy_is_also_the_source_bytes(built):
    out, manifest = built
    root = manifest["bundle"]["root"]
    with zipfile.ZipFile(out / "downloads" / manifest["bundle"]["filename"]) as z:
        for record in manifest["modules"]:
            archived = z.read(root + "/" + record["filename"])
            assert archived == (REPO / record["source"]).read_bytes(), \
                record["filename"]


def _parse_sums(text):
    assert text.endswith(NEWLINE), "a checksum file must end with a newline"
    rows = {}
    for line in text.strip().split(NEWLINE):
        digest, name = line.split("  ", 1)
        assert name not in rows, "listed twice: " + name
        rows[name] = digest
    return rows


def test_the_published_checksums_verify_where_they_are_published(built):
    """Run in the downloads directory as served, with no fallback.

    The first version of this test fell back to the repository when a
    listed file was not in the artifact. That is how a SHA256SUMS naming
    three governance files which are not published, and omitting the
    archive which is, passed as correct: it proved the source digests and
    said nothing about whether anyone could use the file.
    """
    out, manifest = built
    served = out / "downloads"
    rows = _parse_sums((served / "SHA256SUMS").read_text(encoding="utf-8"))

    expected = ({r["filename"] for r in manifest["modules"]}
                | {manifest["bundle"]["filename"]})
    assert set(rows) == expected, sorted(set(rows) ^ expected)

    for name, digest in sorted(rows.items()):
        target = served / name
        assert target.is_file(), (
            "%s is listed but is not in the published directory, so "
            "verification fails for whoever runs it" % name)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name


def test_the_bundled_checksums_verify_beside_the_unpacked_archive(built):
    """The other record, covering the other directory."""
    out, manifest = built
    root = manifest["bundle"]["root"]
    with zipfile.ZipFile(out / "downloads"
                         / manifest["bundle"]["filename"]) as archive:
        rows = _parse_sums(archive.read(root + "/SHA256SUMS").decode("utf-8"))
        present = {n.split("/", 1)[1] for n in archive.namelist()}

        expected = ({r["filename"] for r in manifest["modules"]}
                    | {g["filename"] for g in manifest["governance"]})
        assert set(rows) == expected, sorted(set(rows) ^ expected)

        for name, digest in sorted(rows.items()):
            assert name in present, (
                "%s is listed in the archive checksums but is not in the "
                "archive" % name)
            data = archive.read(root + "/" + name)
            assert hashlib.sha256(data).hexdigest() == digest, name


def test_neither_checksum_record_lists_what_the_other_covers(built):
    """They describe different directories on purpose. A single record
    listing both sets is verifiable in neither."""
    _out, manifest = built
    published = set(manifest["checksums"]["published"]["covers"])
    bundled = set(manifest["checksums"]["in_bundle"]["covers"])
    assert manifest["bundle"]["filename"] in published
    assert manifest["bundle"]["filename"] not in bundled, (
        "the archive cannot contain its own checksum")
    for governance in manifest["governance"]:
        assert governance["filename"] in bundled
        assert governance["filename"] not in published, (
            "%s is not served from the downloads directory"
            % governance["filename"])


def test_the_bundle_checksum_is_the_bundle(built):
    out, manifest = built
    data = (out / "downloads" / manifest["bundle"]["filename"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == manifest["bundle"]["sha256"]
    assert len(data) == manifest["bundle"]["bytes"]


# ========================================================= determinism


def test_two_builds_produce_an_identical_archive(tmp_path):
    """The property a published checksum rests on."""
    commit, epoch = SITE.build_stamp()
    digests = []
    for name in ("first", "second"):
        out = tmp_path / name
        manifest = B.build(out, commit, int(epoch))
        digests.append(hashlib.sha256(
            (out / "downloads" / manifest["bundle"]["filename"]).read_bytes()
        ).hexdigest())
    assert digests[0] == digests[1]


def test_the_archive_records_nothing_that_varies_by_machine(built):
    """Order, time, permissions and creating system are all pinned.

    Any one of them left to the filesystem would make the archive differ
    between a Windows checkout and a Linux one while the ontology inside
    stayed identical -- and the checksum would then be describing the
    build machine.
    """
    out, manifest = built
    with zipfile.ZipFile(out / "downloads" / manifest["bundle"]["filename"]) as z:
        infos = z.infolist()
    assert len({i.date_time for i in infos}) == 1, "more than one timestamp"
    assert {i.external_attr >> 16 for i in infos} == {0o644}
    assert {i.create_system for i in infos} == {3}, "not stamped Unix"
    names = [i.filename for i in infos]
    assert names == sorted(names), "members are not in sorted order"


def test_no_archive_member_carries_a_path_from_this_machine(built):
    """A member name holding a checkout path would make the archive differ
    between two clones of the same commit."""
    out, manifest = built
    root = manifest["bundle"]["root"]
    for member in manifest["bundle"]["members"]:
        assert member.startswith(root + "/"), member
        assert ":" not in member and not member.startswith("/"), member
        assert ".." not in member, member


def test_the_timestamp_comes_from_the_commit_not_the_clock(built):
    """Two builds a minute apart must agree, which they cannot if the
    archive is stamped with now()."""
    out, manifest = built
    commit, epoch = SITE.build_stamp()
    expected = B._zip_time(int(epoch))
    with zipfile.ZipFile(out / "downloads" / manifest["bundle"]["filename"]) as z:
        assert z.infolist()[0].date_time == expected


# ============================================================ extraction


def test_every_manifest_field_is_extracted_not_curated(built):
    """Titles, descriptions and namespaces come from the files."""
    _out, manifest = built
    for record in manifest["modules"]:
        path = REPO / record["source"]
        iri, title, description, licence = B.read_header(path)
        assert record["ontology_iri"] == iri
        assert record["title"] == title
        assert record["description"] == description
        assert record["license"] == licence
        assert record["namespace"] == B.namespace_from(iri)


def test_the_namespace_rule_lands_where_the_terms_are(built):
    """The ontology IRI is written three ways in this suite -- six modules
    end it `.owl`, three `.ttl`, two `#` -- so the namespace is derived by
    a rule. This checks the rule against reality: where a module has terms
    of its own, they are in the namespace the rule produced."""
    _out, manifest = built
    for record in manifest["modules"]:
        if not record["own_terms"]:
            continue
        found = B.declared_iris(REPO / record["source"], record["namespace"],
                                record["ontology_iri"])
        assert len(found) == record["own_terms"]
        assert all(i.startswith(record["namespace"]) for i in found)


def test_the_two_modules_with_no_terms_of_their_own_are_the_expected_two(built):
    """Zero is a measured property here, so it is pinned. A third module
    reading zero would mean an extraction failure, not a design choice."""
    _out, manifest = built
    empty = sorted(r["id"] for r in manifest["modules"] if not r["own_terms"])
    assert empty == ["valuenet-mappings", "vcvf-triggers-semantics"], empty


def test_the_class_index_and_the_manifest_agree_on_namespaces(
        built, class_index):
    """Two generators derive the namespace differently -- the index from
    class IRIs, the manifest from the ontology IRI. Where both have an
    opinion they must match, or one of the two pages is wrong.

    Both are generated for the test. Comparing against the build artifact
    meant this skipped whenever nobody had built, which is precisely when
    a disagreement would go unnoticed.
    """
    _out, manifest = built
    by_key = {m["key"]: m["namespace"] for m in class_index["modules"]}
    for record in manifest["modules"]:
        if record["id"] in by_key:
            assert record["namespace"] == by_key[record["id"]], record["id"]


# ===================================================== generated markup


F = _load("build_fragments", "tools/site/build_fragments.py")


def test_ontology_text_is_escaped_before_it_becomes_a_page():
    """The explorer's rule, applied to the half of the site that is
    generated rather than fetched.

    A definition is authored text in a file anyone can edit. The explorer
    puts it in the page through textContent; these pages build markup as
    a string, so the same guarantee has to come from escaping, and this
    is the test that says it does.
    """
    hostile = {
        "modules": [{
            "id": "syn", "group": "primary",
            "source": "ontology/x.ttl", "filename": "x.ttl",
            "bytes": 1, "sha256": "0" * 64,
            "ontology_iri": "https://ex.invalid/x.owl",
            "namespace": "https://ex.invalid/x#", "own_terms": 1,
            "title": '<script>alert(1)</script>',
            "description": 'ends with " and <img onerror=x>',
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "licence_category": "project-content", "spdx": "CC-BY-4.0",
            "indexed": False, "source_commit": "0" * 40,
            "imports": ["<b>not a tag</b>"], "references": [],
        }],
        "governance": [],
        "bundle": {"filename": "b.zip", "root": "b", "bytes": 1,
                   "sha256": "0" * 64, "members": []},
    }
    index = {"modules": [{"key": "syn", "classes": 0}]}
    rendered = F.module_cards(hostile, index, {"syn": "<em>reason</em>"})

    for forbidden in ("<script>", "<img onerror", "<b>not a tag</b>",
                      "<em>reason</em>"):
        assert forbidden not in rendered, forbidden
    assert "&lt;script&gt;" in rendered, "the title was dropped, not escaped"
    assert "&lt;em&gt;reason&lt;/em&gt;" in rendered


def test_the_marker_replacement_refuses_a_nested_element():
    """The generated section is spliced between a marker and its first
    closing tag. A nested one would leave the page half-generated and
    still looking plausible."""
    with pytest.raises(SystemExit) as exc:
        F.substitute('<div data-generated="modules"><div>x</div></div>',
                     {"modules": "<p>ok</p>"})
    assert "nested" in str(exc.value)


def test_a_page_without_its_marker_is_left_alone():
    """Substitution must not be silently partial across seven pages."""
    text = "<p>no marker here</p>"
    assert F.substitute(text, {"modules": "<p>x</p>"}) == text


# ================================================ the M-002 record


RECORD = REPO / "docs/bfo/ONTOLOGY_METADATA_DECISIONS.md"


def _m002_section():
    whole = RECORD.read_text(encoding="utf-8")
    return whole[whole.index("## M-002"):]


def test_the_iri_form_record_matches_the_manifest(built):
    """M-002 tabulates every ontology IRI and the namespace derived from
    it. Both are extracted, so the record either stays true or fails --
    the alternative is a policy document describing a corpus that moved.
    """
    _out, manifest = built
    section = _m002_section()

    listed = {}
    for line in section.splitlines():
        if line.startswith("| `"):
            cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
            listed[cells[0]] = (cells[1], cells[3])

    actual = {r["id"]: (r["ontology_iri"], r["namespace"])
              for r in manifest["modules"]}
    assert listed == actual, (
        "only in the record: %s; only in the manifest: %s"
        % (sorted(set(listed) - set(actual)), sorted(set(actual) - set(listed))))


def test_the_iri_forms_are_still_the_three_the_record_names(built):
    """The finding is that three forms are in use. If that became one
    form, M-002 is answered and should be closed rather than left open
    describing a problem that no longer exists."""
    _out, manifest = built
    forms = {}
    for record in manifest["modules"]:
        iri = record["ontology_iri"]
        key = (".owl" if iri.endswith(".owl") else
               ".ttl" if iri.endswith(".ttl") else
               "#" if iri.endswith("#") else "other")
        forms[key] = forms.get(key, 0) + 1
    assert forms == {".owl": 6, ".ttl": 3, "#": 2}, forms
    section = _m002_section()
    assert "Six end it `.owl`, three end it `.ttl`, and two already end"         in " ".join(section.split()), "the record's counts have drifted"


def test_the_iri_record_authorises_no_edit():
    """Changing an ontology IRI is a breaking change to identifiers. It
    needs its own decision, its own commit and its own evidence run."""
    assert "**Status:** Open" in _m002_section()
