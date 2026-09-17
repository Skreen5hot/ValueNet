# SPDX-License-Identifier: Apache-2.0
"""What a moral assessment commits the ontology to, decided by HermiT.

The formal review of 2026-09-16 found two commitments the moral epistemics
module made without saying so, and both have the same counterexample inside
the module: `RashJudgmentAct`.

- Plannedness (finding 10, R12, D-008). `MoralAssessmentAct` sat under CCO
  Act of Appraisal, which is a Planned Act through Act of Measuring, so every
  rash judgment was entailed to be planned -- prescribed by a directive its
  agent holds. A spontaneous judgment is the ordinary case of one. The generic
  parent is now CCO Act; discernment, which is deliberate, stays an Act of
  Appraisal.
- Culpability (finding 12, R13, D-009). The role was defined as inhering
  "because a norm-governed moral appraisal treats that agent as accountable".
  A rash judgment does exactly that, so by its definition an unwarranted
  ascription would confer the culpability it wrongly ascribes. The definition
  now grounds the role in the agent's own conduct. That change is to the
  wording; the OWL conditions were already right, and the reasoning test below
  holds them there.

Reasoned over the suite with the worked scenario, in which Agent B's rash
judgment produces an unwarranted ascription describing Agent C.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

from rdflib import Graph, Namespace, URIRef  # noqa: E402
from rdflib.namespace import OWL, SKOS  # noqa: E402

from marep.layout import bfo_artifact  # noqa: E402

try:
    import owlready2
except ImportError:  # pragma: no cover - environment guidance
    owlready2 = None

VN_ME = Namespace("https://fandaws.com/ontology/bfo/valuenet-moral-epistemics#")
SCENARIO_NS = Namespace(
    "https://fandaws.com/ontology/bfo/valuenet-moral-epistemics-scenario#")
CCO = Namespace("https://www.commoncoreontologies.org/")
PROBE = Namespace("https://example.invalid/probe#")

ACT = CCO.ont00000005
PLANNED_ACT = CCO.ont00000228
ACT_OF_APPRAISAL = CCO.ont00000636

MODULE = bfo_artifact("valuenet-moral-epistemics.ttl")
SUITE = tuple(bfo_artifact(name) for name in (
    "bfo-core.ttl",
    "cco-valuenet-extract.ttl",
    "valuenet-core.ttl",
    "valuenet-schwartz-values.ttl",
    "valuenet-moral-foundations.ttl",
    "valuenet-folk.ttl",
    "valuenet-moral-epistemics.ttl",
    "valuenet-moral-epistemics-scenario.ttl",
))

#: A named class for "bears some culpability role", so that HermiT's
#: realization can say which individuals fall under it, and one agent that
#: really does bear the role -- the positive control, without which a check
#: that nobody is culpable could pass because nothing ever is.
#:
#: The probe namespace must not share its base with the ontology IRI given to
#: owlready2. When it did, the inferred class came back under a different IRI
#: (.../obo/bfo.owl#BearerOfCulpability), no individual could ever match, and
#: the negative test passed for that reason alone. The positive control is
#: what showed it.
PROBES = """
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix obo:   <http://purl.obolibrary.org/obo/> .
@prefix cco:   <https://www.commoncoreontologies.org/> .
@prefix vn-me: <https://fandaws.com/ontology/bfo/valuenet-moral-epistemics#> .
@prefix probe: <https://example.invalid/probe#> .
probe:BearerOfCulpability a owl:Class ;
    owl:equivalentClass [ a owl:Restriction ;
                          owl:onProperty obo:BFO_0000196 ;
                          owl:someValuesFrom vn-me:MoralCulpabilityRole ] .
probe:culpableAgent a cco:ont00001017 ; obo:BFO_0000196 probe:culpability .
probe:culpability a vn-me:MoralCulpabilityRole .
"""


def iris(entities) -> set:
    return {str(getattr(e, "iri", e)) for e in entities}


@pytest.fixture(scope="module")
def world():
    if owlready2 is None:  # pragma: no cover - environment guidance
        pytest.skip("owlready2 is required to run HermiT; without it the "
                    "moral assessment commitments are unverified here.")
    if shutil.which("java") is None:  # pragma: no cover - environment guidance
        pytest.skip("HermiT needs a Java runtime on PATH; without one the "
                    "moral assessment commitments are unverified here.")
    graph = Graph()
    for path in SUITE:
        graph.parse(path, format="turtle")
    graph.parse(data=PROBES, format="turtle")
    for triple in list(graph.triples((None, OWL.imports, None))):
        graph.remove(triple)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "merged.owl"
        graph.serialize(path, format="xml")
        reasoned = owlready2.World()
        with open(path, "rb") as stream:
            onto = reasoned.get_ontology(
                "https://example.invalid/moral-assessment").load(fileobj=stream)
        try:
            owlready2.sync_reasoner([onto], debug=0)
        except owlready2.OwlReadyInconsistentOntologyError:
            pytest.fail("HermiT found the suite with the scenario inconsistent")
    return reasoned


def ancestors(world, iri: URIRef) -> set:
    entity = world[str(iri)]
    assert entity is not None, "%s is not in the reasoned graph" % iri
    return iris(entity.ancestors())


def types(world, iri: URIRef) -> set:
    entity = world[str(iri)]
    assert entity is not None, "%s is not in the reasoned graph" % iri
    return iris(entity.INDIRECT_is_a)


# ---------------------------------------------------------------- plannedness


def test_a_rash_judgment_is_an_act_and_is_not_entailed_to_be_planned(world):
    got = ancestors(world, VN_ME.RashJudgmentAct)
    assert str(ACT) in got
    assert str(PLANNED_ACT) not in got, (
        "RashJudgmentAct is entailed to be a Planned Act again")
    assert str(ACT_OF_APPRAISAL) not in got


def test_discernment_is_an_act_of_appraisal_and_so_planned(world):
    """The positive control for the test above, and D-008's other half:
    deliberate assessment keeps the CCO class that says so."""
    got = ancestors(world, VN_ME.MoralDiscernmentAct)
    assert str(ACT_OF_APPRAISAL) in got
    assert str(PLANNED_ACT) in got


def test_a_mixed_assessment_act_remains_satisfiable(world):
    """Discernment is planned and rash judgment no longer is, but nothing
    makes them disjoint, so an act that is both stays possible."""
    unsatisfiable = iris(world.inconsistent_classes())
    assert str(VN_ME.MixedMoralAssessmentAct) not in unsatisfiable
    assert str(PLANNED_ACT) in ancestors(world, VN_ME.MixedMoralAssessmentAct)


# ---------------------------------------------------------------- culpability


def test_an_unwarranted_ascription_does_not_make_its_target_culpable(world):
    """Agent B's rash judgment ascribes culpability to Agent C without
    warrant. Neither C, nor B, may be inferred to bear the role."""
    for agent in ("agentC", "agentB"):
        assert str(PROBE.BearerOfCulpability) not in types(
            world, SCENARIO_NS[agent]), (
            "%s is inferred to bear a MoralCulpabilityRole" % agent)


def test_an_agent_that_bears_the_role_is_recognised_as_culpable(world):
    """The positive control, in the same reasoning run."""
    assert str(PROBE.BearerOfCulpability) in types(world, PROBE.culpableAgent)


def test_culpability_is_defined_by_conduct_not_by_appraisal():
    """D-009. The defect was in the definition, so the definition is what is
    checked: no appraisal, treatment or ascription may be what grounds the
    role, and the agent's own conduct must be."""
    graph = Graph()
    graph.parse(MODULE, format="turtle")
    definitions = [str(d) for d in graph.objects(VN_ME.MoralCulpabilityRole,
                                                 SKOS.definition)]
    assert len(definitions) == 1, definitions
    definition = definitions[0].lower()
    for word in ("apprais", "treats", "ascri", "regarded", "judg"):
        assert word not in definition, (
            "the definition grounds the role in %r again: %s"
            % (word, definitions[0]))
    for phrase in ("participated", "conduct", "violates a moral norm"):
        assert phrase in definition, (
            "the definition no longer grounds the role in the agent's own "
            "conduct: %s" % definitions[0])
