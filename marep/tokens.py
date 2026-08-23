"""Token accounting (MAREP v2.2 §14.1).

Reducing token waste is goal three, which requires that tokens be counted.
Three rules follow from the spec: scoped reads, a compression reserve the
Runtime may not spend on ordinary turns, and defined behaviour on exhaustion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import Cause


@dataclass
class TokenBudget:
    """Budgets declared in AGENTS.md (§14.1)."""

    per_turn_context: int = 32_000
    per_retrospective_total: int = 1_000_000
    compression_trigger: float = 0.75
    compression_reserve: int = 50_000

    def spendable(self) -> int:
        """Total minus the reserve. Ordinary turns draw only from this."""
        return max(0, self.per_retrospective_total - self.compression_reserve)


def empty_ledger() -> dict[str, Any]:
    return {
        "consumed_total": 0,
        "consumed_by_phase": {},
        "consumed_by_agent": {},
        "last_updated_version": 0,
    }


class Ledger:
    """Running token accounting held in canonical state."""

    def __init__(self, data: dict[str, Any] | None, budget: TokenBudget):
        self._d = data or empty_ledger()
        self.budget = budget

    @property
    def consumed(self) -> int:
        return int(self._d.get("consumed_total", 0))

    def record(self, agent: str, phase: str, tokens: int, version: int) -> None:
        if tokens < 0:
            raise ValueError("token count must be non-negative")
        self._d["consumed_total"] = self.consumed + tokens
        self._d.setdefault("consumed_by_phase", {})
        self._d.setdefault("consumed_by_agent", {})
        self._d["consumed_by_phase"][phase] = self._d["consumed_by_phase"].get(phase, 0) + tokens
        self._d["consumed_by_agent"][agent] = self._d["consumed_by_agent"].get(agent, 0) + tokens
        self._d["last_updated_version"] = version

    def compression_due(self) -> bool:
        """§14 trigger: consumption past the configured fraction of total."""
        if self.budget.per_retrospective_total <= 0:
            return False
        return self.consumed >= self.budget.compression_trigger * self.budget.per_retrospective_total

    def exhausted(self) -> bool:
        """Ordinary turns are done once the spendable pool is gone (§14.1).

        The reserve remains, so a final compression can always run. A system
        that spends its way past the ability to compress cannot recover.
        """
        return self.consumed >= self.budget.spendable()

    def check_turn(self, requested_context: int) -> tuple[Cause | None, str]:
        if requested_context > self.budget.per_turn_context:
            return (
                Cause.BUDGET_EXHAUSTED,
                f"requested context {requested_context} exceeds per_turn_context "
                f"{self.budget.per_turn_context}; scope the read (§14.1)",
            )
        if self.exhausted():
            return (
                Cause.BUDGET_EXHAUSTED,
                f"spendable budget exhausted ({self.consumed}/{self.budget.spendable()}); "
                "reserve is held for final compression",
            )
        return None, ""

    def to_dict(self) -> dict[str, Any]:
        return dict(self._d)


def scoped_read(state: dict[str, Any], sections: list[str]) -> dict[str, Any]:
    """Supply an agent only the sections its task requires (§14.1).

    Handing every agent the whole document on every turn makes cost grow as
    agents x phases x state size, which is the dominant term in any
    non-trivial retrospective. ``retro`` is always included: an agent cannot
    submit a compare-and-swap update without knowing the version it read.
    """
    view = {"retro": dict(state.get("retro", {}))}
    for s in sections:
        if s in state:
            view[s] = state[s]
    return view
