# SPDX-License-Identifier: Apache-2.0
"""Canonical state: construction, merge semantics, and the audit log.

MAREP v2.2 §8, §10, §12.1. Updates are YAML-merge-style diffs, so this module
owns what "merge" means: keyed upsert for collections, union for agent lists,
and never a silent overwrite of a whole section.
"""

from __future__ import annotations

import copy
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "2.2.0"

#: Section name -> the field that identifies an element within it.
COLLECTION_KEYS: dict[str, str] = {
    "issues": "id",
    "actions": "id",
    "decisions": "id",
    "votes": "subject",
    "conflict_record": "issue_id",
}

#: Fields merged as a set union rather than replaced.
UNION_FIELDS: frozenset[str] = frozenset(
    {"confirmed_by", "contested_by", "related_actions", "addresses"}
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_state(sprint: str, substrate_checksum: str) -> dict[str, Any]:
    return {
        "retro": {
            "sprint": sprint,
            "sprint_input_checksum": substrate_checksum,
            "phase": "gathering",
            "version": 0,
            "schema_version": SCHEMA_VERSION,
        },
        "issues": [],
        "actions": [],
        "decisions": [],
        "votes": [],
        "conflict_record": [],
        "archive": [],
        "token_ledger": {
            "consumed_total": 0,
            "consumed_by_phase": {},
            "consumed_by_agent": {},
            "last_updated_version": 0,
        },
        "turn": None,
        "audit": [],
    }


def load(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


#: How many times to retry the atomic rename before giving up on atomicity.
SAVE_RETRIES = 6


def save(state: dict[str, Any], path: str | Path, *, retries: int = SAVE_RETRIES) -> None:
    """Write atomically where the platform allows it.

    Write-to-temp-then-rename is atomic on POSIX and merely usual on Windows,
    where any process holding a handle on the target — a sync client, an
    indexer, a virus scanner — makes `os.replace` fail with a sharing
    violation. A live retrospective died three phases in on exactly that,
    because the state file sat inside a synced folder.

    So: retry with backoff, and if the rename still will not go through, write
    in place. That trades atomicity for not losing the run. The trade is worth
    making in this direction — a torn state file is recoverable from the audit
    log and a lost hour of model calls is not — but it is a trade, and callers
    who need the stronger guarantee should keep state off synced storage.
    """
    p = Path(path)
    tmp = p.with_suffix(p.suffix + ".tmp")
    body = yaml.safe_dump(state, sort_keys=False, allow_unicode=True, width=100)
    tmp.write_text(body, encoding="utf-8")

    for attempt in range(retries):
        try:
            tmp.replace(p)
            return
        except PermissionError:
            if attempt == retries - 1:
                break
            time.sleep(0.05 * (2 ** attempt))

    # Rename is being refused persistently. Write directly rather than lose the
    # state, and clean up the temp file so the next save is not confused by it.
    p.write_text(body, encoding="utf-8")
    try:
        tmp.unlink()
    except OSError:
        pass


def clone(state: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(state)


def _merge_element(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(existing)
    for k, v in incoming.items():
        if k in UNION_FIELDS:
            merged = list(out.get(k, []) or [])
            for item in v or []:
                if item not in merged:
                    merged.append(item)
            out[k] = merged
        elif k == "evidence":
            by_id = {e["id"]: copy.deepcopy(e) for e in out.get("evidence", []) or []}
            order = [e["id"] for e in out.get("evidence", []) or []]
            for ev in v or []:
                if ev["id"] in by_id:
                    by_id[ev["id"]].update(ev)
                else:
                    by_id[ev["id"]] = copy.deepcopy(ev)
                    order.append(ev["id"])
            out["evidence"] = [by_id[i] for i in order]
        else:
            out[k] = copy.deepcopy(v)
    return out


def apply_update(current: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Merge an update onto a copy of current state (§12.1).

    Returns a candidate document. The live state is never touched, which is how
    "reject without partial application" (§12) is guaranteed structurally
    rather than by careful unwinding.
    """
    candidate = clone(current)
    for section, key in COLLECTION_KEYS.items():
        incoming = update.get(section)
        if incoming is None:
            continue
        existing = candidate.get(section, []) or []
        index = {e[key]: i for i, e in enumerate(existing) if key in e}
        for element in incoming:
            if key not in element:
                existing.append(copy.deepcopy(element))
                continue
            if element[key] in index:
                pos = index[element[key]]
                existing[pos] = _merge_element(existing[pos], element)
            else:
                index[element[key]] = len(existing)
                existing.append(copy.deepcopy(element))
        candidate[section] = existing

    if "archive" in update:
        candidate["archive"] = (candidate.get("archive") or []) + copy.deepcopy(update["archive"])

    # Anything else the update carries is merged too, even sections an agent is
    # forbidden to touch. Silently dropping an unauthorized write would leave
    # the agent with a `non_substantive` rejection and no idea it had aimed at
    # a reserved section; authorization (§11.4) must be the thing that says no.
    for key, value in update.items():
        if key in COLLECTION_KEYS or key == "archive":
            continue
        if isinstance(value, dict) and isinstance(candidate.get(key), dict):
            merged = copy.deepcopy(candidate[key])
            merged.update(copy.deepcopy(value))
            candidate[key] = merged
        else:
            candidate[key] = copy.deepcopy(value)
    return candidate


def audit_entry(
    version: int, agent: str, update_id: str, summary: str, sections: list[str]
) -> dict[str, Any]:
    return {
        "version": version,
        "agent": agent,
        "timestamp": utcnow(),
        "update_id": update_id,
        "diff_summary": summary,
        "affected_sections": sorted(sections),
    }


def applied_update_ids(state: dict[str, Any]) -> dict[str, int]:
    """update_id -> version at which it was accepted (§12 idempotence)."""
    return {e["update_id"]: e["version"] for e in state.get("audit", []) or [] if e.get("update_id")}


def issues_by_id(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {i["id"]: i for i in state.get("issues", []) or []}


def duplicate_ids(state: dict[str, Any]) -> dict[str, list[str]]:
    """Duplicate identifiers per collection (§4.1.1)."""
    out: dict[str, list[str]] = {}
    for section, key in COLLECTION_KEYS.items():
        seen: dict[str, int] = {}
        for e in state.get(section, []) or []:
            if key in e:
                seen[e[key]] = seen.get(e[key], 0) + 1
        dupes = sorted(k for k, n in seen.items() if n > 1)
        if dupes:
            out[section] = dupes
    return out
