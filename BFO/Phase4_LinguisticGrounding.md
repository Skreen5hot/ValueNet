# Phase 4: A Framework for Linguistic Grounding

This document outlines the strategy for connecting the BFO-aligned ValueNet ontology to linguistic data, fulfilling the goals of Phase 4. It replaces the vague `vcvf:triggers` property from the original ValueNet with a more rigorous and expressive annotation framework.

## Task 4.1: Defining `vn-core:isEvidenceFor`

The core of our new strategy is a new annotation property, `vn-core:isEvidenceFor`. This property provides a formal link between a linguistic entity (like a span of text) and the real-world process that the text describes.

### Property Definition

This property should be added to the `valuenet-core.owl` file.

```turtle
@prefix vn-core: <https://w3id.org/valuenet/core#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .

vn-core:isEvidenceFor rdf:type owl:AnnotationProperty ;
    rdfs:label "is evidence for"@en ;
    rdfs:comment "A relation that links a linguistic entity, such as a text span or document, to a BFO entity (typically a process or state) that the linguistic entity provides evidence for or describes."@en ;
    rdfs:isDefinedBy <https://w3id.org/valuenet/core> ;
    obo:IAO_0000115 "An annotation property used to connect a textual or observational data point to the ontological entity it describes. For example, the text 'The firefighter ran into the building' can be linked via 'isEvidenceFor' to an instance of a ValueRealizationProcess."@en .
```

### How It Works: An Example

Let's consider the sentence: **"Despite the risk, the journalist published the story to expose the corruption."**

In the old model, the word "expose" might have vaguely `vcvf:triggers` a value like "honesty". The new BFO-aligned model allows for a much richer, more precise annotation.

Here is how we would represent this sentence as RDF triples using the new framework:

```turtle
@prefix : <http://example.com/data/> .
@prefix bfo: <http://purl.obolibrary.org/obo/BFO_> .
@prefix vn-core: <https://w3id.org/valuenet/core#> .
@prefix folk: <https://w3id.org/valuenet/folk#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

# 1. Define the instances
:theJournalist rdf:type bfo:0000041 . # bfo:person
:publishingProcess rdf:type vn-core:ValueRealizationProcess .
:textSpan1 rdf:type vn-core:TextSpan ;
           rdfs:label "published the story to expose the corruption" .

# 2. Link the agent to their value dispositions
:theJournalist bfo:0000086 folk:CourageDisposition . # bfo:has_disposition
:theJournalist bfo:0000086 folk:HonestyDisposition .

# 3. Describe the process and what values it realizes
:publishingProcess bfo:0000057 :theJournalist . # bfo:has_participant
:publishingProcess bfo:0000133 folk:CourageDisposition . # bfo:realizes
:publishingProcess bfo:0000133 folk:HonestyDisposition .

# 4. Use the new property to link the text to the process
:textSpan1 vn-core:isEvidenceFor :publishingProcess .
```

### Value Proposition

This approach is vastly superior to the old `vcvf:triggers` model:
1.  **Ontological Precision:** It correctly separates the linguistic description (the text) from the real-world event (the process).
2.  **Causal Reasoning:** It creates a complete, queryable causal chain: an agent has a disposition, which is realized in a process, which is described by a piece of text.
3.  **Richness:** It allows a single action to be seen as the realization of multiple values simultaneously (e.g., Courage and Honesty).
4.  **Explainability:** It provides a clear path to explain *why* an action is valuable, grounded in the agent's internal dispositions.