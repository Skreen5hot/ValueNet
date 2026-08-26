# ValueNet Ontology Testing Framework

This document outlines a rigorous framework for testing, validating, and refining the ValueNet ontology suite, particularly the `valuenet-folk.ttl` module. The goal is to ensure the ontology is logically consistent, structurally sound, and adheres to high-quality development standards.

## Part 1: Automated Reasoner Validation

The most fundamental test is to check for logical consistency using an OWL reasoner (e.g., HermiT, Pellet, ELK). This should be done regularly during development, typically within an ontology editor like Protégé.

**Procedure:**
1.  Load the `valuenet-folk.ttl` ontology (which imports the core and Schwartz modules).
2.  Start the reasoner (e.g., `Reasoner -> Start Reasoner`).
3.  Check for unsatisfiable classes. An unsatisfiable class (one that is equivalent to `owl:Nothing`) indicates a logical contradiction in the axioms. Any such classes must be investigated and fixed immediately.

## Part 2: SPARQL-based Sanity Checks

These SPARQL queries help identify potential modeling errors, inconsistencies, or violations of best practices that a reasoner might not flag as a logical contradiction.

---

### Query 1: Disjoint Parentage Check

**Purpose:** To find any folk value that has been incorrectly classified under two different high-level Schwartz values. Since the Schwartz values are intended to be distinct motivational types, a direct subclass relationship to two of them is a likely modeling error.

```sparql
# scope: component:bfo.ontology-tree
# expect: no-rows
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX folk: <https://fandaws.com/ontology/bfo/valuenet-folk#>
PREFIX vn-schwartz: <https://fandaws.com/ontology/bfo/valuenet-schwartz-values#>
PREFIX vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#>

SELECT ?folk_value ?parent1 ?parent2
WHERE {
  ?folk_value a owl:Class .
  FILTER(STRSTARTS(STR(?folk_value), STR(folk:)))

  ?folk_value rdfs:subClassOf ?parent1 .
  ?folk_value rdfs:subClassOf ?parent2 .
  FILTER(STR(?parent1) < STR(?parent2))

  FILTER EXISTS { ?parent1 rdfs:subClassOf* vn-core:PersonalValueDisposition }
  FILTER EXISTS { ?parent2 rdfs:subClassOf* vn-core:PersonalValueDisposition }
}
```

> **Why this shape.** The query originally placed both `rdfs:subClassOf*` paths
> as ordinary patterns, which rdflib evaluates as two independent path searches
> and then joins. Over the 2,610-triple BFO layer that took **282 seconds** —
> runnable in principle, never run in practice, and far too slow to sit in a
> test. Moving each path into `FILTER EXISTS` turns it into a check against an
> already-bound parent and brings the query to **0.85 seconds**, with a planted
> two-parent violation still detected. `STR(?parent1) < STR(?parent2)` replaces
> `!=`, which also stops each offending pair being reported twice in opposite
> orders.

---

### Query 2: Missing Metadata Check

**Purpose:** To ensure every class in the folk ontology has a human-readable label and a definition, which is essential for usability and maintenance.

```sparql
# scope: component:bfo.ontology-tree
# expect: no-rows
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX folk: <https://fandaws.com/ontology/bfo/valuenet-folk#>

SELECT ?class
WHERE {
  ?class a owl:Class .
  FILTER(STRSTARTS(STR(?class), STR(folk:)))
  
  FILTER NOT EXISTS { ?class rdfs:label ?label . }
  # Or use the query below for definitions
  # FILTER NOT EXISTS { ?class folk:definition ?def . }
}
```

---

### Query 3: Redundant Broader Conceptual Mapping Check

**Purpose:** To find classes where the annotation-only `vn-core:hasBroaderConceptualMatch` points to the same parent as a formal `rdfs:subClassOf` axiom. The logical inclusion makes the conceptual annotation redundant and potentially confusing.

```sparql
# scope: component:bfo.ontology-tree
# expect: no-rows
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX vn-core: <https://fandaws.com/ontology/bfo/valuenet-core#>

SELECT ?class ?redundant_parent
WHERE {
    ?class rdfs:subClassOf ?redundant_parent .
    ?class vn-core:hasBroaderConceptualMatch ?redundant_parent .
}
```

## Part 3: Manual Review and Coverage Analysis

1.  **Definition Review (Task 3.2):** Manually review the definitions for all classes within each cluster to ensure they are sufficiently distinct and avoid ambiguity. For example, check that the definitions for `EqualityDisposition` and `EquityDisposition` clearly articulate the difference.
2.  **Axiom Review (Task 3.3):** Manually review the use of `rdfs:subClassOf` versus `vn-core:hasBroaderConceptualMatch`. Promote a mapping only when every instance of the source universal is an instance of the target universal. Do not infer equivalence from lexical closeness.
3.  **Coverage Analysis:** Compare the set of all modeled classes in `valuenet-folk.ttl` against the `Primary Value Concepts` list in `Phase1_NormalizedTerms.md`. Identify any high-priority concepts that were missed during the modeling sprints and schedule them for a future iteration.
