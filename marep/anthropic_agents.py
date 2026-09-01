# SPDX-License-Identifier: Apache-2.0
"""Analytical agents backed by Claude (MAREP v2.2 §4.2).

Kept apart from `anthropic_backend`, which serves the Adjudicator. The two ask
different questions of the same model and are wanted independently: a
deployment can run scripted agents against a live Adjudicator, or the reverse,
and neither should drag the other's prompts along.

The request plumbing is inherited — same model, same structured outputs, same
refusal handling. What differs is the system prompt, rebuilt per role, because
the roster's entire purpose is that the five agents are *not* interchangeable.
A shared prompt would give five names to one perspective.
"""

from __future__ import annotations

import json
from typing import Any

from .agents import ActionProposal, Assessment, AgentRole, EvidenceRef, Finding
from .anthropic_backend import AnthropicBackend
from .substrate import RECORD_TYPES

AGENT_SYSTEM = """You are {name}, one analytical perspective in a MAREP
retrospective (spec v2.2 §4.2). Your focus is {focus}.

{guidance}

How this system works, and what it means for you:

- You reason over a substrate of measured facts. Every claim must cite one by
  its ref. A finding you cannot ground is recorded verified: false and can
  never be confirmed. That is correct behaviour, not an obstacle, so do not
  invent a reference to get past it.
- Do not restate a measurement as a finding. "127 files do not parse" is a
  number; a finding says what follows from it and why it matters. If you have
  nothing to add beyond the number, add nothing.
- Stay in your lane. Another agent covers each remaining perspective, and
  duplicating their work wastes a turn and pollutes the merge phase.
- Proposing nothing is legitimate and frequently correct. An empty list is
  recorded as a declination, which is itself a contribution.
- You cannot see what the other agents will say, and must not guess."""

_EVIDENCE_ITEM = {
    "type": "object",
    "properties": {
        "claim": {"type": "string"},
        "source_type": {"enum": list(RECORD_TYPES)},
        "source_ref": {"type": "string",
                       "description": "A substrate record ref (preferred) or id"},
    },
    "required": ["claim", "source_type", "source_ref"],
    "additionalProperties": False,
}

FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string",
                               "description": "Short uppercase tag, e.g. PARSE, IRI, DEF"},
                    "title": {"type": "string"},
                    "severity": {"enum": ["low", "medium", "high", "critical"]},
                    "rationale": {"type": "string"},
                    "evidence": {"type": "array", "minItems": 1, "items": _EVIDENCE_ITEM},
                },
                "required": ["domain", "title", "severity", "rationale", "evidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["findings"],
    "additionalProperties": False,
}

ASSESSMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "assessments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string"},
                    "position": {"enum": ["confirm", "contest", "abstain"]},
                    "rationale": {"type": "string"},
                    "added_evidence": {"type": "array", "items": _EVIDENCE_ITEM},
                },
                "required": ["issue_id", "position", "rationale", "added_evidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["assessments"],
    "additionalProperties": False,
}

VOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "position": {"enum": ["confirm", "reject", "abstain"]},
        "rationale": {"type": "string"},
    },
    "required": ["position", "rationale"],
    "additionalProperties": False,
}

ACTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "outcome_criteria": {"type": "string"},
                    "addresses": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["description", "outcome_criteria", "addresses"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["actions"],
    "additionalProperties": False,
}


def _refs(items: list[dict[str, Any]]) -> list[EvidenceRef]:
    return [EvidenceRef(i["claim"], i["source_type"], i["source_ref"]) for i in items]


class AnthropicAgentBackend(AnthropicBackend):
    """One backend instance serves the whole roster; the role is passed per call."""

    def _system_for(self, role: AgentRole) -> str:
        return AGENT_SYSTEM.format(name=role.name, focus=role.focus, guidance=role.guidance)

    @staticmethod
    def _substrate_brief(records: list[dict[str, Any]]) -> str:
        """Substrate as one line per record.

        Summaries only. A finding cites a record, it does not quote it, so
        sending payloads would multiply context by corpus size for nothing.

        Deliberately *not* named `_brief`. The parent's `_brief` takes a state
        dict; naming this one the same silently overrode it, and an Adjudicator
        handed an agent backend then iterated a dict's keys as if they were
        records. Same name, incompatible argument — the subclass was not
        substitutable for its parent, and nothing caught it until a live run.
        """
        return "\n".join(f"{r['ref']}  [{r['type']}]  {r['summary']}" for r in records)

    # ---- §13.1 ---------------------------------------------------------

    def gather(self, role: AgentRole, substrate: list[dict[str, Any]],
               state: dict[str, Any]) -> list[Finding]:
        data = self._ask(
            "These are the measured facts available to you. Propose findings that follow "
            "from them and that matter, each citing at least one record by its ref. "
            "Propose nothing if nothing in your area warrants it.\n\n"
            "SUBSTRATE\n" + self._substrate_brief(substrate),
            FINDINGS_SCHEMA, system=self._system_for(role))
        return [
            Finding(domain=f["domain"], title=f["title"], severity=f["severity"],
                    rationale=f["rationale"], evidence=_refs(f["evidence"]))
            for f in data.get("findings", [])
        ]

    # ---- §13.3 ---------------------------------------------------------

    def evaluate(self, role: AgentRole, substrate: list[dict[str, Any]],
                 state: dict[str, Any]) -> list[Assessment]:
        issues = [
            {"id": i["id"], "title": i["title"], "status": i["status"],
             "severity": i.get("severity"),
             "evidence": [{"id": e["id"], "claim": e["claim"], "source": e["source"],
                           "verified": e.get("verified")}
                          for e in (i.get("evidence") or [])]}
            for i in state.get("issues", []) or []
        ]
        data = self._ask(
            "Assess each issue from your perspective. Confirm only what its evidence "
            "supports, contest anything that outruns its evidence, abstain where you "
            "have no view. Contesting forces adjudication and blocks the consensus "
            "phase from closing, so use it when warranted and not otherwise.\n\n"
            f"ISSUES\n{json.dumps(issues, indent=1)}\n\n"
            "SUBSTRATE\n" + self._substrate_brief(substrate),
            ASSESSMENT_SCHEMA, system=self._system_for(role))
        return [
            Assessment(issue_id=a["issue_id"], position=a["position"],
                       rationale=a["rationale"],
                       added_evidence=_refs(a.get("added_evidence", [])))
            for a in data.get("assessments", [])
        ]

    # ---- §13.4 ---------------------------------------------------------

    def vote(self, role: AgentRole, subject: str, state: dict[str, Any]) -> str:
        data = self._ask(
            f"Cast your vote on: {subject}\n\n"
            "Consensus is not evidence. Do not vote to confirm an issue whose evidence "
            "is unverified; a majority saying so does not make it verified.\n\n"
            f"ISSUES\n{json.dumps(state.get('issues', []), indent=1)[:6000]}",
            VOTE_SCHEMA, system=self._system_for(role))
        return data["position"]

    # ---- §13.5 ---------------------------------------------------------

    def propose_actions(self, role: AgentRole,
                        state: dict[str, Any]) -> list[ActionProposal]:
        confirmed = [i for i in state.get("issues", []) or [] if i["status"] == "confirmed"]
        if not confirmed:
            return []
        data = self._ask(
            "Propose remediation for the confirmed issues below, within your area only. "
            "Each action needs an outcome criterion someone could actually check.\n\n"
            f"CONFIRMED\n{json.dumps(confirmed, indent=1)[:6000]}",
            ACTIONS_SCHEMA, system=self._system_for(role))
        return [
            ActionProposal(description=a["description"],
                           outcome_criteria=a["outcome_criteria"],
                           addresses=a.get("addresses", []))
            for a in data.get("actions", [])
        ]
