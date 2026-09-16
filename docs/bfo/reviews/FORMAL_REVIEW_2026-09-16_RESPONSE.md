# Response to the formal ontology review of 2026-09-16

The review is recorded verbatim in `FORMAL_REVIEW_2026-09-16.md`. This document
records what was done with it: every claim checked against the repository before
being accepted, the places where the check disagreed, and what to do next.

It decides nothing. Several recommendations below are ontology decisions, and they
are marked as such. The recommendation is offered; the decision belongs to whoever
owns the ontology, and should be recorded in `docs/bfo/remediation/DECISION_RECORDS.md`
when it is taken.

**Since written:** the reviewer replied twice the same day. The first reply withdrew
the original recommendation behind R9, which was revised and provisionally adopted as
D-005 (§9). The second accepted C1, C2 and D-005 in substance and raised three further
points (§10). The reviewer then signed off on the response and the plan, and the owner
instructed that it proceed; what has been implemented is in §11.

---

## 1. How the review was checked

Nothing was accepted on the reviewer's word, and nothing was rejected on ours.

- **The ontology.** Every class, property, axiom, definition and comment the review
  cites was read out of the Turtle at `ae52f464412a` — the commit the review names,
  and the repository's `HEAD` when this was written. Counts were measured, not
  estimated.
- **CCO, at both versions.** The reviewer was supplied CCO **2.0**; ValueNet pins
  CCO **2.2**. Both were fetched at their release commits — `v2.0-2024-11-06`
  (`510dad76be0e`) and `v2.2` (`0bc7d33e1bc0`) — and every CCO term the review
  cites was compared across the two. See §4.
- **The decision records.** `docs/bfo/remediation/` was searched for each term, to
  separate findings that are *oversights* from findings that *disagree with a
  recorded decision*. The two need different handling: an oversight is fixed; a
  disagreement is adjudicated.
- **The site.** The two documentation findings were traced to their source, because
  the site derives some text from the ontology and the fix belongs where the text
  originates.

---

## 2. Verdict on each finding

| § | Finding | Review | Verified | What the check showed |
|---|---|---|---|---|
| 1 | Core value pattern | PASS | **Confirmed** | Bearer axiom, `ValueDisposition ∪ ValueRole` equivalence, realization equivalence, and both SHACL bearer checks are present as described. |
| 2 | `contravenes` | Conditional | **Confirmed** | No record anywhere weighs `disrupts`, `inhibits`, or a norm-centred alternative. |
| 3 | `hasInformationalInput/Output` | Major reuse violation | **Confirmed — contradicts a recorded decision** | `EXTERNAL_TERM_INVENTORY.md` records "Retain; the local subproperty narrows the range to ICE." Needs adjudication, not a silent fix. |
| 4 | `hasTextValue` duplicates CCO | Major | **Confirmed as a misclassification; the recommended fix is revised** | CCO `has text value` (`ont00001765`), domain **Information Bearing Entity**, is identical in 2.0 and 2.2, and no record ever weighed it. But it cannot be applied to ValueNet's textual representation without making the ontology inconsistent, and the reviewer has withdrawn the replacement. What stands is the ICE placement. See R9 and D-005. |
| 5 | `TextSpanSelector` vs Designative ICE | Redesign | **Confirmed — oversight** | `designates` and Designative ICE appear in no record. CCO 2.2 *strengthens* the case: `designates` now has Designative ICE in its definition and `entity` as range. |
| 6 | `EvidenceSource` classified by use | Major | **Confirmed, and sharper** | `TextSpan ⊑ EvidenceSource`, so every text span is classified as "used as the subject of an evidence assertion" whether or not anyone ever cites it. |
| 7 | `isEvidenceFor` as annotation | Pass with limitation | **Confirmed** | The property's own comment already states the limitation. |
| 8 | Moral Foundations target; five vs six | Conceptual + doc | **Confirmed** | The five-foundation text is the module's own `dcterms:description`, which the site copies. The same sentence says "modeled as BFO dispositions"; 6 of its 12 classes are processes. |
| 9 | Moral Epistemics strengths | Pass | **Confirmed** | |
| 10 | Hidden Planned Act commitment | Major | **Confirmed — genuine gap** | Phase 6 recorded plannedness for `ActOfBehavioralObservation` ("every instance is a planned … act") and did not for `MoralAssessmentAct`. `RashJudgmentAct` therefore inherits Planned Act. |
| 11 | `AgentBehaviorProcess` | Moderate | **Partly wrong** | The definition/comment contradiction is real. The claimed missing restriction is not: `has participant some Agent` is asserted. |
| 12 | `MoralCulpabilityRole` | Moderate | **Confirmed, and sharper** | The ontology supplies its own counterexample — N3 in §5. |
| 13 | Definition discipline | Major | **Partly overstated** | Genus is aligned in core (12/12) and Schwartz (10/10). The gap is concentrated in folk, Moral Foundations and Moral Epistemics. Comments and examples are sparse everywhere — against a standard the repository has not adopted. |
| 14 | Mapping arrow reversed on the site | Moderate doc | **Confirmed** | Reversed in both the diagram and its text alternative. |
| — | CCO version baseline | Not certifiable | **Real, but changes no finding** | Every cited CCO term compared across 2.0 and 2.2; §4. |

---

## 3. Corrections to the review

**C1 — `AgentBehaviorProcess` does have its participation axiom.** The review says the
class "has no shown existential restriction requiring an Agent participant." It has
exactly the axiom the review proposes:

```turtle
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix obo:   <http://purl.obolibrary.org/obo/> .
@prefix cco:   <https://www.commoncoreontologies.org/> .
@prefix vn-me: <https://fandaws.com/ontology/bfo/valuenet-moral-epistemics#> .

# BFO_0000057 has participant; ont00001017 Agent
vn-me:AgentBehaviorProcess rdfs:subClassOf [ a owl:Restriction ;
    owl:onProperty obo:BFO_0000057 ;
    owl:someValuesFrom cco:ont00001017 ] .
```

The definition/comment contradiction stands and should be fixed (R7).

**C2 — The definition gap is concentrated, not systematic.** Measured over all 187
classes in the five modules that declare them, taking "genus-aligned" to mean the
definition opens with the label of an asserted named parent:

| module | classes | genus-aligned | `rdfs:comment` | `skos:example` |
|---|---:|---:|---:|---:|
| `valuenet-core` | 12 | **12** | 10 | 5 |
| `valuenet-schwartz-values` | 10 | **10** | 0 | 0 |
| `valuenet-moral-epistemics` | 17 | 11 | 15 | 2 |
| `valuenet-moral-foundations` | 12 | 6 | 0 | 0 |
| `valuenet-folk` | 136 | 52 | 0 | 0 |
| **total** | **187** | **91** | **25** | **7** |

The review's examples are accurate. Its word "systematic" fits the comment and example
columns, not the genus column. The Schwartz definitions it quotes ("A personal value
disposition to seek…") use their asserted parent as genus; they differ from the
supplied rule only in phrasing the differentia with *to* rather than *that*.

This also matters for what "nonconformance" means here. **RULES 2.0 is not in this
repository** (it was recorded later; see §11). ValueNet's own remediation plan committed to genus-differentia for
*core* definitions (Objective 3, ALN-004) — a commitment that is met — and did not
adopt the comment-and-example requirement at all. Against the user-supplied rules the
review is right; against the repository's own standard, the comment and example gap is
a decision not yet taken, not a regression (R2).

**C3 — The version mismatch does not overturn anything.** See §4. For the audit record,
in the wording the reviewer asked for: *the original external review was conducted
against supplied CCO 2.0; ValueNet subsequently verified each implicated term against
its normative CCO 2.2 baseline and found no disposition-changing difference.* That is
not a certification of the ontology against 2.2 by the reviewer.

---

## 4. The CCO version question

The reviewer certified against CCO 2.0; ValueNet pins, extracts, and tests against CCO
2.2. Both releases were compared on every CCO term the review relies on:

| CCO term | 2.0 | 2.2 | Effect on the review |
|---|---|---|---|
| `has text value` (`ont00001765`) | domain IBE | domain IBE | none between versions; under both, the property cannot be applied to a form-level text (R9) |
| `disrupts` (`ont00001888`) | Process → Process | identical | none |
| `inhibits` (`ont00001959`) | Process → Process, causal definition | Process → Process, defined via its inverse | none — still not Process → realizable entity |
| `has input` / `has output` | range `continuant` | range SDC ∪ GDC ∪ (independent continuant ∖ spatial region); defined via inverse | none — ICE is in range under both |
| Designative ICE (`ont00000686`) | "symbols that denote" | "symbols that designate" | none |
| `designates` (`ont00001916`) | no declared range | domain Designative ICE in definition; range `entity` | **strengthens** finding 5 |
| Act of Appraisal → Act of Measuring → Planned Act | yes | identical | none — finding 10 holds |
| Information Bearing Entity; `is excerpted from` | as cited | identical | none |
| ICE scope note (subtype by aboutness, not format or language) | present | identical | none — the misclassification in finding 4 holds |

**Every substantive finding holds under 2.2.** Two consequences worth keeping:

- The review quotes the CCO 2.0 definitions of `has input` and `inhibits`. In 2.2
  those definitions moved to the inverse properties. A reply to the reviewer should
  say so, so that citations are not re-checked against text that is no longer where
  it was.
- One ValueNet record is wrong under **both** versions — see N1.

---

## 5. Findings the review did not raise

**N1 — `EXTERNAL_TERM_INVENTORY.md` misstates the CCO signature.** Rows for
`has input` and `has output` say CCO "permits continuant, process, or GDC input."
Neither version permits a process: 2.0 ranges over `continuant`, 2.2 over the union
above. `ActOfBehavioralObservation`'s own comment ("its range excludes processes") is
the correct statement, and it contradicts the inventory — which is the document whose
purpose is to record verification.

**N2 — The folk genus control sampled what it did not measure.** The Phase 4 exit
records "automated controls sample one leaf from every folk-value cluster." Measured in
full, 84 of 136 folk definitions do not open with their asserted parent. A sample that
passes while the population does not is a check reporting on something adjacent to
what it claims.

**N3 — `RashJudgmentAct` is a counterexample to two definitions at once.**
It is a `MoralAssessmentAct`, so it is a Planned Act — a *rash* judgment that is
necessarily *planned* (finding 10). And it is an appraisal that treats an agent as
accountable *without warrant*, so under `MoralCulpabilityRole`'s current definition it
would ground real culpability — precisely what `CulpabilityAscriptionICE`'s comment
exists to prevent (finding 12). One class exposes both defects, which makes it the
natural negative fixture for both repairs.

**N4 — The Moral Foundations description is wrong twice in one sentence.** "Haidt's
Moral Foundations (Care, Fairness, Loyalty, Authority, Sanctity) modeled as BFO
dispositions": six foundations are modelled, and half the module's classes are
processes.

**N5 — "One of 67 such assertions."** The Models page attaches this number to a
`historicallyCorrespondsTo` example. 67 is the count of *all* mapping assertions across
the three mapping properties, matching the Phase 5 record; 17 of them are
`historicallyCorrespondsTo`. The number is also typed into the HTML rather than
derived.

**N6 — Folk coverage.** The review assessed "representative" folk values. Measured
separately, the BFO folk module carries **91 of 278** folk values from the source
corpus, and 45 of its `rdfs:seeAlso` back-links name a value the corpus does not
contain. `tools/bfo/folk_coverage.py` reports this; it is not yet committed.

---

## 6. Recommendations

Each item is marked by what it needs. **Decision** means a judgement about the
ontology or its governance, to be recorded before editing. **Mechanical** means the
correct answer is not in dispute. Following the repository's practice, every change
arrives with the check that would have caught it.

### A. Decide before editing

**R1 — Adopt CCO 2.2 as the conformance baseline.** *Decision.* It is already pinned,
extracted, reasoned over and tested; §4 shows every finding survives it. Downgrading to
2.0 would re-open settled work for no gain. *The reviewer agrees that ValueNet should
declare 2.2 as its normative baseline, while their own verification remains constrained
to the 2.0 corpus they were supplied (§10); record the distinction as C3 words it.*

**R2 — Decide whether RULES 2.0 is ValueNet's standard.** *Decision.* If yes, commit the
rules into the repository and scope them: 162 missing comments and 180 missing examples
is a content programme, not a fix, and should be paid down against a baseline rather
than attempted in one pass. If no, tell the reviewer that the comment and example
requirement is out of scope for this release.

**R3 — Adjudicate `hasInformationalInput/Output`.** *Decision.* The review contradicts a
recorded "Retain." **Recommendation: side with the review.** Every use sits inside an
existential restriction whose filler is already an ICE subclass, so the narrowed range
adds no inference the restriction does not already supply. Record the reversal as a
dated decision superseding the inventory row, then do R11.

### B. Correct now

Each is small, uncontroversial, and currently wrong on the public site or in a
verification record.

**R4 — Reverse the mapping arrow.** *Mechanical.* `site/src/models/index.html`: the
diagram edge and its text alternative. Add a test that reads the direction from the
Turtle, so the diagram cannot disagree with the assertion it depicts.

**R5 — Correct the Moral Foundations description.** *Mechanical.* One line in
`valuenet-moral-foundations.ttl`: six foundations, as dispositions and processes. The
site regenerates. Add a test that the description's foundation count matches the
declared disposition classes.

**R6 — Correct `EXTERNAL_TERM_INVENTORY.md`.** *Mechanical.* The `has input` and
`has output` rows (N1).

**R7 — Fix `AgentBehaviorProcess`'s definition.** *Mechanical.* Drop "and which is
available to the senses of other agents"; the comment already explains why. The
participation axiom exists (C1).

**R8 — Derive or reword "67 such assertions."** *Mechanical* (N5).

### C. Redesign

**R9 — Current ICE classification requires correction; form-level GDC extension
justified.** *Decision, provisionally adopted as D-005; highest priority, largest
reach.* Reopen ALN-005.

*Revised 2026-09-16.* The review's original recommendation was to replace
`vn-core:hasTextValue` with CCO `has text value`. That cannot be done. The CCO
property's domain is Information Bearing Entity, an IBE is a BFO object, and BFO makes
independent, specifically dependent and generically dependent continuants pairwise
disjoint, so on a textual representation it does not reuse a property: it changes
what the subject is, and the ontology becomes inconsistent. The reviewer withdrew the
recommendation, and `tests/bfo/test_text_value_placement.py` now pins the argument as
fourteen HermiT scenarios with two controls.

What the review did identify correctly is a misclassification. `TextualRepresentation`
is individuated by its exact sequence — its own comment says a changed string is a
different representation — while CCO subtypes Information Content Entities by what
they are about. The correction needs a level CCO's information model does not have:

| level | class | individuated by |
|---|---|---|
| content | Information Content Entity | aboutness |
| **form** | **a generically dependent continuant that is not an ICE** | **the exact sequence** |
| bearer | Information Bearing Entity | being that particular carrier |

BFO supplies it: a generically dependent continuant is "the content or the pattern
that multiple copies would share", and BFO's own example is a sequence.

**Recommended ValueNet design (D-005):**

- `TextualRepresentation` is a BFO generically dependent continuant, with the
  existential `generically depends on` (`BFO_0000084`) some Information Bearing Entity.
  Definition: *a generically dependent continuant that is one exact sequence of Unicode
  code points and that generically depends on at least one information bearing
  entity.*
- `TextSpan` is also a form-level GDC: *a continuant part of exactly one textual
  representation, individuated by a contiguous interval of code-point positions in
  it*. It is **not** a subclass of the representation and not individuated by its
  string: `"abc"` at 2–4 and `"abc"` at 20–22 are two spans. Scenarios 13 and 14
  pin that.
- The local property is retained as an extension over the uncovered level, renamed
  `vn-core:hasTextualSequenceValue` so that it no longer reads as a variant of CCO
  `has text value`, with a domain covering both classes.
- SHACL still requires an explicitly recorded carrier, since the OWL existential alone
  accepts a representation with none.
- `TextSpanSelector` becomes a Designative ICE; whether `designates` replaces
  `selectsTextSpan` is tested against the competency questions.
- It lands together with R10, because `TextSpan ⊑ EvidenceSource ⊑ ICE` would
  otherwise put spans back under ICE.

**The alternative: CCO's bearer-level pattern.** An application that does not need
copy-independent form identity — one string recorded per file, no offsets shared
across copies — should use CCO `has text value` on each Information Bearing Entity. It
is conformant and needs no extension. ValueNet is not that application: evidence
offsets and exact-sequence identity are competency requirements (D-004 items 2 and 7),
and one sequence may be carried by several files. Where a CCO consumer needs
bearer-level strings, they can be derived by query from the carrier relation, never
authored separately.

**Implementation notes.** No deprecated alias for `vn-core:hasTextValue`: the text
layer is new and has no consumers to migrate (owner's decision, §10). Add a SHACL
fixture in which the same substring occurs twice in one representation and both spans
validate. The offset and substring-equality SHACL keep their meaning:
offsets are already code-point indexes into the exact sequence. Write the negative
controls first. Add a test that `valuenet-core.ttl` itself follows D-005 — the
placement test deliberately reasons over scenario graphs, not over the published
module.

Reach, by file count: these terms appear in 2 ontology files, 1 shape file, 1–5 docs
and 4–8 test files each.

**R10 — Retire `EvidenceSource`.** *Decision; low reach.* The class does no enforcement
work: the `isEvidenceFor` shape already requires `sh:or ([sh:class TextSpan]
[sh:class ValueEvidenceAnnotation])`, naming the concrete classes. Removing it also
removes the sharper form of finding 6 recorded in §2, `TextSpan ⊑ EvidenceSource`. Update the
property's documentary domain to name the two classes. Consider
`ValueEvidenceAnnotation ⊑ Descriptive ICE`, as the review suggests. **Must land with
R9**: while `TextSpan ⊑ EvidenceSource`, moving spans to the form level would classify
them back under ICE.

**R11 — Retire `hasInformationalInput/Output`.** *Mechanical once R3 is decided.* Use
`cco:has input` and `cco:has output` directly. Reach: the Moral Epistemics module, its
shapes (which use `hasInformationalOutput` as a path), the scenario, 5 docs and
4 test files.

**R12 — Resolve the Planned Act commitment.** *Decision.* The existence of
`RashJudgmentAct` answers the review's question: spontaneous moral judgment is in scope.
**Recommendation:** move the generic parent of `MoralAssessmentAct` above Act of
Appraisal, and keep Act of Appraisal only for a subclass whose meaning includes
deliberation, if one is wanted.

**R13 — Ground `MoralCulpabilityRole` in actual accountability.** *Decision.* Replace
"because a norm-governed moral appraisal treats that agent as accountable" with a
differentia that an unwarranted appraisal cannot satisfy. Use `RashJudgmentAct` (N3) as
the negative control: an unwarranted ascription must not entail the role.

**R14 — Justify `contravenes`, or replace it.** *Decision.* Write the record the review
asks for: why `disrupts` and `inhibits` (Process → Process, causal) cannot express
Process → realizable-entity contravention, with the competency questions that need it.
Settle finding 8's reading in the same record — contravention of an agent-borne
disposition, or violation of a norm — and route norm-centred questions to
`MoralNormICE`. **Recommendation:** conditional acceptance, as the review proposes; the
relation is not wrong, it is undocumented.

### D. Curation programme

**R15 — Decide folk membership before curating folk definitions.** *Decision.* 84 of
the 96 misaligned definitions are in the folk module, whose membership is itself
unsettled (N6). Normalising definitions first risks curating classes that are later
removed, and missing the 187 values that are not there.

**R16 — Align genus to the asserted parent.** *Mostly mechanical.* 96 definitions: folk
84, Moral Foundations 6, Moral Epistemics 6. Gate it with a check against a recorded
baseline, so the count can only go down.

**R17 — Split conflated definitions.** *Decision.* `FaithDisposition` is literally
disjunctive — "trust or confidence in someone or something, *or* a strong belief in a
religious doctrine" — and `OpennessDisposition` joins candour to openness to
experience. Add a warning-level check for disjunction in definitions; it will not be
the last.

**R18 — Comments and examples.** *Only if R2 adopts RULES 2.0.* Against a baseline.

### Order

1. **R1–R3** — the decisions everything else rests on.
2. **R4–R8** — the same day. Each is a public inaccuracy or a wrong verification record,
   and none waits on a redesign.
3. **R9–R11** — one phase: the linguistic and evidence layer and the relations it uses,
   with the most test impact.
4. **R12–R14** — the remaining modelling decisions, each with its record.
5. **R15–R18** — the curation programme, gated.

This differs from the review's order in one respect: the cheap documentation fixes move
ahead of the redesign. The site is publicly wrong about the mapping direction and the
number of foundations today, and correcting that costs an hour.

---

## 7. What this response does not cover

- **Reasoning over the modules.** HermiT was not re-run over the published modules;
  nothing in them was edited, so the Phase 6 result stands, and every change in §6 must
  re-establish it. HermiT *was* run over the fourteen scenario graphs in
  `tests/bfo/test_text_value_placement.py`, which is a different claim.
- **The reviewer's judgements.** Where a finding is a modelling argument rather than a
  fact — whether `contravenes` is needed, how culpability should be grounded — this
  records a recommendation, not a verification.
- **The genus measure is a heuristic.** It checks that a definition opens with an
  asserted named parent's label. It says nothing about the quality of the differentia.
- **RULES 2.0 itself.** Not in the repository when this was written, so not read. It
  has since been recorded; see §11.
- **Out of the table.** The trigger-semantics module and the moral-epistemics scenario
  were not measured for definition discipline.

---

## 8. Suggested reply to the reviewer

- Thank you; nearly every finding verified against the repository.
- **Correction:** `AgentBehaviorProcess` already asserts `has participant some Agent`.
  The definition/comment contradiction is accepted.
- **Scope:** the genus gap is concentrated in folk, Moral Foundations and Moral
  Epistemics; core and Schwartz use their asserted parent. The comment and example
  requirement is under decision (R2).
- **Baseline:** we propose CCO 2.2, the pinned release. Every cited term was compared
  across 2.0 and 2.2 and no finding changes; `has input`, `has output` and `inhibits`
  are now defined through their inverses in 2.2. Would you re-baseline rather than
  re-review?
- **Added:** `RashJudgmentAct` is an internal counterexample to both the Planned Act
  commitment and the culpability-role definition, and we propose it as the negative
  fixture for both repairs.

---

## 9. The reviewer's reply, 2026-09-16

Recorded verbatim in `FORMAL_REVIEW_2026-09-16_REVIEWER_REPLY.md`.

| point in the reply | disposition |
|---|---|
| The correction on text values is well founded; the replacement recommendation "was therefore too strong and should be withdrawn" | Accepted. R9 revised; D-005 provisionally adopted. |
| Endorses content → ICE, form → non-ICE GDC, bearer → IBE, and "consistent but misclassified" for the current model | Adopted as D-005 items 1–2. |
| Asks that the experiment become a permanent test, all eight cases kept, with a ninth: two distinct IBEs carrying one representation | Done: `tests/bfo/test_text_value_placement.py`, twelve scenarios at the time, fourteen after §10. Case 09 is the reviewer's; 10 and 11 test the two arguments below; 12 is the design as D-005 records it. Falsified by removing the stated CCO domain axiom and BFO's disjointness groups, each of which flipped its case. |
| Asks for an OWL existential, `generically depends on` some IBE, with SHACL kept for explicit carrier data | Adopted as D-005 items 2 and 7. Case 10 shows why both are needed: the existential alone accepts a representation with no recorded carrier. |
| Proposes the definition "…is concretized by one or more information bearing entities" | **Not adopted.** BFO restricts what concretizes a GDC to a process or specifically dependent continuant; an IBE is neither. D-004 item 5 already prohibits the direct assertion, and case 11 shows the requirement is unsatisfiable. D-005 uses "generically depends on at least one information bearing entity", which keeps the reviewer's own point that only one copy need exist. |
| Keeping `TextSpanSelector` under Designative ICE is cleaner | Adopted as D-005 item 8. |

Not yet answered by the reviewer, and still worth sending from §8: the
`AgentBehaviorProcess` correction (C1), the scope of the definition gap (C2), the
proposal to re-baseline on CCO 2.2 (R1), and `RashJudgmentAct` as a negative fixture.
One addition for them: D-005 moves `TextSpan` to the form level too, which neither
message had covered, and it cannot land without R10.

---

## 10. The reviewer's second reply, 2026-09-16

Recorded verbatim in `FORMAL_REVIEW_2026-09-16_REVIEWER_REPLY_2.md`. The reviewer
accepts C1 and C2, accepts R9 and D-005 in substance, agrees that the "concretized by an
IBE" wording was wrong, agrees with R3 and with the sharper `EvidenceSource` finding, and
endorses `RashJudgmentAct` as the negative fixture for R12 and R13. Their revised
characterization: the foundational BFO architecture is stronger than the first review
suggested, and the remaining serious problems are localized — the linguistic and evidence
redesign, plannedness in moral assessment, actual versus ascribed culpability, the
justification of `contravenes`, and folk definitions and membership.

| point | disposition |
|---|---|
| **1.** A deprecated `hasTextValue` made equivalent to the new property is safe only if its ICE domain is removed, or the equivalence re-classifies form-level entities as ICE | **Resolved by not having the bridge.** The owner decided no alias is needed: the text layer is new (D-004, 2026-08-25) and has no consumers to migrate. The reviewer's caution is recorded in D-005 item 5 as a constraint on any future alias. |
| **2.** `TextSpan` needs a definition that makes position explicit, and its own competency test | **Adopted, with one change.** D-005 item 4 defines a span as *a continuant part of exactly one textual representation, individuated by a contiguous interval of code-point positions in it*. Scenarios 13 and 14 are the test: two occurrences of `"abc"` are consistent as distinct spans (13), and keying spans by their string collapses them into one and contradicts their distinctness (14). The only difference between the two is the key, and 14 turns consistent once the spans are not asserted different. **"Proper" was not adopted**, as the reviewer left open: BFO 2020 core has no proper-part relation, so it would be a local constraint, and the shapes admit a span over the whole representation — the only way to cite a whole utterance as evidence. |
| **3.** CCO 2.2 as project baseline, but the reviewer's own verification remains on the supplied 2.0 | **Accepted.** C3 now carries the reviewer's wording for the audit record, and R1 records the distinction. |

The reviewer asked for the deprecation warning to be added to D-005 immediately; with no
alias, it is recorded as a constraint rather than as part of a migration. One point for
the reply: the decision not to make spans proper parts is ours to confirm, and the reason
is a capability — whole-utterance evidence — rather than a logical necessity.

---

## 11. Sign-off and implementation, 2026-09-16

The reviewer's sign-off is recorded verbatim in
`FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF.md`. It grants sign-off, raises no further
blocker, and names four breaking changes as the required set: the D-005 text layer, the
retirement of `EvidenceSource`, the retirement of `hasInformationalInput/Output`, and the
re-parenting of `MoralAssessmentAct`. It adds that the `MoralCulpabilityRole` repair is
breaking only if it changes OWL conditions, and `contravenes` only if it is replaced. The
owner instructed that the plan proceed. All four breaking changes are made; the other two
were made without breaking anything.

| rec. | status | where |
|---|---|---|
| R1 | Done. CCO 2.2 is the baseline; the extract manifest records the release digest | D-006; phase A, digest corrected in phase C |
| R2 | Done. RULES 2.0 is adopted as ValueNet's standard (D-013). It is recorded verbatim, and is the operating rules of the reviewing tool, OntoRefiner GPT. The owner adopted it with readings: a definition conforms when it opens with its asserted parent, and "a … disposition *to* …" conforms, so the 148 definitions phrased that way are not rewritten; the five annotations are required of every new or changed term, and the existing gap is gated and paid down; searching CCO first and the three checks are required, web search optional. Measured at adoption over classes and properties: non-folk terms lack 32 comments and 60 examples, folk terms 134 of each | D-013; `FORMAL_REVIEW_2026-09-16_RULES_2.0.md` |
| R3 | Done. "Retain" superseded | D-007; phase A |
| R4 | Done. The mapping arrow points the way it is asserted, checked from the markup | phase B |
| R5 | Done. Six foundations, with their processes, checked against the declared classes | phase B |
| R6 | Done. The has input / has output rows state the real range | phase B |
| R7 | Done. `AgentBehaviorProcess` is defined by participation | phase B |
| R8 | Done. 17 such assertions, 67 overall, both derived | phase B |
| R9 | Done. Representation and span are form-level GDCs; `hasTextualSequenceValue`; the selector is a Designative ICE and `selectsTextSpan` specializes `designates` | D-005; phase C |
| R10 | Done. `EvidenceSource` retired; the evidence annotation is a Descriptive ICE | phase C |
| R11 | Done. Seven restrictions on CCO has input / has output, fillers unchanged | D-007; phase C |
| R12 | Done. `MoralAssessmentAct` is a CCO Act; discernment is an Act of Appraisal; a rash judgment is not entailed to be planned | D-008; phase D |
| R13 | Done. The role is grounded in the agent's conduct; no OWL condition changed, so not breaking | D-009; phase D |
| R14 | Done. `contravenes` retained, with the alternatives recorded against CQ1 and CQ5; not breaking | D-010; phase D |
| R15 | **Open — owner decision.** Folk membership, including whether `OpennessDisposition` merges into `OpenMindednessDisposition` (D-012). The folk curation it unblocks — 84 genus corrections, 134 comments, 134 examples — follows D-013. A researched proposal, with membership criteria and a disposition for every uncovered corpus value and every unpaired class, is in `docs/bfo/remediation/R15_FOLK_MEMBERSHIP_PROPOSAL.md` | blocks folk curation |
| R16 | Done outside folk; gated. Moral Foundations 12/12 and Moral Epistemics 17/17 open with an asserted parent. Folk's 84 are recorded by name and the gate is equality, so a new misalignment fails and a fixed one must be removed from the record. Moral Epistemics measured 3, not 6: phase D had fixed one, and two were the measure reading "ICE" in a label as different from "information content entity" in the definition | `tests/bfo/test_definition_discipline.py`; phase E |
| R17 | Done. The warning check fired on exactly `FaithDisposition` (a comma, "or", then an article or infinitive; a plain "or" matches 107 definitions, nearly all lists) and now fires on none. The owner decided both splits: Faith keeps trust without proof and `ReligionDisposition` takes the religious sense, which is `folk:Religion` in the corpus; Openness keeps openness to experience, and its candour sense is the existing `CandorDisposition` and `TransparencyDisposition`. Openness had conflated by conjunction, which no disjunction pattern could have caught | D-012; `tests/bfo/test_definition_discipline.py`, `tests/bfo/test_folk_sense_splits.py` |
| R18 | Non-folk done; folk after R15. Every class and property in core, Schwartz, Moral Foundations and Moral Epistemics now carries a comment and an example: 32 comments and 60 examples written, worked examples taken from the module's own scenario where one exists. The folk gap, 134 of each, is recorded and gated | D-013; `tests/bfo/test_definition_discipline.py` |

**Found during implementation, and recorded in D-005.**

- CCO 2.2 defines Information Content Entity as *equivalent to* a generically dependent
  continuant that is about some entity. A representation or span stays form only while
  nothing asserts it is about something; if something does, directly or through
  `designates` or `describes`, the reasoner re-classifies it and reports nothing. The rule
  is in the class comments and the annotation guide and is pinned by a test in both
  directions. The owner then decided the disjointness this left open: both form classes
  are disjoint with Information Content Entity (D-011), so such an assertion is now an
  inconsistency a reasoner reports.
- A span individuated by its position has one position, but two selectors at different
  offsets could select one span whenever both positions held the same string, and each
  passed the substring check. A shape now rejects it.
- The first culpability reasoning test passed for the wrong reason: the probe class came
  back from owlready2 under a different IRI, so no individual could ever match it. Its
  positive control failed, which is how that was found.

**Evidence.** HermiT finds the suite consistent with no unsatisfiable named class, with
and without the scenario, after phases C, D and E. Every new test was run against the
unchanged ontology first and failed for its stated reason; each check added to a shape or
a provenance record was falsified by reverting its subject.

**Not yet reconciled, and why each is outside this work.**

- Evidence is current. `config/semantic-baseline.json` and `config/remediation-record.json`
  were regenerated from clean commits after phases D and E with
  `tools/marep/build_evidence.py --remediation`, and the remediation ledger names each
  phase as an event with its measured size and reason. The one measure that moved
  unexpectedly, the reasoner's class count (306 to 308), was traced to two anonymous classes
  phase C added; the named classes net to zero.
- `config/quality-report.json` counts one internal link fewer than the site now has, and
  regenerating it resets the owner's public-content sign-off. The published ontology has
  changed, so that statement is the owner's to make again.
- 23 explorer tests fail on this machine because node 25.2.1 is on PATH and 24.20.0 is
  pinned. They fail identically on the commit before this work.

Nothing has been pushed.
