# SPDX-License-Identifier: Apache-2.0
"""Build the public site into _site/, deterministically.

    python tools/site/build_site.py

Determinism is the point, not a nicety. The site is deployed from an
Actions artifact rather than from a committed tree, so the only way to
tell that a deployment matches a commit is to rebuild it and compare. A
build that embeds the wall clock, walks the filesystem in directory
order, or copies whatever happens to be under site/src/ cannot support
that comparison.

So:

  * every input is enumerated in sorted order;
  * the only timestamp available is the source commit's, never now();
  * the output directory is removed and rewritten, so a file deleted from
    the source cannot survive in the artifact; and
  * bytes are copied, never re-encoded.

Paths in the markup are relative. The site is served from a project
subpath (`/ValueNet/`), and a root-absolute `/assets/...` would work in
local preview and 404 in production -- the failure that only appears
after deployment.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

OUTPUT = "_site"
SOURCE = "site/src"

#: Copied verbatim. Anything else under site/src/ is refused rather than
#: silently shipped: an artifact that deploys whatever it finds cannot say
#: what it deployed.
ALLOWED_SUFFIXES = {".html", ".css", ".js", ".json", ".svg", ".ttl", ".txt"}


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(_root),
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("git " + " ".join(args) + " failed: "
                         + r.stderr.strip()[-300:])
    return r.stdout.strip()


def source_files(src: Path) -> list[Path]:
    """Every input, sorted, with nothing skipped quietly.

    Sorted because filesystem order is not stable across machines and a
    build that depends on it is reproducible only by luck. Refusing an
    unexpected suffix rather than ignoring it means a stray file is a
    build failure and not a silent omission from the deployed site.
    """
    files, refused = [], []
    for path in sorted(src.rglob("*"), key=lambda p: p.as_posix()):
        if path.is_dir():
            continue
        if path.name.startswith("."):
            refused.append(path.relative_to(src).as_posix())
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            refused.append(path.relative_to(src).as_posix())
            continue
        files.append(path)
    if refused:
        raise SystemExit(
            "refusing to build: " + SOURCE + " holds files this build has no "
            "rule for, and shipping or skipping them silently are both wrong: "
            + ", ".join(sorted(refused)[:8])
            + ". Add the suffix to ALLOWED_SUFFIXES or remove the file.")
    return files


def clear_output(out: Path) -> None:
    """Empty the artifact, without depending on removing the directory.

    The invariant is that no file from a previous build survives into
    this one; whether an empty directory remains does not change what
    gets deployed. `shutil.rmtree` conflates the two and fails on the
    weaker one: on a synchronised filesystem the sync client holds a
    directory handle, `rmdir` raises PermissionError, and the build dies
    having already deleted the files it could.

    So a file that cannot be removed is fatal -- it would survive into
    the artifact and be deployed -- and a directory that cannot be is
    not.
    """
    if not out.exists():
        out.mkdir(parents=True)
        return
    # Deepest first, so a directory is only attempted once emptied.
    for path in sorted(out.rglob("*"),
                       key=lambda q: len(q.parts), reverse=True):
        try:
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()
        except OSError as exc:
            if not path.is_dir():
                raise SystemExit(
                    "cannot remove %s from the previous build, so it "
                    "would survive into this artifact and be deployed: "
                    "%s" % (path.name, exc))
    stale = [q for q in out.rglob("*") if q.is_file()]
    if stale:
        raise SystemExit(
            "%d file(s) from the previous build could not be removed: %s"
            % (len(stale), [q.name for q in stale[:4]]))


def build_stamp() -> tuple[str, str]:
    """The commit, and its own timestamp.

    `SOURCE_DATE_EPOCH` if the environment sets it, otherwise the commit's
    author date. Never `now()`: a timestamp that changes between two
    builds of one commit makes the artifacts differ and destroys the only
    check that says a deployment matches its source.
    """
    commit = git("rev-parse", "HEAD")
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if not epoch:
        epoch = git("log", "-1", "--format=%at", commit)
    return commit, epoch


def render(text: str, commit: str) -> str:
    """Substitute the build stamp. The markup carries a placeholder so a
    page opened straight from site/src/ is still valid HTML."""
    return text.replace(
        '<code data-build="commit">unknown</code>',
        '<code data-build="commit">%s</code>' % commit[:12])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=OUTPUT)
    ap.add_argument("--source", default=SOURCE)
    args = ap.parse_args(argv)

    # Absolute paths are honoured so a test can build into a temporary
    # directory without clobbering the working artifact.
    src = Path(args.source)
    src = src if src.is_absolute() else _root / src
    out = Path(args.out)
    out = out if out.is_absolute() else _root / out
    if not src.is_dir():
        raise SystemExit("no site source at " + args.source)

    commit, epoch = build_stamp()
    files = source_files(src)

    # Emptied and rewritten, so a file deleted from the source cannot
    # live on in the artifact and be deployed forever.
    clear_output(out)
    out.mkdir(parents=True, exist_ok=True)

    written = []
    for path in files:
        rel = path.relative_to(src)
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() == ".html":
            text = path.read_text(encoding="utf-8")
            data = render(text, commit).encode("utf-8")
        else:
            data = path.read_bytes()
        # newline="" via binary write: no platform translation, so the
        # artifact is identical on Windows and Linux.
        dest.write_bytes(data)
        os.utime(dest, (int(epoch), int(epoch)))
        written.append((rel.as_posix(), hashlib.sha256(data).hexdigest()))

    print("  commit %s  epoch %s" % (commit[:12], epoch))
    for rel, digest in written:
        print("    %-46s %s" % (rel, digest[:16]))
    tree = hashlib.sha256(
        "\n".join("%s %s" % (r, d) for r, d in written).encode("utf-8")
    ).hexdigest()
    print()
    print("  %d file(s) -> %s" % (len(written), args.out))
    print("  tree digest %s" % tree)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
