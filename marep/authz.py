# SPDX-License-Identifier: Apache-2.0
"""Phase authorization and scope enforcement (MAREP v2.2 §11.4, §18.4).

Outside an exclusive operation an agent's write authority comes from the
current phase and its declared role, not from a lock. That is what makes
parallel append safe without serializing every mutation.
"""

from __future__ import annotations

from typing import Any, Iterable

from .errors import Cause

#: Paths no agent may ever write, in any phase (§11.4, §4.1.1).
RUNTIME_RESERVED: tuple[str, ...] = (
    "retro.version",
    "retro.phase",
    "retro.sprint_input_checksum",
    "audit",
    "token_ledger",
    "turn",
)

#: Field name reserved to the Runtime wherever it appears (§8.3).
RESERVED_FIELDS: frozenset[str] = frozenset({"verified"})

#: phase -> role -> writable top-level sections.
PHASE_AUTHORIZATION: dict[str, dict[str, frozenset[str]]] = {
    # `decisions` is writable by agents in gathering so an agent with nothing
    # to report can record a declination. Without it §13.1's "submitted or
    # explicitly declined" exit criterion is unsatisfiable and one silent agent
    # deadlocks the phase.
    "gathering":   {"agent": frozenset({"issues", "decisions"}),
                    "adjudicator": frozenset(),
                    "runtime": frozenset({"issues", "decisions"})},
    "merge":       {"agent": frozenset(),
                    "adjudicator": frozenset({"issues", "decisions"}),
                    "runtime": frozenset({"issues", "decisions"})},
    "analysis":    {"agent": frozenset({"issues", "conflict_record"}),
                    "adjudicator": frozenset({"issues", "conflict_record", "decisions"}),
                    "runtime": frozenset({"issues", "decisions"})},
    "consensus":   {"agent": frozenset({"votes"}),
                    "adjudicator": frozenset({"votes", "conflict_record", "issues", "decisions"}),
                    "runtime": frozenset({"issues", "votes", "decisions"})},
    "actions":     {"agent": frozenset({"actions", "decisions"}),
                    "adjudicator": frozenset({"actions", "decisions"}),
                    "runtime": frozenset({"actions", "issues", "decisions"})},
    "compression": {"agent": frozenset(),
                    "adjudicator": frozenset({"archive", "decisions", "issues"}),
                    "runtime": frozenset({"archive", "decisions", "issues"})},
    "complete":    {"agent": frozenset(),
                    "adjudicator": frozenset(),
                    "runtime": frozenset()},
}


def role_of(agent: str, adjudicator_name: str = "Adjudicator") -> str:
    if agent == "Runtime":
        return "runtime"
    if agent == adjudicator_name:
        return "adjudicator"
    return "agent"


def changed_sections(current: dict[str, Any], candidate: dict[str, Any]) -> set[str]:
    """Top-level sections that differ between two documents."""
    keys = set(current) | set(candidate)
    return {k for k in keys if current.get(k) != candidate.get(k)}


def _reserved_field_touched(current: dict[str, Any], candidate: dict[str, Any]) -> str | None:
    """Detect an agent setting `verified` (§8.3): only the Runtime may."""
    cur = {i["id"]: i for i in current.get("issues", []) or []}
    for issue in candidate.get("issues", []) or []:
        old_ev = {e["id"]: e for e in cur.get(issue["id"], {}).get("evidence", []) or []}
        for ev in issue.get("evidence", []) or []:
            if "verified" not in ev:
                continue
            prior = old_ev.get(ev["id"], {}).get("verified")
            if ev.get("verified") != prior:
                return f"issues[{issue['id']}].evidence[{ev['id']}].verified"
    return None


def check(
    current: dict[str, Any],
    candidate: dict[str, Any],
    agent: str,
    phase: str,
    *,
    adjudicator_name: str = "Adjudicator",
    permitted_sections: Iterable[str] | None = None,
) -> tuple[Cause | None, str]:
    """Authorize a candidate state for a submitting agent.

    ``permitted_sections`` narrows authority further during an exclusive
    operation (§11.3); outside one it is ``None`` and the phase table governs.
    An empty grant is treated as no narrowing rather than as forbidding
    everything: a lock that silently revokes all authority is a footgun, and
    §11.3 expects a grant to name the sections it permits.
    """
    role = role_of(agent, adjudicator_name)

    if role != "runtime":
        touched = _reserved_field_touched(current, candidate)
        if touched:
            return (
                Cause.OUT_OF_SCOPE,
                f"{touched} is set exclusively by the Runtime (§8.3); "
                "agent-supplied values are discarded",
            )

    changed = changed_sections(current, candidate)
    changed.discard("retro")   # version handled by the Runtime; checked below
    changed.discard("audit")

    if role != "runtime":
        for reserved in RUNTIME_RESERVED:
            top = reserved.split(".")[0]
            if top in changed and top not in ("issues", "actions", "decisions", "votes", "conflict_record", "archive"):
                return Cause.OUT_OF_SCOPE, f"{reserved} is reserved to the Runtime (§11.4)"
        cur_retro, can_retro = current.get("retro", {}), candidate.get("retro", {})
        for f in ("phase", "sprint_input_checksum", "sprint"):
            if cur_retro.get(f) != can_retro.get(f):
                return Cause.OUT_OF_SCOPE, f"retro.{f} is reserved to the Runtime (§11.4)"

    allowed = PHASE_AUTHORIZATION.get(phase, {}).get(role, frozenset())
    if permitted_sections is not None:
        allowed = allowed & set(permitted_sections)

    unauthorized = sorted(changed - set(allowed))
    if unauthorized:
        return (
            Cause.OUT_OF_SCOPE,
            f"{agent} (role {role}) may not write {unauthorized} in phase {phase!r}; "
            f"authorized: {sorted(allowed) or '(none)'}",
        )
    return None, ""
