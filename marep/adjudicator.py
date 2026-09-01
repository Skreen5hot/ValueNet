# SPDX-License-Identifier: Apache-2.0
"""The Adjudicator — the model-driven half of MAREP's control plane (v2.2 §4.1.2).

Four responsibilities, and only four: semantic contradiction, thematic merge,
compression, and tie-break. Everything mechanically decidable belongs to the
Runtime, so this module is deliberately small.

The property that matters most is negative. **The Adjudicator holds no
privileged write path.** Every proposal it makes is submitted through
``Runtime.submit()``, validated under the same rules as any agent's update, and
recorded in `audit` under its own identity. It cannot advance phases, edit the
audit log, set `verified`, or bypass the transition graph. A backend that
hallucinates produces rejected updates, not corrupt state — which is the whole
reason v2.2 split the Orchestrator in two.

The backend is a protocol with a deterministic implementation, so the entire
control plane is testable end to end without an API key or a single model call.
The Anthropic adapter lives in ``marep.anthropic_backend`` and is imported only
when asked for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from . import state as st
from .checks import DEFAULT_TEXT_BUDGETS
from .errors import Cause, Result, reject
from .runtime import Runtime

ADJUDICATOR = "Adjudicator"


# ----------------------------------------------------------------------
# proposals — what a backend returns
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Position:
    agent: str
    claim: str
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ContradictionFinding:
    """Two agents asserting incompatible things about one issue (§15)."""

    issue_id: str
    positions: list[Position]
    rationale: str = ""


@dataclass(frozen=True)
class MergeProposal:
    """Two issues that are the same finding under different names (§13.2)."""

    survivor_id: str
    duplicate_id: str
    rationale: str


@dataclass(frozen=True)
class CompressionProposal:
    """History to relocate under `archive`, plus a summary (§14)."""

    summary: str
    archive_entries: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class TieBreak:
    """Resolution of a vote the decision rules could not settle (§16.1)."""

    subject: str
    outcome: str            # confirmed | rejected | unresolved
    rationale: str


# ----------------------------------------------------------------------
# backend protocol
# ----------------------------------------------------------------------

@runtime_checkable
class AdjudicatorBackend(Protocol):
    """Where judgement happens. The only place a model may be involved.

    Each method receives a scoped read of canonical state and returns
    proposals. A backend never writes: it cannot reach the Runtime.
    """

    def detect_contradictions(self, view: dict[str, Any]) -> list[ContradictionFinding]: ...

    def propose_merges(self, view: dict[str, Any]) -> list[MergeProposal]: ...

    def compress(self, view: dict[str, Any]) -> CompressionProposal | None: ...

    def break_tie(self, view: dict[str, Any], vote: dict[str, Any]) -> TieBreak | None: ...


class NullBackend:
    """Proposes nothing. Models §19.5 degraded operation.

    With this installed the Runtime keeps accepting agent appends and keeps
    advancing phases whose exit criteria are mechanically decidable; only the
    judgement calls stall. That is the specified behaviour when the Adjudicator
    is unavailable, and it is worth having as a first-class object rather than
    as an error path.
    """

    def detect_contradictions(self, view): return []
    def propose_merges(self, view): return []
    def compress(self, view): return None
    def break_tie(self, view, vote): return None


class ScriptedBackend:
    """Deterministic backend driven by pre-supplied proposals.

    Not a mock of a model — a substitute for one. It makes the control plane
    testable without an API key, and it is how the "a hallucinating Adjudicator
    cannot corrupt state" property is exercised: script an illegal proposal and
    watch the Runtime refuse it.
    """

    def __init__(
        self,
        contradictions: list[ContradictionFinding] | None = None,
        merges: list[MergeProposal] | None = None,
        compression: CompressionProposal | None = None,
        tie_breaks: dict[str, TieBreak] | None = None,
        fail_with: Exception | None = None,
    ):
        self._contradictions = contradictions or []
        self._merges = merges or []
        self._compression = compression
        self._tie_breaks = tie_breaks or {}
        self._fail_with = fail_with
        self.calls: list[str] = []

    def _record(self, name: str) -> None:
        self.calls.append(name)
        if self._fail_with is not None:
            raise self._fail_with

    def detect_contradictions(self, view):
        self._record("detect_contradictions"); return list(self._contradictions)

    def propose_merges(self, view):
        self._record("propose_merges"); return list(self._merges)

    def compress(self, view):
        self._record("compress"); return self._compression

    def break_tie(self, view, vote):
        self._record("break_tie"); return self._tie_breaks.get(vote.get("subject", ""))


# ----------------------------------------------------------------------
# the Adjudicator
# ----------------------------------------------------------------------

class Adjudicator:
    """Translates backend judgement into updates the Runtime validates."""

    def __init__(self, runtime: Runtime, backend: AdjudicatorBackend, *, name: str = ADJUDICATOR):
        self.rt = runtime
        self.backend = backend
        self.name = name
        self._seq = 0

    # ---- helpers -----------------------------------------------------

    def _update_id(self, kind: str) -> str:
        self._seq += 1
        return f"ADJ-{kind}-{self._seq:04d}"

    def _fit(self, text: str, key: str = "decision.rationale") -> str:
        """Clip free text to its budget rather than lose the update carrying it.

        A rejected update loses the whole finding; a clipped rationale loses
        only the tail of an explanation, and says so. Losing a correct
        contradiction to a character count is the worse outcome.
        """
        limit = {**DEFAULT_TEXT_BUDGETS, **self.rt.text_budgets}.get(key)
        if limit is None or len(text) <= limit:
            return text
        marker = " [clipped]"
        return text[: limit - len(marker)].rstrip() + marker

    def _next_decision_id(self) -> str:
        existing = self.rt.state.get("decisions", []) or []
        return f"DEC-{len(existing) + 1:03d}"

    def _submit(self, kind: str, body: dict[str, Any], *, tokens: int = 0) -> Result:
        body = {"update_id": self._update_id(kind), "base_version": self.rt.version, **body}
        return self.rt.submit(body, self.name, tokens=tokens)

    def _view(self, sections: list[str]) -> dict[str, Any]:
        return self.rt.read(self.name, sections)

    def propose(self, method: str, *args: Any) -> tuple[Any, Result | None]:
        """Call the backend with §19.5 protection. Returns ``(value, error)``.

        The degradation guarantee only holds for calls that go through here.
        Reaching for ``adjudicator.backend.<method>()`` directly gets the
        proposal but loses the protection, so an API failure becomes an
        unhandled exception instead of a retryable rejection — which is exactly
        how the first live run died. Callers that want to inspect a proposal
        before acting on it should use this rather than the backend.
        """
        try:
            return getattr(self.backend, method)(*args), None
        except Exception as exc:
            return None, reject(Cause.ADJUDICATOR_UNAVAILABLE,
                                f"adjudicator backend failed: {exc}",
                                version=self.rt.version)

    # ---- §15 semantic contradiction ----------------------------------

    def adjudicate_contradictions(
        self, *, tokens: int = 0, findings: list[ContradictionFinding] | None = None
    ) -> list[Result]:
        """Mark contested and record positions for each contradiction found.

        ``findings`` lets a caller supply proposals already obtained from the
        backend. Without it, inspecting what the backend said and then acting on
        it costs two model calls for one decision.
        """
        if findings is None:
            findings, err = self.propose("detect_contradictions",
                                         self._view(["issues", "conflict_record"]))
            if err is not None:
                return [err]

        results = []
        for f in findings:
            body: dict[str, Any] = {
                "issues": [{"id": f.issue_id, "status": "contested"}],
                "conflict_record": [{
                    "issue_id": f.issue_id,
                    "positions": [
                        {"agent": p.agent, "claim": p.claim, "evidence": list(p.evidence)}
                        for p in f.positions
                    ],
                }],
            }
            # The reasoning behind a contradiction is the most useful thing the
            # Adjudicator produces; discarding it leaves the record saying an
            # issue is contested without saying why anyone thought so.
            if f.rationale:
                body["decisions"] = [{
                    "id": self._next_decision_id(), "type": "consensus_outcome",
                    "subject": f"ISSUE:{f.issue_id}", "outcome": "contested",
                    "rationale": self._fit(f.rationale), "basis": "adjudicator",
                    "decided_at": st.utcnow(),
                }]
            results.append(self._submit("contradiction", body, tokens=tokens))
        return results

    # ---- §13.2 thematic merge ----------------------------------------

    def adjudicate_merges(self, *, tokens: int = 0) -> list[Result]:
        """Fold duplicates into a survivor, under an exclusive lock (§11.2).

        The duplicate's evidence is carried over before it is archived, so the
        grounding of the surviving issue is never weakened by a merge.
        """
        lock = self.rt.acquire_lock("merge", self.name,
                                    permitted_sections=["issues", "decisions"])
        if not lock:
            return [lock]
        try:
            merges, err = self.propose("propose_merges", self._view(["issues"]))
            if err is not None:
                return [err]

            results = []
            for m in merges:
                by_id = st.issues_by_id(self.rt.state)
                dup = by_id.get(m.duplicate_id)
                if dup is None or m.survivor_id not in by_id:
                    results.append(reject(
                        Cause.SCHEMA_VIOLATION,
                        f"merge names an issue that does not exist: "
                        f"{m.survivor_id} <- {m.duplicate_id}", version=self.rt.version))
                    continue
                carried = [
                    {k: v for k, v in e.items() if k != "verified"}
                    for e in (dup.get("evidence") or [])
                ]
                results.append(self._submit("merge", {
                    "issues": [
                        {"id": m.survivor_id, "evidence": carried},
                        {"id": m.duplicate_id, "status": "archived"},
                    ],
                    "decisions": [{
                        "id": self._next_decision_id(), "type": "merged",
                        "subject": f"ISSUE:{m.duplicate_id}",
                        "outcome": f"merged into {m.survivor_id}",
                        "rationale": self._fit(m.rationale), "basis": "adjudicator",
                        "decided_at": st.utcnow(),
                    }],
                }, tokens=tokens))
            return results
        finally:
            self.rt.release_lock(self.name)

    # ---- §14 compression ---------------------------------------------

    def adjudicate_compression(self, *, tokens: int = 0) -> list[Result]:
        lock = self.rt.acquire_lock("compression", self.name,
                                    permitted_sections=["archive", "decisions"])
        if not lock:
            return [lock]
        try:
            proposal, err = self.propose("compress",
                                         self._view(["issues", "decisions", "archive"]))
            if err is not None:
                return [err]
            if proposal is None:
                return []
            return [self._submit("compression", {
                "archive": list(proposal.archive_entries),
                "decisions": [{
                    "id": self._next_decision_id(), "type": "compression",
                    "subject": "RETROSPECTIVE", "outcome": "history archived",
                    "rationale": self._fit(proposal.summary), "basis": "adjudicator",
                    "decided_at": st.utcnow(),
                }],
            }, tokens=tokens)]
        finally:
            self.rt.release_lock(self.name)

    # ---- §16.1 tie-break ---------------------------------------------

    def adjudicate_tie_breaks(
        self, *, tokens: int = 0, decisions: dict[str, TieBreak] | None = None
    ) -> list[Result]:
        """Settle open votes. A sub-threshold split is not a tie (§16.2).

        Only votes still marked `open` are offered to the backend; a vote that
        already resolved to `unresolved` is a legitimate terminal outcome and
        must not be reopened by judgement.
        """
        view = self._view(["issues", "votes"])
        results = []
        for vote in view.get("votes", []) or []:
            if vote.get("outcome") != "open":
                continue
            if decisions is not None:
                decision = decisions.get(vote.get("subject", ""))
                if decision is None:
                    continue
                results.append(self._apply_tie_break(vote, decision, tokens))
                continue
            decision, err = self.propose("break_tie", view, vote)
            if err is not None:
                results.append(err)
                continue
            if decision is None:
                continue
            results.append(self._apply_tie_break(vote, decision, tokens))
        return results

    def _apply_tie_break(self, vote: dict[str, Any], decision: TieBreak, tokens: int) -> Result:
            issue_id = decision.subject.split(":")[1] if ":" in decision.subject else decision.subject
            body: dict[str, Any] = {
                "votes": [{**vote, "outcome": decision.outcome, "closed_at": st.utcnow()}],
                "decisions": [{
                    "id": self._next_decision_id(), "type": "consensus_outcome",
                    "subject": decision.subject, "outcome": decision.outcome,
                    "rationale": self._fit(decision.rationale), "basis": "adjudicator",
                    "decided_at": st.utcnow(),
                }],
            }
            if decision.outcome in ("confirmed", "rejected", "unresolved"):
                body["issues"] = [{"id": issue_id, "status": decision.outcome}]
            return self._submit("tiebreak", body, tokens=tokens)

    # ---- convenience --------------------------------------------------

    def run_for_phase(self, *, tokens: int = 0) -> list[Result]:
        """Do whatever the current phase asks of the Adjudicator."""
        phase = self.rt.phase
        if phase == "merge":
            return self.adjudicate_merges(tokens=tokens)
        if phase == "analysis":
            return self.adjudicate_contradictions(tokens=tokens)
        if phase == "consensus":
            return self.adjudicate_tie_breaks(tokens=tokens)
        if phase == "compression":
            return self.adjudicate_compression(tokens=tokens)
        return []
