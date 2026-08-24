# Phase 4: A Framework for Linguistic Grounding

This document outlines the strategy for connecting the BFO-aligned ValueNet ontology to linguistic data, fulfilling the goals of Phase 4. It replaces the vague `vcvf:triggers` property from the original ValueNet with a more rigorous and expressive annotation framework.

> **Namespace policy (decided).** `https://fandaws.com/ontology/bfo/valuenet-<module>#` is the canonical, resolvable namespace for every entity in the suite, and is what all examples below use. The `https://w3id.org/valuenet/<module>#` IRIs that appear throughout as `rdfs:seeAlso` are reserved aliases: nothing is declared under them and no query should rely on them. This is recorded as an `rdfs:comment` on the `valuenet-core` ontology header.

## Task 4.1: Defining `vn-core:isEvidenceFor`

The core of our new strategy is a new annotation property, `vn-core:isEvidenceFor`. This property provides a formal link between a linguistic entity (like a span of text) and the real-world process that the text describes.

### Property Definition

This property is defined in `valuenet-core.ttl` / `valuenet-core.ttl`, together with `vn-core:TextSpan`, the class of annotation units it links from.

```turtle
@prefix vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .

vn-core:isEvidenceFor rdf:type owl:AnnotationProperty ;
    rdfs:label "is evidence for"@en ;
    rdfs:comment "A relation that links a linguistic entity, such as a text span or document, to a BFO entity (typically a process or state) that the linguistic entity provides evidence for or describes."@en ;
    rdfs:isDefinedBy <https://fandaws.com/ontology/bfo/valuenet-core.owl> ;
    obo:IAO_0000115 "An annotation property used to connect a textual or observational data point to the ontological entity it describes. For example, the text 'The firefighter ran into the building' can be linked via 'isEvidenceFor' to an instance of a ValueRealizationProcess."@en .
```

### How It Works: An Example

Let's consider the sentence: **"Despite the risk, the journalist published the story to expose the corruption."**

In the old model, the word "expose" might have vaguely `vcvf:triggers` a value like "honesty". The new BFO-aligned model allows for a much richer, more precise annotation.

Here is how we would represent this sentence as RDF triples using the new framework:

```turtle
@prefix : <http://example.com/data/> .
@prefix bfo: <http://purl.obolibrary.org/obo/BFO_> .
@prefix vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#> .
@prefix folk: <https://fandaws.com/ontology/bfo/valuenet-folk#> .
@prefix cco: <https://www.commoncoreontologies.org/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# 1. Define the instances
:theJournalist rdf:type cco:ont00001017 . # cco:Agent  (BFO itself has no "person" or "agent" class; Agent is MIREOTed into valuenet-core)
:publishingProcess rdf:type vn-core:ValueRealizationProcess .
:article42 rdf:type bfo:0000031 .   # the source document, a generically dependent continuant
:textSpan1 rdf:type vn-core:TextSpan ;
           vn-core:hasTextValue "published the story to expose the corruption" ;
           vn-core:isTextSpanOf :article42 ;
           vn-core:hasStartOffset "18"^^xsd:nonNegativeInteger ;
           vn-core:hasEndOffset   "62"^^xsd:nonNegativeInteger .

# 2. Link the agent to their value dispositions.
#    Dispositions are minted as individuals: this journalist's courage,
#    not the class of courage. Relating a process to the class instead
#    is OWL 2 punning and falls outside OWL 2 DL.
:courageOfJournalist rdf:type folk:CourageDisposition .
:honestyOfJournalist rdf:type folk:HonestyDisposition .
:theJournalist bfo:0000196 :courageOfJournalist . # bfo:bearer_of
:theJournalist bfo:0000196 :honestyOfJournalist .

# 3. Describe the process and what values it realizes
:publishingProcess bfo:0000057 :theJournalist . # bfo:has_participant
:publishingProcess bfo:0000055 :courageOfJournalist . # bfo:realizes
:publishingProcess bfo:0000055 :honestyOfJournalist .

# 4. Use the new property to link the text to the process
:textSpan1 vn-core:isEvidenceFor :publishingProcess .

# 5. Optionally record the frame the span evokes. This is the bridge to the
#    existing MFTriggers data: the frame is the subject of vcvf:triggers
#    statements whose objects are Haidt values, which the BFO-aligned
#    dispositions reach by skos:broadMatch in valuenet-mappings.
:textSpan1 vn-core:evokesFrame <https://w3id.org/framester/framenet/abox/frame/Reveal_secret> .
```

> **Querying MFTriggers.** All 12,338 `vcvf:triggers` statements in that corpus use `http://www.ontologydesignpatterns.org/ont/values/valuecore_with_value_frames.owl#`, the namespace ValueCore itself declares, so one prefix binding reaches all of them.

### Value Proposition

This approach is vastly superior to the old `vcvf:triggers` model:
1.  **Ontological Precision:** It correctly separates the linguistic description (the text) from the real-world event (the process).
2.  **Causal Reasoning:** It creates a complete, queryable causal chain: an agent has a disposition, which is realized in a process, which is described by a piece of text.
3.  **Richness:** It allows a single action to be seen as the realization of multiple values simultaneously (e.g., Courage and Honesty).
4.  **Explainability:** It provides a clear path to explain *why* an action is valuable, grounded in the agent's internal dispositions.