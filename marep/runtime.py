"""The MAREP Runtime (v2.2 §4.1.1).

Deterministic code. No model is consulted anywhere in this module, and none may
be: the Runtime exists precisely so that every mechanically decidable rule is
decided mechanically, leaving the Adjudicator only the judgement calls.

The submission pipeline, in order:

    1. integrity      substrate checksum still matches                   (§19.6)
    2. lock           no exclusive operation in flight                   (§11.2)
    3. budget         spendable tokens remain                            (§14.1)
    4. idempotence    update_id not already applied                      (§12)
    5. CAS            base_version is the current version                (§10)
    6. merge          apply onto a copy; live state untouched            (§12.1)
    7. authorization  phase + role scope, reserved fields                (§11.4)
    8. resolution     Runtime sets `verified` from the substrate         (§8.3)
    9. schema         candidate validates                                (§19.1)
   10. identifiers    no duplicates                                      (§4.1.1)
   11. transitions    status changes legal, grounded, reopen-guarded     (§16)
   12. anti-patterns  persona, openers, budgets, non-substantive         (§18)
   13. commit         version += 1, audit append, atomic write           (§10)

Any failure returns before step 13, so a rejected update leaves no trace in
canonical state beyond nothing at all.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from . import authz, checks, phases, state as st, transitions
from .errors import Cause, Result, ok, reject
from .substrate import Substrate
from .tokens import Ledger, TokenBudget, scoped_read
from .validate import validate_state

RUNTIME = "Runtime"


class Runtime:
    """Sole write path to canonical state.

    ``roster`` is the declared agent roster from AGENTS.md (§4.2), needed for
    phase-exit evaluation and vote denominators.
    """

    def __init__(
        self,
        state: dict[str, Any],
        substrate: Substrate,
        *,
        roster: Iterable[str] = (),
        state_path: str | Path | None = None,
        budget: TokenBudget | None = None,
        max_reopens: int = 2,
        text_budgets: dict[str, int] | None = None,
        adjudicator_name: str = "Adjudicator",
    ):
        self.state = state
        self.substrate = substrate
        self.roster = list(roster)
        self.state_path = Path(state_path) if state_path else None
        self.budget = budget or TokenBudget()
        self.max_reopens = max_reopens
        self.text_budgets = text_budgets or {}
        self.adjudicator_name = adjudicator_name
        self.rejections: list[Result] = []

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    @classmethod
    def initialize(
        cls, sprint: str, substrate: Substrate, *, roster: Iterable[str] = (), **kw
    ) -> "Runtime":
        """Freeze the substrate into a fresh state document (§7.1)."""
        return cls(st.new_state(sprint, substrate.checksum), substrate, roster=roster, **kw)

    @classmethod
    def resume(
        cls, path: str | Path, substrate: Substrate, *, roster: Iterable[str] = (), **kw
    ) -> "Runtime":
        """Continue a run from saved state, at whatever phase it stopped in.

        Run 2 reached version 117 with 28 findings, every one carrying verified
        evidence, and then stopped mid-vote because the API credit ran out.
        Without this the only way forward was `initialize`, which discards all
        of it and re-derives the same findings for the same 366,000 tokens.
        Interruption is not an exotic case for a run that makes hundreds of
        calls over an hour, and paying full price to recover from it is the
        wrong default.

        The substrate checksum must match. Every piece of evidence in the saved
        state was verified against the substrate that was current when it was
        submitted, and the grounding gate's guarantee is that a citation
        resolves to the record it was checked against. Resuming onto a
        different substrate would leave 28 findings marked verified against
        records that may no longer say what they said, which is a worse
        failure than losing the run: it would look sound.
        """
        state = st.load(path)
        saved = (state.get("retro") or {}).get("sprint_input_checksum")
        if saved != substrate.checksum:
            raise ValueError(
                f"cannot resume {Path(path).name}: it was built against substrate "
                f"{saved}, and this one is {substrate.checksum}. Evidence verified "
                "against the old substrate would carry its verified flag onto "
                "records that may have changed. Rebuild the substrate from the "
                "same commit, or start a fresh run.")
        kw.setdefault("state_path", path)
        return cls(state, substrate, roster=roster, **kw)

    # ------------------------------------------------------------------
    # accessors
    # ------------------------------------------------------------------

    @property
    def version(self) -> int:
        return self.state["retro"]["version"]

    @property
    def phase(self) -> str:
        return self.state["retro"]["phase"]

    @property
    def ledger(self) -> Ledger:
        return Ledger(self.state.get("token_ledger"), self.budget)

    def read(self, agent: str, sections: list[str] | None = None) -> dict[str, Any]:
        """Scoped read for an agent (§14.1). Defaults to its phase authority."""
        if sections is None:
            role = authz.role_of(agent, self.adjudicator_name)
            sections = sorted(authz.PHASE_AUTHORIZATION.get(self.phase, {}).get(role, frozenset()))
        return scoped_read(self.state, sections)

    # ------------------------------------------------------------------
    # the submission pipeline
    # ------------------------------------------------------------------

    def submit(self, update: dict[str, Any], agent: str, *, tokens: int = 0) -> Result:
        u = dict(update)
        update_id = u.pop("update_id", None)
        base_version = u.pop("base_version", None)

        # 1. integrity
        if not self.substrate.verify_checksum():
            return self._log(reject(
                Cause.SUBSTRATE_CHECKSUM_MISMATCH,
                "frozen substrate has changed since Phase 1 entry (§19.6)",
                version=self.version,
            ))

        # 2. exclusive operation in flight
        turn = self.state.get("turn")
        if turn and agent != turn.get("holder"):
            if not self._lock_expired(turn):
                return self._log(reject(
                    Cause.EXCLUSIVE_OPERATION_IN_PROGRESS,
                    f"{turn['holder']} holds the lock for {turn['operation']}; retry after release",
                    version=self.version,
                ))
            self._reclaim_lock()
            turn = None  # the reclaimed lock must not go on narrowing scope

        # 3. budget
        if tokens:
            cause, detail = self.ledger.check_turn(tokens)
            if cause:
                return self._log(reject(cause, detail, version=self.version))

        # 4. idempotence
        if not update_id:
            return self._log(reject(
                Cause.SCHEMA_VIOLATION, "update_id is mandatory (§12)", version=self.version))
        applied = st.applied_update_ids(self.state)
        if update_id in applied:
            return self._log(reject(
                Cause.DUPLICATE_UPDATE,
                f"update_id {update_id!r} was already applied at version {applied[update_id]}; "
                "re-application is a no-op",
                version=self.version,
            ))

        # 5. compare-and-swap
        if base_version != self.version:
            return self._log(reject(
                Cause.VERSION_CONFLICT,
                f"update references version {base_version}, current is {self.version}; rebase",
                version=self.version,
            ))

        # 6. merge onto a copy
        candidate = st.apply_update(self.state, u)

        # 7. authorization (before the Runtime writes `verified`, so its own
        #    write is not mistaken for an agent touching a reserved field)
        cause, detail = authz.check(
            self.state, candidate, agent, self.phase,
            adjudicator_name=self.adjudicator_name,
            permitted_sections=(turn or {}).get("permitted_sections") or None,
        )
        if cause:
            return self._log(reject(cause, detail, version=self.version))

        # 8. evidence resolution — only the Runtime may set this
        newly_verified = self._resolve_evidence(candidate)

        # 9. schema
        errors = validate_state(candidate)
        if errors:
            return self._log(reject(
                Cause.SCHEMA_VIOLATION, "; ".join(errors[:3]), version=self.version))

        # 10. identifiers
        dupes = st.duplicate_ids(candidate)
        if dupes:
            return self._log(reject(
                Cause.DUPLICATE_ID, f"duplicate identifiers: {dupes}", version=self.version))

        # 11. transitions
        cause, detail = self._check_transitions(candidate, agent, newly_verified)
        if cause:
            return self._log(reject(cause, detail, version=self.version))

        # 12. anti-patterns
        cause, detail = checks.run_all(candidate, self.state, agent, self.text_budgets)
        if cause:
            return self._log(reject(cause, detail, version=self.version))

        # 13. commit
        return self._commit(candidate, agent, update_id, u, tokens)

    # ------------------------------------------------------------------
    # steps
    # ------------------------------------------------------------------

    def _resolve_evidence(self, candidate: dict[str, Any]) -> dict[str, set[str]]:
        """Set `verified` on every evidence item (§8.3). Runtime-only.

        Returns issue_id -> ids of evidence that are both newly present in this
        candidate and verified, which is what the reopening guard consumes.
        """
        current = st.issues_by_id(self.state)
        newly_verified: dict[str, set[str]] = {}
        for issue in candidate.get("issues", []) or []:
            prior_ids = {e["id"] for e in current.get(issue["id"], {}).get("evidence", []) or []}
            fresh: set[str] = set()
            for ev in issue.get("evidence", []) or []:
                verdict, why = self.substrate.assess(
                    ev.get("source", {}), ev.get("claim", ""))
                ev["grounding"] = verdict
                ev["grounding_note"] = why
                # `verified` now means the record supports the claim, not
                # merely that the reference resolves. A Run 3 agent cited a
                # statement-count metric for a claim about domain and range;
                # the reference resolved, the claim was false, and it was
                # marked verified on three findings. Assessed over Run 3's 228
                # items this leaves 194 supported and blocks none of its 27
                # findings, so the bar rises without rewriting history.
                ev["verified"] = verdict == "supported"
                if ev["verified"] and ev["id"] not in prior_ids:
                    fresh.add(ev["id"])
            if fresh:
                newly_verified[issue["id"]] = fresh
        return newly_verified

    def _check_transitions(
        self, candidate: dict[str, Any], agent: str, newly_verified: dict[str, set[str]]
    ) -> tuple[Cause | None, str]:
        current = st.issues_by_id(self.state)
        may_archive = agent == RUNTIME or (
            agent == self.adjudicator_name and self.phase == "merge")
        for issue in candidate.get("issues", []) or []:
            old = current.get(issue["id"], {}).get("status")
            if old is None:
                # New issue: must enter as `proposed`.
                if issue["status"] != "proposed":
                    return (
                        Cause.ILLEGAL_TRANSITION,
                        f"{issue['id']} enters at status {issue['status']!r}; "
                        "new issues must enter as 'proposed' (§16.3)",
                    )
                continue
            new = issue["status"]
            has_verified = any(e.get("verified") for e in issue.get("evidence", []) or [])
            cause, detail = transitions.check(
                old, new,
                may_archive_proposed=may_archive,
                has_verified_evidence=has_verified,
                new_verified_evidence_ids=newly_verified.get(issue["id"], set()),
                reopen_count=int(issue.get("reopen_count", 0)),
                max_reopens=self.max_reopens,
            )
            if cause:
                return cause, f"{issue['id']}: {detail}"
            if transitions.is_reopening(old, new):
                issue["reopen_count"] = int(issue.get("reopen_count", 0)) + 1
        return None, ""

    def _commit(
        self,
        candidate: dict[str, Any],
        agent: str,
        update_id: str,
        raw_update: dict[str, Any],
        tokens: int,
    ) -> Result:
        version = self.version + 1
        candidate["retro"]["version"] = version
        sections = sorted(authz.changed_sections(self.state, candidate) - {"retro", "audit"})
        summary = self._summarize(raw_update, sections)
        candidate.setdefault("audit", []).append(
            st.audit_entry(version, agent, update_id, summary, sections)
        )
        if tokens:
            ledger = Ledger(candidate.get("token_ledger"), self.budget)
            ledger.record(agent, self.phase, tokens, version)
            candidate["token_ledger"] = ledger.to_dict()
        self.state = candidate
        self._persist()
        return ok(version, sections=sections, summary=summary)

    @staticmethod
    def _summarize(update: dict[str, Any], sections: list[str]) -> str:
        bits = []
        for s in sections:
            n = len(update.get(s, []) or [])
            bits.append(f"{s}({n})" if n else s)
        return ", ".join(bits) or "no-op"

    # ------------------------------------------------------------------
    # exclusive operations (§11.2, §11.3)
    # ------------------------------------------------------------------

    def acquire_lock(
        self, operation: str, holder: str, *, ttl_seconds: int = 300,
        permitted_sections: list[str] | None = None,
    ) -> Result:
        turn = self.state.get("turn")
        if turn and not self._lock_expired(turn):
            return reject(
                Cause.EXCLUSIVE_OPERATION_IN_PROGRESS,
                f"{turn['holder']} holds the lock for {turn['operation']}",
                version=self.version,
            )
        now = datetime.now(timezone.utc)
        self.state["turn"] = {
            "operation": operation,
            "holder": holder,
            "state_version": self.version,
            "lock_acquired": now.isoformat(timespec="seconds"),
            "lock_expiration": (now + timedelta(seconds=ttl_seconds)).isoformat(timespec="seconds"),
            "permitted_sections": permitted_sections or [],
        }
        self._persist()
        return ok(self.version, operation=operation, holder=holder)

    def release_lock(self, holder: str) -> Result:
        turn = self.state.get("turn")
        if not turn:
            return reject(Cause.LOCK_NOT_HELD, "no lock is held", version=self.version)
        if turn["holder"] != holder:
            return reject(
                Cause.LOCK_NOT_HELD,
                f"lock is held by {turn['holder']}, not {holder}", version=self.version)
        self.state["turn"] = None
        self._persist()
        return ok(self.version)

    @staticmethod
    def _lock_expired(turn: dict[str, Any]) -> bool:
        try:
            exp = datetime.fromisoformat(turn["lock_expiration"])
        except (KeyError, ValueError):
            return True
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= exp

    def _reclaim_lock(self) -> None:
        """§19.2 — reclaim on expiry and discard partial in-flight work."""
        turn = self.state.get("turn") or {}
        self.state["turn"] = None
        version = self.version + 1
        self.state["retro"]["version"] = version
        self.state.setdefault("audit", []).append(
            st.audit_entry(
                version, RUNTIME, f"lock-reclaim-{version}",
                f"reclaimed expired {turn.get('operation','?')} lock from {turn.get('holder','?')}",
                ["turn"],
            )
        )
        self._persist()

    # ------------------------------------------------------------------
    # phase control (§13)
    # ------------------------------------------------------------------

    def exit_ready(self) -> tuple[bool, list[str]]:
        return phases.exit_criteria(self.state, self.roster)

    def advance_phase(self, *, archive_unevaluated: bool = False) -> Result:
        """Advance to the next phase if exit criteria are met. Runtime only."""
        if archive_unevaluated and self.phase == "analysis":
            self._archive_unevaluated()

        satisfied, unmet = self.exit_ready()
        if not satisfied:
            return reject(
                Cause.PHASE_EXIT_UNSATISFIED, "; ".join(unmet), version=self.version)

        nxt = phases.next_phase(self.phase)
        if nxt is None:
            return reject(
                Cause.PHASE_EXIT_UNSATISFIED, "already at the terminal phase",
                version=self.version)

        entry_ok, entry_unmet = phases.entry_criteria(
            self.state, nxt, self.substrate.verify_checksum())
        if not entry_ok:
            return reject(
                Cause.PHASE_ENTRY_UNSATISFIED, "; ".join(entry_unmet), version=self.version)

        previous = self.phase
        version = self.version + 1
        self.state["retro"]["phase"] = nxt
        self.state["retro"]["version"] = version
        self.state.setdefault("audit", []).append(
            st.audit_entry(
                version, RUNTIME, f"phase-{previous}-to-{nxt}",
                f"phase {previous} -> {nxt}", ["retro.phase"],
            )
        )
        self._persist()
        return ok(version, phase=nxt, previous=previous)

    def _archive_unevaluated(self) -> list[str]:
        """§13.3 — archive issues nobody evaluated, so one cannot deadlock a phase."""
        ids = phases.unevaluated_issue_ids(self.state)
        if not ids:
            return []
        by_id = st.issues_by_id(self.state)
        n = len(self.state.get("decisions", []) or [])
        for k, iid in enumerate(ids, start=1):
            by_id[iid]["status"] = "archived"
            self.state.setdefault("decisions", []).append({
                "id": f"DEC-{n + k:03d}",
                "type": "unevaluated_archive",
                "subject": f"ISSUE:{iid}",
                "outcome": "archived",
                "rationale": "Archived at analysis close; no agent evaluated it.",
                "basis": "runtime",
                "decided_at": st.utcnow(),
            })
        version = self.version + 1
        self.state["retro"]["version"] = version
        self.state.setdefault("audit", []).append(
            st.audit_entry(
                version, RUNTIME, f"archive-unevaluated-{version}",
                f"archived {len(ids)} unevaluated issues: {ids}", ["issues", "decisions"],
            )
        )
        self._persist()
        return ids

    # ------------------------------------------------------------------
    # reporting (§20)
    # ------------------------------------------------------------------

    def report(self) -> dict[str, Any]:
        """The four figures §20 requires the summary to carry."""
        issues = self.state.get("issues", []) or []
        note_refs = self.substrate.note_only_refs()
        note_only = [
            i["id"] for i in issues
            if i["status"] == "confirmed"
            and (ev := [e for e in i.get("evidence", []) or [] if e.get("verified")])
            and all(e["source"]["ref"] in note_refs for e in ev)
        ]
        return {
            "coverage": self.substrate.coverage(),
            "unavailable_types": self.substrate.unavailable_types(),
            "unresolved": [i["id"] for i in issues if i["status"] == "unresolved"],
            "confirmed_note_only": note_only,
            "reopened": {i["id"]: i.get("reopen_count", 0) for i in issues if i.get("reopen_count")},
            "at_reopen_ceiling": [
                i["id"] for i in issues if int(i.get("reopen_count", 0)) >= self.max_reopens
            ],
            "counts": {
                s: sum(1 for i in issues if i["status"] == s) for s in transitions.STATUSES
            },
            "tokens_consumed": self.ledger.consumed,
        }

    # ------------------------------------------------------------------

    def _persist(self) -> None:
        if self.state_path:
            st.save(self.state, self.state_path)

    def _log(self, result: Result) -> Result:
        self.rejections.append(result)
        return result
