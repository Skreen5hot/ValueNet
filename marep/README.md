# MAREP Runtime

A deterministic implementation of the Runtime half of [MAREP v2.2](../MAREP_v2.2.md) §4.1.1.

MAREP splits its control plane in two. The **Adjudicator** is a language model and handles judgement: semantic contradiction, thematic merge, compression, tie-break. The **Runtime** is this package, and handles everything mechanically decidable. It contains no model call, and per §4.1.1 it must not: an LLM doing JSON Schema validation is both more expensive and less reliable than a validator.

Build the Runtime first. It is plain code, it is where every reliability property of the protocol lives, and it is testable without a single model invocation.

## What it enforces

| Concern | Spec | Module |
| --- | --- | --- |
| Schema validation, reject without partial application | §19.1 | `validate.py` + `schemas/` |
| Compare-and-swap versioning, append-only audit | §10 | `state.py` |
| Optimistic append; locks only for global read-modify-write | §11 | `runtime.py` |
| Evidence resolution against the frozen substrate | §7, §8.3 | `substrate.py` |
| Confirmation grounding gate | §8.3.1, §18.5 | `transitions.py` |
| Status transition graph and reopening guards | §16.3, §16.4 | `transitions.py` |
| Phase authorization and scope | §11.4, §18.4 | `authz.py` |
| Anti-patterns: persona, openers, budgets, non-substantive | §18 | `checks.py` |
| Phase entry/exit criteria and advancement | §13 | `phases.py` |
| Token ledger, scoped reads, compression reserve | §14.1 | `tokens.py` |
| Building the substrate from real repository data | §7 | `ingest.py` |

## Use

```python
from marep import Runtime, Substrate

substrate = Substrate.load("SPRINT_INPUT.yaml")     # frozen and checksummed
rt = Runtime.initialize("sprint-42", substrate, roster=["QA", "Developer"])

result = rt.submit({
    "update_id": "UPD-001",
    "base_version": rt.version,
    "issues": [{
        "id": "DEPLOY-002",
        "title": "Rollback path is not exercised",
        "severity": "high",
        "status": "proposed",
        "evidence": [{
            "id": "EV-001",
            "claim": "Rollback of release 42.3 required manual intervention",
            "source": {"type": "ci_run", "ref": "CI-1204"},
            "submitted_by": "Developer",
        }],
    }],
}, agent="Developer")

if not result:
    print(result.cause.value, result.detail)
```

Agents need not be Python; the CLI takes YAML and returns a structured verdict.

```
python -m marep ingest --sprint sprint-42 --since 2026-08-01 --until 2026-08-14
python -m marep init   --sprint sprint-42 --roster QA,Developer,Architect,Skeptic
python -m marep submit --agent QA --update update.yaml --json
python -m marep status
python -m marep advance --archive-unevaluated
python -m marep report
```

Exit codes: `0` accepted, `1` rejected, `2` usage or integrity error.

## The submission pipeline

Thirteen ordered steps. Any failure returns before step 13, so a rejected update leaves nothing behind — "reject without partial application" is structural, because the merge happens onto a copy and the live document is never touched.

```
 1 integrity      substrate checksum still matches            §19.6
 2 lock           no exclusive operation in flight            §11.2
 3 budget         spendable tokens remain                     §14.1
 4 idempotence    update_id not already applied               §12
 5 CAS            base_version is the current version         §10
 6 merge          apply onto a copy                           §12.1
 7 authorization  phase + role scope, reserved fields         §11.4
 8 resolution     Runtime sets `verified`                     §8.3
 9 schema         candidate validates                         §19.1
10 identifiers    no duplicates                               §4.1.1
11 transitions    legal, grounded, reopen-guarded             §16
12 anti-patterns  persona, openers, budgets, substance        §18
13 commit         version += 1, audit append, atomic write    §10
```

## Three things worth knowing

**Only the Runtime sets `verified`.** An agent that supplies the flag is rejected `out_of_scope`. Verification is resolution of `source.ref` against the frozen substrate, and a reference to a record of the wrong type does not verify — otherwise the type field decays into decoration.

**An unresolvable reference is recorded, not rejected.** It lands with `verified: false`. An unverifiable observation is still worth having; it just cannot ground a confirmation.

**Checks judge what an update introduces, not the whole document.** Re-scanning everything means one string that trips a rule permanently blocks every later update. This was a real bug caught by the walkthrough: the Runtime's own generated rationale opened with "No", which is on the conversational-opener list, and deadlocked the retrospective from Phase 4 onward.

## Building a substrate

`ingest` produces `SPRINT_INPUT.yaml` from sources that exist independently of the retrospective: `git log` for commits, and the `gh` CLI for pull requests, issues, CI runs, and releases. Until it existed the substrate had to be hand-authored, which made the grounding gate circular — evidence was "verified" against a file somebody typed.

Two properties matter more than how many sources it covers:

**Determinism.** The same repository and date range produce byte-identical output. Records are sorted *before* identifiers are minted, so a re-run does not renumber everything and invalidate evidence a previous retrospective already cited.

**Honest gaps.** Every one of the ten record types gets a coverage entry. A source that is missing, unauthenticated, or erroring is reported unavailable with the real reason (§7.3) rather than silently omitted — so a retrospective that draws conclusions about deployment while `deploy` was never collected says so on the face of its own input. This is load-bearing: the first run against this repository reported `deploy` unavailable because `gh release list` rejected a field, which is exactly how the bug was found.

## Tests

```
python -m pytest tests/ -q          # 56 conformance tests
python examples/walkthrough.py      # a full six-phase retrospective, no model
python examples/real_sprint.py      # grounded in this repository's real git history
```

The walkthrough is the useful demo: every agent is a hard-coded dict, which isolates what the Runtime does from what an agent would do. It exercises a stale-version rebase, a lock refusal, an ungrounded confirmation, an unevaluated-issue archive that would otherwise deadlock Phase 3, a sub-threshold vote landing on `unresolved`, and a Phase 5 exit blocked until a confirmed issue gets an action or a waiver.

## Deliberately not here

**Anything requiring judgement.** Semantic contradiction, thematic merge, compression, and tie-break belong to the Adjudicator (§4.1.2), which holds no privileged write path: its updates come through `submit()` and are validated exactly like any agent's.

**Human review.** MAREP is specified as a fully autonomous protocol (§1.1). That is an experimental constraint, not an omission, and implementations that add a human gate are not conforming deployments.

**A reasoner.** MAREP grounds findings by provenance (§7) and socially (§16), but has no *logical* grounding layer: two issues can both be confirmed, both fully evidenced, and be mutually contradictory. Detecting that is currently the Adjudicator's job by reading. A reasoner in the Runtime would mechanise part of it and is the natural v2.3 extension — but only the formalised fragment of a finding is checkable, so it complements the other two layers rather than replacing them.

## Dependencies

`pyyaml`, `jsonschema`. Nothing else, on purpose: a component whose whole value is being trustworthy should be cheap to audit.
