# Competency Questions: Moral Epistemics Module

Competency questions for `valuenet-moral-epistemics.owl`, in the style of the BHV and MFT competency questions listed in the repository README. CQ6 exercises the `vn-core` annotation layer.

All six are satisfied by `valuenet-moral-epistemics-scenario.ttl`, a fictional scenario in which two agents witness the same conduct: one observes, discerns and acts; the other judges rashly. The results below were produced by running each query over the merged graph of `valuenet-core`, `valuenet-schwartz-values`, `valuenet-folk`, `valuenet-moral-foundations`, `valuenet-mappings`, `valuenet-moral-epistemics` and the scenario (1,394 triples). CQ6 additionally loads two MFTriggers files.

Shared prefixes for every query:

```sparql
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX obo:     <http://purl.obolibrary.org/obo/>
PREFIX vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#>
PREFIX vn-me:   <https://fandaws.com/ontology/bfo/valuenet-moral-epistemics#>
```

---

## CQ1. Which acts run against a value that the acting agent themselves bears?

The question the DUL version could not ask, because a value was a description satisfied by a situation rather than something an agent could both bear and act against. Answers cover both hypocrisy and honest moral conflict; distinguishing them is a matter for interpretation, not for the ontology.

```sparql
SELECT ?agent ?act ?value WHERE {
  ?act obo:BFO_0000057 ?agent ;          # has participant
       vn-core:contravenes ?value .
  ?agent obo:BFO_0000196 ?value .        # bearer of
}
```

| agent | act | value |
|---|---|---|
| agentA | protectiveActionByA | trustOfA |
| agentB | rashJudgmentByB | justiceOfB |
| agentB | rashJudgmentByB | honestyOfB |
| agentB | rashJudgmentByB | careOfB |

---

## CQ2. Given a protective action, what grounded it?

The explainability chain the BFOizing rationale promises, recovered end to end: action ← assessment ← evidence ← observation, with the text span that attests to it.

```sparql
SELECT ?action ?assessment ?observation ?evidence ?textSpan WHERE {
  ?action a vn-me:ProtectiveAction ;
          vn-me:hasInformationalInput ?assessment ;
          obo:BFO_0000062 ?discernment .          # preceded by
  ?assessment vn-me:isWarrantedBy ?evidence .
  ?discernment obo:BFO_0000062 ?observation .
  ?observation vn-me:hasInformationalOutput ?evidence .
  OPTIONAL { ?textSpan vn-core:isEvidenceFor ?action }
}
```

| action | assessment | observation | evidence | textSpan |
|---|---|---|---|---|
| protectiveActionByA | assessmentByA | observationByA | obsRecordA | textSpan1 |

---

## CQ3. Which ascriptions of culpability have no recorded evidential warrant, and who produced them?

The operational form of the discernment / rash judgment distinction. `FILTER NOT EXISTS` is closed-world, which is why this is a query rather than an OWL entailment; see the open-world caveat on `vn-me:RashJudgmentAct` and the SHACL shapes in `valuenet-moral-epistemics-shapes.ttl`.

```sparql
SELECT ?act ?agent ?ascription WHERE {
  ?act vn-me:hasInformationalOutput ?ascription ;
       obo:BFO_0000057 ?agent .
  ?ascription a vn-me:CulpabilityAscriptionICE .
  FILTER NOT EXISTS { ?ascription vn-me:isWarrantedBy ?e }
}
```

| act | agent | ascription |
|---|---|---|
| rashJudgmentByB | agentB | verdictByB |

---

## CQ4. Which values does an agent bear that no recorded process realizes?

A coverage check on annotated corpora: a value profile asserted but never evidenced in behaviour.

```sparql
SELECT ?agent ?value WHERE {
  ?agent obo:BFO_0000196 ?value .
  ?value a/rdfs:subClassOf* vn-core:ValueRelatedRealizableEntity .
  FILTER NOT EXISTS { ?p obo:BFO_0000055 ?value }
}
```

| agent | value |
|---|---|
| agentA | trustOfA |
| agentB | justiceOfB |
| agentB | honestyOfB |
| agentB | careOfB |

---

## CQ5. Which processes realize one value while contravening another?

Moral trade-offs. This is the reason `vn-core:ValueViolationProcess` is deliberately not disjoint from `vn-core:ValueRealizationProcess`.

```sparql
SELECT ?process ?realized ?contravened WHERE {
  ?process obo:BFO_0000055 ?realized ;
           vn-core:contravenes ?contravened .
}
```

| process | realized | contravened |
|---|---|---|
| protectiveActionByA | protectorRoleOfA | trustOfA |
| protectiveActionByA | careOfA | trustOfA |

---

## CQ6. What value does a span of text reach through the existing trigger data?

Exercises `vn-core`, not this module, but the scenario is what demonstrates it. This is the path that replaces `vcvf:triggers` without discarding it: the 12,338 trigger statements already in `MFTriggers/` are reused as a lexical layer underneath the BFO model, rather than being re-annotated.

Text span → FrameNet frame → Haidt value → BFO-aligned disposition.

```sparql
PREFIX skos:   <http://www.w3.org/2004/02/skos/core#>
PREFIX vn-core:<https://fandaws.com/ontology/bfo/valuenet-core#>
PREFIX vcvf:   <http://www.ontologydesignpatterns.org/ont/values/valuecore_with_value_frames.owl#>

SELECT DISTINCT ?span ?text ?frame ?haidtValue ?disposition WHERE {
  ?span a vn-core:TextSpan ;
        vn-core:hasTextValue ?text ;
        vn-core:evokesFrame ?frame .
  ?frame vcvf:triggers ?haidtValue .
  OPTIONAL { ?disposition skos:broadMatch ?haidtValue }
}
```

Run over the suite, the scenario, and `MFTriggers/care_frame.ttl` + `MFTriggers/harm_frame.ttl` (11,559 triples):

| text | frame | haidtValue | disposition |
|---|---|---|---|
| "kept an eye on him and made sure he was never alone with the kids" | framenet:Protecting | haidt:Care | vn-mf:CareDisposition |

A single prefix binding suffices. It did not previously: `vcvf` was bound to two rival namespaces across `MFTriggers/`, and this query needed a `UNION` to reach the whole corpus. All 12,338 trigger statements now use the namespace ValueCore itself declares.

---

## Notes on running these

* Queries are over asserted triples only. `vn-core:ValueViolationProcess` is a defined class (`owl:equivalentClass`), so an OWL reasoner will additionally classify `:protectiveActionByA` and `:rashJudgmentByB` under it from their `contravenes` axioms; the queries above do not depend on that inference.
* `obo:BFO_0000057` is *has participant* (process → continuant), not its inverse. `obo:BFO_0000196` is *bearer of* (continuant → realizable entity). `obo:BFO_0000062` is *preceded by*.
* Value dispositions and roles appear as **individuals** (`:justiceOfB a folk:JusticeDisposition`), not as classes in object position. See the instance-level note in `annotationGuide.md`.
* Agents are typed as `cco:ont00001017` (CCO `Agent`), which `valuenet-core` adopts by IRI. Core asserts that every `ValueRelatedRealizableEntity` inheres in some `Agent`, so CQ1 and CQ4 are asking about agents by construction.
