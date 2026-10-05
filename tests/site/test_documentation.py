# SPDX-License-Identifier: Apache-2.0
"""The documentation page is a reading path, and a path has to arrive.

Every other page on the site is generated from the ontology or checked
against it. This one is curated: a list of documents somebody chose, in
an order somebody chose, each with a sentence somebody wrote. Nothing
about a curated list fails when the thing it lists moves, which is how
it came to be the last page built -- it sat as a placeholder reading
"Not built yet" through a deployment.

So the parts of it that can be held are held here. Whether each link
finds a file is `test_public_links.py`'s, because that is a property of
the built artifact and of every page. What is specific to this page is
its shape: that it is no longer a placeholder, that it covers what the
outline says it covers, that every stop on the path says what it is, and
that it makes none of the claims the site has decided not to make.

The sentences themselves are not checked. Whether a description is a
fair one is the owner's to say, and the public-content sign-off is where
they say it.
"""

from __future__ import annotations

import html.parser
import importlib.util
import re

import pytest

from marep import layout

REPO = layout.repository_root()
SRC = layout.component("site.source").resolve()
PAGE = (SRC / "documentation/index.html").read_text(encoding="utf-8")
OUTLINES = (layout.component("site.content").resolve()
            / "OUTLINES.md").read_text(encoding="utf-8")


def _load(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = _load("documentation_check_site", "tools/site/check_site.py")
BLOB = CHECK.repository_url() + "/blob/" + CHECK.PUBLISHED_REF + "/"

#: What the outline promises, as the documents that keep the promise.
#: Named by path because that is what a reader is sent to: a stop that
#: survives as a heading with its link gone is not a stop.
PROMISED = {
    "the BFO alignment rationale":
        "docs/bfo/guides/BFOizing ValueNet.md",
    "the annotation guide":
        "docs/bfo/guides/annotationGuide.md",
    "the competency questions":
        "ontology/bfo/extensions/moral-epistemics/"
        "valuenet-moral-epistemics-CQ.md",
    "the testing framework":
        "docs/bfo/guides/TestingFramework.md",
    "provenance":
        "docs/architecture/PROVENANCE.md",
    "the original ValueNet overview":
        "docs/original-valuenet/README.md",
    "the evidence: the semantic baseline":
        "config/semantic-baseline.json",
    "the evidence: the remediation record":
        "config/remediation-record.json",
    "the decision records":
        "docs/bfo/remediation/DECISION_RECORDS.md",
    "the definition standard":
        "docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_RULES_2.0.md",
    "the formal review":
        "docs/bfo/reviews/FORMAL_REVIEW_2026-09-16.md",
    "the response to it":
        "docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_RESPONSE.md",
    "the reviewer's sign-off":
        "docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF.md",
    "the reviewer's second sign-off":
        "docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF_2.md",
    "the register of open items":
        "docs/bfo/OPEN_ITEMS.md",
}


class ReadingPath(html.parser.HTMLParser):
    """The page's stops: each `dt` with the link in it and the `dd` after.

    Parsed rather than matched, because the one thing a regular
    expression over this markup cannot tell is which description belongs
    to which link.
    """

    def __init__(self):
        super().__init__()
        self.stops: list[dict] = []
        self.sections: list[str] = []
        self._open: str | None = None
        self._in_main = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "main":
            self._in_main = True
        if not self._in_main:
            return
        if tag == "h2":
            self.sections.append(attrs.get("id") or "")
        elif tag == "dt":
            self.stops.append({"href": None, "label": "", "says": ""})
            self._open = "label"
        elif tag == "dd":
            self._open = "says"
        elif tag == "a" and self._open == "label" and self.stops:
            self.stops[-1]["href"] = attrs.get("href")

    def handle_endtag(self, tag):
        if tag == "main":
            self._in_main = False
        if tag in ("dt", "dd"):
            self._open = None

    def handle_data(self, data):
        if self._open and self.stops:
            self.stops[-1][self._open] += data


@pytest.fixture(scope="module")
def path():
    parser = ReadingPath()
    parser.feed(PAGE)
    for stop in parser.stops:
        stop["label"] = " ".join(stop["label"].split())
        stop["says"] = " ".join(stop["says"].split())
    assert len(parser.stops) >= 15, (
        "the page lists %d document(s); these tests would pass on nearly "
        "nothing" % len(parser.stops))
    return parser


def linked_paths(markup: str) -> set[str]:
    """Repository files the markup links to, as repository paths."""
    from urllib.parse import unquote
    return {unquote(href[len(BLOB):])
            for href in re.findall(r'href="([^"]+)"', markup)
            if href.startswith(BLOB)}


def test_the_page_is_no_longer_a_placeholder():
    """It shipped as one. The words are checked because a page can be
    filled in and still carry the apology above the content."""
    for leftover in ("Not built yet", "Phase 2 shell", 'class="placeholder"',
                     "arrive with the content build"):
        assert leftover not in PAGE, leftover


def test_the_path_covers_what_the_outline_promises():
    """Both directions of the same promise.

    The page must link every document the outline names, and the outline
    must name them: a test that pinned the list here and nowhere else
    would let the contract say one thing while the page did another.
    """
    linked = linked_paths(PAGE)
    missing = {what: target for what, target in PROMISED.items()
               if target not in linked}
    assert not missing, missing

    start = OUTLINES.index("## Documentation")
    end = OUTLINES.find("\n## ", start + 1)
    outline = OUTLINES[start:end if end > 0 else len(OUTLINES)]
    unnamed = {what: target for what, target in PROMISED.items()
               if target.rsplit("/", 1)[-1] not in outline}
    assert not unnamed, (
        "the page is required to link these, but the outline's "
        "Documentation section does not name them: %s" % unnamed)


def test_a_missing_stop_would_be_caught():
    """Guards the check above against a set comparison that cannot fail."""
    without = PAGE.replace("docs/bfo/OPEN_ITEMS.md", "docs/bfo/ELSEWHERE.md")
    assert without != PAGE, "the mutation did not apply"
    assert PROMISED["the register of open items"] not in linked_paths(without)


def test_every_stop_links_somewhere_and_says_what_it_is(path):
    """A title alone is an index. The description is what makes it a
    path: it is how a reader decides whether to follow the link."""
    for stop in path.stops:
        assert stop["href"], "%r is listed without a link" % stop["label"]
        assert stop["label"], stop
        assert len(stop["says"].split()) >= 6, (
            "%r has no description worth the name: %r"
            % (stop["label"], stop["says"]))


def test_no_document_is_listed_twice(path):
    hrefs = [stop["href"] for stop in path.stops]
    repeated = sorted({h for h in hrefs if hrefs.count(h) > 1})
    assert not repeated, repeated


def test_every_section_can_be_linked_to(path):
    """The home page sends readers to three of these by fragment, and a
    heading with no id is a heading nobody can be sent to."""
    assert len(path.sections) >= 6, path.sections
    assert all(path.sections), (
        "a section heading has no id: %s" % path.sections)
    assert len(set(path.sections)) == len(path.sections), path.sections

    home = (SRC / "index.html").read_text(encoding="utf-8")
    wanted = set(re.findall(r'href="documentation/#([^"]+)"', home))
    assert wanted, "the home page no longer links into this page"
    assert wanted <= set(path.sections), sorted(wanted - set(path.sections))


def test_the_sections_are_numbered_in_the_order_they_appear():
    """The numbers are the reading order, so they have to be the order."""
    numbers = [int(n) for n in re.findall(r"<h2 id=\"[a-z-]+\">(\d+)\. ", PAGE)]
    assert numbers == list(range(1, len(numbers) + 1)), numbers
    assert len(numbers) == len(re.findall(r"<h2\b", PAGE)), (
        "a section is not numbered")


def test_the_page_says_what_the_evidence_does_not_show():
    """A review, its sign-offs and a row of evidence records, listed one
    after another, read as a verdict unless the page says they are not."""
    text = " ".join(re.sub(r"<[^>]+>", " ", PAGE).split())
    assert "It does not show that the ontology is correct" in text
    assert "A sign-off covers what had been decided when it was given" in text


#: The claims CLAIM_SOURCES.md says the site must never make, as the
#: words that would make them.
NEVER = (
    r"\bis (?:fully )?(?:verified|validated|correct)\b",
    r"\bhas been (?:verified|validated|certified)\b",
    r"\bindependent(?:ly)? (?:review|verif|valid)",
    r"\bpeer[- ]reviewed\b",
    r"\bproves? (?:that )?the ontology\b",
)

#: Both pages say the claim in order to deny it, and a search for the
#: words alone fails on exactly the sentences that are doing the right
#: thing. So a sentence that denies is let through, and the test below
#: checks that the denial is what let it through.
DENIAL = r"\b(?:not|none|never|no)\b"


def verdicts(text: str) -> list[str]:
    """Sentences that make one of the claims and do not deny it."""
    found = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if re.search(DENIAL, sentence, flags=re.IGNORECASE):
            continue
        if any(re.search(pattern, sentence, flags=re.IGNORECASE)
               for pattern in NEVER):
            found.append(sentence)
    return found


def prose(name: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ",
                           (SRC / name).read_text(encoding="utf-8")).split())


@pytest.mark.parametrize("name", ["documentation/index.html", "index.html"])
def test_neither_curated_page_upgrades_the_evidence_into_a_verdict(name):
    assert not verdicts(prose(name)), verdicts(prose(name))


def test_the_verdict_check_can_fire_and_spares_only_a_denial():
    """Each pattern on a sentence of the kind it exists to refuse, and
    then the two sentences the pages really carry, which name the claim
    and must not be mistaken for making it."""
    samples = ("The ontology is validated.",
               "It has been verified against BFO.",
               "An independent review confirmed it.",
               "The suite is peer-reviewed.",
               "This proves the ontology is sound.")
    for pattern, sample in zip(NEVER, samples):
        assert re.search(pattern, sample, flags=re.IGNORECASE), pattern
        assert verdicts(sample) == [sample], sample

    for name, denial in (
            ("index.html",
             "None of this is a claim that the ontology is correct."),
            ("documentation/index.html",
             "It does not show that the ontology is correct, complete, or "
             "validated against an external standard.")):
        assert denial in prose(name), (name, denial)
        assert any(re.search(p, denial, flags=re.IGNORECASE) for p in NEVER), (
            "the denial no longer names the claim, so sparing it proves "
            "nothing")
        assert verdicts(denial) == []
        # The same words with the denial taken out are the claim.
        assert verdicts(denial.replace("None of this is a claim that t", "T")
                        .replace("It does not show that t", "T")), denial
