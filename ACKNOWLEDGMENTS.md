# Acknowledgments

Developed by Aaron Damiano with substantial assistance from Anthropic
Claude and OpenAI Codex agents.

---

## Why this page exists

The AI assistance in this repository was substantive rather than
incidental. It is recorded here in specific terms because a generic
"AI-assisted" footnote would understate what was done and leave a reader
unable to judge it.

The agents are **not** listed as authors in
[CITATION.cff](CITATION.cff). Authorship carries responsibility for the
accuracy and integrity of the work, including the ability to answer for
it, and an AI system cannot assume that responsibility. Established
authorship guidance is explicit on this point, and this project follows
it. They appear instead as software references in the citation record and
as named contributors here.

Aaron Damiano is the citable human author and is answerable for the
content.

## Anthropic Claude

Model identifier `Claude Opus 5`, recorded in the `Co-Authored-By`
trailer of the commits it contributed to. The identifier is used because
it was recorded at the time, not reconstructed afterwards.

Substantive contributions:

- **Ontology engineering.** BFO alignment of the ValueNet vocabulary: the
  disposition/role split beneath a common realizable-entity superclass,
  realization and violation processes, and the CCO-based textual-evidence
  chain. Definition authoring and the category audit.
- **Implementation.** The MAREP audit framework, the layout contract and
  its resolver, the ontology measurement library, the evidence pipeline
  (semantic baseline, transition matrix, remediation record), the CCO
  extract generator, the site build and checker, and the licensing
  classifier.
- **Testing.** The test suite, including its falsification discipline:
  each check is exercised against a deliberately broken input to show it
  can fail, rather than being trusted because it passes.
- **Evidence design.** The document-base and line-ending investigation
  that made corpus digests reproducible independently of checkout
  location; the three-cell transition experiment; and the remediation
  record that lets a frozen experiment be cited across a later corpus
  repair without either being falsified.
- **Review and correction.** Including finding its own errors: a
  fabricated digest, a licence template that passed a test for a licence,
  a checker that read `git ls-files` and so never opened the files it
  reported on, and a full-suite run invalidated by concurrent edits. Those
  are recorded in the commit history rather than tidied away.
- **Documentation.** The README, the publication plan, the provenance and
  licensing records, and this file.

## OpenAI Codex

Product-level name only. No model identifier was recorded at the time, and
none is reconstructed here: a version invented after the fact would be
worse than the absence it replaces.

Contributions to implementation and code assistance during the
repository's development.

## Original ValueNet

The BFO-aligned suite re-expresses the original DUL-aligned ValueNet.

Its published conceptual authorship is Stefano De Giorgis, Aldo Gangemi
and Rossana Damiano, who contributed equally
([10.1007/978-3-031-17105-5_1](https://doi.org/10.1007/978-3-031-17105-5_1)).
Stefano De Giorgis is the sole recorded Git author of the upstream
repository — a measurement of commit authorship, which is a different and
narrower fact. Both are cited in [CITATION.cff](CITATION.cff), separately,
because crediting only the one git can see would erase the other.

That work is the source tradition and the mapping target for this suite.
Its licence has not been identified and this repository grants no rights
over it — see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Upstream ontologies

The Basic Formal Ontology and the Common Core Ontologies, vendored under
their own licences and cited as references. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
