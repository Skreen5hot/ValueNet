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

### `Belief` — 480 triggers — **resolved as `folk:Religion`**

Framed at first as a singular/plural naming split against the declared
`folk:Beliefs`, which receives zero triggers. Reading the fragment settled it
differently, and the framing was wrong.

`folk_Belief.ttl` is headed `# religion lu` and carries a
`# ReligiousBelief frame` section. Its vocabulary is a religion lexicon
throughout — *religion, antireligion, nonreligion, misreligion, parareligion,
pseudoreligion, subreligion, urreligion, religionist, religionize, bishop,
temple, spirit* — with DBpedia targets `Religion`, `Antireligion`, `Bishop`,
`Temple`. Nothing in it is about believing in general or about propositional
content.

`folk:Beliefs` was the wrong home for it. It is a category term subclassing
`vcvf:ValueSituation`, and it already has two more specific children,
`folk:Faith` (48 triggers of its own) and `folk:Belief_in_God`. Putting a
religion lexicon onto the parent would have sat a specific vocabulary above
terms more specific than itself.

**Action taken:** `folk:Religion` declared under `folk:Beliefs` as a third
sibling, matching `folk:Faith`'s shape — `folk:FolkValue, owl:Class,
owl:NamedIndividual`, a label, the `dul:satisfies` ValueSituation restriction,
and `fschema:subsumedUnder`. All 480 triggers retargeted, `folk_Belief.ttl`
renamed to `folk_Religion.ttl` to preserve the filename-equals-object
convention that 126 of 127 fragments follow. `folk:Belief` is not declared: it
names nothing once its triggers move.

Its `prov:wasAttributedTo` names this decision rather than a core-values list.
`folk:Faith` cites one; `folk:Religion` appears on none, which is why it was
never declared, and copying a source it does not have would fabricate
provenance.

*A correction to an earlier draft of this section: `SENSE-001` does not flag
`Belief`. It names Education, Helping, Grace, Faith, Excellence, Independence
and Lively. `folk_Religion.ttl` does target capitalised `Bishop`, `Religion`,
`Spirit` and `Temple` alongside lowercase forms of the same words, which makes
it a further instance of that finding — tracked as SENSE-001 cleanup, not as
part of this modelling decision.*

---

## The six that looked like intended values

Each had a `folk_X.ttl` fragment named for it and no obvious near-match, so
all six were put forward for declaration. Checking the fragments individually
turned **three of them into something else**. The test that mattered was not
"is there a fragment named for it" but "does anything already declared cover
it", and the same signature kept appearing: a declared value with zero
triggers sitting beside an undeclared near-twin holding all of them.

### Declared

| target | triggers | parent | note |
|---|---:|---|---|
| `Involvement` | 10 | `vcvf:ValueSituation` | header, filename and object agree; nothing declared covers it |

`vcvf:ValueSituation` is used where no more specific parent is evidenced.
Asserting a folk-value parent to fill a blank would invent a taxonomic claim,
which is the failure this review exists to avoid; `folk:Beliefs` sits directly
under ValueSituation for the same reason.

### Held — a declared term already covers them

| target | triggers | the declared term | its triggers |
|---|---:|---|---:|
| `Willingness` | 91 | `folk:Will` — fragment is headed `## folk:Will` | 0 |
| `Inclusion` | 21 | `folk:Inclusiveness` — fragment is headed `## folk:Inclusiveness` | 0 |
| `Assertiveness` | 42 | `folk:Assertion` — labelled "assertion, assertion , assertiveness" | 0 |

`folk:Inclusiveness` is the clearest: its definition opens *"Inclusion is a
value that focuses on accepting diversity"*, so the two names denote one
concept and declaring both would duplicate it. `folk:Will` is weaker — the
lexemes are the *willing* family, which serves both readings, and unlike the
`Repayment` case the filename and object agree with each other and only the
header dissents. `folk:Assertion` is weaker still: the fragment is entirely
self-consistent, and the overlap shows only in an alt-label.

None is mechanical. Declaring `Assertiveness` beside `Assertion` would
manufacture exactly the near-synonym pair that Run 1's `DEF-003` and Run 3's
`LEXICON-003` already report as a defect.

### Held — modelling questions

**`BadHealth`** (3,631 triggers) is not a negative-polarity twin of
`folk:Health`, which is separately declared. The declared `NegativeValue`
members are propositional — `LifeIsMeaningless`,
`OtherPeopleCannotBeTrusted`, `PeopleCannotChangeTheirSituation` — a different
kind of thing, and there are no other `Bad*` values. Its relationship to
`Health` and to the NegativeValue convention has to be settled before a type
is assigned.

**`Intuitive`** (201 triggers) is adjectival where most values are nominal —
Run 1's `NAME-002`. The nominal `folk:Intuition` is undeclared and receives no
triggers, so there is nothing to merge into, and adjectival forms are already
present in the vocabulary (`Capable`, `Dutiful`). The question is what concept
was intended, not whether to enforce a grammatical convention the corpus does
not consistently apply.

---

## Sequence

1. ~~Retarget `Repayment` → `Recognition` and `Strenght` → `Strength`; retire
   both bad IRIs.~~ **Done** — `ValueNet_code/retarget_bad_trigger_objects.py`,
   624 occurrences, both bad IRIs retired, untyped targets 9 → 7.
2. ~~Decide `Belief` vs `Beliefs`; retarget to the winner.~~ **Done** —
   resolved as neither: `ValueNet_code/add_folk_religion.py` declares
   `folk:Religion` under `folk:Beliefs` and retargets all 480. Untyped
   targets 7 → 6.
3. ~~Declare the six as `folk:FolkValue` individuals.~~ **Partly done** —
   `folk:Involvement` declared. Five held: `Willingness`, `Inclusion` and
   `Assertiveness` because a declared term already covers each, `BadHealth`
   and `Intuitive` as modelling questions. Untyped targets 6 → 5.
4. Re-measure: untyped trigger objects should be **0**.
5. Only then rely on `rdfs:range vcvf:Value`, and add the SHACL constraints so
   a future untyped target surfaces as a violation instead of disappearing
   into an inference.

Steps 1–3 change trigger data and vocabulary and want review before they are
applied. Step 4 is the gate for step 5.
