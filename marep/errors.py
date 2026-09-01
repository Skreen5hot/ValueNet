# SPDX-License-Identifier: Apache-2.0
"""Rejection causes and result types for the MAREP Runtime.

Every rejection the Runtime can issue is named here. MAREP v2.2 requires that
rejections carry a cause (§19.1), so a submitting agent can tell a version
conflict it should retry from a schema violation it must fix.

Expected conditions are returned, not raised. A version conflict under parallel
append is normal operation, not a fault (§19.3); raising for it would make
ordinary contention look like an error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Cause(str, Enum):
    """Rejection causes. String-valued so they serialize into the audit log."""

    # --- concurrency (§11, §19.3) ---
    VERSION_CONFLICT = "version_conflict"
    EXCLUSIVE_OPERATION_IN_PROGRESS = "exclusive_operation_in_progress"
    LOCK_NOT_HELD = "lock_not_held"
    LOCK_EXPIRED = "lock_expired"

    # --- update semantics (§12) ---
    SCHEMA_VIOLATION = "schema_violation"
    DUPLICATE_UPDATE = "duplicate_update"
    DUPLICATE_ID = "duplicate_id"
    OUT_OF_SCOPE = "out_of_scope"

    # --- grounding (§8.3.1, §18.5) ---
    UNGROUNDED_CONFIRMATION = "ungrounded_confirmation"

    # --- transitions (§16.3, §16.4) ---
    ILLEGAL_TRANSITION = "illegal_transition"
    REOPEN_BLOCKED = "reopen_blocked"

    # --- anti-patterns (§18) ---
    PERSONA_THEATER = "persona_theater"
    NON_SUBSTANTIVE = "non_substantive"
    TEXT_BUDGET_EXCEEDED = "text_budget_exceeded"
    CONVERSATIONAL_ARTIFACT = "conversational_artifact"

    # --- phases (§13) ---
    PHASE_ENTRY_UNSATISFIED = "phase_entry_unsatisfied"
    PHASE_EXIT_UNSATISFIED = "phase_exit_unsatisfied"

    # --- control plane (§19.5) ---
    ADJUDICATOR_UNAVAILABLE = "adjudicator_unavailable"

    # --- budget (§14.1) ---
    BUDGET_EXHAUSTED = "budget_exhausted"

    # --- integrity (§19.6) ---
    STATE_CORRUPTION = "state_corruption"
    SUBSTRATE_CHECKSUM_MISMATCH = "substrate_checksum_mismatch"


#: Causes that mean "retry after rebasing", as opposed to "fix your update".
RETRYABLE = frozenset({
    Cause.VERSION_CONFLICT,
    Cause.EXCLUSIVE_OPERATION_IN_PROGRESS,
    # §19.5: an unavailable Adjudicator degrades rather than fails. The work is
    # worth retrying once it is back, so callers can treat it like contention.
    Cause.ADJUDICATOR_UNAVAILABLE,
})


@dataclass(frozen=True)
class Result:
    """Outcome of a Runtime operation.

    ``accepted`` is the only field a caller must check. ``version`` carries the
    new state version on acceptance and the *current* version on a version
    conflict, so the agent can rebase without a second call (§11.5).
    """

    accepted: bool
    version: int | None = None
    cause: Cause | None = None
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def retryable(self) -> bool:
        return self.cause in RETRYABLE

    def __bool__(self) -> bool:
        """True when the operation was accepted.

        This makes ``if result:`` and ``if not result:`` read naturally, at the
        cost of one trap worth knowing about: a **rejection is falsy**, so a
        presence check written ``if err:`` silently never fires. Test optional
        Results with ``if err is not None:``. This bit the Adjudicator's
        backend-protection path, where a swallowed error let a None proposal
        through to code that iterated it.
        """
        return self.accepted

    def __str__(self) -> str:
        if self.accepted:
            return f"accepted (version {self.version})"
        return f"rejected [{self.cause.value if self.cause else '?'}] {self.detail}"


def ok(version: int, **data: Any) -> Result:
    return Result(accepted=True, version=version, data=data)


def reject(cause: Cause, detail: str = "", version: int | None = None, **data: Any) -> Result:
    return Result(accepted=False, version=version, cause=cause, detail=detail, data=data)


class MarepError(Exception):
    """Raised only for conditions a caller cannot recover from.

    Corruption (§19.6) and programmer error. Never for a rejected update.
    """


class StateCorruption(MarepError):
    """Canonical state or substrate failed integrity checking (§19.6)."""
