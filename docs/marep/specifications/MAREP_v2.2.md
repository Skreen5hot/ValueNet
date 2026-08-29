# Multi-Agent Retrospective Execution Protocol (MAREP)

**Version:** 2.2 (Draft)
**Status:** Specification — Normative
**Supersedes:** 2.1
**Audience:** Runtime implementers, agent implementers, retrospective system integrators
**Purpose:** Execute structured, low-drift, multi-agent retrospectives through shared-state coordination rather than conversational interaction.

---

## 0. Conformance Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119 and RFC 8174 when, and only when, they appear in all capitals.

A conforming implementation MUST satisfy every MUST and MUST NOT requirement in this specification. SHOULD requirements MAY be deviated from when documented justification is provided in the implementation's conformance statement.

---

## 1. Core Principle

The retrospective system is a **deterministic state machine** operated by structurally constrained agents over a shared canonical state. It is not a simulated meeting.

The state machine is deterministic. The agents that drive it are not; they are language models whose outputs vary. The design therefore places every mechanically decidable rule — schema, versioning, transition legality, scope, evidence resolution — in a deterministic component, and confines model judgement to the questions that genuinely require it.

Four invariants govern the system:

1. **Canonicality** — A single, versioned state object is the sole authoritative artifact; all reasoning derives from and reduces to modifications of this state.
2. **Non-conversationality** — Agents MUST NOT communicate with one another directly. All inter-agent influence is mediated through state.
3. **Serialized effect** — Every accepted mutation applies to a known prior version, and the accepted order is total. Agents MAY submit concurrently; conflicting submissions are rejected for rebase, never silently merged.
4. **Grounding** — Every confirmed finding MUST trace to at least one verified reference into the sprint input substrate. Process rigor applied to ungrounded claims produces confident error, not insight.

The objective is not to create the illusion of teamwork. The objective is structured collaborative cognition through controlled state transitions, yielding reliable synthesis and reduced drift.

### 1.1 Deliberate Absence of Human Participation

This protocol specifies a fully autonomous retrospective. There is no human review gate, no human approval step, and no human write path into canonical state. This is a deliberate experimental constraint, not an oversight: the system exists to test whether structured collaborative cognition among agents produces reliable operational insight without human mediation.

Implementations MUST NOT treat the absence of a human gate as a defect to be patched. Implementations that add human review are valid engineering but are **not conforming MAREP deployments**, and MUST say so in their conformance statement.

The consequence is that `Action.owner` (§8.4) names an agent. Whether an autonomously assigned action is executed, and by what, is outside this specification's scope.

---

## 2. Architectural Goals

The system is designed to:

* ground every confirmed finding in verifiable input,
* minimize hallucinated collaboration,
* reduce token waste,
* prevent recursive agreement loops,
* preserve machine-readable state,
* maintain deterministic retrospective evolution,
* support asynchronous or parallel execution,
* and enable downstream automation and analytics.

These goals are listed in priority order; in any tradeoff, earlier goals dominate.

---

## 3. Glossary

* **Canonical state** — The single authoritative state object (`RETRO_STATE.yaml`) representing the retrospective at a point in time. Versioned, schema-validated, monotonically advanced.
* **Sprint input substrate** — The frozen, read-only corpus (`SPRINT_INPUT.yaml`) describing the sprint under analysis. The only admissible ground for evidence.
* **Agent** — A bounded analytical persona with defined role, scope, and update authority.
* **Control plane** — The Runtime and the Adjudicator, taken together.
* **Runtime** — The deterministic, non-model component responsible for every mechanically decidable rule: schema validation, versioning, transition legality, scope enforcement, evidence resolution, phase advancement.
* **Adjudicator** — The single model-driven control agent, responsible for the judgement calls the Runtime cannot make: semantic contradiction, thematic merge, compression, tie-break.
* **Update** — A localized, schema-conformant mutation of canonical state.
* **Append** — An update that adds an element to a collection without reading or altering existing elements. Executed under compare-and-swap without a lock.
* **Exclusive operation** — A global read-modify-write operation requiring a lock (§11.2).
* **Turn** — A bounded interval during which one actor holds the write lock for an exclusive operation.
* **Phase** — A named stage of the retrospective workflow with defined entry and exit criteria.
* **Scratchpad** — Private, non-canonical, agent-local working memory.
* **Issue** — A retrospective finding tracked through defined status transitions.
* **Evidence** — A typed, source-referenced claim supporting an issue (§8.3).
* **Verified evidence** — An evidence item whose `source.ref` resolves to a record in the sprint input substrate, as determined by the Runtime.
* **Action** — A proposed remediation or follow-up with ownership and outcome criteria.
* **Lock** — A time-bounded, exclusive write authorization issued by the Runtime for an exclusive operation.

---

## 4. Agent Model

Each agent represents a distinct analytical perspective. Agents MUST be selected for epistemic diversity, non-overlapping reasoning styles, and unique evaluative function. Redundant personas (two agents covering the same focus area under different names) MUST NOT be instantiated within a single retrospective.

### 4.1 Control Plane

Control responsibilities are split across two components with different implementation requirements. Prior versions of this protocol assigned both sets to a single `@Orchestrator`; that conflated deterministic bookkeeping with semantic judgement, made an LLM responsible for schema validation, and left the only actor capable of steering outcomes unaudited.

#### 4.1.1 Runtime (deterministic, non-agent)

The Runtime MUST be implemented as deterministic code. It MUST NOT be implemented by, or delegated to, a language model.

The Runtime is solely responsible for:

* schema validation and rejection of non-conforming updates,
* compare-and-swap version comparison and increment,
* append-only `audit` maintenance,
* enforcement of the status transition graph (§16.3), including reopening guards,
* duplicate identifier detection,
* lock issue, expiry, and reclamation for exclusive operations,
* resolution of evidence `source.ref` against the sprint input substrate, and the setting of the `verified` flag,
* enforcement of the confirmation grounding gate (§8.3.1),
* authorization and scope checks (§11.4),
* the non-substantive update check (§18.2),
* evaluation of phase entry and exit criteria, and phase advancement.

The Runtime MUST NOT interpret content, resolve semantic conflicts, summarize, or judge the merit of a finding. Where a decision requires reading meaning rather than structure, the Runtime MUST refer it to the Adjudicator.

The `verified` flag is set exclusively by the Runtime. An agent-supplied `verified` value MUST be discarded.

#### 4.1.2 @Adjudicator (model-driven)

The Adjudicator is the single model-driven control agent. It is responsible for:

* semantic contradiction detection across issues and actions,
* thematic merge and semantic deduplication proposals (deduplication by identifier is the Runtime's),
* context compression and summarization (§14),
* tie-break under the configured decision rules (§16.1),
* targeted re-analysis requests to named agents.

**The Adjudicator holds no privileged write path.** Its updates are submitted through the same pipeline, validated by the Runtime under the same rules, subject to the same scope and CAS semantics, and recorded in `audit` under its own identity. It MUST NOT advance phases, edit `audit`, set `verified`, or bypass the transition graph.

Where the Adjudicator proposes a merge, archive, or compression, the proposal is an ordinary update; the Runtime applies it only if it validates.

### 4.2 Possible Analytical Agents

| Agent | Focus |
|---|---|
| `@Architect` | System design, scalability, technical debt, integration concerns |
| `@Developer` | Implementation friction, velocity, maintainability, tooling |
| `@QA` | Defects, verification gaps, regression risks, process quality |
| `@DeliveryManager` | Sprint predictability, throughput, blockers, coordination overhead |
| `@RiskAnalyst` | Hidden failure modes, systemic fragility, operational exposure |
| `@UserAdvocate` | User impact, usability, stakeholder outcomes |
| `@Skeptic` | Challenging assumptions, identifying weak reasoning, preventing false consensus |

A retrospective MAY define additional roles consistent with §4 invariants. The complete agent roster MUST be declared in `AGENTS.md` before Phase 1 entry.

---

## 5. Required and Optional Files

### 5.1 Canonical Files (Required)

```text
/AGENTS.md          — Constitutional protocol; agent definitions, rules, schemas
/SPRINT_INPUT.yaml  — Frozen, read-only substrate under analysis (§7)
/RETRO_STATE.yaml   — Authoritative state; versioned and schema-validated
/RETRO_BOARD.md     — Human-readable projection of canonical state
```

### 5.2 Working Files (Optional)

```text
/private/<agent>_notes.md   — Agent-local scratchpad; non-canonical
```

Scratchpads are temporary working memory serving a single agent's continuity across its own turns. They MUST NOT be referenced by other agents and MUST NOT be treated as authoritative input to consensus.

---

## 6. AGENTS.md Specification

`AGENTS.md` defines the agent roster, behavioral rules, execution constraints, schema requirements, retrospective phases, and orchestration policy for a given retrospective instance. It functions as the constitutional protocol for that retrospective.

`AGENTS.md` MUST be finalized before Phase 1 entry. Mid-retrospective amendments MUST be recorded as numbered amendments and validated by the Runtime before taking effect.

---

## 7. Sprint Input Substrate

`SPRINT_INPUT.yaml` describes the sprint under analysis. It is the **only admissible ground for evidence**: an evidence item is verified if and only if its `source.ref` resolves to a record in this file (§8.3).

Without a specified substrate, a retrospective protocol governs the form of findings while saying nothing about their truth. This section exists so that consensus is reached over checkable claims.

### 7.1 Freezing

The substrate MUST be populated and frozen before Phase 1 entry. The Runtime MUST compute a checksum over the frozen file and record it in `retro.sprint_input_checksum`. If the checksum ever fails to match, the Runtime MUST emit a corruption event and halt mutation (§19.6).

The substrate is read-only for the duration of the retrospective. No agent, including the Adjudicator, MAY mutate it.

### 7.2 Schema

```yaml
sprint:
  id: <string>                  # Sprint identifier; MUST match retro.sprint
  started: <ISO8601 date>
  ended: <ISO8601 date>

records:
  - id: <string>                # Unique within substrate; convention <TYPE>-<NNN>, e.g. CI-1204
    type: <enum>                # commit | pull_request | ticket | ci_run | deploy |
                                # incident | metric | review | document | note
    ref: <string>               # Stable external identifier (SHA, issue key, run id)
    uri: <string>               # Optional dereferenceable location
    timestamp: <ISO8601>
    summary: <string>           # Short human-readable description
    payload: <map>              # Type-specific fields; schema per type

coverage:
  - type: <enum>                # A record type from the enum above
    available: <bool>
    reason: <string>            # Required when available is false
```

### 7.3 Coverage Declaration

Every record type the implementation does not populate MUST appear in `coverage` with `available: false` and a stated reason.

This makes blind spots visible rather than silent. A retrospective that reaches confident conclusions about deployment stability while `coverage` shows `deploy: available: false` is reporting on an absence, and the deliverables MUST surface that. The Runtime MUST copy `coverage` into the final summary (§20).

### 7.4 Note Records

`type: note` exists for material with no machine-retrievable source — an observation with no ticket behind it. Note records are legitimate substrate entries and evidence referencing them verifies normally. They are, however, exactly as trustworthy as whoever wrote them, and implementations SHOULD report the proportion of confirmed issues grounded solely in notes.

---

## 8. Canonical State Model

`RETRO_STATE.yaml` is the sole authoritative state. All retrospective reasoning, history, and decisions reduce to its contents.

Agents MAY modify structured sections, append evidence, update issue status, and propose actions. Agents MUST NOT chat, roleplay, greet other agents, or simulate meetings. Any natural-language content placed into canonical state MUST be confined to designated free-text fields (e.g., `description`, `summary`, `rationale`) and MUST NOT contain conversational artifacts.

### 8.1 Required Top-Level Schema

```yaml
retro:
  sprint: <string>                  # Sprint identifier; MUST match sprint.id in substrate
  sprint_input_checksum: <string>   # Checksum of the frozen substrate (§7.1)
  phase: <enum>                     # gathering | merge | analysis | consensus |
                                    # actions | compression | complete
  version: <int>                    # Monotonically increasing; incremented on every accepted mutation
  schema_version: <string>          # Semver

issues:          # List of <Issue>       (§8.2)
actions:         # List of <Action>      (§8.4)
decisions:       # List of <Decision>     (§8.5)
votes:           # List of <Vote>        (§16.2)
conflict_record: # List of <Conflict>    (§15)
archive:         # Relocated records preserved verbatim (§14)
turn:            # Current exclusive-operation lock, or null (§11.3)
token_ledger:    # Running token accounting          (§14.1)
audit:           # Append-only log of state transitions (§10)
```

`complete` is a terminal marker rather than a phase; no phase activity occurs in it.

Conforming implementations MUST publish a JSON Schema (or equivalent) for the full state document.

### 8.2 Issue Schema

```yaml
- id: <string>            # Unique within the retrospective; convention <DOMAIN>-<NNN>
  title: <string>
  severity: <enum>        # low | medium | high | critical
  status: <enum>          # proposed | contested | confirmed | rejected | unresolved | archived
  evidence: [<Evidence>]  # See §8.3
  confirmed_by: [<agent>]
  contested_by: [<agent>]
  related_actions: [<action_id>]
  reopen_count: <int>     # Maintained by Runtime; see §16.4
```

### 8.3 Evidence Schema

Evidence is typed and source-referenced. Free-string evidence is not conformant.

```yaml
- id: <string>            # Unique within the issue; convention EV-<NNN>
  claim: <string>         # What the evidence asserts
  source:
    type: <enum>          # Record type from §7.2
    ref: <string>         # MUST correspond to a records[].id or records[].ref
  verified: <bool>        # Set exclusively by Runtime; agent-supplied values discarded
  submitted_by: <agent>
```

The Runtime MUST resolve `source.ref` against `SPRINT_INPUT.yaml` on submission and set `verified` accordingly. Resolution accepts a record identifier or a record reference. Identifiers are minted positionally and are stable only while the substrate's record set is unchanged; references are content-derived and survive additions, so evidence intended to outlive one retrospective SHOULD cite a reference. Unresolvable references MUST set `verified: false`; they MUST NOT cause the update to be rejected, because an unverifiable observation is still worth recording as unverifiable.

#### 8.3.1 Confirmation Grounding Gate

An issue MUST NOT enter `status: confirmed` unless it carries at least one evidence item with `verified: true`.

The Runtime MUST reject any transition to `confirmed` that violates this, with cause `ungrounded_confirmation`, regardless of vote outcome. A vote that passes threshold on an ungrounded issue resolves to `unresolved`, not `confirmed`.

This gate is the operative expression of invariant 4 (§1). Agreement is not evidence.

### 8.4 Action Schema

```yaml
- id: <string>            # Unique; convention ACT-<NNN>
  description: <string>
  owner: <agent>          # See §1.1 on autonomous ownership
  status: <enum>          # proposed | accepted | rejected | deferred
  outcome_criteria: <string>
  due_by: <ISO8601 date>
  addresses: [<issue_id>] # Issues this action responds to
```

`addresses` mirrors `Issue.related_actions`. The Runtime MUST maintain the two in agreement, so that an agent proposing an action need not write into the `issues` collection to satisfy the Phase 5 exit criterion.

### 8.5 Decision Schema

A Decision records a settled judgement and the basis for it. Every terminal status change and every `no_action_required` outcome MUST have a corresponding Decision, so that the final state explains itself without recourse to the audit log.

```yaml
- id: <string>            # Unique; convention DEC-<NNN>
  type: <enum>            # consensus_outcome | no_action_required | reopen_blocked |
                          # unevaluated_archive | compression | declination | merged
  subject: <string>       # Reference, e.g. ISSUE:PERF-001 or ACTION:ACT-004
  outcome: <string>       # The settled result
  rationale: <string>     # Why; free text, subject to §18.3 budgets
  basis: <string>         # vote_id | adjudicator | runtime
  decided_at: <ISO8601>
```

`basis: runtime` is reserved for mechanically determined decisions (unevaluated archive, blocked reopening). `basis: adjudicator` MUST cite the judgement made. `basis: <vote_id>` MUST reference an entry in `votes`.

`merged` records a duplicate retired into a survivor during Phase 2. Retiring it moves the duplicate `proposed → archived`, which §16.3 marks control-plane only: the Adjudicator may perform it during the merge phase, and the Runtime at analysis close. Without that, §13.2 specifies a deduplication the transition graph forbids. The duplicate's evidence MUST be carried onto the survivor before the merge, so deduplication never weakens grounding.

`declination` is how an agent satisfies the Phase 1 exit criterion (§13.1) with nothing to report; its `subject` MUST be `AGENT:<name>`. Agents are therefore authorized to write `decisions` during gathering. Without both of those, "submitted findings or explicitly declined" is unsatisfiable for a silent agent, and one such agent deadlocks the phase — the same defect as a status with no outgoing edge.

---

## 9. Markdown Rendering Layer

`RETRO_BOARD.md` is a human-readable projection of canonical state. It exists for readability and inspection; it is not a write path (§1.1). The YAML state remains authoritative; in any divergence, YAML wins. Implementations SHOULD regenerate `RETRO_BOARD.md` from `RETRO_STATE.yaml` rather than edit it directly.

---

## 10. State Versioning

Canonical state version (`retro.version`) is a monotonically increasing integer. Every accepted mutation MUST increment the version by exactly 1. Agents MUST submit updates that reference the version they read; the Runtime MUST reject updates whose referenced version is not the current version (compare-and-swap semantics).

An update MAY contain multiple changes and is applied atomically as a single version increment. Partial application MUST NOT occur.

The Runtime MUST maintain an append-only `audit` log entry for every accepted mutation:

```yaml
audit:
  - version: <int>
    agent: <agent>
    timestamp: <ISO8601>
    update_id: <string>
    diff_summary: <string>
    affected_sections: [<path>]
```

---

## 11. Concurrency Control

### 11.1 Optimistic Append (default)

Compare-and-swap (§10) is the concurrency control for agent updates. Agents MUST NOT be required to hold a lock in order to append.

Prior versions required an exclusive lock for every mutation. Combined with CAS, that was redundant safety at the cost of all parallelism — most damagingly in Phase 1, where agents work independently by design and the workload is inherently parallel.

The following are appends and MUST be permitted concurrently:

* adding an entry to `issues`, `actions`, or `votes`,
* adding an evidence item to an existing issue,
* adding the submitting agent to an issue's `confirmed_by` or `contested_by`.

Appends to distinct collections commute. Appends to the same collection are serialized by CAS: the first submission at version *N* is accepted and advances to *N+1*; the second is rejected with cause `version_conflict`.

Implementations MAY maintain per-section version counters to reduce false conflicts, provided `retro.version` remains globally monotonic and every accepted mutation increments it by exactly 1.

### 11.2 Exclusive Operations

The following are global read-modify-write operations and MUST be performed under an exclusive lock held by the Runtime:

* phase transition,
* context compression and archival (§14),
* thematic merge and semantic deduplication (Phase 2),
* vote closure and status finalization (§16),
* rollback after corruption (§19.6).

At most one exclusive operation MAY be in flight at a time. While an exclusive lock is held, the Runtime MUST reject appends with cause `exclusive_operation_in_progress` and the submitting agent SHOULD retry after release.

### 11.3 Lock Structure and Lifecycle

```yaml
turn:
  operation: <enum>               # phase_transition | compression | merge |
                                  # vote_closure | rollback
  holder: <Runtime | Adjudicator>
  state_version: <int>            # Version at lock acquisition
  lock_acquired: <ISO8601>
  lock_expiration: <ISO8601>
  permitted_sections: [<path>]    # Restricts the scope of permitted mutations
```

The grant MUST specify `permitted_sections`. On expiration without release, the Runtime MUST reclaim the lock and discard any partial in-flight updates (§19.2). A holder MUST NOT self-extend a lock.

### 11.4 Authorization and Scope

Outside an exclusive operation, an agent's write authority is determined by the current phase and its declared role in `AGENTS.md`, not by a lock. The Runtime MUST reject any update touching a path the submitting agent is not authorized for in the current phase, with cause `out_of_scope`.

An agent MUST NOT:

* modify sections outside its phase authorization,
* revise records under `archive`,
* modify another agent's scratchpad,
* set `verified`, edit `audit`, or advance `retro.phase`.

### 11.5 Conflict Handling

On `version_conflict`, the Runtime MUST return the current version so the submitting agent can rebase and resubmit. Agents SHOULD retry a bounded number of times (implementations SHOULD default to 3) and MUST NOT retry indefinitely. An update that has been rebased retains its `update_id` (§12).

---

## 12. Update Semantics

Every update MUST be localized, idempotent, and schema-compliant, and SHOULD be reproducible.

* **Reproducible** — Given the same input state and the same agent prompt, the update SHOULD produce structurally equivalent diffs across runs. Semantic equivalence under field-level normalization is sufficient; LLM nondeterminism is bounded but not eliminated. This is a SHOULD, not a MUST, because no conforming implementation can guarantee it.
* **Localized** — Updates MUST modify only paths the submitting agent is authorized for in the current phase (§11.4), or within `permitted_sections` during an exclusive operation.
* **Idempotent** — Re-applying an accepted update MUST be a no-op. Every update MUST carry a stable `update_id`; the Runtime MUST reject a replayed `update_id` with cause `duplicate_update`.
* **Schema-compliant** — Updates MUST validate against the published schema. The Runtime MUST reject any non-conforming update without partial application.

### 12.1 Update Form

Agents express updates as YAML-merge-style diffs against the current state, not as prose.

Non-conforming — prose:

```text
I think we had some deployment issues.
```

Non-conforming — untyped evidence:

```yaml
issues:
  - id: DEPLOY-002
    evidence:
      - failed rollback in sprint-42
```

Conforming:

```yaml
update_id: UPD-0117
base_version: 42
issues:
  - id: DEPLOY-002
    title: Deployment instability
    severity: medium
    status: proposed
    evidence:
      - id: EV-001
        claim: "Rollback of release 42.3 failed and required manual intervention"
        source: { type: ci_run, ref: CI-1204 }
        submitted_by: Developer
      - id: EV-002
        claim: "Staging and production diverge on runtime version"
        source: { type: deploy, ref: DEP-0311 }
        submitted_by: Developer
```

---

## 13. Phase Workflow

The retrospective progresses through six phases in strict order. Phase transitions are performed exclusively by the Runtime, which MUST evaluate exit criteria mechanically and MUST record each transition in `audit`.

### 13.1 Phase 1 — Independent Gathering

* **Entry:** `AGENTS.md` finalized; `SPRINT_INPUT.yaml` frozen and checksummed into `retro.sprint_input_checksum`; `RETRO_STATE.yaml` initialized.
* **Activity:** Each agent independently analyzes the substrate, records findings in private scratchpad, and submits compressed findings as `proposed` issues with typed evidence.
* **Concurrency:** Agents submit in parallel under CAS (§11.1). No lock is required or granted.
* **Purpose:** Maximize diversity of reasoning; prevent premature convergence.
* **Exit:** Every agent has either submitted findings or explicitly declined.

### 13.2 Phase 2 — Canonical Merge

* **Entry:** Phase 1 exit conditions satisfied.
* **Activity:** The Runtime detects duplicate identifiers and schema violations. The Adjudicator proposes thematic merges and semantic deduplication, submitted as ordinary updates under an exclusive lock.
* **Exit:** No duplicate IDs; every proposed issue conforms to schema; every evidence item has been resolved and flagged by the Runtime.

### 13.3 Phase 3 — Structured Analysis

* **Entry:** Phase 2 exit conditions satisfied.
* **Activity:** Agents evaluate themes, challenge assumptions, validate evidence, refine root causes. Agents MAY add verified evidence to any issue.
* **Exit:** Every issue has reached `confirmed`, `rejected`, `contested`, or `archived`. An issue that no agent has evaluated MAY be moved `proposed → archived` by the Runtime at phase close, recording cause `unevaluated`; this prevents a single ignored issue from blocking the phase indefinitely.

### 13.4 Phase 4 — Consensus Resolution

* **Entry:** Phase 3 exit conditions satisfied.
* **Activity:** The Adjudicator identifies unresolved conflicts and triggers voting where required (§16). The Runtime finalizes issue states, applying the grounding gate (§8.3.1).
* **Exit:** No issue remains `contested`. Issues whose vote fails to reach threshold in either direction are recorded `unresolved`; issues that pass threshold without verified evidence are also recorded `unresolved`. `unresolved` is a legitimate terminal outcome and MUST NOT be forced to `confirmed` or `rejected` to satisfy this criterion.

### 13.5 Phase 5 — Action Assignment

* **Entry:** Phase 4 exit conditions satisfied.
* **Activity:** Agents propose actions with ownership, outcome criteria, due dates, and `addresses` references.
* **Exit:** Every `confirmed` issue has at least one accepted action OR an explicit `no_action_required` decision. `unresolved` issues MUST NOT require an action, but MUST be carried into the final summary.

### 13.6 Phase 6 — Final Compression

* **Entry:** Phase 5 exit conditions satisfied.
* **Activity:** The Adjudicator archives discussion history and generates the final summary and action manifest; the Runtime validates and applies.
* **Exit:** All deliverables (§20) produced and validated.

---

## 14. Context Compression

Large retrospectives accumulate entropy. Compression MUST be triggered when any of the following fires:

* token usage exceeds the configured budget,
* duplicate issues are detected,
* canonical state contains semantically redundant entries,
* historical context begins biasing new analysis (detected by repeated re-derivation of archived conclusions).

Trigger detection is the Runtime's; compression itself is an exclusive operation performed by the Adjudicator (§11.2).

### 14.1 Token Accounting

Reducing token waste is goal three (§2), which requires that tokens be counted. The Runtime MUST maintain a running ledger in canonical state:

```yaml
token_ledger:
  consumed_total: <int>         # Cumulative across all agent and Adjudicator calls
  consumed_by_phase:
    <phase>: <int>
  consumed_by_agent:
    <agent>: <int>
  last_updated_version: <int>
```

Budgets are declared in `AGENTS.md`:

```yaml
token_budget:
  per_turn_context: <int>          # Ceiling on tokens supplied to one agent in one turn
  per_retrospective_total: <int>   # Hard ceiling for the whole retrospective
  compression_trigger: 0.75        # Fraction of total at which compression fires
  compression_reserve: <int>       # Tokens withheld so compression can always run
```

Three rules follow:

* **Scoped reads.** An agent MUST be supplied only the sections relevant to its current task, determined by the same phase authorization that governs its writes (§11.4). Supplying full canonical state to every agent on every turn makes cost grow as agents × phases × state size, which is the dominant cost term in any non-trivial retrospective.
* **Reserve.** The Runtime MUST NOT allocate `compression_reserve` to ordinary turns. Compression is itself a model call, and a system that exhausts its budget before it can compress cannot recover.
* **Exhaustion.** On reaching `per_retrospective_total`, the Runtime MUST halt agent turns, run a final compression from reserve, and advance to Phase 6. A truncated retrospective that completes is more useful than a complete one that stalls; the summary MUST record that it terminated on budget.

Compression preserves canonical conclusions, relocates obsolete sections under `archive`, and generates compressed summaries. Compression MUST NOT alter `confirmed`, `rejected`, `unresolved`, or `accepted` records other than relocating them under `archive`. Evidence items MUST be preserved verbatim under `archive`; compression MUST NOT summarize away a `source.ref`, because doing so would destroy the grounding chain a reopened issue depends on (§16.4).

---

## 15. Contradiction Management

Structural contradictions — duplicate IDs, illegal transitions, scope violations — are detected by the Runtime. Semantic contradictions are detected by the Adjudicator:

* conflicting root causes,
* incompatible action items,
* unresolved disagreements between agents.

When a contradiction is detected, the affected items MUST be marked `status: contested`, the conflicting positions recorded in `conflict_record`, and either targeted re-analysis requested from a specific agent or a consensus vote triggered (§16).

```yaml
conflict_record:
  - issue_id: PERF-001
    positions:
      - agent: Architect
        claim: API latency caused by N+1 query pattern
        evidence: [EV-004]
      - agent: QA
        claim: API latency caused by network egress saturation
        evidence: [EV-009]
    resolution_required_by: <phase | timestamp>
```

---

## 16. Consensus Protocol

Consensus is explicit. Implicit agreement is not consensus. Consensus is also not evidence: a vote determines whether a grounded finding is accepted, and cannot substitute for grounding (§8.3.1).

### 16.1 Decision Rules

```yaml
decision_rules:
  standard_threshold: 0.7              # Fraction of the vote denominator required for confirmation
  vote_denominator: voting_agents      # or: all_agents
  architecture_changes:
    unanimous_required: true
  abstention_policy: counts_against_quorum   # or: ignored
  quorum: 0.6                          # Fraction of roster that MUST cast or abstain for a valid vote
  tie_break: adjudicator               # or: skeptic | re_vote
  max_reopens: 2                       # Per issue; see §16.4
```

`vote_denominator` MUST be stated explicitly. Under `voting_agents`, abstentions are excluded from the denominator; under `all_agents` they are included and therefore count against the threshold. `abstention_policy` governs quorum only. A vote that fails quorum resolves to `unresolved`.

### 16.2 Vote Record

```yaml
votes:
  - subject: ISSUE:PERF-001:status:confirmed
    threshold: 0.7
    denominator: voting_agents
    cast:
      - agent: Architect
        position: confirm
      - agent: QA
        position: confirm
      - agent: Skeptic
        position: reject
    outcome: confirmed        # confirmed | rejected | unresolved
    closed_at: <ISO8601>
```

A vote that reaches neither the confirmation threshold nor its inverse MUST record `outcome: unresolved`. Sub-threshold splits are not ties and MUST NOT be routed to `tie_break`.

### 16.3 Status Transitions

Issue status transitions MUST follow this graph:

```text
proposed   → contested
proposed   → confirmed          [requires verified evidence, §8.3.1]
proposed   → rejected
proposed   → archived           [control plane only: Runtime at Phase 3 close
                                 (cause unevaluated), or Adjudicator during
                                 Phase 2 retiring a merged duplicate]

contested  → confirmed          [requires verified evidence, §8.3.1]
contested  → rejected
contested  → unresolved
proposed   → unresolved         [evaluated, uncontested, and unconfirmable
                                 for want of verified evidence]

confirmed  → contested          [reopening; see §16.4]
rejected   → contested          [reopening; see §16.4]
unresolved → contested          [reopening; see §16.4]

confirmed  → archived
rejected   → archived
unresolved → archived
```

All other transitions MUST be rejected by the Runtime with cause `illegal_transition`.

An issue reaches `unresolved` from `proposed` when it has been evaluated, nobody contested it, and it still cannot be confirmed because no evidence on it verifies. Such a finding may be perfectly true. Without this edge it has nowhere honest to go: `confirmed` is barred by §8.3.1, `rejected` asserts it is false, `archived` is reserved for issues nobody evaluated, and `contested` invents a disagreement that never happened.

`unresolved` is terminal for the purpose of phase exit: it satisfies Phase 4 exit and requires no action in Phase 5. It remains reopenable on new grounds, like any settled status.

### 16.4 Reopening

A retrospective that cannot revise its own conclusions cannot learn from evidence it discovers late. Reopening is therefore permitted from every settled status, under two guards that prevent it from becoming churn.

A transition into `contested` from `confirmed`, `rejected`, or `unresolved` MUST be rejected unless **both** hold:

1. The update introduces at least one evidence item with `verified: true` whose `id` was not present on the issue at the version of the transition being reversed, as determined by the Runtime from `audit`.
2. The issue's `reopen_count` is less than `decision_rules.max_reopens`.

On an accepted reopening the Runtime MUST increment `reopen_count`. An issue at the reopen ceiling MUST be recorded `unresolved` rather than reopened again, and the blocked reopening attempt MUST be logged.

Reopening is permitted in any phase up to Phase 6 entry. Reopening a `confirmed` issue that already has accepted actions does not retract those actions; it marks the issue contested and MUST surface the dependency in `conflict_record`.

---

## 17. Memory Boundaries

Agents MUST NOT recursively inherit unlimited prior retrospectives. Memory is partitioned into three layers with explicit promotion rules.

### 17.1 Working Memory

The current sprint's canonical state and sprint input substrate. Fully accessible to all agents within scope.

### 17.2 Episodic Memory

Compressed summaries of recent retrospectives. Accessible to the Adjudicator; surfaced to agents only on explicit request and only as compressed summaries.

### 17.3 Semantic Memory

Stable operational principles, standards, and team conventions. Accessible to all agents but read-only within the retrospective.

Implementations MUST define explicit boundaries and explicit promotion rules (e.g., when working memory compresses to episodic memory at retrospective close).

---

## 18. Anti-Pattern Enforcement

The Runtime MUST suppress the following anti-patterns. Each is paired with a deterministic detection mechanism so enforcement is mechanical rather than discretionary.

### 18.1 Persona Theater

* **Forbidden:** conversational addresses, affirmations to other agents (e.g., `"Great point @QA!"`).
* **Detection:** schema validation rejects free text containing `@<agent>` outside designated reference fields.

### 18.2 Non-Substantive Update

* **Forbidden:** updates that carry no new information — affirmations, restatements, redundant summaries, synthetic collaboration language.
* **Detection (structural):** the Runtime MUST reject an update with cause `non_substantive` unless it does at least one of the following:
  * introduces an evidence item whose `id` is not already present on the target issue,
  * changes the value of an existing schema field,
  * changes an issue's `status`,
  * adds the submitting agent to `confirmed_by` or `contested_by` where not already present,
  * introduces a new entry in `issues`, `actions`, `votes`, or `conflict_record`.

**Similarity to prior turns MUST NOT be used as a rejection criterion.** Prior versions specified embedding-distance rejection against earlier outputs. That inverts the value of the strongest signal a retrospective produces: when two agents independently arrive at the same finding, the convergence is the point. Such a submission MUST be recorded by adding the agent to `confirmed_by`, and MUST NOT be suppressed as redundant.

The anti-pattern is affirmation without content, which is structurally decidable. Semantic resemblance is not.

### 18.3 Freeform Brainstorm Drift

* **Forbidden:** unconstrained speculation, conversational sprawl, narrative discussion in canonical state.
* **Detection:** two deterministic checks, both performed by the Runtime.

**Length.** Every free-text field carries a character budget. An update whose field exceeds its budget MUST be rejected with cause `text_budget_exceeded`. Defaults, overridable in `AGENTS.md`:

```yaml
text_budgets:            # characters
  issue.title: 120
  evidence.claim: 300
  action.description: 400
  action.outcome_criteria: 300
  decision.rationale: 2000
  conflict_record.positions.claim: 300
```

**Conversational openers.** A free-text field whose first non-whitespace token matches the marker list MUST be rejected with cause `conversational_artifact`. The default list is normative and closed, so the check stays decidable:

```text
I  We  Well  So  Okay  OK  Actually  Honestly  Basically
Great  Agreed  Right  Sure  Thanks  Maybe  Perhaps  Indeed
```

`No`, `Yes` and `Just` are rejected **only when a comma follows**. They open a reply and a technical sentence equally well, and treating them as unconditional markers rejected six sound findings in a live run — "No upper ontology is imported" is a finding, while "No, that is not right" is a reply. The comma is what separates them.

Connectives occurring mid-field (`however`, `moreover`, `that said`) SHOULD be flagged for revision but MUST NOT be auto-rejected: prose glue inside a rationale is not the same failure as a field that opens as dialogue, and rejecting it would fight legitimate technical writing.

### 18.4 Out-of-Scope Mutation

* **Forbidden:** modifying paths outside the agent's phase authorization, or outside `permitted_sections` during an exclusive operation.
* **Detection:** authorization and scope check at update validation (§11.4).

### 18.5 Ungrounded Confirmation

* **Forbidden:** advancing an issue to `confirmed` on agreement alone.
* **Detection:** the grounding gate (§8.3.1); rejection cause `ungrounded_confirmation`.

---

## 19. Error Handling and Recovery

### 19.1 Schema Violation

When an update fails schema validation, the Runtime MUST reject it without partial application and log the violation with cause. The submitting agent MAY resubmit a corrected update.

### 19.2 Lock Expiration

When an exclusive-operation lock expires without release, the Runtime MUST reclaim it, discard any partial in-flight updates, and record an `audit` entry. The operation MAY be rescheduled.

### 19.3 Version Conflict

On CAS failure the Runtime MUST reject with cause `version_conflict` and return the current version. This is expected behavior under parallel append, not an error condition, and MUST NOT be logged as a fault.

### 19.4 Runtime Failure

The Runtime is the sole write path. If it is unavailable, no mutations MAY be accepted. Because the Runtime is deterministic code rather than a model, recovery is restart plus checksum verification against the last `audit` version.

### 19.5 Adjudicator Failure

If the Adjudicator becomes unavailable, the system MUST enter degraded operation rather than halt: agents MAY continue appending under CAS, and the Runtime MAY continue validating and advancing phases whose exit criteria are mechanically decidable. Operations requiring judgement — semantic merge, compression, tie-break, contradiction adjudication — MUST block until the Adjudicator is restored.

A retrospective MUST NOT be declared complete while any Adjudicator-dependent operation is outstanding.

### 19.6 State Corruption

If canonical state fails schema validation outside an in-flight update, or `retro.sprint_input_checksum` fails to match the substrate, the Runtime MUST roll back to the last validated version recorded in `audit` and emit a corruption event.

---

## 20. Final Deliverables

At retrospective completion, the system MUST produce:

```text
/RETRO_BOARD.md        — Final human-readable rendering
/RETRO_STATE.yaml      — Final canonical state
/RETRO_SUMMARY.md      — Executive summary derived from canonical state
/ACTION_ITEMS.yaml     — Extracted action manifest
```

Each deliverable MUST validate against its respective schema. `RETRO_SUMMARY.md` MUST be derivable from `RETRO_STATE.yaml`; the summary is a projection, not an independent artifact.

`RETRO_SUMMARY.md` MUST additionally report:

* the substrate `coverage` declaration (§7.3), so that analytical blind spots are visible alongside conclusions,
* all `unresolved` issues, with the positions recorded in `conflict_record`,
* the count of confirmed issues grounded solely in `note` records (§7.4),
* the count of issues reopened, and any that hit the reopen ceiling.

A retrospective that reports only its conclusions overstates its confidence. These four figures are what make the conclusions readable.

---

## 21. Guiding Philosophy

This system is not simulated human conversation. It is structured collaborative cognition through controlled state transitions. The objective is reliable synthesis, disciplined analysis, reduced drift, and high-quality operational insight — not the appearance of teamwork.

Two commitments distinguish this version. Judgement is confined to the component that requires it, and everything mechanically decidable is decided mechanically. And no finding is confirmed on agreement alone: consensus determines whether a grounded claim is accepted, never whether an ungrounded one becomes true.

---

## Changelog

* **v2.2 (Draft)** — Typed, source-referenced evidence with Runtime-set verification and a grounding gate on confirmation (§8.3, §18.5). Specified the sprint input substrate as a frozen, checksummed, read-only corpus with explicit coverage declaration (§7). Split the Orchestrator into a deterministic Runtime and a model-driven `@Adjudicator` holding no privileged write path (§4.1); degraded rather than halted operation on Adjudicator failure (§19.5). Replaced per-mutation exclusive locking with optimistic CAS append, reserving locks for global read-modify-write operations (§11). Added `unresolved` as a terminal status, `proposed → archived`, and guarded reopening from `confirmed`, `rejected`, and `unresolved` (§16.3, §16.4). Replaced similarity-based redundancy detection with a structural no-new-content test (§18.2). Declared `votes`, `conflict_record`, `archive`, and `token_ledger` in the top-level schema; added the `Decision` schema (§8.5) and `Action.addresses`; defined `quorum` and `vote_denominator`; quantified free-text budgets and closed the conversational-opener list (§18.3); added token accounting with scoped reads, a compression reserve, and defined behaviour on budget exhaustion (§14.1); made `update_id` mandatory and demoted determinism to a SHOULD. Recorded the absence of human participation as a deliberate experimental constraint (§1.1).
* **v2.1 (Draft)** — *(section numbers below refer to v2.1 numbering)* Added conformance language (§0), glossary (§3), state versioning with CAS (§9), formal lock lifecycle (§10), update semantics with idempotence (§11), formal phase entry/exit criteria (§12), structured contradiction records (§14), explicit status transition graph (§15.3), error handling and recovery (§18), detection mechanisms paired with each anti-pattern (§17). Reorganized heading hierarchy; reduced visual noise from horizontal rules.
* **v2.0** — Initial blackboard architecture; agent model; phase workflow; anti-pattern catalog.
