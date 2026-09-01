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
"""

from __future__ import annotations

import argparse
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


def check_built(out: Path) -> list[str]:
    """Every internal reference resolves, and none assumes the domain root."""
    problems = []
    pages = sorted(out.rglob("*.html"))
    if not pages:
        problems.append("no HTML in " + out.name + "; build it first")
        return problems

    for page in pages:
        rel = page.relative_to(out).as_posix()
        text = page.read_text(encoding="utf-8")
        for raw in LINK_ATTR.findall(text):
            target = raw.strip()
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("//"):
                problems.append(
                    "%s references an external origin %r; the site must work "
                    "with no third-party request" % (rel, target))
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
        text = page.read_text(encoding="utf-8")
        rel = page.relative_to(out).as_posix()
        if "not currently HTTP-dereferenceable" not in text:
            problems.append(rel + " omits the IRI-resolution notice")
        if "No project license has been issued" not in text:
            problems.append(rel + " omits the license-pending notice")
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
