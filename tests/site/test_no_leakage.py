# SPDX-License-Identifier: Apache-2.0
"""Nothing reaches the artifact that was not meant to be published.

Four categories, each of which has a plausible route in. Vendored BFO and
CCO are Turtle sitting beside the authored Turtle, and the download build
walks Turtle. Tests and tooling are Python next to the site's Python.
MAREP run state is generated output next to the site's generated output.
Source archives are large files nobody looks at twice.

Deriving the allowed set rather than listing forbidden names is the point:
a deny-list only catches what somebody thought of, and the thing that
leaks is the thing nobody thought of. Every file in the artifact has to be
explicable, and the test names the rule that explains it.
"""

from __future__ import annotations

import importlib.util
import json
import zipfile

import pytest

from marep import layout

REPO = layout.repository_root()


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def artifact(tmp_path_factory):
    """A build of the current tree, not whatever is lying in _site."""
    build = _load("leakage_build_site", "tools/site/build_site.py")
    out = tmp_path_factory.mktemp("leak") / "_site"
    assert build.main(["-o", str(out)]) == 0
    return out


def relative_paths(root):
    return sorted(p.relative_to(root).as_posix()
                  for p in root.rglob("*") if p.is_file())


def test_every_published_file_is_explicable(artifact):
    """The allow-list is a set of rules, not of filenames."""
    manifest = json.loads((artifact / "data/downloads.json")
                          .read_text(encoding="utf-8"))
    published_turtle = {"downloads/" + r["filename"]
                        for r in manifest["modules"]}

    site_source = layout.component("site.source").resolve()
    from_source = {p.relative_to(site_source).as_posix()
                   for p in site_source.rglob("*") if p.is_file()}

    generated = {"data/class-index.json", "data/coverage.json",
                 "data/downloads.json", "downloads/SHA256SUMS",
                 "downloads/" + manifest["bundle"]["filename"]}

    schema_source = layout.component("site.schemas").resolve()
    schemas = {"schemas/" + p.name for p in schema_source.glob("*.json")}

    allowed = from_source | published_turtle | generated | schemas
    unexplained = sorted(set(relative_paths(artifact)) - allowed)
    assert not unexplained, (
        "%d file(s) in the artifact match no publication rule: %s"
        % (len(unexplained), unexplained))


def test_no_vendored_dependency_is_published(artifact):
    """BFO and the CCO extract are upstream material under their own
    licenses and are excluded from the bundle and the site."""
    vendored = set()
    for component in ("bfo.vendor-bfo", "bfo.vendor-cco"):
        target = layout.component(component).resolve()
        members = (sorted(target.rglob("*")) if target.is_dir() else [target])
        vendored |= {p.name for p in members if p.is_file()}
    assert vendored, "no vendored files found, so this test checks nothing"

    published = {p.rsplit("/", 1)[-1] for p in relative_paths(artifact)}
    assert not (vendored & published), sorted(vendored & published)

    with zipfile.ZipFile(artifact / "downloads"
                         / "bfo-aligned-valuenet.zip") as archive:
        inside = {n.rsplit("/", 1)[-1] for n in archive.namelist()}
    assert not (vendored & inside), sorted(vendored & inside)


def test_no_test_or_tooling_file_is_published(artifact):
    published = relative_paths(artifact)
    for path in published:
        assert not path.endswith(".py"), path
        for fragment in ("tests/", "tools/", "marep/", "conftest"):
            assert fragment not in path, path


def test_no_run_artifact_or_source_archive_is_published(artifact):
    """MAREP run state and the archived source corpus."""
    published = relative_paths(artifact)
    for path in published:
        lowered = path.lower()
        for fragment in ("_run/", "run1_", "retro", "sprint"):
            assert fragment not in lowered, path
        for suffix in (".zip", ".tar", ".gz", ".7z", ".rar", ".jsonl"):
            if lowered.endswith(suffix):
                assert path == "downloads/bfo-aligned-valuenet.zip", path


def test_the_archived_corpus_directories_are_absent(artifact):
    """vale2024 and the original-ValueNet trees are excluded material:
    their licence is unidentified and no rights are granted over them."""
    blob = " ".join(relative_paths(artifact)).lower()
    for name in ("vale2024", "original-valuenet", "fred", "synthetic-dataset"):
        assert name not in blob, name


def test_nothing_excluded_by_licensing_reaches_the_artifact(artifact):
    """The strongest form: every file the licensing tool marks as
    excluded-unresolved must be absent by name from the published tree."""
    disposition = _load("leakage_disposition", "tools/licensing/disposition.py")
    excluded = {row.path.rsplit("/", 1)[-1] for row in disposition.classify()
                if row.disposition == disposition.EXCLUDED}
    assert len(excluded) > 100, "the excluded set looks wrong"

    published = {p.rsplit("/", 1)[-1] for p in relative_paths(artifact)}
    leaked = sorted(excluded & published)
    assert not leaked, (
        "%d file(s) this repository grants no rights over are published: %s"
        % (len(leaked), leaked))


def test_the_artifact_carries_no_secret_shaped_string(artifact):
    """No token, key or credential in anything served."""
    suspicious = ("BEGIN PRIVATE KEY", "BEGIN RSA", "ghp_", "github_pat_",
                  "AKIA", "sk-ant-", "xoxb-", "password=", "secret_key")
    for path in artifact.rglob("*"):
        if not path.is_file() or path.suffix in {".zip", ".png"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in suspicious:
            assert needle not in text, "%s in %s" % (needle, path.name)


def test_no_external_origin_is_referenced(artifact):
    """The site must render with no third-party request. Google Fonts, a
    CDN or an analytics beacon would each be one."""
    for path in artifact.rglob("*"):
        if path.suffix not in {".html", ".css", ".js"}:
            continue
        text = path.read_text(encoding="utf-8")
        for scheme in ("//fonts.googleapis", "//cdn.", "//unpkg",
                       "//cdnjs", "googletagmanager", "google-analytics"):
            assert scheme not in text, "%s in %s" % (scheme, path.name)
