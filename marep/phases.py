"""Phase entry and exit criteria, and advancement (MAREP v2.2 §13).

Transitions are performed exclusively by the Runtime, which evaluates exit
criteria mechanically. Every criterion below is decidable from canonical state,
which is the reason phase control does not need the Adjudicator.
"""

from __future__ import annotations

from typing import Any, Iterable

PHASES: tuple[str, ...] = (
    "gathering", "merge", "analysis", "consensus", "actions", "compression", "complete",
)

#: Statuses that satisfy the Phase 3 exit criterion.
_ANALYSIS_SETTLED = frozenset(
    {"confirmed", "rejected", "contested", "unresolved", "archived"})


def next_phase(phase: str) -> str | None:
    i = PHASES.index(phase)
    return PHASES[i + 1] if i + 1 < len(PHASES) else None


def _issues(state: dict[str, Any]) -> list[dict[str, Any]]:
    return state.get("issues", []) or []


def exit_criteria(state: dict[str, Any], roster: Iterable[str]) -> tuple[bool, list[str]]:
    """Evaluate the exit criteria for the state's current phase.

    Returns ``(satisfied, unmet_reasons)``.
    """
    phase = state["retro"]["phase"]
    issues = _issues(state)
    unmet: list[str] = []

    if phase == "gathering":
        # §13.1 — every agent has submitted or explicitly declined.
        submitted = {
            ev.get("submitted_by")
            for i in issues for ev in (i.get("evidence") or [])
        }
        declined = {
            d.get("subject", "").removeprefix("AGENT:")
            for d in state.get("decisions", []) or []
            if d.get("type") == "declination"
        }
        missing = [a for a in roster if a not in submitted and a not in declined]
        if missing:
            unmet.append(f"agents with neither submission nor declination: {sorted(missing)}")

    elif phase == "merge":
        # §13.2 — no duplicate IDs; every evidence item resolved by the Runtime.
        ids = [i["id"] for i in issues]
        dupes = sorted({x for x in ids if ids.count(x) > 1})
        if dupes:
            unmet.append(f"duplicate issue ids: {dupes}")
        unresolved = [
            f"{i['id']}/{ev['id']}"
            for i in issues for ev in (i.get("evidence") or [])
            if "verified" not in ev
        ]
        if unresolved:
            unmet.append(f"evidence not yet resolved by the Runtime: {unresolved[:5]}")

    elif phase == "analysis":
        # §13.3 — every issue settled. `proposed` blocks; the Runtime may
        # archive unevaluated issues at close, which is what prevents one
        # ignored finding from deadlocking the phase forever.
        stuck = [i["id"] for i in issues if i["status"] not in _ANALYSIS_SETTLED]
        if stuck:
            unmet.append(f"issues neither settled nor archived: {stuck}")

    elif phase == "consensus":
        # §13.4 — nothing contested. `unresolved` is a legitimate terminal
        # outcome and MUST NOT be forced to confirmed or rejected.
        contested = [i["id"] for i in issues if i["status"] == "contested"]
        if contested:
            unmet.append(f"issues still contested: {contested}")

    elif phase == "actions":
        # §13.5 — every confirmed issue has an accepted action or an explicit
        # no_action_required decision. Unresolved issues require neither.
        accepted = {a["id"] for a in state.get("actions", []) or [] if a.get("status") == "accepted"}
        addressed: set[str] = set()
        for a in state.get("actions", []) or []:
            if a.get("status") == "accepted":
                addressed.update(a.get("addresses") or [])
        waived = {
            d["subject"].split(":")[-1]
            for d in state.get("decisions", []) or []
            if d.get("type") == "no_action_required"
        }
        for i in issues:
            if i["status"] != "confirmed":
                continue
            has_action = bool(set(i.get("related_actions") or []) & accepted) or i["id"] in addressed
            if not has_action and i["id"] not in waived:
                unmet.append(f"confirmed issue {i['id']} has no accepted action and no waiver")

    elif phase == "compression":
        # §13.6 — deliverable production is checked by the caller producing them.
        pass

    elif phase == "complete":
        unmet.append("retrospective is already complete")

    return (not unmet), unmet


def entry_criteria(state: dict[str, Any], phase: str, substrate_ok: bool) -> tuple[bool, list[str]]:
    """Evaluate entry criteria for a phase about to be entered (§13.1)."""
    unmet: list[str] = []
    if phase == "gathering":
        if not state["retro"].get("sprint_input_checksum"):
            unmet.append("sprint input substrate is not frozen and checksummed (§7.1)")
        if not substrate_ok:
            unmet.append("sprint input substrate checksum does not match (§19.6)")
    return (not unmet), unmet


def unevaluated_issue_ids(state: dict[str, Any]) -> list[str]:
    """Issues the Runtime may archive at Phase 3 close, cause `unevaluated`."""
    return [
        i["id"] for i in _issues(state)
        if i["status"] == "proposed"
        and not (i.get("confirmed_by") or i.get("contested_by"))
    ]
