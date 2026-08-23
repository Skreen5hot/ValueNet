"""MAREP Runtime — a deterministic implementation of MAREP v2.2 §4.1.1.

The Runtime is the half of MAREP's control plane that must not be a language
model. It owns every mechanically decidable rule: schema, compare-and-swap
versioning, the status transition graph and its reopening guards, evidence
resolution against the frozen substrate, scope, the anti-pattern checks, and
phase advancement.

Nothing here calls a model. That is the design, not an omission: v2.2 split the
Orchestrator precisely because an LLM doing JSON Schema validation is both more
expensive and less reliable than a validator.

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
