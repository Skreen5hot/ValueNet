# ValueNet Annotation Guide

This guide provides a step-by-step process for annotating text for human values using the BFO-aligned ValueNet ontology. The goal is to create rich, structured data that captures not just *what* values are present, but *how* they are demonstrated.

## 1. Core Concepts

Our model uses a few key concepts to describe how values work in the real world.

*   **Agent:** The person who holds the value and performs the action. Type these as `cco:ont00001017` (CCO `Agent`), which `valuenet-core` adopts by IRI. BFO itself has no agent or person class.
    *   *Note on groups:* CCO does not put `Organization` under `Agent` — an organization is a `Group of Agents` (`cco:ont00000300`), an aggregate whose members are agents. Value bearing is currently asserted over `Agent` only.
*   **Value Disposition:** An *internal, personal tendency* to act in a certain way. Think of this as a core part of someone's character.
    *   *Example:* A person's general disposition towards `folk:Kindness`.
*   **Value Role:** An *external, social expectation* placed on an agent. This is tied to a job, position, or social context.
    *   *Example:* The duties of a `folk:LeaderRole` or `folk:ProfessionalismRole`.
*   **Value Realization Process:** The specific *action or event* where a value is made real or demonstrated.
    *   *Example:* The *process of helping* someone, which makes the `KindnessDisposition` real.

## 2. The Annotation Workflow

For a given piece of text, follow these five steps to create a complete annotation.

### Step 1: Identify the Action (The Process)

Read the text and find the core action or event that demonstrates a value. This action is your **`ValueRealizationProcess`**.

> **Text:** "The volunteer spent her weekend cleaning the park."
> **Action:** The process of "cleaning the park".

### Step 2: Identify the Agent

Who is performing this action? This person or group is your **`Agent`**.

> **Text:** "The volunteer spent her weekend cleaning the park."
> **Agent:** "The volunteer".

### Step 3: Identify the Value(s)

What value is the agent demonstrating through their action? Look through the `valuenet-folk.ttl` ontology to find the best fit. An action can demonstrate multiple values. These are your **`ValueDisposition`** or **`ValueRole`** classes.

> **Text:** "The volunteer spent her weekend cleaning the park."
> **Values:** This action demonstrates a `folk:ContributionDisposition` (making an impact on the community) and a `folk:DiligenceDisposition` (applying persistent work).

### Step 4: Connect the Pieces

Using the formal BFO relations, you now connect the instances you've identified.

> **Instances, not classes.** A value disposition is a real property of *one particular agent*, so what a process realizes is that agent's individual disposition, not the class. Mint an instance of the disposition class first (`:courageOfJournalist a folk:CourageDisposition`) and relate the process and the agent to *that*. Writing `:someProcess bfo:0000055 folk:CourageDisposition` uses the class IRI in an individual position. OWL 2 permits some forms of class/individual punning, but the two uses have separate interpretations and do not mean that the process realizes a member of the class. The ValueNet SHACL shapes reject this workflow error.

1.  Mint an **instance** of each `ValueDisposition` / `ValueRole` class you selected in Step 3.
2.  The `Agent` **bears** that disposition instance (`bfo:bearer_of`, `BFO_0000196`).
3.  The `ValueRealizationProcess` **has as participant** the `Agent` (`bfo:has_participant`, `BFO_0000057`; the inverse, `bfo:participates_in`, is `BFO_0000056`).
4.  The `ValueRealizationProcess` **realizes** that disposition instance (`bfo:realizes`, `BFO_0000055`).

The inverse bearer assertion is equally valid: instead of `:agent bfo:0000196 :value`, write `:value bfo:0000197 :agent` (`bfo:inheres_in`). Validation accepts either direction. In both cases the recorded bearer must be typed as a CCO `Agent` and at least one recorded bearer of every realized value must participate in the realizing process.

ValueNet does not add a maximum-cardinality or functional axiom to BFO's bearer relations. If merged data records more than one bearer for a value instance, the realization check is existential: at least one recorded bearer must participate. In ordinary annotation, mint a separate value instance for each agent. Collective or group-level value bearing remains outside the current model.

### Step 5: Link to the Text

Finally, distinguish the text's content and coordinates from the thing that carries it. The Phase 3 annotation profile uses five named individuals:

| Individual | Type and required links |
| --- | --- |
| Carrier | `cco:ont00000253` (CCO Information Bearing Entity); link it to the exact representation with `bfo:0000101` (`is carrier of`) |
| Exact representation/version | `vn-core:TextualRepresentation`; give it exactly one canonical `vn-core:hasTextValue` string |
| Span content | `vn-core:TextSpan`; give it its substring and link it to the representation with `vn-core:isTextSpanOf` |
| Coordinate selector | `vn-core:TextSpanSelector`; link it to the representation and span, then record both offsets |
| Evidence record | `vn-core:ValueEvidenceAnnotation`; link it to the span, selector, and process |

The carrier and representation must not be the same individual. A carrier is an independent continuant; a representation, span, selector, and annotation record are information content entities. `isTextSpanOf` specializes BFO `continuant part of`. Do not use `bfo:concretizes` directly between a carrier and its content: BFO reserves that relation for a process or specifically dependent continuant that concretizes a generically dependent continuant. CCO/BFO `is carrier of` is the verified carrier-to-content relation.

Offsets are zero-based Unicode code-point indexes into the exact representation's `hasTextValue` string, with the end offset excluded. Both offsets are required on a selector. No Unicode normalization, line-ending conversion, or other text transformation is implicit; mint a new `TextualRepresentation` if the source string changes.

Optionally add `vn-core:evokesFrame` pointing at the semantic frame a parser assigns to the span. That is the bridge to the existing MFTriggers data: the frame is the subject of `vcvf:triggers` statements whose objects are Haidt values, which the BFO-aligned dispositions reach by the annotation-only `vn-core:historicallyCorrespondsTo` property. It lets a span reach a value disposition through the 12,338 trigger statements already in the repository, without re-annotating anything or treating OWL classes as SKOS concept individuals.

`isEvidenceFor` is an annotation property, so a reasoner will not enforce its domain and range and it cannot be used in a class restriction. The subject may be a `TextSpan` in the simple profile or a `ValueEvidenceAnnotation` in the coordinate-bearing profile; its object must be a named BFO process. Enforce these rules with `valuenet-core-shapes.ttl`.

## 3. Worked Examples

### Example 1: Courage and Honesty

*   **Text:** "Despite the risk, the journalist published the story to expose the corruption."
*   **Text Span:** "published the story to expose the corruption"
*   **Agent:** `:theJournalist`
*   **Process:** `:publishingProcess`
*   **Values Realized:** `folk:CourageDisposition`, `folk:HonestyDisposition`

**Annotation Triples:**
```turtle
:theJournalist rdf:type cco:ont00001017 .    # cco:Agent
:article42Carrier rdf:type cco:ont00000253 ; # cco:Information Bearing Entity
  bfo:0000101 :article42Version1 .           # is_carrier_of
:article42Version1 rdf:type vn-core:TextualRepresentation ;
  vn-core:hasTextValue "Despite the risk, the journalist published the story to expose the corruption." .
:textSpan1 rdf:type vn-core:TextSpan ;
  vn-core:hasTextValue "published the story to expose the corruption" ;
  vn-core:isTextSpanOf :article42Version1 .
:textSpanSelector1 rdf:type vn-core:TextSpanSelector ;
  vn-core:hasSourceRepresentation :article42Version1 ;
  vn-core:selectsTextSpan :textSpan1 ;
  vn-core:hasStartOffset "33"^^xsd:nonNegativeInteger ;
  vn-core:hasEndOffset   "77"^^xsd:nonNegativeInteger .
:evidenceAnnotation1 rdf:type vn-core:ValueEvidenceAnnotation ;
  vn-core:hasEvidenceSource :textSpan1 ;
  vn-core:hasSelector :textSpanSelector1 ;
  vn-core:isEvidenceFor :publishingProcess .
:publishingProcess rdf:type vn-core:ValueRealizationProcess .
:publishingProcess bfo:0000057 :theJournalist .           # has_participant

# the journalist's own dispositions, as individuals
:courageOfJournalist rdf:type folk:CourageDisposition .
:honestyOfJournalist rdf:type folk:HonestyDisposition .
:theJournalist bfo:0000196 :courageOfJournalist .         # bearer_of
:theJournalist bfo:0000196 :honestyOfJournalist .

:publishingProcess bfo:0000055 :courageOfJournalist .     # realizes
:publishingProcess bfo:0000055 :honestyOfJournalist .
```

### Example 2: Role-Based Accountability

*   **Text:** "As the team captain, she took full responsibility for the loss."
*   **Text Span:** "took full responsibility for the loss"
*   **Agent:** `:theCaptain`
*   **Process:** `:takingResponsibilityProcess`
*   **Values Realized:** `folk:ResponsibilityDisposition` (a personal trait), `folk:LeaderRole` (an external role)

**Annotation Triples:**
```turtle
:theCaptain rdf:type cco:ont00001017 .
:matchReport7Carrier rdf:type cco:ont00000253 ;
  bfo:0000101 :matchReport7Version1 .
:matchReport7Version1 rdf:type vn-core:TextualRepresentation ;
  vn-core:hasTextValue "As the team captain, she took full responsibility for the loss." .
:textSpan2 rdf:type vn-core:TextSpan ;
  vn-core:hasTextValue "took full responsibility for the loss" ;
  vn-core:isTextSpanOf :matchReport7Version1 .
:textSpanSelector2 rdf:type vn-core:TextSpanSelector ;
  vn-core:hasSourceRepresentation :matchReport7Version1 ;
  vn-core:selectsTextSpan :textSpan2 ;
  vn-core:hasStartOffset "25"^^xsd:nonNegativeInteger ;
  vn-core:hasEndOffset "62"^^xsd:nonNegativeInteger .
:evidenceAnnotation2 rdf:type vn-core:ValueEvidenceAnnotation ;
  vn-core:hasEvidenceSource :textSpan2 ;
  vn-core:hasSelector :textSpanSelector2 ;
  vn-core:isEvidenceFor :takingResponsibilityProcess .
:takingResponsibilityProcess rdf:type vn-core:ValueRealizationProcess .
:takingResponsibilityProcess bfo:0000057 :theCaptain .

:responsibilityOfCaptain rdf:type folk:ResponsibilityDisposition .
:captaincyOfCaptain      rdf:type folk:LeaderRole .
:theCaptain bfo:0000196 :responsibilityOfCaptain .        # bearer_of
:theCaptain bfo:0000196 :captaincyOfCaptain .

:takingResponsibilityProcess bfo:0000055 :responsibilityOfCaptain .
:takingResponsibilityProcess bfo:0000055 :captaincyOfCaptain .
```

## 4. Best Practices

*   **Be Specific:** Always try to use the most specific value from the `valuenet-folk.ttl` hierarchy. Prefer `folk:KindnessDisposition` over the more general `vn-schwartz:BenevolenceDisposition`.
*   **Multiple Values are Good:** Human actions are complex. Don't hesitate to annotate a single process as realizing multiple values.
*   **Keep Bearers Aligned:** For every value instance that a process realizes, record its bearer and include at least one recorded bearer among that process's participants.
*   **Disposition vs. Role:** Remember the difference. Is the value coming from *within* the person (a disposition) or from the *expectations of their position* (a role)? Sometimes, it's both, as in the captain example above.
*   **Focus on the Action:** The central point of the annotation is always the `ValueRealizationProcess`. Start by finding the verb or action phrase in the text.
*   **Version the Exact String:** Give every `TextualRepresentation` one canonical string and mint a new representation when that string changes. Keep its carrier separate.
*   **Put Coordinates on Selectors:** A `TextSpan` carries substring content; a `TextSpanSelector` carries the complete offset pair and points back to the exact representation.
*   **Not Every Act Realizes a Value:** An act that runs against a value uses `vn-core:contravenes` and is a `vn-core:ValueViolationProcess`, not a `ValueRealizationProcess`. The two are not mutually exclusive: one act can realize one value while contravening another.
