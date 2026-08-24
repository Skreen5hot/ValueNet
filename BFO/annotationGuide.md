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

> **Instances, not classes.** A value disposition is a real property of *one particular agent*, so what a process realizes is that agent's individual disposition, not the class. Mint an instance of the disposition class first (`:courageOfJournalist a folk:CourageDisposition`) and relate the process and the agent to *that*. Writing `:someProcess bfo:0000055 folk:CourageDisposition` points a relation at a class rather than an individual; it is OWL 2 punning, falls outside OWL 2 DL, and produces data that reasoners and SHACL shapes cannot check.

1.  Mint an **instance** of each `ValueDisposition` / `ValueRole` class you selected in Step 3.
2.  The `Agent` **bears** that disposition instance (`bfo:bearer_of`, `BFO_0000196`).
3.  The `ValueRealizationProcess` **has as participant** the `Agent` (`bfo:has_participant`, `BFO_0000057`; the inverse, `bfo:participates_in`, is `BFO_0000056`).
4.  The `ValueRealizationProcess` **realizes** that disposition instance (`bfo:realizes`, `BFO_0000055`).

### Step 5: Link to the Text

Finally, mint the text span itself and link it to the `ValueRealizationProcess` you identified.

A `vn-core:TextSpan` carries four things:

| Property | Purpose |
| --- | --- |
| `vn-core:hasTextValue` | the literal text of the span — use this, not `rdfs:label` |
| `vn-core:isTextSpanOf` | the document or transcript the span came from |
| `vn-core:hasStartOffset` / `vn-core:hasEndOffset` | zero-based character offsets, end exclusive |
| `vn-core:isEvidenceFor` | the process the span attests to |

Optionally add `vn-core:evokesFrame` pointing at the semantic frame a parser assigns to the span. That is the bridge to the existing MFTriggers data: the frame is the subject of `vcvf:triggers` statements whose objects are Haidt values, which the BFO-aligned dispositions reach by `skos:broadMatch`. It lets a span reach a value disposition through the 12,338 trigger statements already in the repository, without re-annotating anything.

`isEvidenceFor` is an annotation property, so a reasoner will not enforce its domain and range and it cannot be used in a class restriction. Enforce annotation well-formedness with the SHACL shapes in `valuenet-core-shapes.ttl` instead.

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
:article42 rdf:type bfo:0000031 .            # the source document
:textSpan1 rdf:type vn-core:TextSpan ;
  vn-core:hasTextValue "published the story to expose the corruption" ;
  vn-core:isTextSpanOf :article42 ;
  vn-core:hasStartOffset "18"^^xsd:nonNegativeInteger ;
  vn-core:hasEndOffset   "62"^^xsd:nonNegativeInteger ;
  vn-core:isEvidenceFor  :publishingProcess .
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
:matchReport7 rdf:type bfo:0000031 .
:textSpan2 rdf:type vn-core:TextSpan ;
  vn-core:hasTextValue "took full responsibility for the loss" ;
  vn-core:isTextSpanOf :matchReport7 ;
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
*   **Disposition vs. Role:** Remember the difference. Is the value coming from *within* the person (a disposition) or from the *expectations of their position* (a role)? Sometimes, it's both, as in the captain example above.
*   **Focus on the Action:** The central point of the annotation is always the `ValueRealizationProcess`. Start by finding the verb or action phrase in the text.
*   **Record the Span, Not Just the Link:** Always give a `TextSpan` a `hasTextValue` and a source. A span that only carries `isEvidenceFor` cannot be checked, re-read, or re-scored later, and the annotation becomes unauditable as soon as the source corpus changes.
*   **Not Every Act Realizes a Value:** An act that runs against a value uses `vn-core:contravenes` and is a `vn-core:ValueViolationProcess`, not a `ValueRealizationProcess`. The two are not mutually exclusive: one act can realize one value while contravening another.
