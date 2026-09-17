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

Three items cannot be checked from the repository, and the register marks each
one *unchecked* with its reason. That marking is itself checked, so the excuse
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
    found = rows("Open")
    assert len(found) >= 5, "the register is nearly empty; these tests would pass on nothing"
    return found


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


def test_the_uncovered_trigger_count_is_the_one_measured(open_items, coverage):
    assert figure(open_items, "OI-6") == len(
        coverage["source"]["fragment_without_a_class"])


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
