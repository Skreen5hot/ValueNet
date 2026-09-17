# SPDX-License-Identifier: Apache-2.0
"""The open-items register describes the repository as it is now.

`docs/bfo/OPEN_ITEMS.md` is the one place that says what is unfinished or
deliberately left. A register nobody checks becomes a list of things that were
true once: the item somebody fixed stays open on the page, and the figure that
moved keeps its old value. This repository has found that shape of defect
repeatedly, most recently in a decision document whose class counts had drifted.

So the register is re-derived here, not read. Every path it names must exist,
every decision it names must exist and still carry its reopen condition, and
every figure in it must equal what the tools measure now. An item that has been
fixed fails these tests until it moves to the closed log; a figure that moves
fails them until its row is updated.

One item cannot be checked from the repository, and the register marks it
*unchecked* with its reason. That marking is itself checked, so the excuse
cannot spread quietly.
"""

from __future__ import annotations

import importlib.util
import re

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import OWL, RDF, RDFS  # noqa: E402

from marep.layout import bfo_artifact, repository_root  # noqa: E402

ROOT = repository_root()
REGISTER = ROOT / "docs/bfo/OPEN_ITEMS.md"
DECISIONS = ROOT / "docs/bfo/remediation/DECISION_RECORDS.md"
PROPOSALS = ROOT / "docs/bfo/remediation/OPEN_ISSUES_PROPOSALS_2026-09-16.md"

#: Items the register may leave unchecked, each because the repository cannot
#: see the thing it is about. Anything else must be derivable here.
UNCHECKABLE = {"OI-3"}

#: Every section that holds items, in the order the register presents them.
#: Named so that a section quietly disappearing, taking its items with it,
#: fails rather than shrinking the backlog.
SECTIONS = ("P0 — next", "P1 — soon", "P2 — when convenient", "Operational",
            "Accepted and deferred — not work")


def rows(section: str) -> list[list[str]]:
    text = REGISTER.read_text(encoding="utf-8")
    start = text.index("## " + section)
    end = text.find("\n## ", start + 1)
    body = text[start:end if end > 0 else len(text)]
    return [[cell.strip() for cell in line.strip("|").split(" | ")]
            for line in body.splitlines()
            if line.startswith("| ") and not line.startswith("| id ")]


@pytest.fixture(scope="module")
def open_items():
    found = [row for section in SECTIONS for row in rows(section)]
    assert len(found) >= 5, "the register is nearly empty; these tests would pass on nothing"
    return found


def test_every_section_is_present_and_holds_something():
    for section in SECTIONS:
        assert rows(section), section
    assert rows("Closed"), "the closed log is empty"


def test_the_register_has_one_row_per_item_and_no_duplicate_ids(open_items):
    ids = [row[0] for row in open_items]
    assert ids == sorted(set(ids), key=ids.index), ids
    for row in open_items:
        assert len(row) == 4, row
        assert all(cell for cell in row), row


def test_every_path_the_register_names_exists(open_items):
    """A register pointing at a file that has moved sends its reader nowhere."""
    seen = 0
    for row in open_items:
        for path in re.findall(r"`([\w./-]+\.\w+|[\w./-]+/)`", row[2]):
            assert (ROOT / path).exists(), "%s: %s" % (row[0], path)
            seen += 1
    assert seen >= 5, "no paths were checked, so this test proved nothing"


def test_every_decision_the_register_names_can_be_reopened(open_items):
    """The register leans on the decision records for reopen conditions. If a
    decision were renumbered or lost its condition, that leaning would break."""
    text = REGISTER.read_text(encoding="utf-8")
    decisions = DECISIONS.read_text(encoding="utf-8")
    named = sorted(set(re.findall(r"\bD-0\d\d\b", text)))
    assert named, "the register names no decision"
    for decision in named:
        start = decisions.find("## " + decision + " ")
        assert start > 0, decision
        end = decisions.find("\n## ", start + 1)
        assert "### Reopen when" in decisions[start:end if end > 0 else len(decisions)], decision


def test_the_unchecked_items_say_why(open_items):
    marked = {row[0] for row in open_items if "*Unchecked:*" in row[1]}
    assert marked == UNCHECKABLE, (
        "an item became unchecked, or stopped being: %s" % (marked ^ UNCHECKABLE))


# ----------------------------------------------------- the figures, re-derived


@pytest.fixture(scope="module")
def coverage():
    spec = importlib.util.spec_from_file_location(
        "folk_coverage", ROOT / "tools/bfo/folk_coverage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.measure()


def figure(open_items, item_id: str) -> int:
    row = next(row for row in open_items if row[0] == item_id)
    return int(re.search(r"\b(\d+)\b", row[1]).group(1))


def test_the_dangling_back_link_count_is_the_one_measured(open_items, coverage):
    assert figure(open_items, "OI-5") == len(coverage["dangling_see_also"])


def test_the_excluded_values_that_still_carry_a_lexicon_are_the_ones_listed(
        open_items, coverage):
    """OI-14 names them, because whoever decides the pipeline question needs to
    see which values it is about. Listed and measured must be the same set."""
    import glob
    import os

    def norm(text):
        return re.sub(r"[^a-z0-9]", "", text.lower())

    row = next(row for row in open_items if row[0] == "OI-14")
    lexicons = {norm(os.path.basename(path)[len("folk_"):-len(".ttl")])
                for path in glob.glob(str(ROOT / "ThatsAllFolks/folk_*.ttl"))}
    measured = sorted(value for value in coverage["coverage"]["excluded"]
                      if norm(value) in lexicons)
    listed = sorted(name.strip() for name in row[1].rsplit(":", 1)[-1].split(","))
    assert listed == measured, (
        "OI-14 lists %s; the values excluded by D-014 that still carry a "
        "trigger lexicon are %s" % (listed, measured))


def test_the_invariant_that_closed_oi6_is_pinned(open_items):
    """OI-6 closed because the invariant it was written against was replaced,
    not because anyone measured differently. The replacement has to be held
    somewhere, or the closure is a claim about one afternoon."""
    closed = {row[0]: row[2] for row in rows("Closed")}
    assert "OI-6" in closed, "OI-6 left the closed log"
    test_name = "test_every_value_with_a_trigger_lexicon_is_reachable_or_excluded"
    assert test_name in closed["OI-6"], "the closed entry names no test"
    coverage_test = (ROOT / "tests/bfo/test_folk_coverage.py").read_text(encoding="utf-8")
    assert "def %s(" % test_name in coverage_test, (
        "the test the closed entry names does not exist")


def test_the_modules_still_declare_the_version_the_register_names(open_items):
    """OI-13 is an item only while every module still says 1.0."""
    from marep.layout import bfo_artifact
    for name in ("valuenet-core.ttl", "valuenet-folk.ttl",
                 "valuenet-schwartz-values.ttl"):
        text = bfo_artifact(name).read_text(encoding="utf-8")
        assert "/bfo/1.0/" in text, "%s no longer declares 1.0; close OI-13" % name


def test_the_measure_that_miscounts_still_miscounts(open_items):
    """OI-1 is only an item while the wording and the behaviour disagree."""
    tool = (ROOT / "tools/marep/build_semantic_baseline.py").read_text(encoding="utf-8")
    assert "bfo_layer_classes" in tool
    assert re.search(r"named classes in the [Hh]ermi[Tt] scope", tool), (
        "the definition no longer says 'named'; close OI-1 or reword it")


def test_the_dated_corpus_counts_are_still_in_the_competency_document(open_items):
    text = (ROOT / "ontology/bfo/extensions/moral-epistemics"
                   "/valuenet-moral-epistemics-CQ.md").read_text(encoding="utf-8")
    assert re.search(r"[\d,]+ triples on \d{4}-\d{2}-\d{2}", text), (
        "the dated counts are gone; close OI-2")


def test_the_archive_is_still_the_one_thing_left_unremediated(open_items):
    import json
    record = json.loads((ROOT / "config/remediation-record.json").read_text(encoding="utf-8"))
    assert record["not_remediated"]["archive"]["path"].endswith(".zip")


def test_the_schwartz_placements_that_differ_are_the_ones_listed(open_items):
    """OI-8 names two classes whose Schwartz parent differs from the corpus's
    own placement. Re-derived, so fixing one, or a third appearing, fails here.

    A corpus placement that is merely coarser is not a disagreement: the corpus
    puts Generosity under Self-Transcendence, and Benevolence, its parent here,
    is a Self-Transcendence value.
    """
    ODP = "http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#"
    BHV = "https://w3id.org/spice/SON/SchwartzValues#"
    SCHWARTZ = "https://fandaws.com/ontology/bfo/valuenet-schwartz-values#"
    FOLK = "https://fandaws.com/ontology/bfo/valuenet-folk#"

    def norm(text: str) -> str:
        return re.sub(r"[^a-z0-9]", "", text.lower())

    corpus = Graph().parse(ROOT / "ThatsAllFolks/folk.ttl", format="turtle")
    folk = Graph().parse(bfo_artifact("valuenet-folk.ttl"), format="turtle")

    def corpus_ancestors(value: URIRef) -> set:
        """The value's Schwartz ancestors in the corpus's own hierarchy,
        itself included."""
        seen, pending = {str(value)}, [value]
        while pending:
            for parent in corpus.objects(pending.pop(), RDFS.subClassOf):
                if isinstance(parent, URIRef) and str(parent) not in seen:
                    seen.add(str(parent))
                    pending.append(parent)
        return {norm(p[len(BHV):]) for p in seen if p.startswith(BHV)}

    differing = set()
    for cls in folk.subjects(RDF.type, OWL.Class):
        name = str(cls)[len(FOLK):]
        here = [str(p)[len(SCHWARTZ):].replace("Disposition", "")
                for p in folk.objects(cls, RDFS.subClassOf)
                if str(p).startswith(SCHWARTZ)]
        if not here:
            continue
        placed = [str(o)[len(BHV):] for o
                  in corpus.objects(URIRef(ODP + name.replace("Disposition", "")),
                                    RDFS.subClassOf)
                  if str(o).startswith(BHV)]
        if not placed:
            continue
        # Comparable either way is agreement: the corpus placing a value under
        # a broader Schwartz value than this module does is coarser, not
        # contrary. Only placements neither of which subsumes the other differ.
        mine = corpus_ancestors(URIRef(BHV + here[0]))
        theirs = set()
        for value in placed:
            theirs |= corpus_ancestors(URIRef(BHV + value))
        if not ({norm(p) for p in placed} & mine or norm(here[0]) in theirs):
            differing.add(name)

    listed = {name for name in re.findall(r"`(\w+Disposition)`",
                                          next(row[1] for row in open_items
                                               if row[0] == "OI-8"))}
    assert differing == listed, (
        "the classes whose Schwartz parent differs from the corpus are %s; "
        "OI-8 lists %s" % (sorted(differing), sorted(listed)))


def test_the_dated_proposals_say_the_register_supersedes_them(open_items):
    """Two documents describing the same open work drift apart. The old one
    has to point at the new one, or a reader can land on the stale half."""
    assert "docs/bfo/OPEN_ITEMS.md" in PROPOSALS.read_text(encoding="utf-8"), (
        "the dated proposals do not point at the register that supersedes them")
