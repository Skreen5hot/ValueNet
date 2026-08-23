"""JSON Schema validation for canonical state and substrate.

MAREP v2.2 §8.1 requires conforming implementations to publish a JSON Schema
for the full state document; §19.1 requires rejection without partial
application when an update fails validation.

Validation is a pure function over a candidate document. The Runtime validates
the *result* of applying an update, never the update in isolation, which is how
"reject without partial application" is achieved: the candidate is discarded
and the live state is never touched.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SCHEMA_DIR = Path(__file__).parent / "schemas"


@lru_cache(maxsize=None)
def _validator(name: str) -> Draft202012Validator:
    schema = json.loads((_SCHEMA_DIR / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(name: str, doc: Any) -> list[str]:
    out = []
    for err in sorted(_validator(name).iter_errors(doc), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "<root>"
        out.append(f"{where}: {err.message}")
    return out


def validate_state(doc: Any) -> list[str]:
    """Return a list of human-readable violations; empty means valid."""
    return _errors("retro_state.schema.json", doc)


def validate_substrate(doc: Any) -> list[str]:
    return _errors("sprint_input.schema.json", doc)


def schema_paths() -> dict[str, Path]:
    """Published schema locations, for implementations that need to cite them."""
    return {
        "retro_state": _SCHEMA_DIR / "retro_state.schema.json",
        "sprint_input": _SCHEMA_DIR / "sprint_input.schema.json",
    }
