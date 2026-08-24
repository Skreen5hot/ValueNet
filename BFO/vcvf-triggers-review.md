# The nine untyped trigger targets

`vcvf:triggers` resolves to 147 distinct objects. Nine carry no `rdf:type`
anywhere in the corpus, and they are not marginal — one is the target of 3,631
statements. This is the review that has to happen before `rdfs:range` is
relied upon.

## The correction that reframes the task

`rdfs:range vcvf:Value` is **already asserted**, in
[`ValueCore.ttl:97`](../ValueCore.ttl#L97), and it already fires. Under RDFS
closure `folk:BadHealth` becomes a `vcvf:Value` on the strength of a single
trigger statement, with nobody having declared it one. Verified directly.

So deferring the range is not achievable by not adding it. All nine are
*already* Values by entailment. Declaring them explicitly does not create a
commitment — it makes an existing one visible and auditable, and lets a
mistyped target be caught rather than absorbed.

Two of the nine are not Values at all, and the entailment is currently
manufacturing type assertions for both.

---

## The two that are errors

### `Repayment` — 102 triggers — **retarget, do not declare**

A whole-file mis-target. `ThatsAllFolks/folk_Repayment.ttl` does not exist;
these triggers live in **`folk_Recognition.ttl`**, which is headed
`## folk:Recognition`, and every trigger inside it is a lexical variant of
*recognition* — `recognition`, `allorecognition`, `autorecognition`,
`biorecognition`, `corecognition`, `derecognition`. All 102 point at
`folk:Repayment`.

`folk:Recognition` is properly declared (`FolkValue`, `NamedIndividual`) and
receives **zero** triggers. The object was simply wrong for the file.

**Action:** retarget all 102 to `folk:Recognition`. `folk:Repayment` then has
no referents and should not be declared. Nothing else in the corpus mentions
it.

### `Strenght` — 122 triggers — **spelling defect; retarget**

Run 1's `NAME-001` flagged this. `folk:Strength` is declared
(`FolkValue`, `NamedIndividual`) and receives **zero** triggers; the misspelled
`folk:Strenght` receives all 122, from `folk_Strenght.ttl`. The vocabulary and
the trigger data name the same value differently and never meet.

**Action:** retarget the 122 to `folk:Strength`, rename the fragment file to
`folk_Strength.ttl`, and retire the misspelled IRI. Do not declare `Strenght`
— declaring it would make the typo permanent and give the value two identities.

---

## The one that is a naming collision

### `Belief` — 480 triggers — **decision required, do not declare yet**

`folk:Beliefs` (plural) is declared and receives **zero** triggers.
`folk:Belief` (singular) is undeclared and receives 480, from
`folk_Belief.ttl`. The same split pattern as `Strenght`, but here neither form
is misspelled and the choice is a modelling one: a folk value named for a
disposition to believe (*Belief*) is not obviously the same as one named for
the set of things believed (*Beliefs*).

**Action:** decide which form is canonical, then retarget to it and retire the
other. This is a governance call, not a mechanical fix. Note that Run 1's
`SENSE-001` separately flags `Belief` as glossed against a proper-name sense.

---

## The six that are intended values

Each has a `folk_X.ttl` fragment named for it, is reached only by
`vcvf:triggers`, and has no near-match among declared values. They were meant
to be values and the declaration was never written.

| target | triggers | note |
|---|---:|---|
| `BadHealth` | 3,631 | largest of the nine by a wide margin |
| `Intuitive` | 201 | adjectival form — see below |
| `Repayment` | — | *excluded, see above* |
| `Willingness` | 91 | |
| `Assertiveness` | 42 | |
| `Inclusion` | 21 | |
| `Involvement` | 10 | |

**Action:** declare each as `owl:NamedIndividual, folk:FolkValue`, matching how
the other 115 FolkValues are declared. Punning is the established pattern here
— 103 of 147 trigger objects are typed both `owl:Class` and
`owl:NamedIndividual`, and **none** is class-only, so the individual
declaration is what `vcvf:triggers` actually refers to.

### Two of the six carry a modelling question

**`BadHealth`** is not a negative-polarity twin of `folk:Health`, which is
separately declared. The declared `NegativeValue` members are propositional —
`LifeIsMeaningless`, `OtherPeopleCannotBeTrusted`,
`PeopleCannotChangeTheirSituation` — a different kind of thing entirely, and
there are no other `Bad*` values. `FolkValue` is the defensible declaration;
whether ValueNet wants a negative-polarity relation between `Health` and
`BadHealth` is a separate question and should not be settled by a typing
decision made to close a gap.

**`Intuitive`** is adjectival where most values are nominal — Run 1's
`NAME-002`. The nominal form `folk:Intuition` is undeclared and receives no
triggers, so there is nothing to merge into. Adjectival forms are already
present in the declared vocabulary (`Capable`, `Dutiful`), so declaring
`Intuitive` as-is is consistent with what exists. The naming inconsistency
belongs to the vocabulary-governance programme (implementation plan §7), not
to this repair — renaming unilaterally would break 201 trigger statements to
enforce a convention nobody has adopted.

---

## Sequence

1. Retarget `Repayment` → `Recognition` and `Strenght` → `Strength`; retire
   both bad IRIs. Purely mechanical, no modelling content.
2. Decide `Belief` vs `Beliefs`; retarget to the winner.
3. Declare the six as `folk:FolkValue` individuals.
4. Re-measure: untyped trigger objects should be **0**.
5. Only then rely on `rdfs:range vcvf:Value`, and add the SHACL constraints so
   a future untyped target surfaces as a violation instead of disappearing
   into an inference.

Steps 1–3 change trigger data and vocabulary and want review before they are
applied. Step 4 is the gate for step 5.
