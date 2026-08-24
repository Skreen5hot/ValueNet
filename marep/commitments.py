"""Semantic commitments that live outside the axioms.

Run 2 asked what the corpus should assert and does not. Run 3 asks a wider
question: what does this corpus already commit to in its naming, its file
layout, its mapping targets and its documentation, without ever saying so in a
form a machine could check.

The three areas Run 2 did not reach — sense ambiguity, IRI ownership, external
mapping quality — all became measurable only after the fragment repair. Run 1
reported on them by reading the raw text of files that did not parse, and
undercounted badly as a result. `LANG-001` says "three value terms take their
lexical gloss from a French dictionary"; the loadable graph holds **889**
French Wiktionary triggers against 2,769 English. `MAPPING-002` reads
`<dbpedia:An_Education> vcvf:triggers folk:Education` as aligning the value
Education to a film, but the triple runs the other way and says the film's page
is a lexical trigger for the value, which is a different and far more
defensible claim. Both findings were the best available from unparseable
files. Neither survives measurement unchanged.

That pattern is the reason this module exists rather than another round of
reading. Every check here reports a population and a distribution, so a Run 3
finding argues from what the corpus contains instead of from a sample of what
would not load.

One commitment worth naming up front, because several checks circle it:
`vcvf:triggers` carries 38,710 statements, no domain, no range and no
definition. Whatever it means is held entirely in the heads of the people who
wrote it and in the shape of the data.
"""

from __future__ import annotations

import collections
from pathlib import Path

from .ontology_source import FileFacts, Metric, merged_graph

#: Hosts whose IRIs this repository does not mint. Asserting about them is not
#: wrong — a trigger layer has to name external resources — but it is a
#: commitment about identity, and identity commitments should be visible.
FOREIGN_HOSTS = (
    "dbpedia.org", "wikidata.dbpedia.org", "cs.dbpedia.org",
    "en.wiktionary.org", "fr.wiktionary.org",
    "babelnet.org", "yago-knowledge.org", "umbel.org",
    "premon.fbk.eu", "wordnet-rdf.princeton.edu",
)


def _host(iri: str) -> str:
    return iri.split("/")[2] if "://" in iri else "relative"


def mapping_metrics(repo: Path, facts: list[FileFacts]) -> list[Metric]:
    """The external alignment layer, by predicate, host and language edition.

    Direction is reported explicitly because reading it wrongly is what
    produced `MAPPING-002`. The corpus states
    `<external> vcvf:triggers <folk value>`, so the external resource is the
    subject and the value is the object. A film title in subject position is a
    claim that the page triggers the value; the same IRI in object position
    would be a claim that the value *is* the film. Only one of those is
    defensible and the substrate should not leave an agent to guess which is
    written.
    """
    import rdflib
    from rdflib.namespace import OWL, SKOS

    MAPPING_PREDICATES = [
        ("skos:exactMatch", SKOS.exactMatch), ("skos:closeMatch", SKOS.closeMatch),
        ("skos:broadMatch", SKOS.broadMatch), ("skos:narrowMatch", SKOS.narrowMatch),
        ("skos:relatedMatch", SKOS.relatedMatch), ("skos:related", SKOS.related),
        ("owl:sameAs", OWL.sameAs), ("owl:equivalentClass", OWL.equivalentClass),
    ]
    TRIGGERS = rdflib.URIRef(
        "http://www.ontologydesignpatterns.org/ont/values/"
        "valuecore_with_value_frames.owl#triggers")

    out: list[Metric] = []
    by_group: dict[str, list[FileFacts]] = {}
    for f in facts:
        if f.parses:
            by_group.setdefault(f.group, []).append(f)

    for group, fs in sorted(by_group.items()):
        g = merged_graph(repo, fs)

        declared = sum(len(list(g.triples((None, p, None))))
                       for _, p in MAPPING_PREDICATES)
        triggers = list(g.triples((None, TRIGGERS, None)))
        if not declared and not triggers:
            continue

        if declared:
            named = ", ".join(f"{n}={len(list(g.triples((None, p, None))))}"
                              for n, p in MAPPING_PREDICATES
                              if list(g.triples((None, p, None))))
            out.append(Metric("mapping_statements", group, declared,
                              detail=f"by predicate: {named}"))

        if not triggers:
            continue

        subj_foreign = collections.Counter()
        obj_foreign = collections.Counter()
        for s, _, o in triggers:
            if isinstance(s, rdflib.URIRef):
                subj_foreign[_host(str(s))] += 1
            if isinstance(o, rdflib.URIRef):
                obj_foreign[_host(str(o))] += 1

        top = ", ".join(f"{h} {n:,}" for h, n in subj_foreign.most_common(5))
        out.append(Metric("trigger_statements", group, len(triggers),
                          detail=f"vcvf:triggers, which declares no domain, no "
                                 f"range and no definition; subject hosts: {top}"))
        out.append(Metric("trigger_source_hosts", group, len(subj_foreign),
                          detail=f"distinct hosts in SUBJECT position, i.e. the "
                                 f"external resource that triggers a value: "
                                 f"{', '.join(sorted(subj_foreign))}"))
        # Direction, stated as a number so a finding cannot assume it.
        out.append(Metric("triggers_with_foreign_subject", group,
                          sum(n for h, n in subj_foreign.items() if h in FOREIGN_HOSTS),
                          detail="external resource is the SUBJECT: the statement "
                                 "says the resource triggers the value, not that "
                                 "the value is the resource"))
        out.append(Metric("triggers_with_foreign_object", group,
                          sum(n for h, n in obj_foreign.items() if h in FOREIGN_HOSTS),
                          detail="external resource in OBJECT position, which would "
                                 "assert the value maps onto the resource"))

        wik = collections.Counter()
        for h, n in subj_foreign.items():
            if "wiktionary" in h:
                wik[h.split(".")[0]] += n
        if wik:
            total = sum(wik.values())
            spread = ", ".join(f"{k}={v:,}" for k, v in wik.most_common())
            out.append(Metric("wiktionary_language_editions", group, len(wik),
                              detail=f"of {total:,} wiktionary triggers: {spread}"))
            non_en = total - wik.get("en", 0)
            out.append(Metric("wiktionary_non_english_triggers", group, non_en,
                              detail=f"of {total:,}; a language edition is a "
                                     f"commitment about which lexicon defines the "
                                     f"term, and nothing in the corpus records it"))
    return out


def iri_ownership_metrics(repo: Path, facts: list[FileFacts]) -> list[Metric]:
    """Which IRIs this corpus mints, which it borrows, and where that blurs.

    Two distinct commitments, both currently implicit:

    *Minting.* An IRI in a namespace this repository controls is a term it is
    responsible for defining. One in `dbpedia.org` is not.

    *Axiom siting.* `IRI-001` found 54 class IRIs receiving class axioms in two
    or more files. That is a statement about who owns a definition, made by
    file layout rather than by anything a reader can check.
    """
    import rdflib
    from rdflib.namespace import OWL, RDF, RDFS

    out: list[Metric] = []
    parsing = [f for f in facts if f.parses]

    groups_of = {f.rel: f.group for f in parsing}
    sites: dict[str, set] = collections.defaultdict(set)
    minted: collections.Counter = collections.Counter()
    subjects_foreign: collections.Counter = collections.Counter()

    for f in parsing:
        g = merged_graph(repo, [f])
        for s in g.subjects(RDF.type, OWL.Class):
            if isinstance(s, rdflib.URIRef):
                sites[str(s)].add(f.rel)
                minted[_host(str(s))] += 1
        for s in set(g.subjects(None, None)):
            if isinstance(s, rdflib.URIRef) and _host(str(s)) in FOREIGN_HOSTS:
                subjects_foreign[_host(str(s))] += 1

    # Same-group and cross-group re-declaration are different facts and must
    # not share a number. 2,240 IRIs are declared in more than one file, which
    # reads as pervasive contested ownership until you look: most are vale2024
    # classes appearing in five parameter variants of one ontology, which is
    # the shape Run 2's Restraint already defended as materialised variants
    # rather than drift. Re-declaration *across groups* is the one that raises
    # a real question about which module owns a term.
    multi = {i: v for i, v in sites.items() if len(v) > 1}
    cross = {i: v for i, v in multi.items()
             if len({groups_of.get(rel, rel) for rel in v}) > 1}
    out.append(Metric("class_iris_declared", "corpus", len(sites),
                      detail="distinct IRIs receiving a class declaration"))
    out.append(Metric("class_iris_declared_in_multiple_files", "corpus", len(multi),
                      detail=f"of {len(sites)}; mostly parameter variants of one "
                             f"ontology within a single group, which is not "
                             f"contested ownership - see the cross-group count"))
    # The IRI count alone is still over-readable, which Run 3's IRI-005 caught:
    # all 378 cross-group IRIs are the same file pair, ThatsAllFolks/folk.ttl
    # against folk_aligned.ttl, 325 of them that pair and nothing else. That is
    # one governance question -- which of two near-copies of a module is
    # canonical -- and not 378 naming collisions. So the number of distinct
    # file pairings ships beside the IRI count, because it is the one that says
    # how many decisions are actually pending.
    pairings = collections.Counter(tuple(sorted(v)) for v in cross.values())
    top = "; ".join(f"{' + '.join(Path(x).name for x in pair)} ({n})"
                    for pair, n in pairings.most_common(3))
    out.append(Metric("class_iris_declared_across_groups", "corpus", len(cross),
                      detail=f"of {len(multi)} multi-file IRIs. Read this with "
                             f"cross_group_file_pairings: a large IRI count over "
                             f"few pairings is one duplicated module, not many "
                             f"collisions. Top: {top or 'none'}"))
    out.append(Metric("cross_group_file_pairings", "corpus", len(pairings),
                      detail=f"distinct sets of files sharing a class IRI across "
                             f"groups; this is the number of ownership decisions "
                             f"pending, not {len(cross)}"))

    out.append(Metric("namespaces_minting_classes", "corpus", len(minted),
                      detail=", ".join(f"{h} {n}" for h, n in minted.most_common(6))))

    if subjects_foreign:
        total = sum(subjects_foreign.values())
        out.append(Metric("foreign_iris_used_as_subjects", "corpus", total,
                          detail="the corpus makes assertions about resources in "
                                 "namespaces it does not control: "
                                 + ", ".join(f"{h} {n:,}" for h, n
                                             in subjects_foreign.most_common(5))))
    return out


def lexical_metrics(repo: Path, facts: list[FileFacts]) -> list[Metric]:
    """Where a term's meaning rests on its name rather than on an axiom.

    `DEF-003` named Smart, Intelligence, Genius and Brilliance as a
    near-synonym family with nothing to separate them. This counts how much of
    the vocabulary is in that position: labelled, placed in a hierarchy, and
    carrying no definition text at all.
    """
    import rdflib
    from rdflib.namespace import OWL, RDF, RDFS, SKOS

    out: list[Metric] = []
    by_group: dict[str, list[FileFacts]] = {}
    for f in facts:
        if f.parses:
            by_group.setdefault(f.group, []).append(f)

    for group, fs in sorted(by_group.items()):
        g = merged_graph(repo, fs)
        classes = {s for s in g.subjects(RDF.type, OWL.Class)
                   if isinstance(s, rdflib.URIRef)}
        if not classes:
            continue

        def has_text(s, preds):
            return any((s, p, None) in g for p in preds)

        undefined = {c for c in classes
                     if not has_text(c, (RDFS.comment, SKOS.definition,
                                         SKOS.scopeNote, RDFS.isDefinedBy))}
        unlabelled = {c for c in classes
                      if not has_text(c, (RDFS.label, SKOS.prefLabel))}
        out.append(Metric("classes_without_definition_text", group, len(undefined),
                          detail=f"of {len(classes)}; no rdfs:comment, "
                                 f"skos:definition, scopeNote or isDefinedBy, so the "
                                 f"term's meaning rests on its name"))
        out.append(Metric("classes_without_a_label", group, len(unlabelled),
                          detail=f"of {len(classes)}"))

        # Local names differing only by case or separator are the same term
        # written twice, which is a naming commitment nothing enforces.
        norm: dict[str, set] = collections.defaultdict(set)
        for c in classes:
            local = str(c).split("#")[-1].split("/")[-1]
            norm[local.lower().replace("_", "").replace("-", "")].add(local)
        collisions = {k: v for k, v in norm.items() if len(v) > 1}
        out.append(Metric("local_names_colliding_on_normalisation", group,
                          len(collisions),
                          detail=f"of {len(norm)} distinct normalised names; "
                                 + ("e.g. " + "; ".join(
                                     "/".join(sorted(v)) for v in
                                     list(collisions.values())[:3])
                                    if collisions else "none")))
    return out
