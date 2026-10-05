# SPDX-License-Identifier: Apache-2.0
"""The home page, where the site speaks in somebody's voice.

Every other page reports the ontology. This one also carries a statement
of why the work was done, written in the first person, about a larger
project that is not in this repository and that no test here can
measure. That is a different kind of content from anything else the
site publishes, and the contract in `site/content/CLAIM_SOURCES.md`
gives it its own kind: an owner statement, published as the owner's
and not as a finding.

What can be held is the frame around it. A first-person sentence has to
have a named speaker. The credit for the original ValueNet has to
travel with the claim to have refactored it. The two things the
statement is careful about -- that the larger system is designed never
to decide, and that it does not exist yet -- have to stay said. And the
parts of the page that are about this repository are held the way every
other page is: the classes it links to exist, the acronyms are glossed,
and no figure is written in by hand.

Whether the statement is what the owner means is not checked here and
could not be. It is theirs, and the public-content sign-off is where
they say so.
"""

from __future__ import annotations

import json
import re

import pytest

from marep import layout

REPO = layout.repository_root()
SRC = layout.component("site.source").resolve()
CONTENT = layout.component("site.content").resolve()
PAGE = (SRC / "index.html").read_text(encoding="utf-8")
MAIN = PAGE[PAGE.index("<main"):PAGE.index("</main>")]


def text_of(markup: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", markup).split())


def statement() -> str:
    """The attributed block, as markup."""
    start = MAIN.index('<div class="statement">')
    return MAIN[start:MAIN.index("</div>", start)]


# ---------------------------------------------------------- the statement


def test_the_statement_names_who_is_speaking():
    """The byline is the first thing in the block, not a credit below it:
    a reader should know whose "I" this is before they meet it."""
    block = statement()
    first = re.search(r"<p\b[^>]*>(.*?)</p>", block, flags=re.DOTALL)
    assert first and 'class="byline"' in first.group(0), (
        "the statement does not open with its byline")
    assert "Aaron Damiano" in text_of(first.group(1))


FIRST_PERSON = r"\b(?:I|[Mm]y|[Mm]ine|me|[Ww]e|[Oo]ur|us)\b"


def test_nothing_outside_the_statement_speaks_in_the_first_person():
    """The rest of the site is impersonal on purpose. An "I" that drifted
    out of the attributed block would be a personal claim with nobody's
    name on it."""
    assert re.search(FIRST_PERSON, text_of(statement())), (
        "the statement is no longer in the first person, so this test "
        "has nothing to tell apart")
    # The section, not only the block: its heading is in the first
    # person too, and the byline directly under it is what attributes it.
    start = MAIN.index('<section aria-labelledby="why">')
    section = MAIN[start:MAIN.index("</section>", start)]
    assert statement() in section
    outside = text_of(MAIN.replace(section, ""))
    stray = re.findall(r"[^.]*" + FIRST_PERSON + r"[^.]*\.", outside)
    assert not stray, stray


def original_authors() -> list[str]:
    """The published authorship of ValueNet, from the citation record."""
    text = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    start = text.index("type: conference-paper")
    end = text.find("\n  - type:", start)
    block = text[start:end if end > 0 else len(text)]
    block = block[block.index("authors:"):]
    names = re.findall(
        r"given-names:\s*(.+?)\s*\n\s*family-names:\s*(.+?)\s*\n", block)
    return ["%s %s" % pair for pair in names]


def test_the_original_authors_are_named_where_the_refactoring_is_claimed():
    """Read from CITATION.cff, so the page cannot credit a different set
    of people from the one the project tells readers to cite."""
    authors = original_authors()
    assert len(authors) >= 2, authors
    said = text_of(statement())
    for author in authors:
        assert author in said, (
            "the statement says ValueNet was refactored here without "
            "naming %s, who the citation record credits with it" % author)
    assert "it is not mine" in said


def test_the_statement_keeps_its_two_cautions():
    """The larger project is described here by its owner and measured by
    nobody. What keeps that honest is that the statement itself says the
    system is designed not to decide and does not exist yet. Losing
    either sentence in an edit would turn a statement of intent into a
    product claim."""
    said = text_of(statement())
    assert "never makes the moral decision" in said
    assert "there is no finished system yet" in said


# ------------------------------------------- the parts about this repository


def test_every_explorer_link_names_a_real_class(class_index):
    """The same check the models page has, for the same reason: a link
    to a class the index does not hold lands on an error state."""
    known = {record["id"] for record in class_index["classes"]}
    linked = sorted(set(re.findall(r'explore/\?class=([^"&]+)', PAGE)))
    assert len(linked) >= 3, linked
    missing = [i for i in linked if i not in known]
    assert not missing, missing
    assert "core:NoSuchClass" not in known


#: Each acronym with the words it stands for. The product name is not a
#: use of the acronym: nobody can gloss a name before saying it.
GLOSSED = (("BFO", "Basic Formal Ontology"),
           ("CCO", "Common Core Ontologies"))


def first_unglossed(text: str) -> list[str]:
    """Acronyms that appear before the sentence that says what they are."""
    plain = text.replace("BFO-Aligned ValueNet", "the suite")
    late = []
    for acronym, expansion in GLOSSED:
        used = re.search(r"\b%s\b" % acronym, plain)
        if not used:
            continue
        sentence_end = plain.find(".", used.start())
        glossed = plain.find(expansion)
        if glossed < 0 or glossed > sentence_end:
            late.append(acronym)
    return late


def test_no_acronym_is_used_before_it_is_glossed():
    """The outline's rule: readable by someone who has never heard of BFO."""
    assert first_unglossed(text_of(MAIN)) == []


def test_an_unglossed_acronym_would_be_caught():
    without = text_of(MAIN).replace("Basic Formal Ontology", "foundation")
    assert first_unglossed(without) == ["BFO"]


def test_the_quality_statement_is_the_curated_one():
    """`site.json` holds the sentence and the tone it has to keep. Bound,
    because the page and the record of what the page says had already
    drifted apart once, on the three points above this one."""
    site = json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))
    assert site["evidence_statement"]["body"] in text_of(MAIN)


#: Digits a curated page may carry: none. Derivable figures come from the
#: build, and the pages that show them are generated.
def figures(markup: str) -> list[str]:
    return re.findall(r"\S*\d\S*", text_of(markup))


def test_no_figure_is_written_into_the_home_page():
    """"No counts in curated copy": a number typed here is a number that
    stops being true the next time the ontology changes."""
    assert figures(MAIN) == []
    assert figures("<p>All 186 classes</p>") == ["186"]


def test_the_only_figures_on_the_documentation_page_are_its_own_order():
    """Its section numbers, and the name of one standard."""
    page = (SRC / "documentation/index.html").read_text(encoding="utf-8")
    main = page[page.index("<main"):page.index("</main>")]
    allowed = re.compile(r"^(?:\d\.|2\.0)$")
    stray = [f for f in figures(main) if not allowed.match(f)]
    assert not stray, stray
