# SPDX-License-Identifier: Apache-2.0
"""Accessibility properties that can be decided from the files that ship.

Contrast is arithmetic on the declared colour tokens, so it is computed
here rather than eyeballed or asserted in a review document that nothing
re-reads. The keyboard properties checked are the structural ones: a skip
link with a target that can actually receive focus, no tab stop on
something that does nothing when focused, no inline handler.

What this file cannot do is render. Focus order under a real layout,
screen-reader announcement of the live regions, and ontology text drawn
into a live page all need a browser, and remain owed to the browser and
accessibility gate. Nothing here should be read as standing in for that.
"""

from __future__ import annotations

import glob
import re

from marep import layout

REPO = layout.repository_root()
SRC = layout.component("site.source").resolve()

CSS = (SRC / "assets/css/site.css").read_text(encoding="utf-8")
EXPLORER_JS = (SRC / "assets/js/explorer.js").read_text(encoding="utf-8")
PAGES = sorted(glob.glob(str(SRC / "**/index.html"), recursive=True))


# ---------------------------------------------------------------- colour


def _relative_luminance(colour):
    """WCAG 2.x relative luminance."""
    raw = colour.lstrip("#")
    channels = [int(raw[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
              for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a, b):
    high, low = sorted((_relative_luminance(a), _relative_luminance(b)),
                       reverse=True)
    return (high + 0.05) / (low + 0.05)


def _tokens(selector):
    """The custom properties declared in one rule block."""
    start = CSS.index("{", CSS.index(selector)) + 1
    body = CSS[start:CSS.index("}", start)]
    found = dict(re.findall(r"--([a-z-]+):\s*(#[0-9a-fA-F]{6})", body))
    assert found, "no colour tokens under " + selector
    return found


LIGHT = _tokens(":root {")
#: The dark block redefines a subset, so it is read as an overlay. Reading
#: it as a whole palette would silently drop any token the two share.
DARK = dict(LIGHT, **_tokens(':root:not([data-theme="light"])'))

#: Foreground/background pairs that carry text. 4.5:1 is WCAG AA for body
#: sizes, which is every one of these -- none is large-scale text.
TEXT_PAIRS = [
    ("body text on the page", "ink", "bg"),
    ("body text on a card", "ink", "surface"),
    ("result metadata and definitions", "ink-soft", "bg"),
    ("muted text on a card", "ink-soft", "surface"),
    ("muted text in a notice", "ink-soft", "notice-bg"),
    ("the skip link", "accent-ink", "accent"),
    # --focus began as a ring colour and is now also the bypass link's
    # text, which asks 4.5 of it rather than 3.
    ("the bypass link", "focus", "bg"),
]

#: Boundaries that identify a control. 1.4.11 asks 3:1 of these. The
#: separators drawn with --rule are decorative and exempt, which is why
#: the controls stopped using it.
NON_TEXT_PAIRS = [
    ("the edge of a text input or button", "field-edge", "surface"),
    ("the edge of a control on the page", "field-edge", "bg"),
    ("the focus ring", "focus", "bg"),
    ("the focus ring on a card", "focus", "surface"),
]


def test_every_text_pair_meets_wcag_aa():
    poor = []
    for theme, palette in (("light", LIGHT), ("dark", DARK)):
        for what, fg, bg in TEXT_PAIRS:
            ratio = contrast(palette[fg], palette[bg])
            if ratio < 4.5:
                poor.append("%s/%s: %s is %.2f:1, needs 4.5"
                            % (theme, what, fg, ratio))
    assert not poor, poor


def test_every_control_boundary_meets_wcag_non_text_contrast():
    """The failure this test was written for: the controls drew their
    borders with --rule, which is 1.43:1 against the surface behind them.
    A sighted user could not see where the search field was."""
    poor = []
    for theme, palette in (("light", LIGHT), ("dark", DARK)):
        for what, fg, bg in NON_TEXT_PAIRS:
            ratio = contrast(palette[fg], palette[bg])
            if ratio < 3.0:
                poor.append("%s/%s: %s is %.2f:1, needs 3.0"
                            % (theme, what, fg, ratio))
    assert not poor, poor


def test_the_decorative_rule_is_not_used_for_a_control_edge():
    """--rule is exempt because it separates rather than identifies. That
    exemption only holds while no control is drawn with it."""
    for block in re.findall(r"\.(?:explorer-controls|copy)[^{]*\{[^}]*\}",
                            CSS):
        assert "var(--rule)" not in block, block[:120]


# -------------------------------------------------------------- keyboard


def test_every_page_has_a_skip_link_that_can_receive_focus():
    """A skip link pointing at a non-focusable element scrolls the page
    and leaves focus where it was, so the next Tab returns to the
    navigation the user was trying to skip."""
    assert PAGES, "no pages found"
    broken = []
    for path in PAGES:
        html = open(path, encoding="utf-8").read()
        if 'class="skip" href="#main"' not in html:
            broken.append(path + ": no skip link")
        elif '<main id="main" tabindex="-1">' not in html:
            broken.append(path + ": #main cannot take focus")
    assert not broken, broken


def test_a_deep_linked_class_can_be_reached_without_crossing_the_results():
    """The defect: arriving on a shared ?class= URL rendered the detail
    after as many as 187 result links, focused nothing, and offered no way
    past. Following a result link moved focus; arriving at one did not,
    and arriving at one is what a shared URL is.

    Focus is not moved on load -- that would wrench it from someone who
    came to read -- so the bypass has to be offered instead, which means a
    link, and it only helps if it comes before the list.
    """
    html = (SRC / "explore/index.html").read_text(encoding="utf-8")
    assert 'id="jump-wrap"' in html, "no bypass to the detail pane"

    # A button, not a link. WebKit's default keyboard model puts no anchor
    # in the tab order, so the bypass was unreachable by Tab there while
    # working in Chromium, Chrome and Firefox. It also moves focus rather
    # than navigating, which is a button's job; it had been a link with
    # preventDefault, which is the same thing wearing the wrong element.
    assert '<button class="jump"' in html, (
        "the bypass is not a button; as an anchor it is not a tab stop in "
        "WebKit")
    assert 'type="button"' in html
    assert html.index('id="jump-wrap"') < html.index('id="results"'), (
        "the bypass comes after the result list, so it bypasses nothing")

    #: Hidden in the markup so it is not a tab stop with nothing selected.
    wrap = html[html.index('id="jump-wrap"'):]
    assert "hidden" in wrap[:wrap.index(">")], (
        "the bypass ships visible, so it is a tab stop that leads nowhere")

    js = code_only(EXPLORER_JS)
    assert js.count("jump-wrap") == 2, (
        "the bypass should be shown and hidden, once each")
    assert 'hidden = true' in js and 'hidden = false' in js
    jump = js[js.index('$("jump").addEventListener'):]
    assert '$("detail").focus()' in jump[:400], (
        "activating the bypass does not move focus")


def test_no_page_carries_an_inline_event_handler():
    offenders = []
    for path in PAGES:
        html = open(path, encoding="utf-8").read()
        for match in re.findall(r"\son[a-z]+\s*=", html):
            offenders.append(path + ": " + match.strip())
    assert not offenders, offenders


def code_only(source):
    """Comments removed.

    A substring scan cannot tell code from prose about code. Written
    because the first version of the test below failed on the comment
    explaining why the tabindex was taken away -- the same shape as the
    markup guard in test_explorer.py, which failed for the same reason.
    """
    return re.sub(r"(?m)//.*$", "", re.sub(r"/\*.*?\*/", "", source,
                                           flags=re.S))


def test_the_iri_display_is_not_a_tab_stop():
    """It was focusable, which spent a Tab per IRI on an element that
    does nothing when focused -- focus does not select its text. The copy
    button beside it is the control, and it is in the tab order."""
    row = EXPLORER_JS[EXPLORER_JS.index("function iriRow"):]
    row = code_only(row[:row.index("function renderDetail")])
    assert "tabindex" not in row, (
        "iriRow puts a tab stop on non-interactive text")
    assert 'el("button"' in row, "the IRI row offers no real control"


# ------------------------------------------------------------ responsive


def test_no_control_is_pinned_wider_than_its_container():
    """min-width beats max-width when the two disagree, so
    `min-width: 20rem; max-width: 100%` held the search input at 320px
    inside a 280px column and scrolled the entire page sideways.

    The rule is narrow on purpose: min-width on a control is what caused
    this, and a container that needs one is a different question.
    """
    for block in re.findall(r"\.explorer-controls[^{]*\{[^}]*\}", CSS):
        if "min-width" not in block:
            continue
        assert "min-width: 0" in block, (
            "a control declares a floor width, which no max-width can "
            "override: " + " ".join(block.split())[:160])


def test_the_two_column_layout_is_the_exception_not_the_default():
    """Single column first, so a narrow viewport is the case that needs
    no media query to be correct."""
    panes = re.search(r"\.explorer-panes\s*\{([^}]*)\}", CSS)
    assert panes, "no .explorer-panes rule"
    assert "grid-template-columns" not in panes.group(1), (
        "two columns are the unconditional default")
    assert "grid-template-columns" in CSS[panes.end():], (
        "no wide-viewport rule adds the second column")


def test_wide_content_scrolls_inside_itself():
    """Long IRIs are the widest thing the explorer renders."""
    assert "word-break: break-all" in CSS
