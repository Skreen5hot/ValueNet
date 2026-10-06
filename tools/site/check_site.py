# SPDX-License-Identifier: Apache-2.0
"""Check the site source and the built artifact.

    python tools/site/check_site.py            # source + built _site/
    python tools/site/check_site.py --source-only

WHY THIS WALKS THE FILESYSTEM

The repository's path-allowance sweep enumerates inputs with `git
ls-files`. During Phase 1 three new files were added under `site/`,
the sweep was run, it passed, and it had opened none of them: they were
untracked, so a tracked-file checker could not see them. The pass was
real and said nothing about the new work.

A pre-commit gate that only sees committed files reports on the past. So
every check here starts from `Path.rglob`, and an untracked file under
`site/` is a finding in its own right -- not because being untracked is
wrong mid-edit, but because a file the review tooling cannot see must not
reach a build that deploys it. `--allow-untracked` exists for local
iteration and is refused in CI by not passing it.

The inverse is checked too: a path git tracks under `site/` that is no
longer on disk means the source and the repository disagree about what
the site is made of.

WHAT MAY LEAVE THE SITE

The publication plan forbids a required third-party request -- no CDN, no
web font, no analytics -- and it also says the documentation page is
curated and that "deep records remain repository links". The first form
of this check refused every reference with a scheme, which enforced the
first sentence by making the second impossible: a documentation page
could not link to a single document.

A link a reader chooses to follow is not a request the page makes. So the
two are told apart by the element that carries the reference, and the
permission is as narrow as the plan's wording. Anything that loads -- a
script, a stylesheet, an image, a frame -- stays refused at any origin.
An anchor may leave the site for one place only, this project's own
repository as CITATION.cff names it, on the branch the site is built
from, and only to a path git tracks. That last condition is the plan's
"repository source links exist at the measured commit": a reading path
pointing at a document that has moved sends its reader to a 404.
"""

from __future__ import annotations

import argparse
import html.parser
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())

SITE = "site"
OUTPUT = "_site"
ALLOWED_SUFFIXES = {".html", ".css", ".js", ".json", ".svg", ".ttl", ".txt",
                    ".md"}


def tracked_under(prefix: str) -> set[str]:
    r = subprocess.run(["git", "ls-files", "--", prefix], cwd=str(_root),
                       capture_output=True, text=True)
    return set(r.stdout.splitlines()) if r.returncode == 0 else set()


def on_disk_under(prefix: str) -> set[str]:
    base = _root / prefix
    if not base.is_dir():
        return set()
    return {p.relative_to(_root).as_posix()
            for p in base.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts}


def check_source(allow_untracked: bool) -> list[str]:
    """Filesystem first, git second, and the difference is the finding."""
    problems = []
    disk = on_disk_under(SITE)
    tracked = tracked_under(SITE)

    untracked = sorted(disk - tracked)
    if untracked and not allow_untracked:
        problems.append(
            "%d file(s) under %s/ are on disk but untracked. A checker that "
            "enumerates git would not open them, so they must not reach a "
            "build that deploys them: %s"
            % (len(untracked), SITE, ", ".join(untracked[:8])))

    missing = sorted(tracked - disk)
    if missing:
        problems.append(
            "%d path(s) are tracked under %s/ but absent from disk, so the "
            "repository and the source tree disagree: %s"
            % (len(missing), SITE, ", ".join(missing[:8])))

    bad_suffix = sorted(p for p in disk
                        if Path(p).suffix.lower() not in ALLOWED_SUFFIXES)
    if bad_suffix:
        problems.append(
            "%d file(s) under %s/ have a suffix no rule covers: %s"
            % (len(bad_suffix), SITE, ", ".join(bad_suffix[:8])))
    return problems


LINK_ATTR = re.compile(r'(?:href|src)="([^"]+)"')

#: The branch the Pages workflow deploys, and so the one a reader of the
#: site is reading. A link to any other ref would show a document the
#: site was not built beside.
PUBLISHED_REF = "main"


class References(html.parser.HTMLParser):
    """Every href and src, with the element and attribute that carried it.

    LINK_ATTR finds the values and cannot say what they are on, and what
    they are on is the whole question: `<a href>` is somewhere a reader
    may go, `<link href>` is something the page fetches.
    """

    def __init__(self):
        super().__init__()
        self.found: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value and value.strip():
                self.found.append((tag, name, value.strip()))


def references(text: str) -> list[tuple[str, str, str]]:
    parser = References()
    parser.feed(text)
    return parser.found


def leaves_the_site(target: str) -> bool:
    """A scheme, or the protocol-relative form that borrows one."""
    return bool(urlparse(target).scheme) or target.startswith("//")


def repository_url() -> str:
    """Where the repository is, read from the citation record.

    Read rather than retyped. CITATION.cff is the project's own statement
    of where its source lives; a second copy here could name a different
    repository from the one a reader is told to cite. The top-level key
    only: the file also records the original ValueNet's repository, under
    a reference, and that one is indented.
    """
    text = (_root / "CITATION.cff").read_text(encoding="utf-8")
    found = re.findall(r"(?m)^repository-code:[ \t]*(\S+)[ \t]*$", text)
    if len(found) != 1:
        raise SystemExit(
            "CITATION.cff names %d top-level repository-code value(s); "
            "exactly one is needed to say which repository the site may "
            "link to" % len(found))
    return found[0].rstrip("/")


def tracked_files() -> set[str]:
    """Every path git tracks. Empty when git cannot answer, which refuses
    every repository link rather than waving them through unchecked."""
    r = subprocess.run(["git", "ls-files"], cwd=str(_root),
                       capture_output=True, text=True)
    return set(r.stdout.splitlines()) if r.returncode == 0 else set()


def outbound_problem(tag: str, attr: str, target: str,
                     tracked: set[str]) -> str | None:
    """Why a reference that leaves the site may not ship, or None.

    The order matters. What the reference is on is asked first, so the
    repository's address on a `<script src>` is refused as a load and not
    accepted as a link.
    """
    if (tag, attr) != ("a", "href"):
        return ("<%s %s> loads %r from an external origin; the site must "
                "work with no third-party request" % (tag, attr, target))

    repository = repository_url()
    if target.rstrip("/") == repository:
        return None
    if not target.startswith(repository + "/"):
        return ("links to %r. The only place a link may leave the site for "
                "is this project's repository, %s" % (target, repository))

    parsed = urlparse(target)
    if parsed.query or parsed.fragment:
        return ("links to %r with a query or fragment. Neither can be "
                "resolved against the repository, so neither is checked, "
                "and an unchecked link is not published" % target)

    rest = unquote(parsed.path)[len(urlparse(repository).path) + 1:]
    kind, _, remainder = rest.partition("/")
    ref, _, path = remainder.partition("/")
    path = path.rstrip("/")
    if kind not in ("blob", "tree") or not path:
        return ("links to %r, which is not a file or directory view of the "
                "repository" % target)
    if ref != PUBLISHED_REF:
        return ("links to %r at %r. The site is built from %r, and a link "
                "to another ref shows a document it was not built beside"
                % (path, ref, PUBLISHED_REF))

    if kind == "blob":
        present = path in tracked and (_root / path).is_file()
    else:
        present = (any(name.startswith(path + "/") for name in tracked)
                   and (_root / path).is_dir())
    if not present:
        return ("links to %r, which git does not track as a %s here. The "
                "link would resolve to nothing once published"
                % (path, "file" if kind == "blob" else "directory"))
    return None


def check_built(out: Path) -> list[str]:
    """Every internal reference resolves, none assumes the domain root,
    and nothing leaves the site except a checked link to the repository."""
    problems = []
    pages = sorted(out.rglob("*.html"))
    if not pages:
        problems.append("no HTML in " + out.name + "; build it first")
        return problems

    tracked = None
    for page in pages:
        rel = page.relative_to(out).as_posix()
        text = page.read_text(encoding="utf-8")
        for tag, attr, target in references(text):
            parsed = urlparse(target)
            if leaves_the_site(target):
                if tracked is None:
                    tracked = tracked_files()
                problem = outbound_problem(tag, attr, target, tracked)
                if problem:
                    problems.append("%s %s" % (rel, problem))
                continue
            if target.startswith("#") or not target:
                continue
            if target.startswith("/"):
                problems.append(
                    "%s uses the root-absolute URL %r. The site is served "
                    "from a project subpath, so this resolves in local "
                    "preview and 404s in production -- the failure that only "
                    "appears after deployment." % (rel, target))
                continue
            resolved = (page.parent / unquote(parsed.path)).resolve()
            if resolved.is_dir():
                resolved = resolved / "index.html"
            if not resolved.exists():
                problems.append("%s -> %s resolves to nothing"
                                % (rel, target))
                continue
            try:
                resolved.relative_to(out.resolve())
            except ValueError:
                problems.append("%s -> %s escapes the deployed tree"
                                % (rel, target))

    # The notices the plan requires on every page, checked as text rather
    # than assumed from the template.
    for page in pages:
        # Whitespace-normalised: the notices are wrapped prose, so a
        # literal substring can fall across a line break and report a
        # page as missing text it plainly carries.
        text = " ".join(page.read_text(encoding="utf-8").split())
        rel = page.relative_to(out).as_posix()
        if "not currently HTTP-dereferenceable" not in text:
            problems.append(rel + " omits the IRI-resolution notice")
        if "substantial assistance from Anthropic Claude and OpenAI "                 "Codex" not in text:
            problems.append(
                rel + " omits the contributor acknowledgment. The AI "
                      "assistance here was substantive; a page that states "
                      "authorship without it understates what was done.")
        if "CC BY 4.0" not in text or "Apache 2.0" not in text:
            problems.append(rel + " omits the licence notice")
        if "not covered" not in text:
            problems.append(
                rel + " states the project licences without the "
                      "upstream exclusion, so a permissive grant "
                      "reads as covering the whole repository")
        if 'data-build="commit">unknown' in text:
            problems.append(rel + " still carries the unsubstituted build "
                                  "placeholder")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUTPUT)
    ap.add_argument("--source-only", action="store_true")
    ap.add_argument("--allow-untracked", action="store_true",
                    help="permit untracked files under site/ for local "
                         "iteration. Not passed in CI: an untracked file is "
                         "invisible to every git-based check in this "
                         "repository.")
    args = ap.parse_args(argv)

    problems = check_source(args.allow_untracked)
    if not args.source_only:
        out = Path(args.out)
        problems += check_built(
            out if out.is_absolute() else _root / out)

    if problems:
        print("check_site: %d problem(s)" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("check_site: source and artifact both clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
