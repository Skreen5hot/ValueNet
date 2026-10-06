# SPDX-License-Identifier: Apache-2.0
"""The site must work where it is actually served, and be checkable before
it is committed.

Two failures shape this file.

A root-absolute URL works in local preview and 404s in production, because
the site is served from a project subpath. That failure appears only after
deployment, so it is checked by building the artifact and resolving every
reference from inside a simulated subpath.

And in Phase 1 three new files under `site/` passed the repository's
allowance sweep without being opened: the sweep enumerates `git ls-files`
and they were untracked. A pre-commit gate that reads git reports on the
past, so the site checker walks the filesystem and treats an untracked
file under `site/` as a finding.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from urllib.parse import unquote, urlparse

import pytest

from marep import layout

REPO = layout.repository_root()


def _tool(component: str, name: str):
    path = layout.component(component).resolve()
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BUILD = _tool("tool.build-site", "build_site_links")
CHECK = _tool("tool.check-site", "check_site")

#: The approved deployment, read from configuration rather than retyped.
#: The subpath test below builds its directory name from this, so a
#: changed project path moves the test with it instead of leaving it
#: passing against a name nobody serves from.
DEPLOYMENT = json.loads(
    (layout.component("site.content").resolve() / "site.json")
    .read_text(encoding="utf-8"))["deployment"]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("site") / "_site"
    assert BUILD.main(["-o", str(out)]) == 0
    return out


def references(page):
    for raw in CHECK.LINK_ATTR.findall(page.read_text(encoding="utf-8")):
        yield raw.strip()


def test_the_build_produced_the_expected_pages(built):
    """So every assertion below is over a real population."""
    pages = {p.relative_to(built).as_posix() for p in built.rglob("*.html")}
    assert pages == {
        "index.html", "explore/index.html", "models/index.html",
        "modules/index.html", "downloads/index.html",
        "documentation/index.html", "about/index.html",
    }


def test_no_page_uses_a_root_absolute_url(built):
    """`/assets/site.css` resolves locally and 404s under /ValueNet/."""
    offenders = []
    for page in sorted(built.rglob("*.html")):
        for target in references(page):
            if target.startswith("/") and not target.startswith("//"):
                offenders.append(
                    "%s -> %s" % (page.relative_to(built).as_posix(), target))
    assert not offenders, (
        "root-absolute URLs resolve in local preview and 404 in production: "
        + str(offenders))


def outbound(built):
    """Every reference that leaves the site, with what carries it."""
    for page in sorted(built.rglob("*.html")):
        rel = page.relative_to(built).as_posix()
        for tag, attr, target in CHECK.references(
                page.read_text(encoding="utf-8")):
            if CHECK.leaves_the_site(target):
                yield rel, tag, attr, target


def test_no_page_requires_a_third_party_origin(built):
    """The site must render with no external request: no CDN, no web font,
    no analytics.

    This asserted that no reference had a scheme at all, which is a
    stronger rule than the one in its own first line and made the
    documentation page the plan asks for impossible: a link a reader
    chooses to follow is not a request the page makes. It now asks the
    question it names. Anything that is not an anchor loads, and nothing
    that loads may leave the site. Where an anchor may go is the next
    test's.
    """
    loads = ["%s <%s %s> -> %s" % row for row in outbound(built)
             if row[1:3] != ("a", "href")]
    assert not loads, loads


def test_every_outbound_link_goes_to_the_repository_and_finds_a_file(built):
    """The plan's "repository source links exist at the measured commit".

    One destination, read from the citation record, on the branch the
    site is built from, and only to a path git tracks. A reading path
    that names a document which has since moved sends its reader to a
    404, and nothing about the page looks wrong.
    """
    tracked = CHECK.tracked_files()
    assert tracked, "git listed no files, so no link could be confirmed"

    rows = list(outbound(built))
    assert len(rows) >= 20, (
        "only %d outbound link(s) were found. The documentation page is "
        "a reading path into the repository, so this checked almost "
        "nothing" % len(rows))
    refused = ["%s %s" % (rel, problem)
               for rel, tag, attr, target in rows
               for problem in [CHECK.outbound_problem(tag, attr, target,
                                                      tracked)]
               if problem]
    assert not refused, refused

    assert CHECK.repository_url() == "https://github.com/Skreen5hot/ValueNet"
    workflow = (REPO / ".github/workflows/pages.yml").read_text(
        encoding="utf-8")
    assert "branches: [%s]" % CHECK.PUBLISHED_REF in workflow, (
        "the links name a branch the Pages workflow does not deploy")


def test_every_reference_resolves_from_a_project_subpath(built, tmp_path):
    """The production shape, not the local one.

    The artifact is copied under a directory named like the GitHub project
    path and every reference is resolved from there. A page that only
    works at the domain root fails here.
    """
    served = tmp_path / DEPLOYMENT["base_path"].strip("/")
    shutil.copytree(built, served)

    broken = []
    for page in sorted(served.rglob("*.html")):
        for target in references(page):
            parsed = urlparse(target)
            if parsed.scheme or not target or target.startswith("#"):
                continue
            resolved = (page.parent / unquote(parsed.path)).resolve()
            if resolved.is_dir():
                resolved = resolved / "index.html"
            if not resolved.exists():
                broken.append("%s -> %s"
                              % (page.relative_to(served).as_posix(), target))
            else:
                try:
                    resolved.relative_to(served.resolve())
                except ValueError:
                    broken.append("%s -> %s escapes the served tree"
                                  % (page.relative_to(served).as_posix(),
                                     target))
    assert not broken, broken

    # The approved deployment, asserted so the simulated subpath is the
    # one the site will actually be served from.
    assert DEPLOYMENT["public_url"] == "https://skreen5hot.github.io/ValueNet/"
    assert DEPLOYMENT["base_path"] == "/ValueNet/"
    assert DEPLOYMENT["public_url"].endswith(DEPLOYMENT["base_path"]), (
        "the recorded URL and base path disagree, so the subpath simulated "
        "here is not the one production serves")


def test_every_page_carries_the_notices_the_plan_requires(built):
    """Checked as rendered text, not inferred from a shared template.

    A template refactor that dropped the footer from one page would leave
    the source looking correct.
    """
    for page in sorted(built.rglob("*.html")):
        # Normalised, because these notices are wrapped prose and a
        # literal search can straddle a line break -- which it did, and
        # reported six pages as missing text every one of them carried.
        text = " ".join(page.read_text(encoding="utf-8").split())
        rel = page.relative_to(built).as_posix()
        assert "not currently HTTP-dereferenceable" in text, rel
        assert "CC BY 4.0" in text and "Apache 2.0" in text, rel
        # The grant and its limit travel together. A page stating
        # the project licences without the exclusion reads as
        # licensing the upstream corpus too.
        assert "not covered" in text, rel
        # The contributor credit sits in every footer, not only on the
        # About page. A credit reachable only by navigating to it is one
        # most readers never see, and the assistance was substantive
        # enough that understating it would misdescribe the work.
        assert ("substantial assistance from Anthropic Claude and OpenAI "
                "Codex") in text, rel
        assert "Aaron Damiano" in text, rel


def test_the_build_stamp_is_substituted_on_every_page(built):
    """An unsubstituted placeholder would publish the word `unknown` as the
    commit a reader is asked to trust."""
    for page in sorted(built.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        assert 'data-build="commit">unknown' not in text, (
            page.relative_to(built).as_posix())


def test_navigation_is_usable_without_javascript(built):
    """Every destination is reachable by an anchor.

    The explorer needs JavaScript; navigating to it must not.
    """
    home = (built / "index.html").read_text(encoding="utf-8")
    for target in ("explore/", "models/", "modules/", "downloads/",
                   "documentation/"):
        assert 'href="%s"' % target in home, target
    assert "<script" not in home, (
        "the shell should need no script to navigate")


# ======================================================================
# the checker itself, and the miss it exists to prevent
# ======================================================================


def test_the_checker_reads_the_filesystem_rather_than_git(tmp_path,
                                                          monkeypatch):
    """Encodes the Phase 1 failure.

    Three files were added under site/, the allowance sweep was run, it
    passed, and it had opened none of them because it enumerates git and
    they were untracked. A checker that cannot see an uncommitted file is
    not a pre-commit gate.
    """
    monkeypatch.setattr(CHECK, "tracked_under", lambda prefix: set())
    problems = CHECK.check_source(allow_untracked=False)
    assert problems, (
        "with nothing tracked, every file on disk is untracked and the "
        "checker must say so")
    assert any("untracked" in p for p in problems)
    assert any("site/src" in p for p in problems), (
        "the checker did not reach the site source at all")


def test_the_checker_accepts_the_committed_source():
    """And is not simply always unhappy."""
    assert CHECK.check_source(allow_untracked=False) == []


def test_the_checker_reports_a_tracked_file_that_left_the_disk(monkeypatch):
    """The inverse direction: git and the source tree disagreeing the other
    way round is equally a finding."""
    monkeypatch.setattr(CHECK, "tracked_under",
                        lambda prefix: {"site/src/vanished.html"})
    problems = CHECK.check_source(allow_untracked=False)
    assert any("absent from disk" in p for p in problems), problems


def test_the_checker_rejects_a_root_absolute_url(built, tmp_path):
    """Forced rather than described."""
    broken = tmp_path / "broken"
    shutil.copytree(built, broken)
    page = broken / "index.html"
    page.write_text(
        page.read_text(encoding="utf-8").replace(
            'href="assets/css/site.css"', 'href="/assets/css/site.css"'),
        encoding="utf-8")

    problems = CHECK.check_built(broken)
    assert any("root-absolute" in p for p in problems), problems


def test_the_checker_rejects_a_missing_target(built, tmp_path):
    broken = tmp_path / "missing"
    shutil.copytree(built, broken)
    (broken / "assets" / "css" / "site.css").unlink()
    problems = CHECK.check_built(broken)
    assert any("resolves to nothing" in p for p in problems), problems


def test_the_checker_rejects_a_page_that_lost_a_notice(built, tmp_path):
    stripped = tmp_path / "stripped"
    shutil.copytree(built, stripped)
    page = stripped / "models" / "index.html"
    page.write_text(
        page.read_text(encoding="utf-8").replace(
            "not currently HTTP-dereferenceable", "resolvable"),
        encoding="utf-8")
    problems = CHECK.check_built(stripped)
    assert any("IRI-resolution notice" in p for p in problems), problems


REPOSITORY = "https://github.com/Skreen5hot/ValueNet"

#: Each is one way a reference could leave the site that must stay
#: refused, with the words the refusal has to contain. The last four are
#: all the repository's own address, which is the case a rule keyed on
#: the address alone would wave through.
REFUSED_OUTBOUND = [
    ("a script from a CDN",
     '<script src="https://cdn.example.org/lib.js"></script>',
     "loads"),
    ("a stylesheet from another origin",
     '<link rel="stylesheet" href="https://example.org/site.css">',
     "loads"),
    ("an image from another origin",
     '<img src="//example.org/pixel.gif" alt="">',
     "loads"),
    ("a link to somewhere else",
     '<a href="https://example.org/">elsewhere</a>',
     "only place a link may leave"),
    ("the repository's address on something that loads",
     '<script src="%s/blob/main/README.md"></script>' % REPOSITORY,
     "loads"),
    ("a repository link to a file that is not there",
     '<a href="%s/blob/main/docs/NO_SUCH_DOCUMENT.md">gone</a>' % REPOSITORY,
     "does not track"),
    ("a repository link on another branch",
     '<a href="%s/blob/some-branch/README.md">elsewhere</a>' % REPOSITORY,
     "another ref"),
    ("a repository link with a fragment nothing can resolve",
     '<a href="%s/blob/main/README.md#quick-start">anchor</a>' % REPOSITORY,
     "query or fragment"),
    ("a repository page that is not a file or a directory",
     '<a href="%s/issues">issues</a>' % REPOSITORY,
     "not a file or directory view"),
    ("a file addressed as a directory",
     '<a href="%s/tree/main/README.md">not a directory</a>' % REPOSITORY,
     "does not track"),
    ("a repository whose name merely begins the same way",
     '<a href="%s-elsewhere/blob/main/README.md">lookalike</a>' % REPOSITORY,
     "only place a link may leave"),
]


@pytest.mark.parametrize("what, markup, expected",
                         REFUSED_OUTBOUND,
                         ids=[row[0] for row in REFUSED_OUTBOUND])
def test_the_checker_rejects_what_may_not_leave_the_site(
        built, tmp_path, what, markup, expected):
    """Forced, one case at a time, into a copy of the real artifact."""
    broken = tmp_path / "outbound"
    shutil.copytree(built, broken)
    page = broken / "documentation" / "index.html"
    original = page.read_text(encoding="utf-8")
    mutated = original.replace("</main>", markup + "\n  </main>", 1)
    assert mutated != original, "the mutation did not apply"
    page.write_text(mutated, encoding="utf-8", newline="")

    problems = CHECK.check_built(broken)
    assert len(problems) == 1, (what, problems)
    assert expected in problems[0], (what, problems)


def test_the_checker_accepts_the_repository_links_it_is_meant_to(built,
                                                                 tmp_path):
    """And is not simply refusing every absolute reference, as it did.

    A file, a directory, the repository itself, and a path with an
    escaped space, which is how one of the guides is actually named.
    """
    accepted = tmp_path / "accepted"
    shutil.copytree(built, accepted)
    page = accepted / "documentation" / "index.html"
    markup = "".join('<a href="%s%s">ok</a>' % (REPOSITORY, suffix)
                     for suffix in ("", "/", "/blob/main/README.md",
                                    "/tree/main/docs",
                                    "/tree/main/docs/",
                                    "/blob/main/docs/bfo/guides/"
                                    "BFOizing%20ValueNet.md"))
    page.write_text(
        page.read_text(encoding="utf-8").replace(
            "</main>", markup + "\n  </main>", 1),
        encoding="utf-8", newline="")
    assert CHECK.check_built(accepted) == []


def test_a_link_to_an_untracked_file_is_refused(built, tmp_path,
                                                monkeypatch):
    """On disk is not published. The repository a reader lands in holds
    what git tracks, so a document that exists only in this working tree
    is a 404 there -- and a check that asked the filesystem would pass."""
    monkeypatch.setattr(CHECK, "tracked_files",
                        lambda: CHECK.tracked_under("docs") - {
                            "docs/HANDOFF.md"})
    problems = CHECK.check_built(built)
    assert any("docs/HANDOFF.md" in p and "does not track" in p
               for p in problems), problems


def test_the_checker_passes_on_the_real_artifact(built):
    """Both halves clean on the committed source and a fresh build, so the
    refusals above are specific rather than a checker that always fails."""
    assert CHECK.check_source(allow_untracked=False) == []
    assert CHECK.check_built(built) == []


def test_the_site_components_resolve_through_the_contract():
    """Consumers use logical identifiers rather than counting directories."""
    for cid in ("site.source", "site.content", "tool.build-site",
                "tool.check-site"):
        assert layout.component(cid).resolve().exists(), cid
    generated = layout.component("site.generated")
    assert generated.role == "generated-site-output"
    assert generated.generator == "tool.build-site"
