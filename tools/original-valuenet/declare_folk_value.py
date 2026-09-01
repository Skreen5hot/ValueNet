# SPDX-License-Identifier: Apache-2.0
"""Declare a folk value that trigger data references but nothing declares.

Six trigger objects remained undeclared after the Repayment, Strenght and
Belief corrections. Checking each fragment before declaring turned three of
them into something else entirely, so this script declares only what has been
individually reviewed, and the list below is the record of that review.

The check that matters is not "is there a fragment named for it" but "does
anything already declared cover it". Three of the six failed that check:

* `Willingness` — the fragment is headed `## folk:Will`, and `folk:Will` is
  declared, carries the label "will", and receives zero triggers.
* `Inclusion` — the fragment is headed `## folk:Inclusiveness`, and
  `folk:Inclusiveness` is declared with a definition that opens "Inclusion is
  a value that focuses on accepting diversity", so the two name one concept.
  It too receives zero triggers.
* `Assertiveness` — the fragment is self-consistent, but `folk:Assertion` is
  declared with the label "assertion, assertion , assertiveness" and receives
  zero triggers. Declaring both would manufacture the near-synonym pair that
  Run 1's DEF-003 and Run 3's LEXICON-003 already report.

Each is a modelling decision, not a mechanical gap, and is held for review.

    python tools/original-valuenet/declare_folk_value.py [--check]
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

#: Values cleared for declaration: fragment header, filename and trigger object
#: all agree, and nothing already declared covers the term.
#:
#: `parent` is `vcvf:ValueSituation` where no more specific parent is
#: evidenced. Asserting a folk-value parent would be inventing a taxonomic
#: claim to fill a blank, which is the failure mode this whole review exists
#: to avoid; `folk:Beliefs` sits directly under ValueSituation for the same
#: reason.
VALUES = [
    {
        "name": "Involvement",
        "label": "involvement",
        "comment": (
            "Valuing involvement refers to taking an active part in something "
            "rather than remaining apart from it. Evoked by the involvement "
            "lexicon and its variants: involvement, noninvolvement, "
            "overinvolvement, reinvolvement."
        ),
        "parent": "vcvf:ValueSituation",
        "attributed": (
            "ValueNet modelling decision, docs/bfo/guides/vcvf-triggers-review.md ; "
            "derived from the lexicon of ThatsAllFolks/folk_Involvement.ttl"
        ),
    },
]

FULL_TEMPLATE = """
folk:{name} a folk:FolkValue,
        owl:Class,
        owl:NamedIndividual ;
    rdfs:label "{label}" ;
    rdfs:comment "{comment}" ;
    rdfs:subClassOf {parent} ;
    owl:equivalentClass [ a owl:Restriction ;
            owl:onProperty dul:satisfies ;
            owl:someValuesFrom [ a owl:Class ;
                    owl:oneOf ( folk:{name} ) ] ] ;
    prov:wasAttributedTo "{attributed}" .
"""

ALIGNED_TEMPLATE = """
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

#: Both representations are written. They hold the same content — 3,006 against
#: 3,000 ground triples, differing in about five ontology-level metadata
#: statements and in blank-node identity — and differ in serialization style
#: rather than in what they say. Which is canonical is open under
#: implementation plan §4.
#: Writes ONLY to the authored source. folk_aligned.ttl is generated from it by
#: tools/original-valuenet/generate_folk_aligned.py, and writing there by hand would be
#: overwritten on the next run and fail the staleness test in CI. Run the
#: generator after this script.
TARGETS = [("ThatsAllFolks/folk.ttl", FULL_TEMPLATE)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report without writing")
    args = ap.parse_args(argv)

    for value in VALUES:
        print(f"folk:{value['name']} -> {value['parent']}")
        for rel, template in TARGETS:
            path = os.path.join(HERE, rel)
            with open(path, encoding="utf-8", newline="") as fh:
                text = fh.read()
            if f"folk:{value['name']} " in text:
                print(f"    already declared in {rel}")
                continue
            block = template.format(**value).strip("\n")
            if not args.check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(text.rstrip("\n") + "\n\n" + block + "\n")
            print(f"    {'would declare' if args.check else 'declared'} in {rel}")

    print("\nHeld for individual review, each a modelling decision:")
    for name, why in [
        ("BadHealth", "relationship to folk:Health and the NegativeValue convention"),
        ("Intuitive", "intended concept, not a grammatical-convention rename"),
        ("Willingness", "fragment headed ## folk:Will; folk:Will declared, 0 triggers"),
        ("Inclusion", "fragment headed ## folk:Inclusiveness; that term declared, 0 triggers"),
        ("Assertiveness", "folk:Assertion declared with 'assertiveness' in its label, 0 triggers"),
    ]:
        print(f"    folk:{name:<14} {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
