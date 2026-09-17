# Open Issues After the Formal-Review Remediation: Proposals

**Status:** Proposals, 2026-09-16. None of them is decided here.
**Scope:** everything still open on branch `formal-review-remediation` other than folk membership, which has its own document, `R15_FOLK_MEMBERSHIP_PROPOSAL.md`.

The issues are listed in the order they should be done. Most of them depend on the one before.

## O1. The explorer tests fail on this machine: install Node 24

**Facts, checked 2026-09-16.**

- `.nvmrc` pins Node **24.20.0**. The Pages workflow reads that file (`actions/setup-node` with `node-version-file: .nvmrc`), so CI already runs the pinned version.
- This machine has Node **25.2.1** on PATH and no version manager.
- **v25 reached end of life on 2026-06-01.** v24 ("Krypton") is LTS until 2028-04-30, moving to maintenance on 2026-10-20. Source: [Node.js release schedule](https://raw.githubusercontent.com/nodejs/Release/main/schedule.json).
- **24.20.0 exists**, released 2026-08-26, with a Windows x64 installer ([dist/v24.20.0](https://nodejs.org/dist/v24.20.0/)). The newest v24 release is 24.21.0.

**Proposal.** Install Node 24.20.0 on this machine and keep the pin. Either use the MSI from the dist directory, or install a version manager (nvm-windows or Volta) so that the pinned version follows `.nvmrc`. No repository change is needed.

Do not move the pin to v25, which is end-of-life, or to v26, which does not become LTS until 2026-10-28. Moving to 24.21.0 is a separate site change with its own browser review; there is no reason to do it now.

**Why first.** O2's fresh-clone check runs the site suite, which includes these tests.

## O2. Re-sign the public-content sign-off

**Facts.**

- `config/quality-report.json` holds the owner's sign-off, signed 2026-09-03 against commit d9a4cb43. The published content has changed since: the text layer, two split folk classes, the folk membership D-014 decided (seven classes removed, six added), every term's comment and example, and new definitions.
- `test_the_link_report_still_holds` fails because the models page now has one more internal link.
- The report must be regenerated with `--fresh-clone`, because the tests require that section. That step clones the repository and runs the site and licensing suites.

**Proposal.** After O1, and after D-014 is implemented — so the sign-off covers the content that will be published — run:

```
python tools/site/build_site.py
python tools/site/quality_report.py --fresh-clone --sign "Aaron Damiano"
```

Then commit `config/quality-report.json`. Only the owner can make this statement; the tool records it.

## O3. Tell the reviewer what happened after the sign-off

**Facts.** The reviewer signed off on breaking changes 1–4 and said nothing further was needed. These things were decided after that:

- **D-011** makes the form-level text classes disjoint with ICE. By the reviewer's own test — "breaking only if the repair introduces or changes OWL conditions" — this is a breaking change: data asserting aboutness of a representation was consistent before and is inconsistent now.
- **D-012** narrows two folk definitions and adds a class. The IRIs are unchanged.
- **D-013** adopts the reviewer's RULES 2.0 with two readings they did not state:
  - "a … disposition *to* …" conforms to "b is a c that d's";
  - web search is optional.
- **D-014** answers the reviewer's folk-membership concern: criteria M1–M7, coverage reported by kind, and a decision on every unpaired value and class. It retires seven folk IRIs — the three Schwartz copies, Openness, Impact, Discretion and Resourcefulness — which is an IRI break, re-parents five classes and adds six.

**Proposal.** Send the reviewer:

- §11 of the review response;
- D-011 to D-014;
- the R15 record, revision 4.

Ask three questions: whether D-011 needs the same review as the original breaking set, whether the two readings of RULES 2.0 are acceptable, and whether the membership criteria M1–M7 meet their concern. Record their reply beside the others in `docs/bfo/reviews/`.

## O4. Push the branch and open the pull request

**Facts.** Nothing on `formal-review-remediation` has been pushed. The constraint was "cannot push until after the review"; the review has since signed off. CI runs the full site suite with the pinned Node, so the explorer tests that fail locally should pass there.

**Proposal.** Push after O2 and O3, so that the pull request carries a current sign-off and the reviewer's view of the post-sign-off decisions. The pull request description can be §11 of the response. If you want the work visible sooner, push to the branch without merging.

## O5. An evidence measure says "named" and counts anonymous classes too

**Facts.** In `tools/marep/build_semantic_baseline.py`, `bfo_layer_classes` is defined as "named classes in the HermiT scope". It counts every `owl:Class` node, including anonymous class expressions.

This came to light when D-005 moved the count from 306 to 308: named classes were unchanged, and two anonymous ones had been added. The evidence tests now explain the difference in a comment.

**Proposal.** Correct the definition to "classes, named and anonymous, in the HermiT scope". Bump `TOOL_VERSION` to 6, since the tool's own rule is to bump when a definition changes, and regenerate the evidence in the same commit.

Alternatively, count named classes only and bump the version. That makes the measure match its name, but changes the number every earlier record used. The first option is recommended: it changes words, not history. This is low priority.

## O6. Dated corpus counts in the competency-question document

**Facts.** `valuenet-moral-epistemics-CQ.md` says the queries ran over "1,604 triples on 2026-08-25" and "11,769 triples on 2026-08-25". Both numbers are dated, so neither is false. Neither is checked, though, and both moved in phases C to E.

**Proposal.** Drop the counts and keep the lists of files loaded. `tests/integration/test_competency_questions.py` already runs every query and checks that each returns rows, which is the claim that matters. A hand-typed size is the kind of number this repository has repeatedly found drifting.

## O7. Stale worktree records under OneDrive

**Facts.** `.git/worktrees/` holds 40 directories for worktrees that no longer exist, some from earlier sessions. `git worktree prune` fails with "Permission denied" on every one of them. The repository sits in OneDrive, which holds file locks. They are harmless: `git worktree list` shows only the main checkout.

**Proposal.** Pause OneDrive sync, run `git worktree prune`, and resume. Longer term, consider keeping the working copy outside a synced folder, since file locks are what blocked the prune. Not urgent.

## O8. The two text classes show as "other" in the explorer

**Facts.** After D-005, `TextualRepresentation` and `TextSpan` reach none of the explorer's four category roots, so the class index files them under "other". They are listed as reviewed there. Adding a fifth category would change the site schema and the explorer.

**Proposal.** No change. They are two of 186 classes, "other" is accurate, and a category for them would be a site feature built for a single decision. Reconsider if a later module adds more form-level classes.

## Order

1. **O1** — install Node 24.
2. **R15** — done: D-014 implemented, and the folk curation pass complete.
3. **O2** — re-sign.
4. **O3** — reviewer update. D-014 is already implemented, so the reviewer is asked about M1–M7 after the fact; a disagreement reopens D-014 under its own terms.
5. **O4** — push and open the pull request.
6. **O5–O8** — whenever convenient.
