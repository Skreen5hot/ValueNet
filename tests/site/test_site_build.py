"""The site build has to be reproducible, or a deployment proves nothing.

The site is deployed from an Actions artifact rather than from a committed
tree. Nobody can diff the deployed bytes against the repository, so the
only way to tell that a deployment corresponds to a commit is to rebuild
that commit and compare. Every property checked here exists to keep that
comparison meaningful.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys

import pytest

from marep import layout

REPO = layout.repository_root()


def _tool(component: str, name: str):
    path = layout.component(component).resolve()
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BUILD = _tool("tool.build-site", "build_site")


def build_into(out, source=None) -> dict:
    """Run the builder and return {relative path: sha256}."""
    argv = ["-o", str(out)]
    if source is not None:
        argv += ["--source", str(source)]
    assert BUILD.main(argv) == 0
    return {p.relative_to(out).as_posix():
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(out.rglob("*")) if p.is_file()}


def test_two_builds_of_one_commit_are_byte_identical(tmp_path):
    """The gate the whole design serves.

    A build that embedded the wall clock, or walked the filesystem in
    whatever order it came back, would pass every other test in this file
    and still make the artifact unverifiable.
    """
    first = build_into(tmp_path / "a")
    second = build_into(tmp_path / "b")
    assert first == second, "two builds of one commit differ"
    assert first, "the build produced nothing, so equality is vacuous"


def test_the_stamp_comes_from_the_commit_and_not_the_clock():
    """Asserted against git rather than against a second build.

    Two builds a millisecond apart would agree even if the stamp were
    `now()`, so equality alone cannot detect this.
    """
    commit, epoch = BUILD.build_stamp()
    expected = subprocess.run(
        ["git", "log", "-1", "--format=%at", commit], cwd=str(REPO),
        capture_output=True, text=True).stdout.strip()
    assert epoch == expected
    assert commit == subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO),
        capture_output=True, text=True).stdout.strip()


def test_source_date_epoch_overrides_the_commit_time(monkeypatch):
    """So a reproducible-build environment can pin the stamp."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1234567890")
    _commit, epoch = BUILD.build_stamp()
    assert epoch == "1234567890"


def test_the_build_refuses_a_file_it_has_no_rule_for(tmp_path):
    """Shipping an unexpected file and silently skipping it are both wrong.

    An artifact that deploys whatever it finds cannot say what it
    deployed; one that quietly omits a file looks complete and is not.
    """
    src = tmp_path / "src"
    shutil.copytree(layout.component("site.source").resolve(), src)
    (src / "notes.docx").write_bytes(b"not a site asset")

    with pytest.raises(SystemExit) as exc:
        build_into(tmp_path / "out", source=src)
    assert "notes.docx" in str(exc.value)
    assert "no rule for" in str(exc.value)


def test_a_file_removed_from_the_source_does_not_survive_the_rebuild(tmp_path):
    """Otherwise a deleted page is deployed forever.

    An incremental build that only writes what it finds leaves the old
    file in place, and nothing in the source says it is still being
    served.
    """
    src = tmp_path / "src"
    shutil.copytree(layout.component("site.source").resolve(), src)
    out = tmp_path / "out"

    (src / "retired.html").write_text("<!doctype html><title>x</title>",
                                      encoding="utf-8")
    first = build_into(out, source=src)
    assert "retired.html" in first

    (src / "retired.html").unlink()
    second = build_into(out, source=src)
    assert "retired.html" not in second, (
        "a page deleted from the source survived into the artifact")


def test_a_stale_file_that_cannot_be_removed_fails_the_build(tmp_path,
                                                             monkeypatch):
    """The distinction clear_output is built on.

    An empty directory that will not delete is harmless -- nothing is
    served from it. A *file* that will not delete is deployed. The first
    is tolerated so a locked directory on a synchronised filesystem does
    not break the build; the second must never be.
    """
    out = tmp_path / "out"
    out.mkdir()
    (out / "leftover.html").write_text("stale", encoding="utf-8")

    real_unlink = type(out).unlink

    def refuse(self, *a, **k):
        if self.name == "leftover.html":
            raise PermissionError("held open")
        return real_unlink(self, *a, **k)

    monkeypatch.setattr(type(out), "unlink", refuse)
    with pytest.raises(SystemExit) as exc:
        BUILD.clear_output(out)
    assert "leftover.html" in str(exc.value)
    assert "deployed" in str(exc.value)


def test_an_undeletable_empty_directory_does_not_fail_the_build(tmp_path,
                                                               monkeypatch):
    """The tolerated half, so the leniency is scoped rather than assumed."""
    out = tmp_path / "out"
    (out / "stuck").mkdir(parents=True)

    real_rmdir = type(out).rmdir

    def refuse(self, *a, **k):
        if self.name == "stuck":
            raise PermissionError("sync client holds a handle")
        return real_rmdir(self, *a, **k)

    monkeypatch.setattr(type(out), "rmdir", refuse)
    BUILD.clear_output(out)          # must not raise
    assert (out / "stuck").is_dir()


def test_the_artifact_is_not_committed():
    """It is generated, so a committed copy is a second description of the
    site that can drift from the source it was built from."""
    tracked = subprocess.run(["git", "ls-files", "--", "_site"],
                             cwd=str(REPO), capture_output=True,
                             text=True).stdout.strip()
    assert not tracked, "_site is tracked: " + tracked.splitlines()[0]
    ignored = subprocess.run(["git", "check-ignore", "-q", "_site/index.html"],
                             cwd=str(REPO))
    assert ignored.returncode == 0, "_site/ is not ignored by git"


def test_building_leaves_the_repository_clean(tmp_path):
    """A build tool that mutates the tree turns every later clean-tree gate
    into a question about the tool rather than the work."""
    before = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                            capture_output=True, text=True).stdout
    build_into(tmp_path / "out")
    after = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO),
                           capture_output=True, text=True).stdout
    assert before == after, "the build changed the working tree"


def test_the_artifact_is_outside_the_measured_corpus(tmp_path):
    """The trap Phase 5 would have sprung.

    The download build copies canonical Turtle into `_site/` byte for
    byte. If corpus discovery walked it, every authored module would be
    counted twice and every digest would move -- with nothing in the
    ontology to explain it, and the obvious remedy being to accept the new
    numbers.

    Asserted by putting a Turtle file there and requiring it not to be
    found. The artifact holds no Turtle yet, so a test that merely
    compared counts would pass today and for the wrong reason.
    """
    from marep import ontology_source as onto

    assert "_site" in onto.EXCLUDED_DIRS

    artifact = REPO / "_site"
    artifact.mkdir(exist_ok=True)
    planted = artifact / "planted-by-a-test.ttl"
    planted.write_text("@prefix ex: <https://probe.invalid/> .\n"
                       "ex:a ex:b ex:c .\n", encoding="utf-8", newline="\n")
    try:
        found = {p.name for p in onto.discover(REPO)}
        assert "planted-by-a-test.ttl" not in found, (
            "the deployment artifact is inside the measured corpus, so a "
            "built download would be counted as a second copy of the module "
            "it was copied from")
    finally:
        planted.unlink()
