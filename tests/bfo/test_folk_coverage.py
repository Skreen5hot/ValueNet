# SPDX-License-Identifier: Apache-2.0
"""Does the BFO folk module carry the folk corpus, and does the tool know?

The occasion: somebody demonstrating the site searched for "frugal" and found
nothing. `folk:Frugality` is in ThatsAllFolks/folk.ttl and in the generated
alignment view; it was not in ontology/bfo/core/valuenet-folk.ttl, and the site
class index is built from the BFO modules. Nothing had ever compared the two,
while `docs/bfo/guides/BFOizing ValueNet.md` described the result as
"comprehensive in its coverage".

D-014 then decided every corpus value, and coverage is reported by kind --
exact class, alternative label, correspondence, exclusion -- because the kinds
are different claims and a blended total would overstate what the ontology
names.

Two halves here, and the second is the one that makes the first mean anything.
The synthetic cases exercise each rule and each kind directly, each handed its
own mapping graph and exclusions so the real ones cannot leak in; the real
corpus is then pinned, so the figures can move only visibly.
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
VN_CORE = "https://fandaws.com/ontology/bfo/valuenet-core#"


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
    """Measured once. Parses folk.ttl, the BFO layer, the mappings and the
    exclusions record."""
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
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
        "@prefix vn-core: <%s> .\n" % VN_CORE + body),
        format="turtle")
    return graph


KINDNESS = ('<%sKindnessDisposition> a owl:Class ; '
            'rdfs:seeAlso <%sKindnessDisposition> .' % (BFO, W3ID))


def run(tool, tmp_path, values, layer, mappings="", excluded=()):
    return tool.measure(source_graph(*values), tmp_path, layer_graph(layer),
                        layer_graph(mappings),
                        [{"value": name} for name in excluded])


# ------------------------------------------------- each rule, on its own


def test_the_see_also_rule_pairs_a_class_with_its_value(tool, tmp_path):
    record = run(tool, tmp_path, ["Kindness"], KINDNESS)
    assert record["coverage"]["by_kind"]["exact"] == 1
    assert record["bfo_layer"]["matched_by_rule"] == {"seeAlso": 1}


def test_the_label_rule_strips_the_disposition_suffix(tool, tmp_path):
    record = run(tool, tmp_path, ["Kindness"],
                 '<%sKindnessDisposition> a owl:Class ; '
                 'rdfs:label "Kindness Disposition"@en .' % BFO)
    assert record["coverage"]["by_kind"]["exact"] == 1
    assert record["bfo_layer"]["matched_by_rule"] == {"label": 1}


def test_an_alternative_label_naming_another_value_is_a_synonym(tool, tmp_path):
    """The case that started this: Frugality as a label of Thrift. A label
    is a name, so the value counts as named -- but as a synonym, not as a
    class of its own."""
    record = run(tool, tmp_path, ["Thrift", "Frugality"],
                 '<%sThriftDisposition> a owl:Class ; '
                 'rdfs:seeAlso <%sThriftDisposition> ; '
                 'skos:altLabel "Thrift"@en, "Frugality"@en .' % (BFO, W3ID))
    kinds = record["coverage"]["by_kind"]
    assert (kinds["exact"], kinds["synonym"]) == (1, 1), kinds
    assert record["coverage"]["synonyms"] == [{
        "value": "Frugality", "class": BFO + "ThriftDisposition",
        "label": "Frugality"}]


def test_an_alternative_label_repeating_its_own_value_is_not_a_synonym(
        tool, tmp_path):
    """Every class in the module repeats its own word as skos:altLabel.
    Counting those as synonyms would double every exact pairing."""
    record = run(tool, tmp_path, ["Kindness"],
                 '<%sKindnessDisposition> a owl:Class ; '
                 'rdfs:seeAlso <%sKindnessDisposition> ; '
                 'skos:altLabel "Kindness"@en .' % (BFO, W3ID))
    assert record["coverage"]["by_kind"] == {
        "exact": 1, "synonym": 0, "correspondence": 0, "excluded": 0}


def test_spelling_differences_are_not_reported_as_a_gap(tool, tmp_path):
    """`Affective_autonomy` and `AffectiveAutonomy` are one value written by
    two generations of the corpus. Comparing raw strings invents a gap."""
    record = run(tool, tmp_path, ["Affective_autonomy"],
                 '<%sAffectiveAutonomyDisposition> a owl:Class ; '
                 'rdfs:seeAlso <%sAffectiveAutonomyDisposition> .'
                 % (BFO, W3ID))
    assert record["coverage"]["pending"] == []


# ------------------------------------------- the kinds that no label makes


def test_a_mapping_to_a_corpus_iri_is_a_correspondence_not_a_name(
        tool, tmp_path):
    record = run(tool, tmp_path, ["Kindness", "Grace"], KINDNESS,
                 mappings='<%sKindnessDisposition> '
                          'vn-core:hasRelatedConceptualMatch <%sGrace> .'
                          % (BFO, ODP))
    coverage = record["coverage"]
    assert coverage["by_kind"]["correspondence"] == 1
    assert coverage["named_by_the_ontology"] == 1, (
        "a correspondence was counted as a name")
    assert coverage["correspondences"][0]["predicate"] == (
        "hasRelatedConceptualMatch")


def test_a_recorded_exclusion_is_its_own_kind(tool, tmp_path):
    record = run(tool, tmp_path, ["Kindness", "Management"], KINDNESS,
                 excluded=["Management"])
    assert record["coverage"]["by_kind"]["excluded"] == 1
    assert tool.findings(record) == []


# --------------------------------------------------- the findings fire


def test_a_value_of_no_kind_is_pending_and_a_finding(tool, tmp_path):
    record = run(tool, tmp_path, ["Kindness", "Frugality"], KINDNESS)
    assert record["coverage"]["pending"] == ["Frugality"]
    assert any("of no kind" in f for f in tool.findings(record))


def test_a_value_of_two_kinds_is_a_finding(tool, tmp_path):
    """D-014 gives each value one kind. A word both a label and a
    correspondence says two incompatible things about it."""
    record = run(tool, tmp_path, ["Kindness", "Grace"],
                 '<%sKindnessDisposition> a owl:Class ; '
                 'rdfs:seeAlso <%sKindnessDisposition> ; '
                 'skos:altLabel "Grace"@en .' % (BFO, W3ID),
                 mappings='<%sKindnessDisposition> '
                          'vn-core:hasRelatedConceptualMatch <%sGrace> .'
                          % (BFO, ODP))
    assert record["coverage"]["in_more_than_one_kind"] == [
        {"value": "Grace", "kinds": ["synonym", "correspondence"]}]
    assert any("more than one kind" in f for f in tool.findings(record))


def test_a_correspondence_or_exclusion_naming_nothing_is_a_finding(
        tool, tmp_path):
    record = run(tool, tmp_path, ["Kindness"], KINDNESS,
                 mappings='<%sKindnessDisposition> '
                          'vn-core:hasRelatedConceptualMatch <%sInvented> .'
                          % (BFO, ODP),
                 excluded=["Imaginary"])
    unknown = record["coverage"]["not_a_folk_value"]
    assert unknown == {"correspondence_targets": [ODP + "Invented"],
                       "exclusions": ["Imaginary"]}
    assert any("does not have" in f for f in tool.findings(record))


def test_a_back_link_naming_nothing_is_reported_dangling(tool, tmp_path):
    """A link that reads as provenance and resolves to nothing is worse
    than no link, because it answers the question a reader would ask."""
    record = run(tool, tmp_path, ["Kindness"],
                 '<%sInventedDisposition> a owl:Class ; '
                 'rdfs:seeAlso <%sInventedDisposition> .' % (BFO, W3ID),
                 excluded=["Kindness"])
    assert len(record["dangling_see_also"]) == 1
    assert record["dangling_see_also"][0]["names_no_folk_value"] == "Invented"
    assert any("does not exist in the corpus" in f
               for f in tool.findings(record))


def test_a_clean_pairing_produces_no_finding(tool, tmp_path):
    """Guards every assertion above. If findings() returned something for
    everything, each test would pass without discriminating."""
    record = run(tool, tmp_path, ["Kindness"], KINDNESS)
    assert tool.findings(record) == []


def test_check_mode_exits_non_zero_only_on_a_finding(tool):
    assert tool.findings({
        "coverage": {"pending": [], "in_more_than_one_kind": [],
                     "not_a_folk_value": {"correspondence_targets": [],
                                          "exclusions": []}},
        "dangling_see_also": [],
        "source": {"union": 0, "fragment_without_a_class": []}}) == []


# ------------------------------------------ what the real corpus says


#: Pinned so the figures can move only visibly. These are findings about
#: the ontology, not about the tool: D-014's coverage, by kind.
FOLK_VALUES = 278
BY_KIND = {"exact": 98, "synonym": 9, "correspondence": 146, "excluded": 25}
#: 45 until D-014 removed seven of the classes whose back-links named
#: nothing: Power, Security, Tradition, Openness, Impact, Discretion and
#: Resourcefulness.
DANGLING_BACK_LINKS = 38
FRAGMENT_WITHOUT_A_CLASS = 37


def test_every_folk_value_has_the_kind_d014_gave_it(live):
    assert live["source"]["union"] == FOLK_VALUES, live["source"]
    assert live["coverage"]["by_kind"] == BY_KIND, (
        "coverage moved to %s; a change to folk membership needs a decision "
        "that says so, and these figures raised in the same commit"
        % live["coverage"]["by_kind"])
    assert live["coverage"]["pending"] == []
    assert live["coverage"]["in_more_than_one_kind"] == []
    assert live["coverage"]["not_a_folk_value"] == {
        "correspondence_targets": [], "exclusions": []}


def test_frugality_is_still_the_worked_example(live):
    """The value that started this. It is now an alternative label of
    ThriftDisposition, which is what the site's search reads as a synonym;
    it did not need a class of its own."""
    assert {"value": "Frugality", "class": BFO + "ThriftDisposition",
            "label": "Frugality"} in live["coverage"]["synonyms"]


def test_the_dangling_back_links_are_the_ones_recorded(live):
    assert len(live["dangling_see_also"]) == DANGLING_BACK_LINKS


def test_values_evocable_but_not_expressible_are_recorded(live):
    """A trigger fragment with no class is a value the annotation pipeline
    can evoke and the ontology cannot express."""
    assert (len(live["source"]["fragment_without_a_class"])
            == FRAGMENT_WITHOUT_A_CLASS)


def test_the_tool_says_which_rules_carried_the_result(live):
    """Exact pairings rest on rdfs:seeAlso and synonyms on skos:altLabel.
    That has to be visible in the record, or a reader takes the figures as
    the product of three independent rules agreeing."""
    assert live["bfo_layer"]["rules_that_never_fired"] == ["label"]
    assert live["bfo_layer"]["matched_by_rule"] == {
        "seeAlso": BY_KIND["exact"], "altLabel": BY_KIND["synonym"]}


def test_the_exclusions_record_gives_every_exclusion_a_kind(tool):
    rows = tool.recorded_exclusions()
    assert len(rows) == BY_KIND["excluded"]
    for row in rows:
        assert row["kind"] and row["iri"].startswith(ODP), row


def test_the_tool_states_what_it_does_not_check(live):
    """A partial measure that does not say it is partial is the defect
    this repository keeps finding."""
    assert live["not_covered_by_this_tool"]
    assert any("does not guess" in line
               for line in live["not_covered_by_this_tool"])
