# Handoff

For whoever picks this up next. What the repository is in the middle of, the conventions that will bite you if you ignore them, and what to do first.

Written 2026-09-18, with `main` at the merge commit `85b1ef5` and the site deployed from it.

## Where things stand

The formal ontology review of 2026-09-16 has been remediated, reviewed again, signed off, merged and deployed.

- **Decisions D-005 to D-015** are in `docs/bfo/remediation/DECISION_RECORDS.md`, each with its rationale, its consequences and the conditions that would reopen it. The gate table at the end says which are implemented.
- **The reviewer** signed off twice: on the plan (`FORMAL_REVIEW_2026-09-16_REVIEWER_SIGNOFF.md`) and, after the work, on everything done since (`..._REVIEWER_SIGNOFF_2.md`). They recognize six breaking changes. D-015 came after that and is a seventh.
- **The folk module** is settled: membership decided by criteria (D-014), then curated (D-013). Every definition in all five modules opens with its asserted parent, and every term has a comment and an example. Both gates are at zero, and their records in `tests/bfo/test_definition_discipline.py` are empty.
- **The site** is deployed at https://skreen5hot.github.io/ValueNet/ and the owner's public-content sign-off in `config/quality-report.json` is current as of `dda2b84`.

## What to do next

`docs/bfo/OPEN_ITEMS.md` is the backlog and the only place to look for one. It is ordered P0, P1, P2, operational, and accepted-or-deferred, and `tests/bfo/test_open_items.py` re-derives it, so it cannot quietly go stale. Start at P0.

Two P1 items matter most to anyone outside the project, and they go together: the migration manifest (OI-10) and release identity (OI-13). Seven breaking changes have landed while every module still declares `owl:versionIRI …/1.0/…`, there is no release tag, and the downloads carry no release identifier.

## Conventions that are not optional

Each of these exists because something went wrong without it. Breaking one usually fails a test; the ones that do not are marked.

**Every claim is measured, not transcribed.** Figures in documents are re-derived by tests: the class counts in `ONTOLOGY_METADATA_DECISIONS.md`, the coverage figures in D-014, the register's figures, the mapping counts on the site's models page. If you write a number into a document, expect to add or update the test that checks it.

**Falsify every check you add.** Make the thing the test is about actually wrong, in a state you have verified is different, and watch the test fail; then restore. A check that has never failed is not known to work. This has caught real mistakes here, including a test asserting an ancestor relation it did not mean.

**Ontology changes carry evidence.** After any change to a `.ttl` file:

1. Commit the ontology change with its tests and site pins.
2. Regenerate the evidence **in a clean worktree**, because the untracked `.claude/` directory makes the main tree dirty:
   `git worktree add --detach <scratch>/wt <commit>` then `python tools/marep/build_evidence.py --remediation` there.
3. Copy `config/remediation-record.json` and `config/semantic-baseline.json` back, and commit them alone.
4. Add the event to `LEDGER` in `tests/integration/test_semantic_baseline.py`, with its measured `(added, removed)` ground triples and the reason, and commit that alone.

Event boundaries are re-derived from the commits that touch Turtle, so an event can move to a different commit hash when a later change lands. That happened to D-013's event. Update the ledger entry rather than forcing the old hash.

**Site pins move with published content.** Definitions and labels are published. When they change, `tests/site/test_class_index.py`'s `NORMALISED_CONTENT` digest changes (the test prints the new value), and the browser review must be re-run:
`python tools/site/build_site.py -o <scratch>/site` then `python tools/site/browser_review.py --site <scratch>/site`. It writes `config/browser-review.json` and screenshots under `docs/site/browser-review/`.

**The pinned Node runtime is per-process.** `.nvmrc` pins 24.20.0; this machine's system Node is 25.2.1 and stays that way. The pinned runtime lives in `%LOCALAPPDATA%\ValueNet\toolchains\node-v24.20.0-win-x64`, verified against nodejs.org's published SHA-256. Put it at the front of PATH for the one process that needs it — the site suite, the full suite, or the quality report — and verify `node --version` before proceeding. Do not change the machine PATH, PowerShell profiles, or the HIRI project's toolchain. Without it, 23 explorer tests fail.

**The public-content sign-off is the owner's.** `python tools/site/quality_report.py --fresh-clone --sign "<name>"` is a statement about what the site publishes. An agent runs it without `--sign`, writing to a scratch path, to check that the measured sections pass. Only the owner signs.

**Git.** `origin` is the owner's fork, `Skreen5hot/ValueNet`; `upstream` is the original authors' repository and never receives anything. Push only when asked. `gh` defaults to the parent repository for a fork, so always pass `--repo Skreen5hot/ValueNet`. **Merge with a merge commit, never squash or rebase:** the evidence ledger and the quality report cite commit hashes, and rewriting them breaks tests that require those commits in `main`'s history. Merging `main` deploys the public site.

**Records are inputs, not prose.** `tests/bfo/test_folk_membership.py` reads D-014 and the R15 tables and checks the ontology against them. `tests/bfo/test_open_items.py` does the same for the register, and `tests/bfo/test_text_layer_follows_d005.py` reads D-005's wording. Change a record and a test may follow, which is the point.

## Running things

```
python -m pytest -q -p no:randomly tests            # ~8-12 min; slow tests are deselected by default
python tools/bfo/folk_coverage.py                   # folk coverage by kind (D-014)
python tools/bfo/check_bfo_consistency.py           # HermiT over the BFO layer
python tools/site/build_site.py -o <scratch>/site   # never commit _site
python tools/marep/build_evidence.py --remediation  # in a clean worktree only
```

The full suite needs the pinned Node on PATH, `owlready2` and a Java runtime for HermiT, and Playwright browsers for the browser review. Tests skip rather than fail when a reasoner or browser is missing, so a green run on a bare machine proves less than it looks.

## Traps this project has already fallen into

- **OneDrive holds file locks.** `git worktree prune` fails, leaving stale `.git/worktrees` entries. Harmless; it is OI-3.
- **`_site` goes stale silently.** A build that did not run leaves the previous one in place, and the quality report will happily measure it. Check the build printed `29 file(s) -> _site` and a tree digest.
- **Pasting multi-line commands into Windows PowerShell** can crash PSReadLine and leave a `>>` continuation prompt, so the command never runs and nothing says so. Type them, or paste one line at a time.
- **`Expand-Archive` takes minutes** on an npm-sized zip. It is not hung.
- **Heredocs break** on large Python or on backslashes. Write a scratchpad script instead.
- **The extract generator refuses to write outside the repository,** which matters when reproducing it for comparison.
- **A probe namespace that shares a base IRI with the ontology** gets mangled by owlready2 and quietly breaks a positive control. Use `https://example.invalid/...`.

## Ground truth, in order

| what | where |
|---|---|
| what is left to do | `docs/bfo/OPEN_ITEMS.md` |
| why the ontology is the way it is | `docs/bfo/remediation/DECISION_RECORDS.md` |
| the review, the replies and both sign-offs | `docs/bfo/reviews/` |
| folk membership: criteria, research, every decided value | `docs/bfo/remediation/R15_FOLK_MEMBERSHIP_PROPOSAL.md` |
| the definition and annotation standard | `docs/bfo/reviews/FORMAL_REVIEW_2026-09-16_RULES_2.0.md`, as read by D-013 |
| what changed, triple by triple, and when | `config/remediation-record.json`, `config/semantic-baseline.json`, and `LEDGER` |
| where every file belongs | `config/repository-layout.yaml` |
