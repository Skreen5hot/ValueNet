"""A citation that resolves is not evidence that the claim is true.

`resolve` answers a structural question: does this reference name a real record
of the declared type. It says nothing about the sentence wrapped around the
citation, and the gap is not theoretical.

A Run 3 agent wrote "vcvf:triggers declares no domain, no range and no
definition" citing `trigger_statements:thats-all-folks`, a record that counts
statements and mentions neither domain nor range. The claim was false — the
predicate declares both, at ValueCore.ttl:97 — and it was marked `verified`
because the reference resolved. It came back as verified evidence on three
findings. The premise had come from an agent brief I wrote, so a mistake in
the framing was laundered into grounded evidence.

The general problem needs to understand the sentence. This narrows it: a
metric exists to assert a figure, so a claim drawing on a metric quotes the
figure. Over Run 3's 228 resolving items that leaves 194 supported, 6 quoting
figures the record does not carry, and 28 — including the laundered claim —
resting on a reference and nothing checkable.
"""

from __future__ import annotations

import pytest
import yaml
from _support import SUBSTRATE_DOC

from marep import Substrate


@pytest.fixture
def sub(tmp_path):
    doc = dict(SUBSTRATE_DOC)
    doc["records"] = list(doc["records"]) + [{
        "id": "M-001", "type": "metric", "ref": "widgets:corpus",
        "timestamp": "2026-08-14T16:00:00Z",
        "summary": "widgets for corpus: 38714",
        "payload": {"check": "widgets", "scope": "corpus", "value": 38714,
                    "detail": "of 41000 examined"},
    }]
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return Substrate.load(p)


METRIC = {"type": "metric", "ref": "widgets:corpus"}


# ======================================================================
# the failure this exists for
# ======================================================================

def test_a_claim_quoting_none_of_the_metric_is_not_supported(sub):
    """The laundered claim, in miniature.

    The record counts things. The claim asserts a property of something else
    entirely and quotes no figure. It resolves, and that is all it does.
    """
    verdict, why = sub.assess(METRIC, "the predicate declares no domain and no range")
    assert verdict == "resolves_only"
    assert "quotes none of it" in why


def test_shared_words_do_not_rescue_it(sub):
    """An earlier version accepted token overlap here and let the real claim
    through on the word "declares"."""
    assert sub.assess(METRIC, "widgets are declared for the corpus")[0] == "resolves_only"


# ======================================================================
# the three other verdicts
# ======================================================================

def test_quoting_the_value_is_supported(sub):
    verdict, why = sub.assess(METRIC, "the corpus carries 38714 widgets")
    assert verdict == "supported"
    assert "38714" in why


def test_thousands_separators_are_normalised(sub):
    """A claim writes 38,714 where a payload holds 38714."""
    assert sub.assess(METRIC, "the corpus carries 38,714 widgets")[0] == "supported"


def test_a_figure_from_the_detail_counts(sub):
    """Denominators live in the detail, and citing one is citing the record."""
    assert sub.assess(METRIC, "41000 were examined")[0] == "supported"


def test_a_figure_the_record_does_not_carry_is_unsupported(sub):
    verdict, why = sub.assess(METRIC, "the corpus carries 99999 widgets")
    assert verdict == "unsupported"
    assert "99999" in why


def test_a_bad_reference_is_unresolved(sub):
    assert sub.assess({"type": "metric", "ref": "nope:nope"}, "anything")[0] == "unresolved"


def test_a_type_mismatch_is_unresolved(sub):
    """Carried over from resolve: citing a metric as a deploy is a misreading."""
    assert sub.assess({"type": "deploy", "ref": "widgets:corpus"}, "38714")[0] == "unresolved"


# ======================================================================
# non-metric records are judged differently, and deliberately
# ======================================================================

def test_a_document_claim_naming_the_record_is_supported(sub):
    """A document's content is the thing it names, not a figure.

    Applying the metric rule here would reject every legitimate claim about a
    file that happens not to quote a number.
    """
    src = {"type": "ticket", "ref": "PROJ-7781"}
    assert sub.assess(src, "PROJ-7781 reports staging/prod runtime divergence")[0] == "supported"


def test_a_vague_claim_about_a_document_is_not_supported(sub):
    src = {"type": "ticket", "ref": "PROJ-7781"}
    assert sub.assess(src, "something is wrong somewhere")[0] == "resolves_only"


# ======================================================================
# what the runtime does with the verdict
# ======================================================================

def test_runtime_records_the_verdict_and_gates_on_it(rt):
    """`verified` now means supported, and the verdict is kept for a reader."""
    from marep.errors import Cause
    r = rt.submit({
        "update_id": "U-1", "base_version": rt.version,
        "issues": [{"id": "X-001", "title": "t", "status": "proposed",
                    "severity": "high",
                    "evidence": [{"id": "EV-001", "claim": "nothing checkable here",
                                  "source": {"type": "ci_run", "ref": "gh-actions/12841"},
                                  "submitted_by": "QA"}]}]}, "QA")
    assert r.accepted, r
    ev = rt.state["issues"][0]["evidence"][0]
    assert ev["grounding"] == "resolves_only"
    assert ev["verified"] is False
    assert ev["grounding_note"]
