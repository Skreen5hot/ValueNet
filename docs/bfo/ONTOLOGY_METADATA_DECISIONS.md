# Ontology Metadata Decisions

Decisions about the ontology's annotation metadata -- labels, definitions,
synonyms -- as distinct from its logical content. A record here does not
authorise an RDF edit; it states a question and, once adopted, the policy an
edit would have to follow.

## M-001 -- Label capitalisation style

**Status:** Open, recorded 2026-09-02
**Raised by:** the Phase 4 explorer review, which surfaced the inconsistency
while testing search ranking
**Blocks:** any evidence-bearing edit to `rdfs:label` in the authored modules

### Finding

18 of the 187 authored classes carry a label that does not begin with a
capital letter. They fall into two groups, which is why this is a policy
question rather than a typo list:

- **all lower case** -- 12 label(s)
- **lower-case first word, capitalised remainder** -- 6 label(s)

The remaining 169 labels are title case.

### Inventory

Derived from the generated class index, not transcribed. A test asserts
this table still matches what the index reports, so it cannot drift
silently as the corpus changes.

| Class | Label | Pattern |
| --- | --- | --- |
| `core:EvidenceSource` | `evidence source` | all lower case |
| `core:MoralValueDisposition` | `moral value disposition` | all lower case |
| `core:PersonalValueDisposition` | `personal value disposition` | all lower case |
| `core:TextSpan` | `text span` | all lower case |
| `core:TextSpanSelector` | `text span selector` | all lower case |
| `core:TextualRepresentation` | `textual representation` | all lower case |
| `core:ValueDisposition` | `value disposition` | all lower case |
| `core:ValueEvidenceAnnotation` | `value evidence annotation` | all lower case |
| `core:ValueRealizationProcess` | `value realization process` | all lower case |
| `core:ValueRelatedRealizableEntity` | `value-related realizable entity` | all lower case |
| `core:ValueRole` | `value role` | all lower case |
| `core:ValueViolationProcess` | `value violation process` | all lower case |
| `moral-foundations:AuthorityDisposition` | `authority Disposition` | lower-case first word, capitalised remainder |
| `moral-foundations:CareDisposition` | `care Disposition` | lower-case first word, capitalised remainder |
| `moral-foundations:FairnessDisposition` | `fairness Disposition` | lower-case first word, capitalised remainder |
| `moral-foundations:LibertyDisposition` | `liberty Disposition` | lower-case first word, capitalised remainder |
| `moral-foundations:LoyaltyDisposition` | `loyalty Disposition` | lower-case first word, capitalised remainder |
| `moral-foundations:SanctityDisposition` | `sanctity Disposition` | lower-case first word, capitalised remainder |

### Why this is not a Phase 4 change

Two reasons, and the second is the operative one.

Phase 4 publishes what the ontology asserts. A site phase that quietly
rewrote 18 labels would make the published index disagree with the Turtle
it claims to extract, which is the one thing the class index exists not to
do.

More importantly, the two groups may not be one defect. `valuenet-core`
uses all-lower-case labels throughout -- every one of its 12 classes -- which
reads as a deliberate convention rather than an oversight. The
`valuenet-moral-foundations` group is mixed within single labels, which
reads more like drift. Normalising both to title case would impose one
convention on a module that may have chosen another, and the choice belongs
to whoever owns the ontology's authoring style.

### What adoption requires

1. One label-style policy, stated for the whole suite: title case,
   sentence case, or lower case, and whether it binds every module.
2. A decision on whether `valuenet-core`'s convention is grandfathered or
   converted.
3. Only then an RDF edit. It moves the ground digest and the pinned
   class-index content digest, both evidence-bearing, so it needs its own
   commit and its own evidence cycle and must not ride along with
   unrelated work.

   The blank-node fingerprint should **not** move, and that is a check
   rather than a footnote. `rdfs:label` on a named class is a ground
   triple: subject, predicate and object are all named, so no blank node
   is touched. If the fingerprint moves during a label edit, the edit
   reached something other than labels -- a restriction, an axiom, a
   SHACL shape -- and should be rejected until it is understood.

   An earlier revision of this record listed the fingerprint among the
   measures that would move. That was asserted rather than checked;
   editing a label in a loaded graph and recomputing both measures shows
   the ground digest changing and the blank-node shape identical.

### Reopen when

- a label-style policy is chosen; or
- a consumer reports the inconsistency as a defect rather than a variation;
  or
- new modules add labels in a third pattern, which would mean the
  convention is not being inherited from anywhere.
