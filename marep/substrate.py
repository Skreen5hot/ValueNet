# SPDX-License-Identifier: Apache-2.0
"""Sprint input substrate: freezing, checksumming, and reference resolution.

MAREP v2.2 §7. The substrate is the only admissible ground for evidence. An
evidence item is verified if and only if its ``source.ref`` resolves to a record
here (§8.3), and only the Runtime may make that determination.

This module is why the grounding gate can be mechanical: verification is a
dictionary lookup, not a judgement.
"""

from __future__ import annotations

import re

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


#: Digits with optional thousands separators, normalised so that "38,710" in a
#: claim matches "38710" in a payload.
_NUMBER_RE = re.compile(r"\d[\d,]*")

#: Words distinctive enough to be worth matching. Short tokens and the
#: vocabulary every record shares would match everything.
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{3,}")
_COMMON_TOKENS = frozenset({
    "the", "and", "that", "this", "with", "from", "have", "which", "there",
    "their", "than", "then", "them", "these", "those", "into", "over", "under",
    "corpus", "record", "metric", "value", "values", "class", "classes",
    "file", "files", "triples", "statements", "group", "groups", "declared",
})


def _numbers(text: str) -> set[str]:
    return {m.replace(",", "") for m in _NUMBER_RE.findall(text or "")}


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "")
            if t.lower() not in _COMMON_TOKENS}


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

    def assess(self, source: dict[str, Any], claim: str) -> tuple[str, str]:
        """How well a record actually supports the claim made from it (§8.3).

        `resolve` answers a structural question: does this reference name a
        real record of the declared type. It says nothing about the sentence
        wrapped around the citation, and that gap is not theoretical. A Run 3
        agent wrote "vcvf:triggers declares no domain, no range and no
        definition" against `trigger_statements:thats-all-folks`, a record that
        counts statements and mentions neither domain nor range. The claim was
        false — the predicate declares both — and it was marked `verified`,
        because the reference resolved. A false premise in an agent brief was
        laundered into verified evidence on three findings.

        This cannot be solved in general without understanding the sentence.
        It can be narrowed usefully, because a metric record asserts a number,
        and a claim that draws on a metric almost always states that number.
        Across Run 3's 228 resolving evidence items, 157 quote a figure that
        appears in the record they cite. So:

        ``supported``
            The claim quotes a number the record carries, or — for records
            with no number to quote — names something distinctive from the
            record's own reference or summary.
        ``unsupported``
            The claim quotes numbers and the record carries none of them. Six
            Run 3 items are in this position. Most turned out to be sound
            claims citing a record for a different figure, which is why this
            is reported rather than treated as a falsehood.
        ``resolves_only``
            The reference is good and nothing in the claim can be checked
            against it. This is the state the laundered claim was in, and
            naming it is most of the value: it is not evidence of anything
            except that a real record was named.
        ``unresolved``
            No such record, or the declared type is wrong.

        Returns the verdict and a short reason, both recorded on the evidence
        item so a reader can see which kind of grounding a finding rests on.
        """
        if not self.resolve(source):
            return "unresolved", "no record of that reference and type"

        rec = self.get(source.get("ref", ""))
        claim_numbers = _numbers(claim)
        record_numbers = _numbers(str((rec.payload or {}).get("value", "")))
        record_numbers |= _numbers(rec.summary or "")
        record_numbers |= _numbers(str((rec.payload or {}).get("detail", "")))

        if rec.type == "metric" and record_numbers:
            # A metric exists to assert a figure; that figure is its content,
            # so a claim drawing on it quotes the figure. Token overlap is
            # deliberately NOT accepted here — the laundered Run 3 claim shares
            # the word "declares" with its record and would pass on that alone,
            # which is exactly the standard being raised.
            #
            # Restricted to metrics on purpose. A document record carries
            # triple and class counts in its payload, but its content is the
            # file it names, so a claim naming that file is drawing on it
            # properly even with no number in sight.
            if not claim_numbers:
                return ("resolves_only",
                        "the record asserts a figure and the claim quotes none "
                        "of it, so nothing here can be checked")
            shared = claim_numbers & record_numbers
            if shared:
                return "supported", f"claim quotes {sorted(shared)[0]} from the record"
            return ("unsupported",
                    f"claim quotes {sorted(claim_numbers)[:3]} and the record "
                    f"carries none of them")

        # No figure to quote — a document, commit or note. Distinctive token
        # overlap is the only check available, and it is a weak one.
        tokens = _tokens(rec.ref) | _tokens(rec.summary or "")
        hit = tokens & _tokens(claim)
        if hit:
            return "supported", f"claim names {sorted(hit)[0]} from the record"
        return ("resolves_only",
                "the reference is good and nothing in the claim can be checked "
                "against it")

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
