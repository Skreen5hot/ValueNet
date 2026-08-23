"""Command-line interface to the Runtime.

Agents in MAREP need not be Python. They submit YAML update documents and read
back a structured verdict, which is all this exposes. Every command is a thin
wrapper over :class:`marep.Runtime`; no decision logic lives here.

    python -m marep init      --sprint sprint-42 --substrate SPRINT_INPUT.yaml \\
                              --roster QA,Architect,Developer,Skeptic
    python -m marep submit    --agent QA --update update.yaml
    python -m marep status
    python -m marep advance   [--archive-unevaluated]
    python -m marep lock      --operation compression --holder Adjudicator
    python -m marep unlock    --holder Adjudicator
    python -m marep report
    python -m marep validate

Exit codes: 0 accepted, 1 rejected, 2 usage or integrity error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import state as st
from .errors import MarepError
from .runtime import Runtime
from .substrate import Substrate
from .tokens import TokenBudget
from .validate import validate_state

DEFAULT_STATE = "RETRO_STATE.yaml"
DEFAULT_SUBSTRATE = "SPRINT_INPUT.yaml"


def _load(args) -> Runtime:
    substrate = Substrate.load(args.substrate)
    doc = st.load(args.state)
    roster = [a for a in (args.roster or "").split(",") if a] or _roster_from(doc)
    return Runtime(
        doc, substrate, roster=roster, state_path=args.state,
        budget=TokenBudget(), max_reopens=args.max_reopens,
    )


def _roster_from(doc) -> list[str]:
    """Best-effort roster recovery from the audit log when none is supplied."""
    return sorted({e["agent"] for e in doc.get("audit", []) or []} - {"Runtime", "Adjudicator"})


def _resolve_common(args) -> None:
    """Let global flags be given after the subcommand as well as before."""
    if getattr(args, "roster_sub", None):
        args.roster = args.roster_sub
    if getattr(args, "json_sub", False):
        args.json = True


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        for k, v in payload.items():
            print(f"{k:24} {v}")


def cmd_init(args) -> int:
    substrate = Substrate.load(args.substrate)
    if Path(args.state).exists() and not args.force:
        print(f"{args.state} already exists; pass --force to overwrite", file=sys.stderr)
        return 2
    rt = Runtime.initialize(
        args.sprint, substrate,
        roster=[a for a in (args.roster or "").split(",") if a],
        state_path=args.state,
    )
    st.save(rt.state, args.state)
    _emit({"initialized": args.state, "sprint": args.sprint,
           "records": len(substrate), "checksum": substrate.checksum,
           "coverage_gaps": substrate.unavailable_types()}, args.json)
    return 0


def cmd_submit(args) -> int:
    rt = _load(args)
    update = yaml.safe_load(Path(args.update).read_text(encoding="utf-8"))
    result = rt.submit(update, args.agent, tokens=args.tokens)
    _emit({"accepted": result.accepted, "version": result.version,
           "cause": result.cause.value if result.cause else None,
           "detail": result.detail, "retryable": result.retryable}, args.json)
    return 0 if result.accepted else 1


def cmd_status(args) -> int:
    rt = _load(args)
    ready, unmet = rt.exit_ready()
    _emit({"sprint": rt.state["retro"]["sprint"], "phase": rt.phase,
           "version": rt.version, "issues": len(rt.state.get("issues") or []),
           "lock": (rt.state.get("turn") or {}).get("operation", "none"),
           "exit_ready": ready, "blocked_by": "; ".join(unmet) or "-"}, args.json)
    return 0


def cmd_advance(args) -> int:
    rt = _load(args)
    result = rt.advance_phase(archive_unevaluated=args.archive_unevaluated)
    _emit({"accepted": result.accepted, "phase": rt.phase, "version": rt.version,
           "cause": result.cause.value if result.cause else None,
           "detail": result.detail}, args.json)
    return 0 if result.accepted else 1


def cmd_lock(args) -> int:
    rt = _load(args)
    result = rt.acquire_lock(args.operation, args.holder, ttl_seconds=args.ttl,
                             permitted_sections=[s for s in (args.sections or "").split(",") if s])
    _emit({"accepted": result.accepted, "detail": result.detail}, args.json)
    return 0 if result.accepted else 1


def cmd_unlock(args) -> int:
    rt = _load(args)
    result = rt.release_lock(args.holder)
    _emit({"accepted": result.accepted, "detail": result.detail}, args.json)
    return 0 if result.accepted else 1


def cmd_report(args) -> int:
    rt = _load(args)
    _emit(rt.report(), True if args.json else False)
    return 0


def cmd_validate(args) -> int:
    doc = st.load(args.state)
    errors = validate_state(doc)
    substrate = Substrate.load(args.substrate)
    checksum_ok = doc["retro"].get("sprint_input_checksum") == substrate.checksum
    _emit({"schema_errors": len(errors), "first": errors[0] if errors else "-",
           "substrate_checksum_matches": checksum_ok}, args.json)
    return 0 if (not errors and checksum_ok) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="marep", description=__doc__.split("\n")[0])
    p.add_argument("--state", default=DEFAULT_STATE)
    p.add_argument("--substrate", default=DEFAULT_SUBSTRATE)
    p.add_argument("--roster", default="")
    p.add_argument("--max-reopens", type=int, default=2)
    p.add_argument("--json", action="store_true", help="machine-readable output")
    sub = p.add_subparsers(dest="command", required=True)

    q = sub.add_parser("init", help="freeze the substrate into a fresh state")
    q.add_argument("--sprint", required=True)
    q.add_argument("--force", action="store_true")
    # Accepted here as well as globally: `init --roster ...` is the form people
    # reach for, and a parser that refuses it teaches nothing useful.
    q.add_argument("--roster", dest="roster_sub", default=None)
    q.set_defaults(func=cmd_init)

    q = sub.add_parser("submit", help="submit an update document")
    q.add_argument("--json", dest="json_sub", action="store_true", default=False)
    q.add_argument("--agent", required=True)
    q.add_argument("--update", required=True)
    q.add_argument("--tokens", type=int, default=0)
    q.set_defaults(func=cmd_submit)

    sub.add_parser("status", help="phase, version, and exit readiness").set_defaults(func=cmd_status)

    q = sub.add_parser("advance", help="advance the phase if exit criteria are met")
    q.add_argument("--archive-unevaluated", action="store_true")
    q.set_defaults(func=cmd_advance)

    q = sub.add_parser("lock", help="acquire an exclusive-operation lock")
    q.add_argument("--operation", required=True,
                   choices=["phase_transition", "compression", "merge", "vote_closure", "rollback"])
    q.add_argument("--holder", required=True)
    q.add_argument("--ttl", type=int, default=300)
    q.add_argument("--sections", default="")
    q.set_defaults(func=cmd_lock)

    q = sub.add_parser("unlock", help="release a lock")
    q.add_argument("--holder", required=True)
    q.set_defaults(func=cmd_unlock)

    sub.add_parser("report", help="the figures §20 requires").set_defaults(func=cmd_report)
    sub.add_parser("validate", help="schema and checksum check").set_defaults(func=cmd_validate)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _resolve_common(args)
    try:
        return args.func(args)
    except MarepError as exc:
        print(f"integrity error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"not found: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
