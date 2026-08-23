"""Sprint input substrate: freezing, checksumming, and reference resolution.

MAREP v2.2 §7. The substrate is the only admissible ground for evidence. An
evidence item is verified if and only if its ``source.ref`` resolves to a record
here (§8.3), and only the Runtime may make that determination.

This module is why the grounding gate can be mechanical: verification is a
dictionary lookup, not a judgement.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .errors import StateCorruption
from .validate import validate_substrate

RECORD_TYPES = (
    "commit", "pull_request", "ticket", "ci_run", "deploy",
    "incident", "metric", "review", "document", "note",
)


def checksum(path: Path) -> str:
    """SHA-256 over the raw bytes of the frozen substrate (§7.1).

    Hashing bytes rather than parsed content is deliberate: a reformatting that
    preserves semantics still breaks the checksum, which is the conservative
    behaviour for a file the protocol declares immutable.
    """
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Record:
    id: str
    type: str
    ref: str
    timestamp: str
    summary: str
    uri: str | None = None
    payload: dict[str, Any] | None = None


class Substrate:
    """A frozen, read-only view of SPRINT_INPUT.yaml.

    Read-only is enforced by not offering a mutator. Nothing in the Runtime,
    and no agent including the Adjudicator, may write here (§7.1).
    """

    def __init__(self, doc: dict[str, Any], path: Path | None = None, digest: str | None = None):
        errors = validate_substrate(doc)
        if errors:
            raise StateCorruption(f"substrate failed schema validation: {errors[0]}")
        self._doc = doc
        self.path = path
        self.checksum = digest or ""
        self._records: dict[str, Record] = {}
        self._by_ref: dict[str, Record] = {}
        for r in doc.get("records", []):
            if r["id"] in self._records:
                raise StateCorruption(f"duplicate record id in substrate: {r['id']}")
            self._records[r["id"]] = Record(
                id=r["id"], type=r["type"], ref=r["ref"],
                timestamp=r["timestamp"], summary=r["summary"],
                uri=r.get("uri"), payload=r.get("payload"),
            )
            self._by_ref.setdefault(r["ref"], self._records[r["id"]])

    # ----- construction -------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> "Substrate":
        p = Path(path)
        doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        return cls(doc, path=p, digest=checksum(p))

    # ----- queries ------------------------------------------------------

    @property
    def sprint_id(self) -> str:
        return self._doc["sprint"]["id"]

    def __len__(self) -> int:
        return len(self._records)

    def __contains__(self, record_id: str) -> bool:
        return record_id in self._records

    def get(self, key: str) -> Record | None:
        """Look up by identifier, then by reference."""
        return self._records.get(key) or self._by_ref.get(key)

    def resolve(self, source: dict[str, Any]) -> bool:
        """Determine whether an evidence ``source`` verifies (§8.3).

        Accepts a record identifier or a record reference. Identifiers are
        minted positionally, so they are stable only while the corpus is
        unchanged: add one file to a directory and every later identifier
        shifts, silently breaking evidence an earlier retrospective cited.
        References are content-derived — a commit SHA, a `check:scope` pair —
        and survive that. Prefer them for anything meant to outlive one run.

        Both the key and the declared type must match. A key that resolves to a
        record of a different type is *not* verified: an agent citing a deploy
        record as a ci_run has misread its own evidence, and accepting it
        silently would let the type field decay into decoration.
        """
        key = source.get("ref", "")
        rec = self._records.get(key) or self._by_ref.get(key)
        if rec is None:
            return False
        return rec.type == source.get("type")

    def coverage(self) -> list[dict[str, Any]]:
        """Declared coverage (§7.3). Unavailable types must state a reason."""
        return list(self._doc.get("coverage", []))

    def unavailable_types(self) -> list[str]:
        return [c["type"] for c in self.coverage() if not c.get("available", True)]

    def note_only_refs(self) -> set[str]:
        """Record ids whose type is ``note`` (§7.4).

        Used by reporting to say what share of confirmed findings rest on
        material with no machine-retrievable source.
        """
        return {r.id for r in self._records.values() if r.type == "note"}

    def verify_checksum(self) -> bool:
        """Re-check the frozen file against the recorded digest (§7.1, §19.6)."""
        if self.path is None or not self.checksum:
            return True
        return checksum(self.path) == self.checksum

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(self._doc))  # defensive deep copy
