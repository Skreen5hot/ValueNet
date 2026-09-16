<!--
Provenance (added on receipt; not part of the review)

  received        2026-09-16
  reviewed commit ae52f464412a
  reviewer's CCO  Version 2.0 (tag v2.0-2024-11-06, commit 510dad76be0e), as
                  supplied to the reviewer. ValueNet pins CCO v2.2 (commit
                  0bc7d33e1bc0); see the response for what that does and does
                  not change.
  response        FORMAL_REVIEW_2026-09-16_RESPONSE.md, beside this file

Recorded verbatim. Nothing below this comment has been edited.
-->

# Formal ontology review: BFO-Aligned ValueNet

I completed an architecture-level formal review of the current published suite at commit `ae52f464412a`, concentrating on the Core, Moral Foundations, Moral Epistemics, mappings, SHACL constraints, Schwartz values, representative Folk values, and the linguistic/evidence pattern. The site currently publishes eleven reviewed Turtle deliverables. 

One correction to my earlier interim finding is important: **the agent-bearer OWL axiom is present**. It occurs near the end of `valuenet-core.ttl`, where `ValueRelatedRealizableEntity` is restricted by `BFO_0000197 inheres in some cco:Agent`. The SHACL documentation is therefore correct on that point. 

## Overall determination

**ValueNet is genuinely BFO-shaped and substantially BFO-aligned, but it does not yet satisfy the stricter BFO/CCO conformance profile you have specified.**

Its strongest aspect is the ontological separation of values, agents, processes, information entities, and realizations. Its weakest aspect is **CCO reuse discipline**, especially in the linguistic/evidence layer and in several project-authored object/data properties.

My formal status would be:

| Area | Determination |
|---|---|
| BFO continuant/occurrent discipline | **PASS** |
| Disposition/role distinction | **PASS** |
| BFO realization pattern | **PASS** |
| Agent bearer semantics | **PASS** |
| CCO class reuse | **PASS WITH CONCERNS** |
| CCO/ERO relation reuse | **NOT YET CONFORMANT** |
| Linguistic/evidence modeling | **MAJOR REVISION REQUIRED** |
| Moral Foundations modeling | **CONDITIONALLY ACCEPTABLE** |
| Moral Epistemics modeling | **PASS WITH MATERIAL ISSUES** |
| Definition discipline under RULES 2.0 | **NOT CONFORMANT** |
| Documentation/ontology synchronization | **MINOR–MODERATE ISSUES** |
| Strict certification against supplied CCO 2.0 | **NOT YET CERTIFIABLE** |

The last point is partly a governance issue: the published ValueNet Core imports a project-specific **CCO 2.2 / 2026-08-25 extract**, whereas the CCO files supplied here are **Version 2.0 / 2024-11-06**.  The attached Extended Relations Ontology explicitly identifies itself as CCO Version 2.0.  Consequently, I can certify conformance only against the supplied 2.0 corpus—not assume that a 2.2 relation or changed modeling convention supersedes it.

---

## 1. Core value pattern — PASS

The central modeling decision is defensible and well implemented.

`ValueRelatedRealizableEntity` is a subclass of BFO `realizable entity`; it is exhaustively defined as the union of `ValueDisposition` and `ValueRole`. `ValueDisposition` is also a BFO `disposition`; `ValueRole` is also a BFO `role`. `ValueRealizationProcess` is a BFO `process` equivalent to a process that `BFO_0000055 realizes` some value-related realizable entity. 

This corresponds closely to BFO itself. A BFO disposition is an internally grounded realizable entity, whereas a role is externally grounded in contingent physical, social, or institutional circumstances.   BFO's `realizes` relation has process as domain and realizable entity as range. 

The explicit bearer axiom is also correct:

`ValueRelatedRealizableEntity ⊑ inheres in some cco:Agent`

and the SHACL layer additionally verifies that recorded bearers are Agents and that, when a value is actually realized, at least one recorded bearer participates in the realizing process.  BFO's own `inheres in` relation is precisely the relation from specifically dependent continuants to their independent-continuant bearers. 

**Finding:** no BFO category error here.

The choice not to declare `ValueRealizationProcess` and `ValueViolationProcess` disjoint is also sensible. A process may realize one value while running contrary to another. 

---

## 2. `contravenes` — conditional acceptance, but not strict CCO reuse

This is the most important relation-governance issue.

ValueNet creates:

`vn-core:contravenes`

with domain BFO Process and range `ValueRelatedRealizableEntity`. Its intended meaning is that a process runs contrary to the characteristic realization of a value-related realizable entity. It is then used to define `ValueViolationProcess`. 

Following your required procedure, I checked the supplied **Extended Relations Ontology first**.

The closest existing CCO relation is `cco:ont00001888 disrupts`, but its signature is **Process → Process**, and its meaning is causal/processual: one process prevents, degrades, or stops another process from occurring as it otherwise would. Its scope explicitly includes cases where a process prevents a disposition or role from being realized **by another process**. 

ERO also contains `inhibits`, again Process → Process, with an explicit causal structure involving a decrease of realizable entity and the process in which that entity is realized. 

Therefore:

**`disrupts` is not semantically equivalent to `contravenes`.**

A cheating process may normatively contravene fairness without causally disrupting an actual fairness-realizing process. Replacing `contravenes` mechanically with `disrupts` would change the ontology's meaning.

At the same time, ValueNet's current comment merely says that a process cannot both realize and violate the same value and therefore “violation requires a relation of its own.”  That is not enough under your new-property policy. It demonstrates a need for *some representation*, not necessarily a new primitive relation.

My disposition is therefore **CONDITIONAL ACCEPTANCE**. No equivalent relation exists in the supplied ERO. If competency questions genuinely require direct Process → Value-Realizable-Entity normative contravention, a project-local extension can be defended. But ValueNet should document the ERO alternatives explicitly and state why `disrupts`, `inhibits`, realization patterns, and norm-centered ICE modeling fail the required competency questions.

Until that is documented, `contravenes` fails the project's **relation reuse governance test**, even though it is not obviously ontologically incorrect.

---

## 3. `hasInformationalInput` and `hasInformationalOutput` — unnecessary new object properties

This is clearer.

Moral Epistemics creates:

`hasInformationalInput ⊑ cco:has input`

and

`hasInformationalOutput ⊑ cco:has output`

with their ranges narrowed to `Information Content Entity`. 

But the supplied ERO already provides `cco:ont00001921 has input`, Process → Continuant, where the input's presence at the beginning is necessary for the process to start.  It likewise provides `cco:ont00001986 has output`, Process → Continuant, where the output's presence at the end is necessary for completion. 

No new relation is required merely because the fillers are ICEs. The class axioms can directly say, for example:

`cco:has input some BehavioralObservationICE`

and

`cco:has output some MoralAssessmentICE`.

That already supplies the desired range specialization locally.

**Finding: MAJOR REUSE VIOLATION under the strict profile.**

Recommendation: retire both project-local object properties and use the two existing CCO ERO relations directly.

This change would actually simplify Moral Epistemics without sacrificing inference.

---

## 4. Linguistic representation layer — the most serious CCO conflict

The current Core declares `TextualRepresentation` to be a CCO Information Content Entity defined as one exact, version-specific sequence of Unicode code points. It then creates a project-local `hasTextValue` datatype property whose domain is CCO ICE. 

Against the supplied CCO 2.0, that is problematic for two independent reasons.

First, CCO defines an Information Content Entity as informational content generically dependent upon an Information Bearing Entity. Its scope note explicitly says ICE subtyping should be based on the entity the ICE is **about**, rather than characteristics such as format, language, measurement scale, or media. 

An “exact version-specific Unicode code-point sequence” is primarily a representational/token-level criterion, not an aboutness criterion.

More decisively, CCO 2.0 already has:

`cco:ont00001765 has text value`

and its domain is **Information Bearing Entity**, not Information Content Entity. 

ValueNet has therefore created an almost identically named datatype property but changed the ontological category of its subject.

That is exactly the sort of duplication your reuse policy is intended to prevent.

### Required redesign

The text-bearing part of the pattern should be reconsidered around CCO's ICE/IBE distinction.

CCO defines `Information Bearing Entity` as an Object upon which an ICE generically depends.  It also already provides `is excerpted from` between Information Bearing Entities. 

Accordingly, a more CCO-native design would separate:

**textual content as ICE**

from

**the particular encoded/text-bearing representation against which character offsets are calculated as an IBE or appropriate information-bearing artifact**.

The existing CCO `has text value` should then carry the actual string.

I would **not approve `vn-core:hasTextValue`** under the supplied CCO 2.0 baseline.

Severity: **MAJOR**.

---

## 5. `TextSpanSelector` misses an existing CCO designative pattern

`TextSpanSelector` is currently merely an ICE that “identifies” a text span, and ValueNet creates `selectsTextSpan` to relate it to that span. 

CCO already contains `Designative Information Content Entity`: an ICE consisting of symbols that designate an Entity.  It also supplies the object property `designates`. 

A selector whose defining function is to identify a particular span is therefore an obvious candidate for this existing designative pattern.

**Finding: CCO reuse opportunity sufficiently strong to require redesign before creating `selectsTextSpan`.**

At minimum, `TextSpanSelector` should be reviewed as a subtype of CCO Designative ICE and the existing `designates` relation tested against the competency questions.

This may eliminate another custom object property.

---

## 6. `EvidenceSource` is classified by contingent use — ontologically questionable

`EvidenceSource` is an ICE defined as:

> an ICE “used as the subject of an assertion that it supplies evidence for some process.”

Its differentia is therefore not what the information content *is*, but the contingent way in which someone is using it. 

That is role-like rather than content-essential.

The supplied CCO materials provide corroborating evidence for this interpretation: the Event Ontology explicitly describes introducing an artifact “as a piece of evidence in a trial” as a case of **role creation**, not a modification of the artifact itself. 

Thus an ICE should not normally change ontological type merely because an annotation workflow begins using it as evidence.

**Finding: MAJOR CLASSIFICATION CONCERN.**

The concrete `ValueEvidenceAnnotation` may perfectly reasonably be an ICE—indeed probably a **Descriptive ICE**—because it records an assertion. But “evidence source” as defined here is a context-dependent status of an entity.

I found no sufficiently specific named Evidence Role in the supplied CCO files that I would authorize reusing without further evidence. So I am **not proposing a new class**. The safe conclusion is narrower: the existing `EvidenceSource ⊑ ICE` classification should not be retained solely on the present use-based differentia.

---

## 7. `isEvidenceFor` — reasonable as non-logical metadata, but semantically weak

ValueNet deliberately makes `isEvidenceFor` an **annotation property**, specifically to avoid imposing OWL consequences when text is connected to reality. SHACL then checks that its source is an approved evidence individual and that its target is a BFO process. 

That design choice is defensible if the goal is metadata/provenance rather than ontological inference.

It should, however, be clearly documented that:

**OWL does not know that evidence supports anything.**

The domain and range attached to the annotation property are documentary and are not usable in OWL class restrictions; ValueNet itself acknowledges this. 

So I rate this **PASS WITH LIMITATION**, rather than a violation.

---

## 8. Moral Foundations pattern — category structure is good; normative target remains debatable

The six foundation classes are dispositions, and Harm/Cheating/Betrayal/Subversion/Degradation/Oppression are processes. This correctly avoids turning “harm” into a psychological disposition. 

That is a real improvement over loosely reifying words without regard to BFO category.

The deeper issue is that:

`HarmProcess contravenes some CareDisposition`

requires the target of contravention to be a **particular realizable-entity instance**, hence ultimately something borne by an agent.

Conceptually, however, the phrase “harm violates care” can mean either:

1. a process runs contrary to an actual agent's care disposition, or
2. a process violates a normative principle of care irrespective of whether some particular agent bears that disposition.

ValueNet currently chooses the former ontological reading.

That choice is coherent, but it must be stated explicitly. Otherwise a moral foundation universal is liable to be confused with an agent-dependent disposition instance.

This matters particularly because the Moral Epistemics module already recognizes `MoralNormICE` as a **Prescriptive Information Content Entity**, which is an excellent CCO distinction.  If some competency questions concern violation of a normative rule rather than contravention of an individual's value disposition, those should not be collapsed.

Severity: **CONCEPTUAL CONCERN, not BFO violation**.

There is also a documentation inconsistency: the Modules page describes the ontology as Haidt's five foundations—Care, Fairness, Loyalty, Authority, Sanctity—while the actual published model contains a sixth Liberty/Oppression pair. 

---

## 9. Moral Epistemics: several very good CCO modeling decisions

This is probably the strongest extension module.

`ObservationalEvidenceICE` is under Descriptive ICE; `MoralNormICE` is under Prescriptive ICE; `MoralAssessmentICE` is under Descriptive ICE.  These distinctions respect CCO's information-entity architecture.

`CulpabilityAscriptionICE` also contains an especially good safeguard: it describes an Agent but deliberately **does not existentially require a MoralCulpabilityRole**, because a false assertion that someone is culpable must not cause OWL to manufacture actual culpability. 

That is correct realist modeling.

Similarly, `ActOfBehavioralObservation` reuses CCO `Act of Observation` and explains why the observed process is not incorrectly treated as an input. 

Those decisions should be preserved.

---

## 10. Hidden “Planned Act” commitment in MoralAssessmentAct

There is nevertheless a significant issue with `MoralAssessmentAct`.

ValueNet subclasses it from CCO `Act of Appraisal`. 

In the supplied CCO Event Ontology, Act of Appraisal is downstream of **Act of Measuring**, and CCO defines Act of Measuring as a **Planned Act** that determines an entity's extent, dimensions, quantity, or quality relative to some standard. 

Therefore every ValueNet `MoralAssessmentAct`, including every `RashJudgmentAct`, inherits plannedness.

But ValueNet's definition merely says:

> an act of appraisal in which an agent evaluates another agent or conduct under an actual or purported moral standard...

It does not state that the assessment is planned. 

This creates a hidden parent-class commitment.

The formal question is simple:

**Does ValueNet intend to exclude spontaneous, unplanned moral judgments?**

If yes, plannedness needs to appear in the definition and documentation.

If no, `Act of Appraisal` is too narrow as the universal parent.

Severity: **MAJOR INCLUSIVENESS ISSUE**.

---

## 11. `AgentBehaviorProcess` contains an internal definition/comment contradiction

`AgentBehaviorProcess` is defined as a process in which an agent participates and “which is available to the senses of other agents.” Immediately afterward, its comment says observability **is not a feature of the process** but rather of the relation between process and perceiver. 

The comment is ontologically preferable, but it contradicts the definition.

Moreover, the class has no shown existential restriction requiring an Agent participant, despite participation being part of its defining text.

A BFO/CCO-aligned repair can use only existing vocabulary:

`AgentBehaviorProcess ⊑ BFO has participant some cco:Agent`

and remove observability from its essential differentia.

Severity: **MODERATE**, but easy to fix.

---

## 12. `MoralCulpabilityRole` needs tighter existential criteria

The class definition says a Moral Culpability Role inheres in an agent **because a norm-governed moral appraisal treats the agent as accountable**. Yet its comment says a culpability ascription does not entail that the target actually bears this role. 

The desired distinction is good, but the definition is not sufficiently exclusive.

A false appraisal still “treats the agent as accountable.” If mere treatment grounds the role, the comment's safeguard is undermined conceptually even if not currently undermined by OWL axioms.

The differentia should distinguish an **actual externally grounded normative status** from merely being represented as having one.

Severity: **MODERATE CLARITY/EXCLUSIVENESS DEFECT**.

---

## 13. Definition policy — systematic nonconformance with your RULES 2.0

Your supplied rules require definitions in the form:

**“b is a c that d's”**

with the immediate parent as genus, followed by a distinguishing differentia. They also require each ontology term to carry `rdfs:label`, `skos:definition`, `rdfs:comment`, and `skos:example`.  

ValueNet does not consistently meet that profile.

The Schwartz module, for example, defines classes with forms such as “A personal value disposition to seek...” and provides neither class-specific comments nor examples for the classes shown. 

The Folk ontology exhibits the same pattern: definitions such as “A personal value disposition to...” are widespread, while the reviewed portion contains no `skos:example` annotations at all. 

The Moral Foundations definitions similarly say things such as “A disposition to...” rather than using the actual immediate genus `Moral Value Disposition`. 

This is not an OWL consistency error. But under **your formal ontology-development standard**, it is a systematic curation failure.

Severity: **MAJOR TERMINOLOGICAL NONCONFORMANCE**.

There are also lexical examples that need individual inclusiveness/exclusiveness review. `OpennessDisposition`, for example, combines transparency/candor with openness to experiences, which are distinct senses, while `FaithDisposition` combines confidence/trust with religious doctrinal belief.  These definitions risk conflating different realizable dispositions under one label.

---

## 14. Mapping layer — good ontology policy, but the public diagram reverses the assertion

The decision to use weak annotation mappings instead of `owl:equivalentClass` is good. The Core explicitly states that the mapping predicates assert neither identity nor extension inclusion. 

However, the website says:

`HaidtValues#Care historicallyCorrespondsTo CareDisposition`

whereas the actual Turtle asserts:

`CareDisposition historicallyCorrespondsTo HaidtValues#Care`. 

This matters because `historicallyCorrespondsTo` is not declared symmetric.

The module description agrees with the Turtle: it says mappings run **from BFO-aligned ValueNet entities to original entities**. 

Therefore the diagram documentation is wrong and should be corrected.

Severity: **MODERATE DOCUMENTATION DEFECT**.

---

# Required remediation before strict approval

My recommended correction order is:

1. **Freeze the conformance baseline.** Decide whether the authoritative target is supplied CCO 2.0 or the newer project CCO 2.2 extract. No formal certification should mix them silently.
2. **Replace `vn-core:hasTextValue` with the existing CCO `has text value` pattern** and redesign the TextualRepresentation/TextSpan carrier-content distinction accordingly. This is the highest-priority CCO defect. 
3. **Re-evaluate TextSpanSelector against CCO Designative ICE + `designates`**, and TextSpan against the CCO IBE/excerpt pattern where applicable.  
4. **Remove `hasInformationalInput` and `hasInformationalOutput` unless an unambiguous competency question demonstrates that the CCO parent relations cannot express the required semantics.** At present I see no such necessity.
5. **Rework EvidenceSource.** Its current use-based differentia should not make it an ICE subtype.
6. **Retain `contravenes` only after a formal extension justification** showing why ERO `disrupts`, `inhibits`, realization modeling, and norm-centered modeling cannot satisfy the required competency questions.
7. **Resolve the Planned Act commitment** inherited by MoralAssessmentAct.
8. **Repair AgentBehaviorProcess and MoralCulpabilityRole definitions**, then apply the mandated clarity/inclusiveness/exclusiveness checks.
9. **Normalize all definitions to the required genus–differentia format and add required comments/examples.**
10. **Fix the mapping-arrow direction and five-versus-six-foundation documentation discrepancies.**

## Final judgment

I would **not reject BFO-Aligned ValueNet as a whole**. The project has made several nontrivial, correct ontological decisions: values are not confused with acts or text labels; role versus disposition is respected; realization uses BFO correctly; bearer semantics are explicit; process violations remain occurrents; informational outputs are separated from acts; and false culpability ascriptions are carefully prevented from manufacturing real culpability statuses. Those are substantial strengths. 

But I also would **not certify the current release as strictly BFO/CCO conformant under your rules**. The principal blocking issues are the duplicate/non-reused CCO text-value modeling, avoidable object-property proliferation, the evidence-source category choice, the CCO version-baseline mismatch, and systematic definition-policy nonconformance.

The most consequential discovery is probably this one: **CCO 2.0 already has `has text value`, with Information Bearing Entity as its domain.** That changes how I would architect the entire linguistic-grounding portion of ValueNet and should be addressed before refining the smaller lexical classes. 
