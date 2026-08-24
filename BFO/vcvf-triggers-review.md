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
these triggers live in **`folk_Recognition.ttl`**, headed `## folk:Recognition`,
and all 106 statement lines point at `folk:Repayment` while the properly
declared `folk:Recognition` receives **zero**.

*An earlier draft of this section said every trigger in the file was a lexical
variant of "recognition". That was too narrow, and checking it properly is what
settled the question.* The file has three kinds of section: a `recognition lu`
block (33 triggers), a `reward lu` block (44), and roughly 29 triggers drawn
from the FrameNet **Repayment** frame — `framestercore/Repayment`,
`fn17-repayment`, `Debtor.repayment`, `Loan.repayment` and so on. So it is not
simply misspelled content; the file genuinely draws on repayment semantics.

The decisive evidence is the corpus-wide convention rather than the wording of
any one section. Of 127 fragment files, **126 use exactly their own filename as
the trigger object**, and `folk_Recognition.ttl` is the sole exception. One
file names one value, and every section in it lists resources that evoke that
value — which is exactly what a FrameNet frame about repayment is doing inside
a file about Recognition.

**Action taken:** all 106 retargeted to `folk:Recognition`, which now receives
102 distinct triggers where it received none. `folk:Repayment` has no referents
and is not declared. The `# Repayment frame` heading is left alone: it
correctly names the FrameNet frame supplying those triggers.

### `Strenght` — 122 triggers — **spelling defect; retarget**

Run 1's `NAME-001` flagged this. `folk:Strength` is declared
(`FolkValue`, `NamedIndividual`) and receives **zero** triggers; the misspelled
`folk:Strenght` receives all 122, from `folk_Strenght.ttl`. The vocabulary and
the trigger data name the same value differently and never meet.

Here the file follows the convention correctly — filename and object agree —
so both are wrong together and both are renamed together.

**Action taken:** 206 occurrences retargeted to `folk:Strength`, which now
receives 122 distinct triggers where it received none, and
`folk_Strenght.ttl` renamed to `folk_Strength.ttl`. `folk:Strenght` is retired,
not declared: declaring it would make the typo permanent and give one value two
identities.

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
| `BadHealth` | 3,631 | largest by a wide margin |
| `Intuitive` | 201 | adjectival form — see below |
| `Willingness` | 91 | |
| `Assertiveness` | 42 | |
| `Inclusion` | 21 | |
| `Involvement` | 10 | |

With the two retargets applied, untyped trigger objects are down from nine to
**seven**: these six plus `Belief`.

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

1. ~~Retarget `Repayment` → `Recognition` and `Strenght` → `Strength`; retire
   both bad IRIs.~~ **Done** — `ValueNet_code/retarget_bad_trigger_objects.py`,
   624 occurrences, both bad IRIs retired, untyped targets 9 → 7.
2. Decide `Belief` vs `Beliefs`; retarget to the winner.
3. Declare the six as `folk:FolkValue` individuals.
4. Re-measure: untyped trigger objects should be **0**.
5. Only then rely on `rdfs:range vcvf:Value`, and add the SHACL constraints so
   a future untyped target surfaces as a violation instead of disappearing
   into an inference.

Steps 1–3 change trigger data and vocabulary and want review before they are
applied. Step 4 is the gate for step 5.
