"""Settle the last five undeclared trigger targets.

Each decision rests on the fragment, the hierarchy and the surrounding
ontology, and the five did not come out the same way.

**BadHealth — declare, negative polarity.** 3,631 triggers, anchored on the
FrameNet MedicalConditions frame with YAGO and BabelNet ailment synsets. Header,
filename and object agree, and `folk:Health` is a separate declared value, so
this is not a mis-target. The folk layer already carries five negative-polarity
values — `LifeIsMeaningless`, `OtherPeopleCannotBeTrusted`,
`SelfDoesntDeserveGood`, `StrongSurviveInBrutalWorld`,
`PeopleCannotChangeTheirSituation` — all under `vcvf:NegativeValueSituation`,
and all 11 children of that class carry `mft:NegativeValue`. BadHealth follows
them.

One tension recorded rather than silently resolved: `mft:NegativeValue` is
commented "a value that is considered negative to those that commit to it
(used for Haidt opposites)", and nobody commits to bad health. Consistency with
11 of 11 siblings beat a parenthetical, but the class comment is a poor fit for
a condition and is worth revisiting as vocabulary governance.

**Intuitive — declare as written, no rename.** Header, filename and object
agree; lexemes are the intuitive family including the nominal `intuitiveness`
and `intuitivism`; the frame is FrameNet Grasp. `folk:Intuition` is undeclared
with no triggers, so there is nothing to merge into, and adjectival names are
already present in the vocabulary (`Capable`, `Dutiful`). Renaming would break
201 trigger statements to enforce a convention the corpus does not hold.

**Willingness — declare, and fix its header.** The fragment is headed
`## folk:Will` while filename and object say Willingness, so one of them is
stale. `folk:Will` carries no comment and sits `fschema:subsumedUnder
folk:Strength`, which reads as willpower; the lexemes are *willing, unwilling,
willingly, overwilling, well-willing*, which is readiness rather than
determination. The hierarchy therefore does not support retargeting, so the
value is declared and the stale header corrected.

**Inclusion — retarget to `folk:Inclusiveness`.** The fragment is headed
`## folk:Inclusiveness`; that term is declared, receives zero triggers, and its
definition opens "Inclusion is a value that focuses on accepting diversity".
One concept, two names.

**Assertiveness — retarget to `folk:Assertion`.** `folk:Assertion` is declared,
receives zero triggers, carries the alt-label "assertion , assertiveness", and
its comment reads "Those who value being assertive know what they want". The
definition is about assertiveness. Declaring both would manufacture the
near-synonym pair Run 1's DEF-003 and Run 3's LEXICON-003 report as a defect.

    python tools/original-valuenet/settle_trigger_targets.py [--check]
"""

from __future__ import annotations

import argparse
import os

# Root by upward search for the layout contract, not by counting
# directories. This script moves under tools/, at which point two
# dirname calls resolve to repo/tools -- a path that exists, so the
# failure is silent.
_here = os.path.abspath(__file__)
HERE = _here
while not os.path.isfile(os.path.join(HERE, "config", "repository-layout.yaml")):
    _up = os.path.dirname(HERE)
    if _up == HERE:
        raise SystemExit("no config/repository-layout.yaml above " + _here)
    HERE = _up

#: Writes ONLY to the authored source. folk_aligned.ttl is generated from it by
#: tools/original-valuenet/generate_folk_aligned.py, and writing there by hand would be
#: overwritten on the next run and fail the staleness test in CI. Run the
#: generator after this script.

FULL = """
folk:{name} a folk:FolkValue,
        owl:Class,
        owl:NamedIndividual{extra_types} ;
    rdfs:label "{label}" ;
    rdfs:comment "{comment}" ;
    rdfs:subClassOf {parent} ;
    owl:equivalentClass [ a owl:Restriction ;
            owl:onProperty dul:satisfies ;
            owl:someValuesFrom [ a owl:Class ;
                    owl:oneOf ( folk:{name} ) ] ] ;
    prov:wasAttributedTo "{attributed}" .
"""

ALIGNED = """
###  http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#{name}
folk:{name} rdf:type owl:Class ;
            owl:equivalentClass [ rdf:type owl:Restriction ;
                                  owl:onProperty dul:satisfies ;
                                  owl:someValuesFrom [ rdf:type owl:Class ;
                                                       owl:oneOf ( folk:{name}
                                                                 )
                                                     ]
                                ] ;
            rdfs:subClassOf {parent} .
"""

ATTRIB = ("ValueNet modelling decision, docs/bfo/guides/vcvf-triggers-review.md ; "
          "derived from the lexicon of ThatsAllFolks/{}")

DECLARE = [
    {"name": "BadHealth", "label": "bad health",
     "extra_types": ",\n        mft:NegativeValue",
     "parent": "vcvf:NegativeValueSituation",
     "comment": "The negative value situation of being in poor health. Evoked "
                "by the FrameNet MedicalConditions frame and the ailment, "
                "illness and injury vocabulary aligned to it. Distinct from "
                "folk:Health, which is the corresponding positive value.",
     "attributed": ATTRIB.format("folk_BadHealth.ttl")},
    {"name": "Intuitive", "label": "intuitive",
     "extra_types": "", "parent": "vcvf:ValueSituation",
     "comment": "Valuing intuitive understanding: grasping something directly "
                "rather than by explicit reasoning. Evoked by the intuitive "
                "lexicon and its variants, and by the FrameNet Grasp frame.",
     "attributed": ATTRIB.format("folk_Intuitive.ttl")},
    {"name": "Willingness", "label": "willingness",
     "extra_types": "", "parent": "vcvf:ValueSituation",
     "comment": "Valuing readiness to act or consent when asked. Evoked by the "
                "willing lexicon: willing, unwilling, willingly, overwilling, "
                "well-willing. Distinct from folk:Will, which sits under "
                "folk:Strength and reads as willpower rather than readiness.",
     "attributed": ATTRIB.format("folk_Willingness.ttl")},
]

#: (wrong, right, files, rename). The trailing space keeps longer IRIs that
#: start with the same characters untouched.
RETARGET = [
    ("folk:Inclusion", "folk:Inclusiveness",
     ["ThatsAllFolks/folk_Inclusion.ttl", "ThatsAllFolks/taf.ttl"],
     ("ThatsAllFolks/folk_Inclusion.ttl", "ThatsAllFolks/folk_Inclusiveness.ttl")),
    ("folk:Assertiveness", "folk:Assertion",
     ["ThatsAllFolks/folk_Assertiveness.ttl", "ThatsAllFolks/taf.ttl"],
     ("ThatsAllFolks/folk_Assertiveness.ttl", "ThatsAllFolks/folk_Assertion.ttl")),
]

#: The Willingness fragment is headed for a different value. It is declared,
#: not retargeted, so the header is what has to change.
HEADER_FIX = [("ThatsAllFolks/folk_Willingness.ttl",
               "## folk:Will\n", "## folk:Willingness\n"),
              ("ThatsAllFolks/taf.ttl", "## folk:Will\n", "## folk:Willingness\n")]


def read(rel):
    with open(os.path.join(HERE, rel), encoding="utf-8", newline="") as fh:
        return fh.read()


def write(rel, text):
    with open(os.path.join(HERE, rel), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    print("DECLARE")
    for v in DECLARE:
        print(f"  folk:{v['name']} -> {v['parent']}")
        for rel, template in (("ThatsAllFolks/folk.ttl", FULL),):
            text = read(rel)
            if f"folk:{v['name']} " in text:
                print(f"      already declared in {rel}")
                continue
            block = template.format(**v).strip("\n")
            if not args.check:
                write(rel, text.rstrip("\n") + "\n\n" + block + "\n")
            print(f"      {'would declare' if args.check else 'declared'} in {rel}")

    print("\nRETARGET")
    for wrong, right, files, rename in RETARGET:
        print(f"  {wrong} -> {right}")
        pairs = [(wrong + " ", right + " "),
                 ("## " + wrong + "\n", "## " + right + "\n")]
        for rel in files:
            path = os.path.join(HERE, rel)
            if not os.path.exists(path):
                print(f"      missing (already renamed?) {rel}")
                continue
            text = read(rel)
            n = sum(text.count(w) for w, _ in pairs)
            if n and not args.check:
                for w, r in pairs:
                    text = text.replace(w, r)
                write(rel, text)
            if n:
                print(f"      {'would rewrite' if args.check else 'rewrote':<14} "
                      f"{n:>4} in {rel}")
        src, dst = (os.path.join(HERE, p) for p in rename)
        if os.path.exists(src):
            if args.check:
                print(f"      would rename {rename[0]} -> {rename[1]}")
            else:
                os.replace(src, dst)
                print(f"      renamed      {rename[0]} -> {rename[1]}")

    print("\nHEADER FIX")
    for rel, wrong, right in HEADER_FIX:
        text = read(rel)
        n = text.count(wrong)
        if n and not args.check:
            write(rel, text.replace(wrong, right))
        print(f"  {rel}: {n} stale header(s) "
              f"{'to fix' if args.check else 'fixed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
