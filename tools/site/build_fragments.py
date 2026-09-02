# SPDX-License-Identifier: Apache-2.0
"""Page sections generated from the ontology, at build time.

The module cards and the download table are not written by hand. Every
title, description, namespace, count and checksum on those pages is
extracted, so a page cannot describe a module the repository no longer
contains or a checksum the bundle no longer has.

Generated at build time rather than fetched in the browser, unlike the
explorer: these are lists, not searches. A reader with scripting disabled
gets the whole modules page and the whole download table, and only the
search stops working.

Everything interpolated is escaped. The explorer's rule is that ontology
text reaches the page as text and never as markup; the same rule holds
here, and `html.escape` is the single place it is enforced. A definition
containing a `<` is authored text in a file anyone can edit.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())

#: The build replaces the whole element. The source page keeps a plain
#: fallback inside it so it is valid HTML on its own and says what is
#: missing when opened straight from site/src/.
MARKERS = ("modules", "downloads")


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def _thousands(number: int) -> str:
    return "{:,}".format(int(number))


def _link_list(items, empty: str) -> str:
    if not items:
        return '<span class="muted">%s</span>' % esc(empty)
    return ", ".join("<code>%s</code>" % esc(i) for i in items)


def module_cards(manifest: dict, index: dict, editorial: dict) -> str:
    """One card per reviewed deliverable, primary and supporting apart."""
    counts = {m["key"]: m["classes"] for m in index["modules"]}
    out = []

    for group, heading, blurb in (
        ("primary", "Primary modules",
         "These carry the ontology and its semantics."),
        ("supporting", "Validation and examples",
         "Published and downloadable, and part of the bundle. A shape "
         "graph constrains rather than declares and a scenario is "
         "individuals, so neither contributes class records."),
    ):
        members = [r for r in manifest["modules"] if r["group"] == group]
        out.append('<section class="module-group">')
        out.append("<h2>%s</h2>" % esc(heading))
        out.append('<p class="lead-small">%s</p>' % esc(blurb))
        for record in members:
            out.append(_card(record, counts, editorial))
        out.append("</section>")
    return "\n".join(out)


def _card(record: dict, counts: dict, editorial: dict) -> str:
    key = record["id"]
    rows = []

    if record["indexed"]:
        total = counts.get(key, 0)
        rows.append((
            "Classes",
            "%s &mdash; <span class=\"muted\">all %s carry a definition; "
            "the index refuses a class without one, so this is a property "
            "of the build rather than a survey</span>"
            % (esc(total), esc(total))))
    else:
        # Zero with its reason, taken from the reviewed catalog. A bare
        # 0 reads as a broken extractor.
        rows.append(("Classes",
                     '0 &mdash; <span class="muted">%s</span>'
                     % esc(editorial.get(key, "declares no classes"))))

    rows.append(("Terms of its own",
                 esc(record["own_terms"]) if record["own_terms"] else
                 '0 <span class="muted">&mdash; it asserts about terms '
                 'defined elsewhere</span>'))
    rows.append(("Namespace", "<code>%s</code>" % esc(record["namespace"])))
    rows.append(("Ontology IRI", "<code>%s</code>" % esc(record["ontology_iri"])))
    rows.append(("Source", "<code>%s</code>" % esc(record["source"])))
    rows.append(("Imports", _link_list(record["imports"], "none declared")))
    rows.append(("Uses terms from",
                 _link_list(record["references"], "no other reviewed module")))
    rows.append(("License", "<code>%s</code>" % esc(record["license"])))

    facts = "\n".join("<dt>%s</dt><dd>%s</dd>" % (esc(label), value)
                      for label, value in rows)

    actions = ['<a href="../downloads/%s">Download %s</a> (%s bytes)'
               % (esc(record["filename"]), esc(record["filename"]),
                  esc(_thousands(record["bytes"])))]
    if record["indexed"]:
        actions.append('<a href="../explore/?module=%s">Explore its classes</a>'
                       % esc(key))

    return ('<article class="module-card">\n'
            '<h3>%s</h3>\n<p>%s</p>\n<dl class="module-facts">\n%s\n</dl>\n'
            '<p class="module-actions">%s</p>\n</article>'
            % (esc(record["title"]), esc(record["description"]), facts,
               " &middot; ".join(actions)))


def download_table(manifest: dict) -> str:
    """Individual files, the bundle, and every published checksum."""
    bundle = manifest["bundle"]
    rows = []
    for record in manifest["modules"]:
        rows.append(
            "<tr><td><a href=\"%s\">%s</a></td><td class=\"num\">%s</td>"
            "<td><code class=\"digest\">%s</code></td></tr>"
            % (esc(record["filename"]), esc(record["filename"]),
               esc(_thousands(record["bytes"])), esc(record["sha256"])))

    governance = "\n".join(
        "<tr><td><code>%s</code></td><td class=\"num\">%s</td>"
        "<td><code class=\"digest\">%s</code></td></tr>"
        % (esc(g["filename"]), esc(_thousands(g["bytes"])), esc(g["sha256"]))
        for g in manifest["governance"])

    return """<section>
<h2>The bundle</h2>
<p>Every reviewed module, the license, the third-party notices, the
citation record, and a <code>SHA256SUMS</code> file, in one archive.
Vendored BFO and CCO dependencies are not included: they are upstream
material under their own licenses.</p>
<p class="module-actions"><a href="%(bundle)s">Download %(bundle)s</a>
(%(bundle_bytes)s bytes)</p>
<dl class="module-facts">
<dt>SHA-256</dt><dd><code class="digest">%(bundle_sha)s</code></dd>
<dt>Archive root</dt><dd><code>%(root)s/</code></dd>
<dt>Members</dt><dd>%(members)s files</dd>
</dl>
<p>The archive is byte-reproducible. Member order, timestamps,
permissions and the recorded creating system are all fixed, so two builds
of one commit produce the same bytes and the checksum above identifies
the content rather than the machine that packed it.</p>
</section>

<section>
<h2>Individual modules</h2>
<p>Canonical Turtle, copied byte for byte from the repository. The build
does not re-serialize RDF, so these files are the ontology as authored
and their checksums match the source.</p>
<div class="scroll-x">
<table class="downloads">
<caption>Reviewed Turtle deliverables with sizes and SHA-256 checksums</caption>
<thead><tr><th scope="col">File</th><th scope="col">Bytes</th>
<th scope="col">SHA-256</th></tr></thead>
<tbody>
%(rows)s
</tbody>
</table>
</div>
</section>

<section>
<h2>Also in the bundle</h2>
<div class="scroll-x">
<table class="downloads">
<caption>License, attribution and citation records carried with the ontology</caption>
<thead><tr><th scope="col">File</th><th scope="col">Bytes</th>
<th scope="col">SHA-256</th></tr></thead>
<tbody>
%(governance)s
</tbody>
</table>
</div>
</section>

<section>
<h2>Verifying what you downloaded</h2>
<p>The published <a href="SHA256SUMS">SHA256SUMS</a> covers every file
listed above. The same file travels inside the archive, so an unpacked
bundle can be checked without fetching anything further.</p>
<p>A machine-readable record of this page, including the source commit
each file was published from, is at
<a href="../data/downloads.json">downloads.json</a>.</p>
</section>""" % {
        "bundle": esc(bundle["filename"]),
        "bundle_bytes": esc(_thousands(bundle["bytes"])),
        "bundle_sha": esc(bundle["sha256"]),
        "root": esc(bundle["root"]),
        "members": esc(len(bundle["members"])),
        "rows": "\n".join(rows),
        "governance": governance,
    }


def build(out: Path) -> dict[str, str]:
    """The generated sections, keyed by marker name."""
    manifest = json.loads((out / "data/downloads.json")
                          .read_text(encoding="utf-8"))
    index = json.loads((out / "data/class-index.json")
                       .read_text(encoding="utf-8"))
    site = json.loads((_root / "site/content/site.json")
                      .read_text(encoding="utf-8"))
    editorial = {}
    for group in ("primary", "supporting"):
        for entry in site["catalog"][group]:
            if entry.get("editorial"):
                editorial[entry["key"]] = entry["editorial"]

    return {
        "modules": module_cards(manifest, index, editorial),
        "downloads": download_table(manifest),
    }


def substitute(text: str, fragments: dict[str, str]) -> str:
    """Replace each generated element's contents.

    The fallback inside a marker must not itself contain a `<div>`: the
    replacement runs to the first closing tag, and a nested one would
    leave the page half-generated and still look plausible.
    """
    for name, html_fragment in fragments.items():
        opening = '<div data-generated="%s">' % name
        start = text.find(opening)
        if start == -1:
            continue
        end = text.find("</div>", start)
        if end == -1:
            raise SystemExit("the %s marker is never closed" % name)
        inner = text[start + len(opening):end]
        if "<div" in inner:
            raise SystemExit(
                "the %s marker contains a nested <div>, so the generated "
                "section would be spliced into the middle of it" % name)
        text = (text[:start + len(opening)] + "\n" + html_fragment + "\n"
                + text[end:])
    return text
