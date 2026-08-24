"""Declare folk:Religion under folk:Beliefs and retarget the orphaned triggers.

`folk:Belief` was the object of 480 trigger statements and was declared
nowhere. Its fragment, `folk_Belief.ttl`, is headed `# religion lu` with a
`# ReligiousBelief frame` section, and its vocabulary is a religion lexicon
throughout — religion, antireligion, nonreligion, pseudoreligion, religionist,
religionize, bishop, temple, spirit. The triggers are not about believing in
general and not about propositional content; they are about religion.

Retargeting them to `folk:Beliefs` would have put a specific lexicon onto a
category term that already has two more specific children, `folk:Faith` and
`folk:Belief_in_God`, each with its own vocabulary. `folk:Religion` takes the
place the data was already describing, as a third sibling.

`folk:Belief` is deliberately not declared. It names nothing once its triggers
move, and formalising it would create a value whose only justification was a
mis-set object.

The fragment is renamed with the triggers. Of 127 fragment files, 126 use
exactly their own filename as their trigger object; that convention is what
identified the `folk_Recognition.ttl` mis-target, and leaving
`folk_Belief.ttl` pointing at `folk:Religion` would break it here.

Both declaring files are written, in each one's own style. `ThatsAllFolks/
folk.ttl` carries labels, comments and provenance; `folk_aligned.ttl` is a
reduced alignment view carrying only type, equivalence and subclass. Which of
the two is canonical is a separate open question (implementation plan §4), and
writing only one would deepen the divergence while that is undecided.

Idempotent.

    python ValueNet_code/add_folk_religion.py [--check]
"""

from __future__ import annotations

import argparse
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Writes ONLY to the authored source. folk_aligned.ttl is generated from it by
#: ValueNet_code/generate_folk_aligned.py, and writing there by hand would be
#: overwritten on the next run and fail the staleness test in CI. Run the
#: generator after this script.

#: Matches the shape of folk:Faith, its sibling under folk:Beliefs.
#:
#: `rdfs:comment` describes what the value covers and says where that reading
#: comes from. Faith's comment is attributed to a published core-values list;
#: Religion appears on no such list, which is why it was never declared, so
#: inventing a matching `prov:wasAttributedTo` would fabricate a source. The
#: attribution names this decision instead.
FULL = """
folk:Religion a folk:FolkValue,
        owl:Class,
        owl:NamedIndividual ;
    rdfs:label "religion" ;
    rdfs:comment "Valuing religion refers to holding a system of religious belief and practice as a guide to living. It sits under Beliefs alongside Faith and Belief in God, and is the value evoked by religious vocabulary: religion itself, its negations and variants, and the roles and places of religious practice." ;
    rdfs:subClassOf folk:Beliefs ;
    owl:equivalentClass [ a owl:Restriction ;
            owl:onProperty dul:satisfies ;
            owl:someValuesFrom [ a owl:Class ;
                    owl:oneOf ( folk:Religion ) ] ] ;
    prov:wasAttributedTo "ValueNet modelling decision, BFO/vcvf-triggers-review.md ; derived from the religion lexicon of ThatsAllFolks/folk_Religion.ttl" ;
    fschema:subsumedUnder folk:Beliefs .
"""

#: The reduced form used by folk_aligned.ttl: type, equivalence, subclass.
ALIGNED = """
###  http://www.ontologydesignpatterns.org/ont/values/FolkValues.owl#Religion
folk:Religion rdf:type owl:Class ;
              owl:equivalentClass [ rdf:type owl:Restriction ;
                                    owl:onProperty dul:satisfies ;
                                    owl:someValuesFrom [ rdf:type owl:Class ;
                                                         owl:oneOf ( folk:Religion
                                                                   )
                                                       ]
                                  ] ;
              rdfs:subClassOf folk:Beliefs .
"""

MARKER = "folk:Religion"

#: The trailing space matters: it keeps `folk:Belief_in_God` untouched, which
#: is a sibling under folk:Beliefs and must not be renamed. Neither edited file
#: contains it, but the guard is cheap and the mistake would be silent.
#: The second pair is the `## folk:Belief` section header each file carries;
#: the header names the value the file is about, so it moves with the triggers.
RETARGETS = [("folk:Belief ", "folk:Religion "),
             ("## folk:Belief" + chr(10), "## folk:Religion" + chr(10))]
TRIGGER_FILES = ["ThatsAllFolks/folk_Belief.ttl", "ThatsAllFolks/taf.ttl"]
RENAME = ("ThatsAllFolks/folk_Belief.ttl", "ThatsAllFolks/folk_Religion.ttl")


def read(rel: str) -> str:
    with open(os.path.join(HERE, rel), encoding="utf-8", newline="") as fh:
        return fh.read()


def write(rel: str, text: str) -> None:
    with open(os.path.join(HERE, rel), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def declare(rel: str, block: str, check: bool) -> bool:
    text = read(rel)
    if MARKER in text:
        print(f"    already declares folk:Religion   {rel}")
        return False
    if not check:
        write(rel, text.rstrip("\n") + "\n\n" + block.strip("\n") + "\n")
    print(f"    {'would declare' if check else 'declared'} folk:Religion in {rel}")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args(argv)

    print("declaring folk:Religion under folk:Beliefs")
    declare("ThatsAllFolks/folk.ttl", FULL, args.check)

    print("\nretargeting folk:Belief -> folk:Religion")
    total = 0
    for rel in TRIGGER_FILES:
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            print(f"    missing (already renamed?)      {rel}")
            continue
        text = read(rel)
        n = sum(text.count(wrong) for wrong, _ in RETARGETS)
        total += n
        if n and not args.check:
            for wrong, right in RETARGETS:
                text = text.replace(wrong, right)
            write(rel, text)
        if n:
            print(f"    {'would rewrite' if args.check else 'rewrote':<14} "
                  f"{n:>4} occurrence(s) in {rel}")

    src, dst = (os.path.join(HERE, p) for p in RENAME)
    if os.path.exists(src):
        if args.check:
            print(f"    would rename   {RENAME[0]} -> {RENAME[1]}")
        else:
            os.replace(src, dst)
            print(f"    renamed        {RENAME[0]} -> {RENAME[1]}")

    print(f"\n{total} trigger occurrence(s) "
          f"{'would be ' if args.check else ''}retargeted.")
    print("folk:Belief is not declared: it names nothing once its triggers move.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
