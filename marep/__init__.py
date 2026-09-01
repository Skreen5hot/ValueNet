# SPDX-License-Identifier: Apache-2.0
"""MAREP Runtime — a deterministic implementation of MAREP v2.2 §4.1.1.

The Runtime is the half of MAREP's control plane that must not be a language
model. It owns every mechanically decidable rule: schema, compare-and-swap
versioning, the status transition graph and its reopening guards, evidence
resolution against the frozen substrate, scope, the anti-pattern checks, and
phase advancement.

The Runtime calls no model, by design rather than omission: v2.2 split the
Orchestrator precisely because an LLM doing JSON Schema validation is both more
expensive and less reliable than a validator. The Adjudicator (§4.1.2) is the
other half — four judgement calls, a pluggable backend, and no privileged write
path. `marep.anthropic_backend` is the only module that imports the SDK, and
only when constructed.

Typical use::

    from marep import Runtime, Substrate

    substrate = Substrate.load("SPRINT_INPUT.yaml")
    rt = Runtime.initialize("sprint-42", substrate, roster=["QA", "Architect"])

    result = rt.submit({
        "update_id": "UPD-001",
        "base_version": 0,
        "issues": [{
            "id": "DEPLOY-002",
            "title": "Deployment instability",
            "severity": "medium",
            "status": "proposed",
            "evidence": [{
                "id": "EV-001",
                "claim": "Rollback of release 42.3 required manual intervention",
                "source": {"type": "ci_run", "ref": "CI-1204"},
                "submitted_by": "Developer",
            }],
        }],
    }, agent="Developer")

    if not result:
        print(result.cause, result.detail)
"""

from .adjudicator import (
    Adjudicator,
    AdjudicatorBackend,
    CompressionProposal,
    ContradictionFinding,
    MergeProposal,
    NullBackend,
    Position,
    ScriptedBackend,
    TieBreak,
)
from .agents import (
    COMMITMENT_ROSTER,
    CONSTRAINT_ROSTER,
    ONTOLOGY_ROSTER,
    ActionProposal,
    Agent,
    AgentBackend,
    AgentRole,
    Assessment,
    EvidenceRef,
    Finding,
    ScriptedAgentBackend,
    SilentAgentBackend,
    build_roster,
)
from .errors import Cause, MarepError, Result, StateCorruption
from .runtime import Runtime
from .substrate import Record, Substrate
from .tokens import TokenBudget
from .validate import schema_paths, validate_state, validate_substrate

__version__ = "0.1.0"
#: Version of the MAREP specification this Runtime implements.
SPEC_VERSION = "2.2"

__all__ = [
    "Runtime",
    "Adjudicator",
    "AdjudicatorBackend",
    "ScriptedBackend",
    "NullBackend",
    "ContradictionFinding",
    "Agent",
    "AgentBackend",
    "AgentRole",
    "COMMITMENT_ROSTER",
    "CONSTRAINT_ROSTER",
    "ONTOLOGY_ROSTER",
    "build_roster",
    "ScriptedAgentBackend",
    "SilentAgentBackend",
    "Finding",
    "Assessment",
    "EvidenceRef",
    "ActionProposal",
    "MergeProposal",
    "CompressionProposal",
    "TieBreak",
    "Position",
    "Substrate",
    "Record",
    "Cause",
    "Result",
    "MarepError",
    "StateCorruption",
    "TokenBudget",
    "validate_state",
    "validate_substrate",
    "schema_paths",
    "SPEC_VERSION",
    "__version__",
]
