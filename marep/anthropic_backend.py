"""Anthropic-backed Adjudicator (MAREP v2.2 §4.1.2).

The only module in this package that talks to a model, and the only one that
imports the `anthropic` SDK. Both are deliberate: everything mechanically
decidable lives in the Runtime, so the model's surface area is four methods.

Nothing here is invoked unless you construct it. `marep` core has no dependency
on `anthropic`; the import is deferred to construction so the package installs
and tests without it.

Design notes worth keeping:

* **Structured outputs, not prose parsing.** Every call constrains the response
  with `output_config.format`, so a proposal is either well-formed JSON or an
  API-level failure. Free-text parsing would put a second failure mode between
  the model and the Runtime.
* **The schema is not a safety boundary.** A well-formed proposal can still be
  wrong — a merge of two unrelated issues, a tie-break that confirms an
  ungrounded finding. That is fine, and it is the point of §4.1.2: proposals go
  through `Runtime.submit()` and are refused there. The schema buys parseability,
  not correctness.
* **Errors propagate.** A failed call raises, and `Adjudicator` turns it into a
  rejection rather than corrupt state, which is §19.5 degraded operation.
"""

from __future__ import annotations

import json
from typing import Any

from .adjudicator import (
    CompressionProposal,
    ContradictionFinding,
    MergeProposal,
    Position,
    TieBreak,
)

#: Claude Opus 5. Adaptive thinking is on by default on this model.
DEFAULT_MODEL = "claude-opus-5"

SYSTEM = """You are the Adjudicator in a MAREP retrospective (spec v2.2 §4.1.2).

You make only judgement calls. Schema validation, versioning, transition
legality, evidence verification, scope, and phase control are handled
deterministically by the Runtime and are not your concern. You hold no
privileged write path: your proposals are submitted and validated exactly like
any agent's, and an unfounded proposal is refused, not applied.

Principles:
- Consensus is not evidence. Never propose confirming an issue whose evidence
  is not verified; the Runtime will refuse it and the refusal is correct.
- A sub-threshold vote is not a tie. If a vote genuinely failed to reach
  threshold in either direction, `unresolved` is a legitimate terminal outcome.
  Do not manufacture agreement to tidy the record.
- Independent convergence is signal, not redundancy. Two agents reaching the
  same finding is the most valuable thing a retrospective produces; do not
  propose merging findings that merely resemble each other.
- Propose nothing rather than something speculative. An empty list is a valid
  and frequently correct answer."""

CONTRADICTION_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string"},
                    "rationale": {"type": "string"},
                    "positions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "agent": {"type": "string"},
                                "claim": {"type": "string"},
                                "evidence": {
                                    "type": "array",
                                    "items": {"type": "string", "pattern": "^EV-[0-9]{3,}$"},
                                    "description": "Evidence item ids on the issue, e.g. EV-001. Ids only, never prose.",
                                },
                            },
                            "required": ["agent", "claim", "evidence"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["issue_id", "positions", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["findings"],
    "additionalProperties": False,
}

MERGE_SCHEMA = {
    "type": "object",
    "properties": {
        "merges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "survivor_id": {"type": "string"},
                    "duplicate_id": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": ["survivor_id", "duplicate_id", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["merges"],
    "additionalProperties": False,
}

COMPRESSION_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "archive_entries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"kind": {"type": "string"}, "note": {"type": "string"}},
                "required": ["kind", "note"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "archive_entries"],
    "additionalProperties": False,
}

TIEBREAK_SCHEMA = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["confirmed", "rejected", "unresolved"]},
        "rationale": {"type": "string"},
    },
    "required": ["outcome", "rationale"],
    "additionalProperties": False,
}


class AnthropicBackend:
    """An Adjudicator backend that asks Claude.

    Construct explicitly; nothing in `marep` reaches for it. Credentials resolve
    the way the SDK resolves them — ``ANTHROPIC_API_KEY``, ``ANTHROPIC_AUTH_TOKEN``,
    or an ``ant auth login`` profile — so no key is passed here by default.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        client: Any | None = None,
        max_tokens: int = 16_000,
        effort: str = "high",
        enable_fallbacks: bool = True,
    ):
        if client is None:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - environment dependent
                raise ImportError(
                    "AnthropicBackend needs the `anthropic` package: pip install anthropic. "
                    "marep core does not depend on it; use ScriptedBackend or NullBackend "
                    "to run without a model."
                ) from exc
            client = anthropic.Anthropic()
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.effort = effort
        self.enable_fallbacks = enable_fallbacks

    # ------------------------------------------------------------------

    def _ask(self, prompt: str, schema: dict[str, Any],
             system: str | None = None) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system or SYSTEM,
            "messages": [{"role": "user", "content": prompt}],
            "thinking": {"type": "adaptive"},
            "output_config": {
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": schema},
            },
        }
        if self.enable_fallbacks:
            # A policy decline on a retrospective is unlikely but not
            # impossible; without fallbacks a refused request simply stops.
            kwargs["betas"] = ["server-side-fallback-2026-07-01"]
            kwargs["fallbacks"] = "default"
            response = self.client.beta.messages.create(**kwargs)
        else:
            response = self.client.messages.create(**kwargs)

        if getattr(response, "stop_reason", None) == "refusal":
            details = getattr(response, "stop_details", None)
            raise RuntimeError(
                f"Adjudicator request declined: {getattr(details, 'category', 'unknown')}")

        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            raise RuntimeError("Adjudicator response contained no text block")
        return json.loads(text)

    @staticmethod
    def _brief(view: dict[str, Any]) -> str:
        """A compact rendering of the scoped view.

        The Runtime already scopes reads to the sections the Adjudicator is
        authorized for (§14.1); this trims further to the fields that bear on
        judgement, since token cost is goal three.
        """
        issues = [
            {
                "id": i["id"], "title": i["title"], "status": i["status"],
                "severity": i.get("severity"),
                "confirmed_by": i.get("confirmed_by", []),
                "contested_by": i.get("contested_by", []),
                "evidence": [
                    {"id": e["id"], "claim": e["claim"],
                     "source": e["source"], "verified": e.get("verified")}
                    for e in (i.get("evidence") or [])
                ],
            }
            for i in view.get("issues", []) or []
        ]
        return json.dumps({"issues": issues}, indent=1)

    # ------------------------------------------------------------------

    def detect_contradictions(self, view: dict[str, Any]) -> list[ContradictionFinding]:
        data = self._ask(
            "Identify issues where two agents assert incompatible things — conflicting "
            "root causes, or claims that cannot both be true. Resemblance is not "
            "contradiction, and two agents agreeing is not a conflict. Return an empty "
            "list if nothing genuinely conflicts.\n\n" + self._brief(view),
            CONTRADICTION_SCHEMA)
        return [
            ContradictionFinding(
                issue_id=f["issue_id"], rationale=f["rationale"],
                positions=[Position(agent=p["agent"], claim=p["claim"],
                                    evidence=p.get("evidence", []))
                           for p in f["positions"]],
            )
            for f in data.get("findings", [])
        ]

    def propose_merges(self, view: dict[str, Any]) -> list[MergeProposal]:
        data = self._ask(
            "Identify pairs of issues that are the same finding recorded twice under "
            "different names. Merge only true duplicates. Two agents independently "
            "reporting the same underlying problem from different angles are corroborating "
            "each other, not duplicating — leave those alone.\n\n" + self._brief(view),
            MERGE_SCHEMA)
        return [MergeProposal(**m) for m in data.get("merges", [])]

    def compress(self, view: dict[str, Any]) -> CompressionProposal | None:
        data = self._ask(
            "Summarize this retrospective's history for archival. Preserve every "
            "conclusion and every evidence reference; a source reference summarized away "
            "destroys the chain a reopened issue depends on.\n\n" + self._brief(view),
            COMPRESSION_SCHEMA)
        return CompressionProposal(summary=data["summary"],
                                   archive_entries=data.get("archive_entries", []))

    def break_tie(self, view: dict[str, Any], vote: dict[str, Any]) -> TieBreak | None:
        data = self._ask(
            "Settle this vote. If it failed to reach threshold in either direction it is "
            "not a tie, and `unresolved` is the correct terminal outcome — do not "
            "manufacture agreement. Confirming requires verified evidence on the issue.\n\n"
            f"Vote: {json.dumps(vote, indent=1)}\n\n" + self._brief(view),
            TIEBREAK_SCHEMA)
        return TieBreak(subject=vote.get("subject", ""),
                        outcome=data["outcome"], rationale=data["rationale"])
