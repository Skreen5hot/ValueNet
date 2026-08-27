"""Shared fixtures, and nothing else.

Constants and helpers moved to `_support.py`. What is left is the set of
things pytest genuinely has to own: fixtures, which tests request by name and
which no import statement could supply.

The root comes from an upward search for the layout contract rather than from
`parents[1]`. This is the one file that cannot ask the resolver where the
repository is, because the answer is what makes the resolver importable in the
first place; `marep.layout.BOOTSTRAP_DOC` records the four lines and why they
are duplicated rather than imported. Counting parents happens to be right for
`tests/conftest.py` today and is wrong the moment a file at another depth
copies it -- which three tools had already done, each resolving to a directory
that exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root))

from marep import Runtime, Substrate, TokenBudget  # noqa: E402

from _support import ROSTER, SUBSTRATE_DOC  # noqa: E402


@pytest.fixture
def substrate_path(tmp_path: Path) -> Path:
    p = tmp_path / "SPRINT_INPUT.yaml"
    p.write_text(yaml.safe_dump(SUBSTRATE_DOC, sort_keys=False), encoding="utf-8")
    return p


@pytest.fixture
def substrate(substrate_path: Path) -> Substrate:
    return Substrate.load(substrate_path)


@pytest.fixture
def rt(substrate: Substrate, tmp_path: Path) -> Runtime:
    return Runtime.initialize(
        "sprint-42", substrate, roster=ROSTER,
        state_path=tmp_path / "RETRO_STATE.yaml",
        budget=TokenBudget(per_turn_context=8000, per_retrospective_total=100_000,
                           compression_reserve=20_000),
    )
