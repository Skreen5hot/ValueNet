"""Issue status transition graph and reopening guards.

MAREP v2.2 §16.3 and §16.4. Every edge is enumerated; anything not enumerated
is rejected. Reopening is permitted from every settled status, which is what
lets a retrospective revise a conclusion in light of evidence found late, and
is guarded so that permission does not become churn.
"""

from __future__ import annotations

from typing import Iterable

from .errors import Cause

STATUSES = ("proposed", "contested", "confirmed", "rejected", "unresolved", "archived")

SETTLED = frozenset({"confirmed", "rejected", "unresolved"})
TERMINAL = frozenset({"archived"})

#: The complete transition graph (§16.3). Edges absent here MUST be rejected.
EDGES: frozenset[tuple[str, str]] = frozenset({
    ("proposed", "contested"),
    ("proposed", "confirmed"),
    ("proposed", "rejected"),
    ("proposed", "archived"),     # Runtime only, at Phase 3 close, cause `unevaluated`

    ("contested", "confirmed"),
    ("contested", "rejected"),
    ("contested", "unresolved"),

    ("confirmed", "contested"),   # reopening
    ("rejected", "contested"),    # reopening
    ("unresolved", "contested"),  # reopening

    ("confirmed", "archived"),
    ("rejected", "archived"),
    ("unresolved", "archived"),
})

#: Edges that constitute reopening, and so attract the §16.4 guards.
REOPENING: frozenset[tuple[str, str]] = frozenset(
    (s, "contested") for s in SETTLED
)

#: Edges an ordinary agent may never perform. `proposed -> archived` retires an
#: issue without anyone judging it, which is a control-plane act: the Runtime
#: does it at Phase 3 close for unevaluated issues, and the Adjudicator does it
#: during Phase 2 to retire a duplicate it has folded into a survivor.
CONTROL_PLANE_ONLY: frozenset[tuple[str, str]] = frozenset({("proposed", "archived")})
RUNTIME_ONLY = CONTROL_PLANE_ONLY  # retained name; see CONTROL_PLANE_ONLY

#: Edges gated on verified evidence (§8.3.1).
REQUIRES_VERIFIED_EVIDENCE: frozenset[tuple[str, str]] = frozenset({
    ("proposed", "confirmed"),
    ("contested", "confirmed"),
})


def is_legal(old: str, new: str) -> bool:
    return (old, new) in EDGES


def is_reopening(old: str, new: str) -> bool:
    return (old, new) in REOPENING


def outgoing(status: str) -> set[str]:
    return {b for a, b in EDGES if a == status}


def check(
    old: str,
    new: str,
    *,
    may_archive_proposed: bool = False,
    has_verified_evidence: bool = False,
    new_verified_evidence_ids: Iterable[str] = (),
    reopen_count: int = 0,
    max_reopens: int = 2,
) -> tuple[Cause | None, str]:
    """Decide whether a status change is permitted.

    Returns ``(None, "")`` when permitted, otherwise a cause and a detail
    string. Every condition here is decidable from state plus the audit log,
    which is what keeps this out of the Adjudicator's hands.
    """
    if old == new:
        return None, ""  # no-op; the substantive-content check handles it

    if new not in STATUSES:
        return Cause.SCHEMA_VIOLATION, f"unknown status {new!r}"

    if not is_legal(old, new):
        allowed = sorted(outgoing(old)) or ["<terminal>"]
        return (
            Cause.ILLEGAL_TRANSITION,
            f"{old} -> {new} is not in the transition graph; from {old!r} allowed: {allowed}",
        )

    if (old, new) in CONTROL_PLANE_ONLY and not may_archive_proposed:
        return (
            Cause.ILLEGAL_TRANSITION,
            f"{old} -> {new} is a control-plane transition: the Runtime at analysis "
            "close, or the Adjudicator retiring a merged duplicate during merge",
        )

    if (old, new) in REQUIRES_VERIFIED_EVIDENCE and not has_verified_evidence:
        return (
            Cause.UNGROUNDED_CONFIRMATION,
            "confirmation requires at least one evidence item with verified: true (§8.3.1)",
        )

    if is_reopening(old, new):
        fresh = list(new_verified_evidence_ids)
        if not fresh:
            return (
                Cause.REOPEN_BLOCKED,
                "reopening requires at least one newly introduced verified evidence item (§16.4)",
            )
        if reopen_count >= max_reopens:
            return (
                Cause.REOPEN_BLOCKED,
                f"issue is at the reopen ceiling ({reopen_count}/{max_reopens}); "
                "record it unresolved instead (§16.4)",
            )

    return None, ""


def graph_report() -> str:
    """Render the graph, for documentation and for eyeballing in tests."""
    lines = []
    for s in STATUSES:
        outs = sorted(outgoing(s))
        lines.append(f"{s:11} -> {', '.join(outs) if outs else '(terminal)'}")
    return "\n".join(lines)
