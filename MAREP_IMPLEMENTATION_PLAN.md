# Implementation plan — decisions drawn from Runs 1–3

**Status:** discovery closed. Three runs, 82 findings, 100% verified evidence.
No Run 4 is planned.

Run 3's actions phase waived every confirmed issue rather than attaching
accepted actions, which reads plainly: **it diagnosed the corpus and did not
remediate it.** That is a reasonable outcome for a discovery run, and it is the
reason the next stage is not another one. There is enough evidence. What is
missing is decisions.

Each item below names the decision to be made, who or what it binds, and the
findings that support it. Several are governance calls rather than code, and
are marked so — writing code before the call is made is how a convention ends
up encoded in a script instead of in the artefacts.

---

## 1. Define `vcvf:triggers` — semantics and direction

**Decision, not code.** The single most load-bearing relation in the corpus:
57,578 statements resolving to 147 distinct objects.

*Correction.* An earlier draft of this section said the predicate had no
domain and no range. That was false. ValueCore 0.4 declares
`rdfs:domain owl:Thing` and `rdfs:range vcvf:Value`; only the **definition** is
missing. The error went into the Run 3 agent briefs and came back as
"verified" evidence on three findings, which says something about the
grounding gate worth recording: it checks that a citation resolves to a
record, not that the prose around the citation is true.

The consequence is not cosmetic. Because the range is already asserted, it
already entails — under RDFS closure every trigger object becomes a
`vcvf:Value` whether or not anyone declared it one. The nine untyped targets
are Values today, by inference, with nobody having said so.

The data already exhibits a total convention. Across `thats-all-folks`, 18,668
trigger statements put the external resource in **subject** position and
**zero** put one in object position; `mf-triggers` agrees. The direction is
therefore not in dispute — it is simply unstated, and unstateable in OWL as the
predicate currently stands.

Direction carries real semantic weight. `<dbpedia:An_Education> vcvf:triggers
folk:Education` says a film's page evokes the value Education. Reversed, it
would say the value *is* the film. Run 1's `MAPPING-002` read it the second way
and drew a defect from it; Run 3's `ALIGN-001` archived that reading as settled.

What has to be written: a definition of the relation, an `rdfs:domain` and
`rdfs:range` (or an explicit statement of why they must stay open, if the
subject genuinely ranges over anything nameable), and a statement of what a
trigger claim asserts and does not assert.

*Supported by:* `ALIGN-002`, `SHACL-002`, `MAPPING-001`, `ALIGN-001` (archived),
Run 1 `MAPPING-002` (reconciled).

---

## 2. Implement the direction shape, once §1 is settled

Depends on §1 and not before it: a shape enforcing a convention nobody has
written down encodes the convention in the tooling, which is the failure this
repository has spent three runs removing from its artefacts.

Once the definition exists, this is the highest-value shape available. It is
the only proposed constraint with tens of thousands of nodes able to violate
it, and it currently has zero violations — so it locks in a property that
holds, rather than reporting a mess.

*Supported by:* `SHACL-002` (confirmed, 9/9 verified).

---

## 3. Decide the lexicon-edition policy, then implement or revise §3's shape

**Decision, not code.** 889 of 3,658 `thats-all-folks` Wiktionary triggers are
French; 147 of 624 at repository-root. Nothing records which lexicon governs a
term, and a French source may be entirely correct for a term borrowed from
French — Run 3's Skeptic said exactly that.

Note the correction before acting: these are **trigger sources, not glosses**.
The French IRIs sit in subject position, so the question is which lexicons may
serve as trigger sources, not which dictionary defines a term. Run 1's
`LANG-001` framed it the second way and was wrong about the kind of thing, not
only the count.

`SHACL-003` is the only proposed shape that **fails against the corpus as it
stands**, which is what makes it worth writing — and also why the policy has to
come first. A shape written before the decision would mass-flag content that
may be correct.

*Supported by:* `SHACL-003`, `ALIGN-005`, `LANG-002` (unresolved, to be
rewritten against a like-for-like count).

---

## 4. Establish canonical IRI and module ownership rules

**Decision, then a small correction.** The measurement here was wrong twice and
is now right, which is worth stating before anyone acts on the number.

`class_iris_declared_in_multiple_files` reports 2,240, which reads as pervasive
contested ownership; most are `vale2024` classes across five parameter variants
of one ontology. The cross-group figure, 378, looked like the honest version —
but all 378 are the **same file pair**, `ThatsAllFolks/folk.ttl` against
`folk_aligned.ttl`, 325 of them that pair alone. `cross_group_file_pairings`
now ships beside it and reports **4**, which is the number of ownership
decisions actually pending.

So the decision is small and concrete: which of `folk.ttl` and
`folk_aligned.ttl` is canonical. They hold 5,828 triples each and are **not
isomorphic**, so this is a real question with a real answer, and it is one
question rather than 378.

Beyond that: a stated rule for which namespace mints a term and who may define
it. The corpus mints in four namespaces it controls and asserts about 43,616
resources in namespaces it does not.

*Supported by:* `IRI-005`, `IRI-001`, `IRI-002`, `IRI-003`, `LEXICON-004`
(superseded), Run 1 `IRI-001`.

---

## 5. Retarget SHACL at predicates and the real ABox

Three of seven groups declare **no individuals at all**, so class-targeted
shapes cannot bind there in principle — `mf-triggers` carries 12,338 trigger
statements behind zero classes and zero individuals. This is why repairing 127
unparseable files moved SHACL violations from 0 to 0, and why coverage was
never the binding constraint.

The population worth shaping: 1,080 declared individuals, currently reached
through five undeclared-domain properties and 21 undeclared predicates. Those
declarations are a prerequisite, not a nice-to-have — a shape over an
undeclared predicate is guesswork.

Do **not** invest in class-targeted shapes for `vale2024`, `moral-molecules` or
`mf-triggers` until they carry instances. That is an action, resting on the
confirmable fact that such shapes bind zero focus nodes there.

*Supported by:* `SHACL-001`, `SHACL-005`, `SHACL-004` (reformulated as fact
plus action).

---

## 6. Make every green result state its tested population and whether it could fail

Partly built, and to be finished and made a standing rule rather than a series
of individual repairs.

Every clean verdict in this corpus comes from roughly a 2% slice.
`reasoner_consistent: 1` was true of a layer with no individuals and 32
contradiction-capable axioms; four of seven groups have **zero** such axioms,
so their consistency verdicts were guaranteed before the reasoner started.
`shacl_violations: 0` was true over 14 focus nodes in 6 of 165 files.

Already done: `reasoner_*` reach metrics and the `VACUOUS` caveat,
`shacl_violations` carrying its focus-node denominator, `duplicate_triple_ratio`,
`contradiction_capacity` per group.

Still to do: make it a rule rather than a habit — no verdict metric ships
without its denominator and a statement of whether the check was capable of
failing. A test enforcing that on new metrics would put the rule in the
artefacts.

*Supported by:* `ASSURANCE-001`, `LOGIC-001`, `TEST-001`, Run 2 `SCOPE-001`,
Run 1 `VALIDATION-001` (reconciled: conclusion upheld, cause refuted).

---

## 7. Vocabulary governance as a programme, not a fix

2,794 classes carry no definition text of any kind: all 1,861 in `vale2024`,
629 at repository-root, 278 in `thats-all-folks`, all 26 in `moral-molecules`.
798 `owl:equivalentClass` assertions identify terms that carry no definitions
to compare. Near-synonym families — Smart, Intelligence, Genius, Brilliance —
are separated by nothing statable.

This will not be fixed mechanically and should not be attempted that way. A
generated definition is worse than none: it looks like an audited decision and
is not. Treat it as a long-running vocabulary-governance programme with a
stated policy on what a definition must contain and which families need
adjudicating first.

*Supported by:* `LEXICON-001`, `LEXICON-002`, `LEXICON-003`, `DEF-001`
(archived), Run 1 `DEF-003`.

---

## Deliberately not here

**Duplicate-triple cleanup.** ~50% in `mf-triggers`, ~46% in
`thats-all-folks`. Run 2's Restraint and Run 3's `DUP-001` both hold these are
materialised aggregates and build products rather than drift. Deferred, as
scoped, unless duplicates are actively confusing tooling. The one duplication
that *does* need a decision — `folk.ttl` against `folk_aligned.ttl` — is §4,
because it is an ownership question rather than a storage one.

**Run 4.** Three runs have produced enough evidence. The bottleneck is now
decisions, not discovery.
