# SPDX-License-Identifier: Apache-2.0
"""Anti-pattern enforcement (MAREP v2.2 §18).

Every check here is deterministic and decidable from the documents in front of
it. That is the point of the section: enforcement is mechanical rather than
discretionary, and none of it requires a model.

Note what is deliberately absent. v2.1 rejected updates by semantic similarity
to prior turns. v2.2 §18.2 forbids that, because when two agents independently
reach the same finding the convergence is the most valuable signal a
retrospective produces. The test below is structural.
"""

from __future__ import annotations

import re
from typing import Any

from .errors import Cause

# --- §18.1 persona theater -------------------------------------------------

#: Fields where an agent name is data rather than prose.
AGENT_REFERENCE_FIELDS = frozenset({
    "owner", "submitted_by", "agent", "holder", "confirmed_by", "contested_by", "basis",
})

_AGENT_MENTION = re.compile(r"@[A-Za-z][A-Za-z0-9_]*")

# --- §18.3 freeform drift --------------------------------------------------

#: Character budgets for free-text fields. Overridable from AGENTS.md.
DEFAULT_TEXT_BUDGETS: dict[str, int] = {
    "issue.title": 120,
    "evidence.claim": 300,
    "action.description": 400,
    "action.outcome_criteria": 300,
    # Reasoning, not prose. §18.3 exists to stop conversational sprawl, not to
    # cap explanation, and 600 characters is about a hundred words — too tight
    # to say why two causal accounts are incompatible. A live run lost a correct
    # contradiction to this number.
    "decision.rationale": 2000,
    "conflict_record.positions.claim": 300,
}

#: Closed, normative list applied to the FIRST token of a free-text field.
#: Mid-field connectives are flagged, never auto-rejected: prose glue inside a
#: rationale is not the same failure as a field that opens as dialogue.
CONVERSATIONAL_OPENERS = frozenset({
    "i", "we", "well", "so", "okay", "ok", "actually", "honestly", "basically",
    "great", "agreed", "right", "sure", "thanks", "maybe", "perhaps", "indeed",
})

#: Words that open a reply conversationally *and* open a technical sentence
#: perfectly well. A live run rejected six sound findings — "No upper ontology
#: is imported", "No class-bearing file declares an import" — because "no" was
#: on the list above. They are rejected only when a comma follows, which is
#: what separates "No, that's wrong" from "No import graph exists".
AMBIGUOUS_OPENERS = frozenset({"no", "yes", "just"})

MID_FIELD_CONNECTIVES = frozenset({"however", "moreover", "furthermore", "that said", "of course"})

_FIRST_TOKEN = re.compile(r"^\s*([A-Za-z']+)")

#: Which document paths carry free text, and which budget key governs each.
FREE_TEXT_FIELDS: tuple[tuple[str, str], ...] = (
    ("issues[].title", "issue.title"),
    ("issues[].evidence[].claim", "evidence.claim"),
    ("actions[].description", "action.description"),
    ("actions[].outcome_criteria", "action.outcome_criteria"),
    ("decisions[].rationale", "decision.rationale"),
    ("conflict_record[].positions[].claim", "conflict_record.positions.claim"),
)


def _walk_free_text(doc: dict[str, Any]):
    """Yield ``(path, budget_key, text)`` for every free-text field present.

    Paths are keyed by identifier rather than list position, so the same field
    has the same path across two versions of the document. That is what lets
    the checks below compare a candidate against current state and judge only
    the text an update actually introduces.
    """
    for issue in doc.get("issues", []) or []:
        iid = issue.get("id", "?")
        if isinstance(issue.get("title"), str):
            yield f"issues[{iid}].title", "issue.title", issue["title"]
        for ev in issue.get("evidence", []) or []:
            if isinstance(ev.get("claim"), str):
                yield f"issues[{iid}].evidence[{ev.get('id','?')}].claim", "evidence.claim", ev["claim"]
    for act in doc.get("actions", []) or []:
        for f, key in (("description", "action.description"),
                       ("outcome_criteria", "action.outcome_criteria")):
            if isinstance(act.get(f), str):
                yield f"actions[{act.get('id','?')}].{f}", key, act[f]
    for dec in doc.get("decisions", []) or []:
        if isinstance(dec.get("rationale"), str):
            yield f"decisions[{dec.get('id','?')}].rationale", "decision.rationale", dec["rationale"]
    for cf in doc.get("conflict_record", []) or []:
        cid = cf.get("issue_id", "?")
        for j, pos in enumerate(cf.get("positions", []) or []):
            if isinstance(pos.get("claim"), str):
                yield (f"conflict_record[{cid}].positions[{j}].claim",
                       "conflict_record.positions.claim", pos["claim"])


def introduced_text(candidate: dict[str, Any], current: dict[str, Any] | None):
    """Free-text fields an update adds or changes.

    Checks must judge what an update introduces, never re-judge the whole
    document. Re-scanning everything means one string that trips a rule — a
    tightened budget, or text the Runtime itself wrote — permanently blocks
    every subsequent update, which turns a content rule into a deadlock.
    """
    if current is None:
        yield from _walk_free_text(candidate)
        return
    before = {path: text for path, _k, text in _walk_free_text(current)}
    for path, key, text in _walk_free_text(candidate):
        if before.get(path) != text:
            yield path, key, text


def check_persona_theater(
    doc: dict[str, Any], current: dict[str, Any] | None = None
) -> tuple[Cause | None, str]:
    """§18.1 — reject conversational addresses in text the update introduces."""
    for path, _key, text in introduced_text(doc, current):
        m = _AGENT_MENTION.search(text)
        if m:
            return (
                Cause.PERSONA_THEATER,
                f"{path} contains an agent mention {m.group(0)!r}; agent names belong in "
                f"reference fields ({', '.join(sorted(AGENT_REFERENCE_FIELDS))}), not prose",
            )
    return None, ""


def check_text_budgets(
    doc: dict[str, Any], budgets: dict[str, int] | None = None,
    current: dict[str, Any] | None = None,
) -> tuple[Cause | None, str]:
    """§18.3 length half — a hard reject."""
    budgets = {**DEFAULT_TEXT_BUDGETS, **(budgets or {})}
    for path, key, text in introduced_text(doc, current):
        limit = budgets.get(key)
        if limit is not None and len(text) > limit:
            return (
                Cause.TEXT_BUDGET_EXCEEDED,
                f"{path} is {len(text)} characters, budget for {key} is {limit}",
            )
    return None, ""


def check_conversational_openers(
    doc: dict[str, Any], current: dict[str, Any] | None = None
) -> tuple[Cause | None, str]:
    """§18.3 opener half — a hard reject on a closed marker list."""
    for path, _key, text in introduced_text(doc, current):
        m = _FIRST_TOKEN.match(text)
        if not m:
            continue
        first = m.group(1).lower()
        conversational = first in CONVERSATIONAL_OPENERS or (
            first in AMBIGUOUS_OPENERS and text[m.end():m.end() + 1] == ",")
        if conversational:
            return (
                Cause.CONVERSATIONAL_ARTIFACT,
                f"{path} opens with {m.group(1)!r}, a conversational marker; "
                "state the finding rather than narrating it",
            )
    return None, ""


def flag_connectives(doc: dict[str, Any]) -> list[str]:
    """§18.3 — advisory only. Flagged for revision, never auto-rejected."""
    flags = []
    for path, _key, text in _walk_free_text(doc):
        low = text.lower()
        for c in MID_FIELD_CONNECTIVES:
            if c in low:
                flags.append(f"{path}: mid-field connective {c!r}")
    return flags


# --- §18.2 non-substantive update -----------------------------------------

_SUBSTANTIVE_SECTIONS = ("issues", "actions", "decisions", "votes", "conflict_record", "archive")


def substantive_change(
    current: dict[str, Any], candidate: dict[str, Any], agent: str
) -> tuple[bool, str]:
    """§18.2 — does the candidate carry new information?

    Returns ``(is_substantive, which_condition)``. The five conditions are the
    spec's, checked in order so the audit detail names the one that was met.

    A known and accepted limit: an agent that restates an existing claim under a
    fresh evidence id satisfies condition 1. v2.2 takes that over similarity
    detection deliberately, because the alternative suppresses independent
    convergence, which is worth more than the duplicates it would catch.
    """
    cur_issues = {i["id"]: i for i in current.get("issues", []) or []}
    can_issues = {i["id"]: i for i in candidate.get("issues", []) or []}

    # 5. a new entry in issues / actions / votes / conflict_record
    for section in ("issues", "actions", "votes", "conflict_record"):
        if len(candidate.get(section, []) or []) > len(current.get(section, []) or []):
            return True, f"new entry in {section}"

    # 1. an evidence item whose id is not already on the target issue
    for iid, issue in can_issues.items():
        old_ids = {e["id"] for e in cur_issues.get(iid, {}).get("evidence", []) or []}
        new_ids = {e["id"] for e in issue.get("evidence", []) or []}
        if new_ids - old_ids:
            return True, f"new evidence on {iid}: {sorted(new_ids - old_ids)}"

    # 3. a status change
    for iid, issue in can_issues.items():
        old = cur_issues.get(iid, {}).get("status")
        if old is not None and issue.get("status") != old:
            return True, f"status change on {iid}: {old} -> {issue.get('status')}"

    # 4. the submitting agent joining confirmed_by / contested_by
    for iid, issue in can_issues.items():
        for f in ("confirmed_by", "contested_by"):
            old = set(cur_issues.get(iid, {}).get(f, []) or [])
            new = set(issue.get(f, []) or [])
            if agent in (new - old):
                return True, f"{agent} added to {iid}.{f}"

    # 2. any other change to an existing schema field
    for section in _SUBSTANTIVE_SECTIONS:
        if (candidate.get(section) or []) != (current.get(section) or []):
            return True, f"field change within {section}"

    return False, ""


def run_all(
    candidate: dict[str, Any],
    current: dict[str, Any],
    agent: str,
    budgets: dict[str, int] | None = None,
) -> tuple[Cause | None, str]:
    """Run every hard check in §18 against a candidate state."""
    for fn in (check_persona_theater, check_conversational_openers):
        cause, detail = fn(candidate, current)
        if cause:
            return cause, detail
    cause, detail = check_text_budgets(candidate, budgets, current)
    if cause:
        return cause, detail
    substantive, _which = substantive_change(current, candidate, agent)
    if not substantive:
        return (
            Cause.NON_SUBSTANTIVE,
            "update carries no new information; see §18.2 for the five conditions "
            "that make an update substantive",
        )
    return None, ""
