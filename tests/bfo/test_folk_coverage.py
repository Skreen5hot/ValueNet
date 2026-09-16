# SPDX-License-Identifier: Apache-2.0
"""Does the BFO folk module carry the folk corpus, and does the tool know?

The occasion: somebody demonstrating the site searched for "frugal" and found
nothing. `folk:Frugality` is in ThatsAllFolks/folk.ttl and in the generated
alignment view; it is not in ontology/bfo/core/valuenet-folk.ttl, and the site
class index is built from the BFO modules. Nothing had ever compared the two,
while `docs/bfo/guides/BFOizing ValueNet.md` described the result as
"comprehensive in its coverage".

Two halves here, and the second is the one that makes the first mean anything.
The synthetic cases exercise each matching rule directly, because on the real
corpus every pairing comes from `rdfs:seeAlso` alone -- `altLabel` and `label`
fire on nothing, and a rule that never fires is indistinguishable from a rule
that does not work.
"""

import importlib.util
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph  # noqa: E402

from marep.layout import repository_root  # noqa: E402

ROOT = repository_root()

ODP = "http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#"
W3ID = "https://w3id.org/valuenet/folk#"
BFO = "https://fandaws.com/ontology/bfo/valuenet-folk#"


def load_tool():
    """Import the tool by path, so the file that ships is the file tested."""
    spec = importlib.util.spec_from_file_location(
        "folk_coverage", ROOT / "tools/bfo/folk_coverage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def tool():
    return load_tool()


@pytest.fixture(scope="module")
def live(tool):
    """Measured once. Parses folk.ttl and the BFO layer."""
    return tool.measure()


def source_graph(*names):
    graph = Graph()
    turtle = "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
    for name in names:
        turtle += "<%s%s> a owl:Class .\n" % (ODP, name)
    graph.parse(data=turtle, format="turtle")
    return graph


def layer_graph(body):
    graph = Graph()
    graph.parse(data=(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n" + body),
        format="turtle")
    return graph


# ------------------------------------------------- each rule, on its own


def test_the_see_also_rule_pairs_a_class_with_a_value(tool, tmp_path):
    record = tool.measure(
        source_graph("Kindness"), tmp_path,
        layer_graph('<%sKindnessDisposition> a owl:Class ; '
                    'rdfs:seeAlso <%sKindnessDisposition> .' % (BFO, W3ID)))
    assert record["coverage"]["folk_values_covered"] == 1
    assert record["bfo_layer"]["matched_by_rule"] == {"seeAlso": 1}


def test_the_alt_label_rule_pairs_when_there_is_no_back_link(tool, tmp_path):
    """Fires on nothing in the real corpus. Without this it would be a
    branch nobody has executed, sitting in a tool whose whole subject is
    checks that do not fire."""
    record = tool.measure(
        source_graph("Kindness"), tmp_path,
        layer_graph('<%sKindnessDisposition> a owl:Class ; '
                    'skos:altLabel "Kindness"@en .' % BFO))
    assert record["coverage"]["folk_values_covered"] == 1
    assert record["bfo_layer"]["matched_by_rule"] == {"altLabel": 1}


def test_the_label_rule_strips_the_disposition_suffix(tool, tmp_path):
    record = tool.measure(
        source_graph("Kindness"), tmp_path,
        layer_graph('<%sKindnessDisposition> a owl:Class ; '
                    'rdfs:label "Kindness Disposition"@en .' % BFO))
    assert record["coverage"]["folk_values_covered"] == 1
    assert record["bfo_layer"]["matched_by_rule"] == {"label": 1}


def test_spelling_differences_are_not_reported_as_a_gap(tool, tmp_path):
    """`Affective_autonomy` and `AffectiveAutonomy` are one value written by
    two generations of the corpus. Comparing raw strings invents a gap."""
    record = tool.measure(
        source_graph("Affective_autonomy"), tmp_path,
        layer_graph('<%sAffectiveAutonomyDisposition> a owl:Class ; '
                    'skos:altLabel "Affective Autonomy"@en .' % BFO))
    assert record["coverage"]["folk_values_uncovered"] == 0


# --------------------------------------------------- the findings fire


def test_a_value_with_no_class_is_reported_uncovered(tool, tmp_path):
    record = tool.measure(source_graph("Kindness", "Frugality"), tmp_path,
                          layer_graph(
                              '<%sKindnessDisposition> a owl:Class ; '
                              'rdfs:seeAlso <%sKindnessDisposition> .'
                              % (BFO, W3ID)))
    assert record["coverage"]["uncovered"] == ["Frugality"]
    assert any("no class in the BFO folk module" in f
               for f in tool.findings(record))


def test_a_back_link_naming_nothing_is_reported_dangling(tool, tmp_path):
    """A link that reads as provenance and resolves to nothing is worse
    than no link, because it answers the question a reader would ask."""
    record = tool.measure(source_graph("Kindness"), tmp_path,
                          layer_graph(
                              '<%sInventedDisposition> a owl:Class ; '
                              'rdfs:seeAlso <%sInventedDisposition> .'
                              % (BFO, W3ID)))
    assert len(record["dangling_see_also"]) == 1
    assert record["dangling_see_also"][0]["names_no_folk_value"] == "Invented"
    assert any("does not exist in the corpus" in f
               for f in tool.findings(record))


def test_a_clean_pairing_produces_no_finding(tool, tmp_path):
    """Guards every assertion above. If findings() returned something for
    everything, each test would pass without discriminating."""
    record = tool.measure(source_graph("Kindness"), tmp_path,
                          layer_graph(
                              '<%sKindnessDisposition> a owl:Class ; '
                              'rdfs:seeAlso <%sKindnessDisposition> .'
                              % (BFO, W3ID)))
    assert tool.findings(record) == []


def test_check_mode_exits_non_zero_only_on_a_finding(tool):
    assert tool.findings({"coverage": {"folk_values_uncovered": 0,
                                       "folk_values_covered": 0},
                          "dangling_see_also": [],
                          "source": {"fragment_without_a_class": []}}) == []


# ------------------------------------------ what the real corpus says


#: Pinned so the gap can close visibly and cannot widen quietly. These are
#: findings about the ontology, not about the tool.
FOLK_VALUES = 278
#: 91 until D-012 added ReligionDisposition, the class for folk:Religion.
COVERED = 92
DANGLING_BACK_LINKS = 45
FRAGMENT_WITHOUT_A_CLASS = 37


def test_the_coverage_gap_is_the_one_recorded(live):
    assert live["source"]["union"] == FOLK_VALUES, live["source"]
    assert live["coverage"]["folk_values_covered"] == COVERED, (
        "coverage moved to %d of %d; if values were added to the BFO folk "
        "module, raise COVERED here in the same commit"
        % (live["coverage"]["folk_values_covered"], live["source"]["union"]))


def test_frugality_is_still_the_worked_example(live):
    """The value that started this. When it is modelled, this test is the
    one that should fail, and deleting it is the wrong response."""
    assert "Frugality" in live["coverage"]["uncovered"], (
        "Frugality now has a BFO counterpart -- remove it from this test "
        "and lower COVERED")


def test_the_dangling_back_links_are_the_ones_recorded(live):
    assert len(live["dangling_see_also"]) == DANGLING_BACK_LINKS


def test_values_evocable_but_not_expressible_are_recorded(live):
    """A trigger fragment with no class is a value the annotation pipeline
    can evoke and the ontology cannot express."""
    assert (len(live["source"]["fragment_without_a_class"])
            == FRAGMENT_WITHOUT_A_CLASS)


def test_the_tool_says_which_rules_carried_the_result(live):
    """The coverage figure rests on rdfs:seeAlso alone. That has to be
    visible in the record, or a reader takes 91 as the product of three
    independent rules agreeing."""
    assert live["bfo_layer"]["rules_that_never_fired"] == ["altLabel", "label"]
    assert set(live["bfo_layer"]["matched_by_rule"]) == {"seeAlso"}


def test_the_tool_states_what_it_does_not_check(live):
    """A partial measure that does not say it is partial is the defect
    this repository keeps finding."""
    assert live["not_covered_by_this_tool"]
    assert any("does not guess" in line
               for line in live["not_covered_by_this_tool"])
