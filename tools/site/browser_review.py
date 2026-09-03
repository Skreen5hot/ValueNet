# SPDX-License-Identifier: Apache-2.0
"""Drive the built site in real browsers and record what happened.

    python tools/site/browser_review.py --out config/browser-review.json

Everything Phase 4 and Phase 5 deferred needs a rendering engine: whether
focus actually lands where the tab order says, whether a live region is
exposed to assistive technology, whether hostile ontology text stays
text once a browser has parsed it, and whether three diagrams survive a
320-pixel viewport. None of that can be decided from source.

The output is a record, not a pass/fail exit. Every check writes what it
observed -- the focused element, the announced text, the measured
overflow -- so a reviewer can see the result rather than a green tick, and
so a later run can be compared with this one. `tests/site` holds the
record to its claims.

WHAT THIS CANNOT DO, AND SAYS SO

Safari is not tested. This runs on Windows, Safari has had no Windows
build since 2012, and Playwright's WebKit is a different browser that
shares an engine lineage. It is recorded as `playwright-webkit`, never as
Safari, because a record claiming Safari coverage would be worse than one
admitting the gap.

No screen reader is run. The live-region checks read the accessibility
tree the browser exposes, which is what a screen reader consumes, but
consuming it is not the same as announcing it. Whether NVDA, JAWS or
VoiceOver actually speak the text at the right moment is a listening test
and remains open.
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import hashlib
import http.server
import json
import os
import platform
import re
import socketserver
import threading
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())

FORMAT_VERSION = 1
GENERATOR = "tools/site/browser_review.py"

#: The class the deep-link checks open. Named rather than discovered so
#: the record says which record was exercised.
DEEP_LINK_CLASS = "core:ValueDisposition"

#: narrow is a phone. wide is a laptop. high-zoom is what a 1280x1024
#: screen becomes at 400% browser zoom, which is the WCAG 1.4.4 limit and
#: the case that actually breaks layouts -- the viewport loses height as
#: well as width, and a fixed-width control has nowhere to go.
VIEWPORTS = {
    "narrow": {"width": 360, "height": 780},
    "wide": {"width": 1440, "height": 900},
    "high-zoom-400pct": {"width": 320, "height": 256},
}

#: Payloads placed in ontology-derived fields. Each would do something
#: observable if the page built markup from the string.
HOSTILE = {
    "label": '<img src=x onerror="window.__pwned=1">Hostile Label',
    "definition": '</p><script>window.__pwned=1</script><p>ok',
    "synonym": '"><svg onload="window.__pwned=1">',
}


@contextlib.contextmanager
def serve(directory: Path):
    """A local HTTP server, because the explorer fetches its index.

    file:// gives a null origin, and the fetch is refused before any of
    the behaviour under test can run. Testing over file:// would have
    measured the protocol rather than the page.
    """
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(directory))

    class Quiet(socketserver.TCPServer):
        allow_reuse_address = True

        def handle_error(self, request, client_address):
            pass

    with Quiet(("127.0.0.1", 0), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield "http://127.0.0.1:%d" % httpd.server_address[1]
        finally:
            httpd.shutdown()


def tab_order(page, limit: int = 40) -> list[str]:
    """Where focus goes, pressing Tab from the top of the document."""
    page.evaluate("document.body.focus()")
    seen = []
    for _ in range(limit):
        page.keyboard.press("Tab")
        described = page.evaluate("""() => {
            const a = document.activeElement;
            if (!a || a === document.body) { return 'body'; }
            const id = a.id ? '#' + a.id : '';
            const cls = a.className && typeof a.className === 'string'
                ? '.' + a.className.split(' ')[0] : '';
            return a.tagName.toLowerCase() + id + cls;
        }""")
        seen.append(described)
        if described == "body":
            break
    return seen


def check_deep_link_keyboard(page, base: str) -> dict:
    """Arriving on a shared ?class= URL, reachable by keyboard alone."""
    page.goto("%s/explore/?class=%s" % (base, DEEP_LINK_CLASS))
    page.wait_for_selector("#jump-wrap:not([hidden])")

    order = tab_order(page)
    # The descriptor carries the first class as well as the id, so an
    # equality test against "a#jump" missed an element that was there.
    jump_at = next((i + 1 for i, stop in enumerate(order)
                    if "#jump" in stop), None)
    results = page.locator("a.result").count()

    # Reload before tabbing again. `document.body.focus()` does not move
    # focus -- body is not focusable -- so the second run continued from
    # wherever the survey left off, and pressing Enter there activated a
    # result link instead of the bypass. The detail pane then showed a
    # different class, and the check reported that as the deep link.
    page.goto("%s/explore/?class=%s" % (base, DEEP_LINK_CLASS))
    page.wait_for_selector("#jump-wrap:not([hidden])")
    for _ in range(jump_at or 0):
        page.keyboard.press("Tab")
    focused_before = page.evaluate("document.activeElement.id")
    page.keyboard.press("Enter")
    page.wait_for_timeout(120)
    focused_after = page.evaluate("document.activeElement.id")
    detail_visible = page.locator("#detail").is_visible()
    heading = page.locator("#detail .detail-label").inner_text()

    return {
        "url": "/explore/?class=" + DEEP_LINK_CLASS,
        "results_rendered": results,
        "tab_stops_to_bypass": jump_at,
        "tab_stops_to_detail_without_bypass": (jump_at + results
                                               if jump_at else None),
        "focus_before_activation": focused_before,
        "focus_after_activation": focused_after,
        "detail_visible": detail_visible,
        "detail_heading": heading,
        "tab_order_prefix": order[:16],
        "anchors_in_tab_order": sum(1 for stop in order
                                    if stop.startswith("a")),
        "passed": (focused_before == "jump" and focused_after == "detail"
                   and detail_visible and bool(heading)),
    }


def check_live_regions(page, base: str) -> dict:
    """What the accessibility tree exposes, and that it updates.

    Not a screen-reader test. This is the data a screen reader reads;
    whether one speaks it at the right moment is a listening test.
    """
    page.goto("%s/explore/" % base)
    page.wait_for_selector("#status:not(:empty)")
    before = page.locator("#status").inner_text()

    page.locator("#q").fill("betrayal")
    page.wait_for_timeout(200)
    after = page.locator("#status").inner_text()

    # page.accessibility was removed in Playwright 1.62. Role resolution
    # works in all three engines and is computed from ARIA semantics, so
    # it answers the same question: is this element exposed as a status
    # region rather than as an anonymous paragraph.
    by_role = page.get_by_role("status")
    exposed = by_role.count() > 0

    # Where a real accessibility tree is available, take it. Chromium
    # only -- CDP is not a cross-browser protocol, and pretending the
    # weaker check is the stronger one is the failure this whole record
    # exists to avoid.
    ax_node = None
    try:
        session = page.context.new_cdp_session(page)
        session.send("Accessibility.enable")
        tree = session.send("Accessibility.getFullAXTree")
        for node in tree.get("nodes", []):
            role = (node.get("role") or {}).get("value")
            if role == "status":
                ax_node = {
                    "role": role,
                    "name": (node.get("name") or {}).get("value"),
                    "live": next((p.get("value", {}).get("value")
                                  for p in node.get("properties", [])
                                  if p.get("name") == "live"), None),
                }
                break
        session.detach()
    except Exception:                                     # noqa: BLE001
        ax_node = None

    attrs = page.evaluate("""() => {
        const s = document.getElementById('status');
        return {role: s.getAttribute('role'),
                live: s.getAttribute('aria-live')};
    }""")
    # The copy-result region, which is created when a detail pane renders
    # rather than existing in the markup. It was never exercised: a live
    # region that is built at runtime is exactly the one that can be
    # built without its role, and nothing static would notice.
    page.goto("%s/explore/?class=%s" % (base, DEEP_LINK_CLASS))
    page.wait_for_selector("#detail:not([hidden])")
    copy_before = page.locator(".copy-result").inner_text()
    copy_attrs = page.evaluate("""() => {
        const s = document.querySelector('.copy-result');
        return {role: s.getAttribute('role'),
                live: s.getAttribute('aria-live'),
                present: true};
    }""")
    page.locator("button.copy").first.click()
    page.wait_for_timeout(300)
    copy_after = page.locator(".copy-result").inner_text()
    copy_exposed = page.get_by_role("status").count() >= 1

    return {
        "status_role": attrs["role"],
        "status_aria_live": attrs["live"],
        "exposed_as_status_role": exposed,
        "chromium_accessibility_node": ax_node,
        "text_before": before,
        "text_after_typing": after,
        "text_changed": before != after,
        "copy_result": {
            "role": copy_attrs["role"],
            "aria_live": copy_attrs["live"],
            "text_before_click": copy_before,
            "text_after_click": copy_after,
            "text_changed": copy_before != copy_after,
            "exposed_as_status_role": copy_exposed,
            "note": ("the clipboard is commonly refused without a user "
                     "gesture the browser recognises; either outcome must "
                     "announce, and the text recorded above is what it "
                     "said"),
        },
        "screen_reader_used": None,
        "note": ("accessibility tree only; no screen reader was run, so "
                 "announcement timing and verbosity are unverified"),
        "passed": (attrs["role"] == "status"
                   and attrs["live"] == "polite"
                   and exposed
                   and before != after
                   and copy_attrs["role"] == "status"
                   and copy_attrs["live"] == "polite"
                   and copy_before == ""
                   and copy_after != ""),
    }


def check_hostile_text(page, base: str) -> dict:
    """Ontology text with payloads in it, rendered by a real browser."""
    hostile_record = {
        "id": "syn:Hostile",
        "iri": "https://synthetic.invalid/h#Hostile",
        "label": HOSTILE["label"],
        "definition": HOSTILE["definition"],
        "synonyms": [HOSTILE["synonym"]],
        "category": "disposition",
        "module": "valuenet-core",
        "source": "synthetic.ttl",
        "parents": [],
        "mappings": [],
    }

    def inject(route):
        response = route.fetch()
        payload = response.json()
        payload["classes"] = [hostile_record] + payload["classes"]
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps(payload))

    page.route("**/data/class-index.json", inject)
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    page.goto("%s/explore/?class=syn:Hostile" % base)
    page.wait_for_selector("#detail:not([hidden])")
    page.wait_for_timeout(250)

    pwned = page.evaluate("() => window.__pwned === undefined ? null : 1")
    injected_img = page.locator("#detail img").count()
    injected_svg = page.locator("#detail svg").count()
    injected_script = page.locator("#detail script").count()
    shown_label = page.locator("#detail .detail-label").inner_text()
    shown_definition = page.locator("#detail .detail-definition").inner_text()
    page.unroute("**/data/class-index.json")

    return {
        "payloads": HOSTILE,
        "window_flag_set": pwned,
        "dialogs_raised": dialogs,
        "elements_injected": {"img": injected_img, "svg": injected_svg,
                              "script": injected_script},
        "label_rendered_as_text": shown_label,
        "definition_rendered_as_text": shown_definition,
        "passed": (pwned is None and not dialogs
                   and injected_img == 0 and injected_svg == 0
                   and injected_script == 0
                   and shown_label == HOSTILE["label"]
                   and shown_definition == HOSTILE["definition"]),
    }


#: Read out of the page rather than described. Each returns plain
#: data so the record holds measurements a reviewer can check.
MEASURE_JS = r"""() => {
        const out = [];
        document.querySelectorAll('svg.diagram').forEach((svg, i) => {
            const frame = svg.getBoundingClientRect();
            const parts = {rect: 0, text: 0, path: 0, marker: 0};
            const clipped = [], empty = [], texts = [];
            svg.querySelectorAll('rect, text, path, marker').forEach(el => {
                const tag = el.tagName.toLowerCase();
                parts[tag] = (parts[tag] || 0) + 1;
                if (tag === 'marker') { return; }
                const r = el.getBoundingClientRect();
                if (tag === 'path') {
                    if (el.getTotalLength && el.getTotalLength() < 1) {
                        empty.push(el.getAttribute('d') || 'no d');
                    }
                    return;
                }
                if (r.width === 0 && r.height === 0) { return; }
                const slack = 1.5;
                if (r.left < frame.left - slack || r.top < frame.top - slack
                    || r.right > frame.right + slack
                    || r.bottom > frame.bottom + slack) {
                    clipped.push({tag: tag,
                                  text: (el.textContent || '').slice(0, 30),
                                  left: Math.round(r.left - frame.left),
                                  right: Math.round(r.right - frame.left)});
                }
                if (tag === 'text') {
                    // Grouped by the <g> that wraps a node, because a
                    // label and its caption are two lines of one label
                    // and are meant to sit together. Comparing them
                    // reported every box in the suite as a collision.
                    const g = el.closest('g');
                    texts.push({t: (el.textContent || '').slice(0, 30),
                                g: g ? (g.getAttribute('data-iri') || 'g')
                                     : 'loose',
                                x: r.left, y: r.top,
                                w: r.width, h: r.height});
                }
            });
            const overlaps = [];
            for (let a = 0; a < texts.length; a += 1) {
                for (let b = a + 1; b < texts.length; b += 1) {
                    const p = texts[a], q = texts[b];
                    if (p.g === q.g && p.g !== 'loose') { continue; }
                    const dx = Math.min(p.x + p.w, q.x + q.w)
                             - Math.max(p.x, q.x);
                    const dy = Math.min(p.y + p.h, q.y + q.h)
                             - Math.max(p.y, q.y);
                    if (dx > 1 && dy > 1) {
                        overlaps.push([p.t, q.t,
                                       Math.round(dx), Math.round(dy)]);
                    }
                }
            }
            out.push({
                index: i,
                frame: {width: Math.round(frame.width),
                        height: Math.round(frame.height)},
                visible: frame.width > 0 && frame.height > 0,
                elements: parts,
                labels_measured: texts.length,
                clipped: clipped,
                zero_length_paths: empty,
                overlapping_labels: overlaps
            });
        });
        return out;
    }"""

ARROWS_JS = r"""() => {
        const markers = document.querySelectorAll('svg.diagram marker').length;
        let referencing = 0;
        document.querySelectorAll('svg.diagram path').forEach(p => {
            if (p.getAttribute('marker-end')) { referencing += 1; }
        });
        return {markers: markers, paths_with_marker_end: referencing};
    }"""

OVERFLOW_JS = r"""() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth
    })"""

WIDEST_JS = r"""() => {
        let worst = null;
        for (const el of document.querySelectorAll('main *')) {
            const r = el.getBoundingClientRect();
            if (r.right > document.documentElement.clientWidth + 1) {
                if (!worst || r.right > worst.right) {
                    worst = {tag: el.tagName.toLowerCase(),
                             cls: (el.className || '').toString().split(' ')[0],
                             right: Math.round(r.right)};
                }
            }
        }
        return worst;
    }"""


def check_diagrams(page, base: str, viewport: str, shots: Path,
                   engine: str) -> dict:
    """Three diagrams, and what is actually inside them.

    Whole-SVG visibility and document overflow say the figure is on the
    page and the page does not scroll sideways. They say nothing about
    whether a label sits outside its box, whether two labels collide, or
    whether a relation path has any length -- which is what a reader
    notices first and what a viewport change actually breaks.
    """
    page.goto("%s/models/" % base)
    page.wait_for_selector("svg.diagram")

    measured = page.evaluate(MEASURE_JS)
    arrowheads = page.evaluate(ARROWS_JS)
    overflow = page.evaluate(OVERFLOW_JS)
    horizontal = overflow["scrollWidth"] > overflow["clientWidth"] + 1
    widest = page.evaluate(WIDEST_JS)

    shots.mkdir(parents=True, exist_ok=True)
    shot = shots / ("models-%s-%s.png" % (engine, viewport))
    page.screenshot(path=str(shot), full_page=True)
    image = shot.read_bytes()

    return {
        "viewport": VIEWPORTS[viewport],
        "diagrams_found": len(measured),
        "diagrams": measured,
        "arrowheads": arrowheads,
        "document_scroll_width": overflow["scrollWidth"],
        "document_client_width": overflow["clientWidth"],
        "horizontal_scroll": horizontal,
        "widest_overflowing_element": widest,
        "screenshot": {
            "path": shot.relative_to(_root).as_posix(),
            "bytes": len(image),
            "sha256": hashlib.sha256(image).hexdigest(),
        },
        "passed": (
            len(measured) == 3
            and all(d["visible"] for d in measured)
            and all(not d["clipped"] for d in measured)
            and all(not d["overlapping_labels"] for d in measured)
            and all(not d["zero_length_paths"] for d in measured)
            and all(d["elements"]["rect"] > 0 and d["elements"]["text"] > 0
                    for d in measured)
            and arrowheads["markers"] >= 3
            and arrowheads["paths_with_marker_end"] >= 10
            and not horizontal),
    }


def review_one(engine, name: str, base: str, channel: str | None,
               shots: Path) -> dict:
    launch = {"channel": channel} if channel else {}
    browser = engine.launch(**launch)
    version = browser.version
    record: dict = {"engine": name, "version": version,
                    "channel": channel or "playwright bundled build",
                    "checks": {}}
    try:
        context = browser.new_context(viewport=VIEWPORTS["wide"])
        page = context.new_page()
        record["checks"]["deep_link_keyboard"] = \
            check_deep_link_keyboard(page, base)
        record["checks"]["live_regions"] = check_live_regions(page, base)
        record["checks"]["hostile_ontology_text"] = \
            check_hostile_text(page, base)
        context.close()

        diagrams = {}
        for viewport in VIEWPORTS:
            context = browser.new_context(viewport=VIEWPORTS[viewport])
            page = context.new_page()
            diagrams[viewport] = check_diagrams(page, base, viewport,
                                                shots, name)
            context.close()
        record["checks"]["diagrams"] = diagrams
    finally:
        browser.close()

    def passed(node):
        if isinstance(node, dict):
            if "passed" in node:
                return bool(node["passed"]) and all(
                    passed(v) for k, v in node.items() if k != "passed")
            return all(passed(v) for v in node.values())
        return True

    record["passed"] = passed(record["checks"])
    return record


#: The build stamp, which every page carries and which changes on every
#: commit. Normalised out of the review digest for the same reason the
#: class index excludes provenance: a record committed alongside the
#: site it measures can never match a build of the commit it lands in,
#: so a digest including the stamp is stale the instant it is written.
STAMP = re.compile(r'(<code data-build="commit">)[0-9a-f]*(</code>)')


def normalise(path: Path) -> bytes:
    """A file's content with provenance removed.

    Two kinds carry it. Every page carries the build stamp, and the
    generated JSON carries `source_commit` -- in downloads.json, once at
    the top and once per module. Normalising only the pages left the
    digest still moving with every commit, which the first clone to
    rebuild it reported as a stale record.
    """
    data = path.read_bytes()
    if path.suffix == ".html":
        return STAMP.sub(r"\1STAMP\2",
                         data.decode("utf-8")).encode("utf-8")
    if path.suffix == ".json":
        def strip(node):
            if isinstance(node, dict):
                return {k: ("PROVENANCE" if k == "source_commit"
                            else strip(v)) for k, v in node.items()}
            if isinstance(node, list):
                return [strip(v) for v in node]
            return node
        try:
            loaded = json.loads(data.decode("utf-8"))
        except ValueError:
            return data
        return json.dumps(strip(loaded), sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
    return data


#: What a browser actually loads. The digest is scoped to these because
#: the archive's timestamp comes from the commit, so it changes on every
#: commit by design -- a freshness check including it would call the
#: record stale for a reason the review never observed, on a file no
#: browser fetches. The archive's integrity is Phase 5's and has its own
#: tests.
#: Named, not matched by suffix, because the set has to be exactly what
#: the checks below load. Matching *.html swept in downloads/index.html,
#: which publishes the bundle's checksum -- and the bundle's timestamp
#: comes from the commit, so that page changes on every commit and made
#: the record stale for a reason no browser check had observed.
REVIEWED_FILES = (
    "explore/index.html",
    "models/index.html",
    "assets/css/site.css",
    "assets/js/explorer.js",
    "assets/js/ranking.js",
    "data/class-index.json",
)


def reviewed_files(out: Path) -> list:
    """The files the checks fetch, in a fixed order.

    Missing is fatal rather than skipped: a digest over five of six files
    would be a perfectly stable number describing less than it claims.
    """
    found = []
    for relative in REVIEWED_FILES:
        path = out / relative
        if not path.is_file():
            raise SystemExit(
                "%s is not in the build, so the review would cover less "
                "than it records" % relative)
        found.append(path)
    return found


def tree_digest(out: Path) -> str:
    """What was reviewed, so a stale record is detectable.

    Content only, over the files a browser loads. A page differing solely
    in its build stamp is the same page as far as anything this review
    checked.
    """
    rows = []
    for path in reviewed_files(out):
        data = normalise(path)
        rows.append("%s %s" % (path.relative_to(out).as_posix(),
                               hashlib.sha256(data).hexdigest()))
    return hashlib.sha256(chr(10).join(rows).encode("utf-8")).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="config/browser-review.json")
    ap.add_argument("--site", default="_site")
    ap.add_argument("--shots", default="docs/site/browser-review",
                    help="where the reviewed screenshots are written")
    args = ap.parse_args(argv)

    from playwright.sync_api import sync_playwright

    site = Path(args.site)
    site = site if site.is_absolute() else _root / site
    if not (site / "explore/index.html").is_file():
        raise SystemExit("no built site at %s; run build_site.py first" % site)

    # Edge is required by the plan and is a distinct product with its own
    # release train, even though it shares Chromium's engine. Chromium and
    # Chrome were standing in for it, which is not the same as running it.
    shots = Path(args.shots)
    shots = shots if shots.is_absolute() else _root / shots

    engines = [("chromium", None), ("chrome", "chrome"),
               ("edge", "msedge"), ("firefox", None),
               ("playwright-webkit", None)]

    reviewed = []
    with serve(site) as base:
        with sync_playwright() as pw:
            for name, channel in engines:
                launcher = {"chromium": pw.chromium, "chrome": pw.chromium,
                            "edge": pw.chromium, "firefox": pw.firefox,
                            "playwright-webkit": pw.webkit}[name]
                print("  %s ..." % name, flush=True)
                try:
                    reviewed.append(
                        review_one(launcher, name, base, channel, shots))
                except Exception as error:                # noqa: BLE001
                    reviewed.append({"engine": name, "channel": channel,
                                     "error": repr(error)[:400],
                                     "passed": False})

    record = {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "reviewed_files_sha256": tree_digest(site),
        "reviewed_files": [p.relative_to(site).as_posix()
                           for p in reviewed_files(site)],
        "operating_system": platform.platform(),
        "deep_link_class": DEEP_LINK_CLASS,
        "viewports": VIEWPORTS,
        "screenshots_at": Path(args.shots).as_posix(),
        "browsers": reviewed,
        "not_covered": {
            "safari": ("not tested. This machine runs Windows, Safari has "
                       "had no Windows build since 2012, and Playwright's "
                       "WebKit is a different browser sharing an engine "
                       "lineage. It is recorded as playwright-webkit."),
            "screen_reader": ("not run. The live-region checks read the "
                              "accessibility tree, which is what a screen "
                              "reader consumes; whether NVDA, JAWS or "
                              "VoiceOver announce it at the right moment "
                              "is a listening test and remains open."),
        },
        "passed": all(b.get("passed") for b in reviewed),
    }

    out = Path(args.out)
    out = out if out.is_absolute() else _root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(json.dumps(record, indent=2, sort_keys=True,
                               ensure_ascii=False).encode("utf-8") + b"\n")

    print()
    for browser in reviewed:
        mark = "ok  " if browser.get("passed") else "FAIL"
        print("  %s %-18s %s" % (mark, browser["engine"],
                                 browser.get("version",
                                             browser.get("error", ""))[:60]))
    print()
    print("  wrote %s" % args.out)
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
