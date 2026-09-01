# SPDX-License-Identifier: Apache-2.0
"""Analytical agents (MAREP v2.2 §4.2).

The Runtime decides what is legal and the Adjudicator decides what is
contradictory. Agents are the only component that decides what is *worth
saying*, which is why they are the only one that reads the substrate directly.

Everything they produce goes through ``Runtime.submit()``. An agent has no more
authority than the Adjudicator does: it cannot set `verified`, advance a phase,
or write outside its phase authorization, and a finding it cannot ground is
recorded unverified and refused confirmation. That is not a restriction on
agents so much as the reason it is safe to let a model write into canonical
state at all.

On the Skeptic. An earlier review of this protocol observed that at
`standard_threshold: 0.7` a lone Skeptic can never swing a vote, which is true
and made the role look decorative. The conclusion was wrong. The Skeptic's power
is not in the tally, it is in `proposed → contested`: any single agent can
contest an issue, and Phase 4 cannot exit while anything is contested (§13.4).
One dissenter therefore forces adjudication of any finding, which is more
authority than a vote share would give it. No special capability is needed, and
inventing one would have obscured a mechanism that already works.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from . import state as st
from .checks import DEFAULT_TEXT_BUDGETS
from .errors import Cause, Result, reject
from .runtime import Runtime

_ID_TAIL = re.compile(r"-(\d+)$")


# ----------------------------------------------------------------------
# what an agent produces
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceRef:
    """A claim and the substrate record that backs it.

    ``source_ref`` may be a record id or a record ref; the Runtime resolves
    either, and refs survive corpus changes that renumber ids.
    """

    claim: str
    source_type: str
    source_ref: str


@dataclass(frozen=True)
class Finding:
    """A proposed issue. ``domain`` becomes the identifier prefix."""

    domain: str
    title: str
    severity: str
    evidence: list[EvidenceRef]
    rationale: str = ""


@dataclass(frozen=True)
class Assessment:
    """An agent's position on an existing issue, with any evidence it adds."""

    issue_id: str
    position: str                      # confirm | contest | abstain
    rationale: str = ""
    added_evidence: list[EvidenceRef] = field(default_factory=list)


@dataclass(frozen=True)
class ActionProposal:
    description: str
    outcome_criteria: str
    addresses: list[str]
    owner: str | None = None


@dataclass(frozen=True)
class AgentRole:
    """A perspective. §4 forbids two agents covering the same ground."""

    name: str
    focus: str
    guidance: str
    substrate_types: tuple[str, ...] = ("metric", "document", "commit")


#: The roster for an ontology retrospective. The spec's default roster
#: (@Developer, @QA, @DeliveryManager) is shaped for a software sprint and
#: would have three agents reading the same metrics with no distinct lens.
ONTOLOGY_ROSTER: tuple[AgentRole, ...] = (
    AgentRole(
        "Realist", "BFO conformance and categorial correctness",
        "Look for category errors: a disposition modelled as a process, a quality "
        "inhering in something that cannot bear it, a class defined by our epistemic "
        "access rather than by what it is. Unsatisfiability and punning are yours. "
        "Do not report naming or documentation problems; another agent has those.",
        ("metric", "document"),
    ),
    AgentRole(
        "Lexicographer", "labels, definitions, and naming",
        "Look for missing or circular definitions, definitions that merely restate the "
        "label, inconsistent naming conventions, and altLabels that contradict the "
        "class they sit on. Say nothing about logical structure or IRIs.",
        ("metric", "document"),
    ),
    AgentRole(
        "Interoperability", "IRIs, imports, namespaces, and mappings",
        "Look for dangling references, namespace drift between modules, imports that "
        "cannot resolve, and skos mappings asserting more than the evidence supports. "
        "Structure and wording belong to others.",
        ("metric", "document"),
    ),
    AgentRole(
        "Corpus", "file-level health of the collection",
        "Look at the corpus as a set of files: what parses, what duplicates what, what "
        "nothing imports, where scale is lopsided. You are the only agent who sees the "
        "collection rather than the content.",
        ("metric", "document", "commit"),
    ),
    AgentRole(
        "Skeptic", "whether the others have earned their conclusions",
        "You are not a fifth topic. Read what the others proposed and ask whether each "
        "finding is supported by the evidence attached to it, or merely restates a "
        "metric without interpreting it. Contest anything that outruns its evidence. "
        "Contesting is your real power: one contest forces adjudication.",
        ("metric", "document"),
    ),
)


#: Run 2's roster. A different question from Run 1's, and so a different
#: division of labour.
#:
#: Run 1 asked whether the corpus was sound and found it largely was, then the
#: reasoner survey found that four of seven groups could not have been found
#: otherwise: 143,717 triples with no disjointness, cardinality, functionality
#: or complement anywhere in them. A corpus that cannot be found inconsistent
#: is not thereby correct. It is unconstrained.
#:
#: So these roles are cut by *where a constraint belongs* rather than by
#: subject matter, because that is the judgement being asked for. The
#: Formalist and the Validator will often want the same rule and disagree
#: about which language it belongs in, and that disagreement is the point:
#: OWL's open-world reading makes most data-quality rules silently vacuous as
#: axioms, and the corpus has no way to record that distinction today.
#:
#: The Restraint role exists because "leave this open" is a real answer and an
#: unpopular one. Without an agent whose standing is measured by defending
#: absences, a roster asked to find missing constraints will find missing
#: constraints, and folk value vocabularies are meant to overlap.
CONSTRAINT_ROSTER: tuple[AgentRole, ...] = (
    AgentRole(
        "Formalist", "constraints that belong in OWL",
        "Propose axioms whose job is to license entailment or expose a "
        "contradiction: disjointness between siblings that genuinely cannot "
        "overlap, domain and range where the property is not polymorphic, "
        "inverses, functionality, equivalences that would let a reasoner "
        "derive a classification nobody stated. For each, say what a reasoner "
        "could newly derive or detect if it were added. If the answer is "
        "'nothing, but it documents intent', it is not your finding - it "
        "belongs to the Validator or to Restraint. Cite the metric showing "
        "the axiom is absent.",
        ("metric", "document"),
    ),
    AgentRole(
        "Validator", "constraints that belong in SHACL",
        "Propose shapes for rules that should make a dataset invalid without "
        "making the ontology inconsistent: required fields, cardinality on "
        "annotation data, datatype conformance, value patterns, a trigger "
        "statement that must carry a source. Remember why these are not OWL: "
        "under an open-world reading a missing value is unknown rather than "
        "wrong, so most of these are silently vacuous as axioms. The corpus "
        "offers 14 focus nodes across 6 of 165 files, so say which populated "
        "classes your shapes would newly reach and how many instances that is.",
        ("metric", "document"),
    ),
    AgentRole(
        "Restraint", "what should stay unconstrained, and why",
        "Argue the negative case, and understand that it is a finding rather "
        "than an objection. Folk value vocabularies are built to overlap: "
        "Kindness and Generosity share instances, and declaring them disjoint "
        "would encode a claim the domain does not make. Look for proposals "
        "that would make the corpus assert more than its authors know, that "
        "would break a legitimate use, or that impose a closed reading on an "
        "open vocabulary. Where an absence looks deliberate, say what evidence "
        "makes it look deliberate. Contest proposals that would harm the "
        "corpus if adopted.",
        ("metric", "document"),
    ),
    AgentRole(
        "Grounding", "what the constraints would attach to",
        "You cover the ground the other three stand on. 2,269 classes reach no "
        "upper ontology at all; vale2024 declares 1,840 object properties with "
        "no domain, range or characteristic on any of them; thats-all-folks "
        "uses 21 predicates the corpus never declares. Ask which of these are "
        "prerequisites: a domain axiom on an undeclared property is not a "
        "constraint, it is a declaration. Say what must exist before any of "
        "the other three roles' proposals can be stated at all.",
        ("metric", "document"),
    ),
    AgentRole(
        "Skeptic", "whether the others have earned their conclusions",
        "You are not a fifth topic. Read what the others proposed and ask "
        "whether each finding is supported by its evidence or merely restates "
        "a metric. Watch for the specific failure this corpus invites: a count "
        "of absences read as a count of defects. 'Sibling sets without "
        "disjointness: 49 of 49' is not 49 missing axioms unless someone "
        "argues it is. Contest anything that outruns its evidence. Contesting "
        "is your real power: one contest forces adjudication.",
        ("metric", "document"),
    ),
)


#: Run 3's roster. The question is what this corpus already commits to in its
#: naming, file layout, mapping targets and documentation, without saying so
#: anywhere a machine could check.
#:
#: Cut by *where the commitment is hiding* rather than by artefact type,
#: because that is what makes a commitment invisible. A term whose meaning
#: rests on its label, a definition whose owner is settled by which file it
#: sits in, and a mapping whose direction determines whether it is defensible
#: are three different failures, and an agent looking for one will not see the
#: others.
#:
#: Two facts shape the briefs. Run 1 reported on all three areas by reading
#: files that did not parse, and undercounted: it says three terms take a
#: French gloss where the loadable graph holds 889 French Wiktionary triggers.
#: And `vcvf:triggers` carries 38,710 statements while declaring
#: `rdfs:domain owl:Thing` and `rdfs:range vcvf:Value` but no definition. The
#: brief given to Run 3 said it had no domain and no range, which was false and
#: came back as verified evidence on three findings; corrected here.
COMMITMENT_ROSTER: tuple[AgentRole, ...] = (
    AgentRole(
        "Lexicon", "meaning that rests on a name",
        "Find terms whose sense is carried by their label, their gloss or "
        "their neighbours rather than by anything asserted. Near-synonym "
        "families with no definition separating them; classes glossed against "
        "the proper-name sense of a word rather than the value sense; "
        "vocabulary split across language editions with nothing recording "
        "which lexicon governs. Say for each what the corpus would have to "
        "state for the distinction to survive someone who was not there when "
        "it was written. Cite the definition-coverage and language metrics.",
        ("metric", "document", "note"),
    ),
    AgentRole(
        "Identity", "who owns an IRI and who may define it",
        "Two commitments, both currently made by layout. Which namespace mints "
        "a term, and therefore who is responsible for defining it. And which "
        "file owns a definition when several declare the same class - 378 IRIs "
        "are declared across group boundaries, which is the live question; the "
        "larger 2,240 figure is mostly parameter variants of one ontology and "
        "is not. The corpus also asserts about 43,616 resources in namespaces "
        "it does not control. That is legitimate for a trigger layer and still "
        "a commitment about identity. Say which of these need a stated rule.",
        ("metric", "document", "note"),
    ),
    AgentRole(
        "Alignment", "what the external mappings actually claim",
        "The alignment layer is measurable for the first time: 38,710 "
        "vcvf:triggers statements across 12 hosts. Direction matters and Run 1 "
        "got it wrong. The corpus states <external> triggers <value>, so a "
        "film title in subject position claims the page evokes the value - a "
        "lexical-trigger claim, not an equivalence. Check what the mappings "
        "commit to, whether the predicate can bear it given that its declared "
        "range already entails Value membership for every object while its "
        "meaning is defined nowhere, and whether different hosts are being "
        "used for different purposes under one relation.",
        ("metric", "document", "note"),
    ),
    AgentRole(
        "Validation", "which commitments belong in SHACL",
        "Not a measurement exercise. The reconciliation of VALIDATION-001 "
        "showed repairing 127 files moved SHACL violations from 0 to 0, "
        "because the shapes load 6 of 165 files and target classes the folk "
        "corpus never instantiates. So the question is not coverage but "
        "subject: given what the other three roles surface as an unstated "
        "commitment, which of those should become a shape, and over which "
        "focus nodes. A commitment that cannot be violated by any instance in "
        "this corpus does not belong in SHACL, and saying so is a finding.",
        ("metric", "document", "note"),
    ),
    AgentRole(
        "Skeptic", "whether the others have earned their conclusions",
        "Two hazards specific to this run. First, the Run 1 findings enter as "
        "notes, which are exactly as trustworthy as whoever wrote them, and "
        "several are already reconciled as superseded or refuted - a finding "
        "that restates a note without testing it against a metric has earned "
        "nothing. Second, a naming or mapping irregularity is not automatically "
        "a defect: a French gloss may be correct for a term borrowed from "
        "French. Contest anything that outruns its evidence.",
        ("metric", "document", "note"),
    ),
)


# ----------------------------------------------------------------------
# backend protocol
# ----------------------------------------------------------------------

@runtime_checkable
class AgentBackend(Protocol):
    """Where an agent's judgement happens. The only place a model may sit."""

    def gather(self, role: AgentRole, substrate: list[dict[str, Any]],
               state: dict[str, Any]) -> list[Finding]: ...

    def evaluate(self, role: AgentRole, substrate: list[dict[str, Any]],
                 state: dict[str, Any]) -> list[Assessment]: ...

    def vote(self, role: AgentRole, subject: str,
             state: dict[str, Any]) -> str: ...

    def propose_actions(self, role: AgentRole,
                        state: dict[str, Any]) -> list[ActionProposal]: ...


class ScriptedAgentBackend:
    """Deterministic backend. Lets the whole roster run with no API key."""

    def __init__(self, findings=None, assessments=None, votes=None, actions=None,
                 fail_with: Exception | None = None):
        self._findings = findings or {}
        self._assessments = assessments or {}
        self._votes = votes or {}
        self._actions = actions or {}
        self._fail_with = fail_with
        self.calls: list[str] = []

    def _record(self, what: str) -> None:
        self.calls.append(what)
        if self._fail_with is not None:
            raise self._fail_with

    def gather(self, role, substrate, state):
        self._record(f"gather:{role.name}"); return list(self._findings.get(role.name, []))

    def evaluate(self, role, substrate, state):
        self._record(f"evaluate:{role.name}"); return list(self._assessments.get(role.name, []))

    def vote(self, role, subject, state):
        self._record(f"vote:{role.name}"); return self._votes.get(role.name, "abstain")

    def propose_actions(self, role, state):
        self._record(f"actions:{role.name}"); return list(self._actions.get(role.name, []))


class SilentAgentBackend:
    """Proposes nothing. An agent with nothing to say still has to say so (§13.1)."""

    def gather(self, role, substrate, state): return []
    def evaluate(self, role, substrate, state): return []
    def vote(self, role, subject, state): return "abstain"
    def propose_actions(self, role, state): return []


# ----------------------------------------------------------------------
# the agent
# ----------------------------------------------------------------------

class Agent:
    """Turns one perspective's judgement into updates the Runtime validates."""

    def __init__(self, runtime: Runtime, role: AgentRole, backend: AgentBackend):
        self.rt = runtime
        self.role = role
        self.backend = backend
        self._seq = 0

    @property
    def name(self) -> str:
        return self.role.name

    # ---- plumbing ----------------------------------------------------

    def _update_id(self, kind: str) -> str:
        self._seq += 1
        return f"{self.name}-{kind}-{self._seq:04d}"

    def _submit(self, kind: str, body: dict[str, Any], *, tokens: int = 0) -> Result:
        body = {"update_id": self._update_id(kind), "base_version": self.rt.version, **body}
        return self.rt.submit(body, self.name, tokens=tokens)

    def ask(self, method: str, *args: Any) -> tuple[Any, Result | None]:
        """Call the backend with §19.5 protection. Check ``err is not None``."""
        try:
            return getattr(self.backend, method)(self.role, *args), None
        except Exception as exc:
            return None, reject(Cause.ADJUDICATOR_UNAVAILABLE,
                                f"agent backend failed for {self.name}: {exc}",
                                version=self.rt.version)

    def substrate_view(self, limit: int | None = None) -> list[dict[str, Any]]:
        """The records this role is allowed to reason from (§14.1).

        Summaries only. Full payloads would multiply the context by the size of
        the corpus for no gain: a finding cites a record, it does not quote it.
        """
        recs = [
            {"id": r.id, "type": r.type, "ref": r.ref, "summary": r.summary}
            for r in self.rt.substrate._records.values()
            if r.type in self.role.substrate_types
        ]
        recs.sort(key=lambda r: (r["type"], r["ref"]))
        return recs[:limit] if limit else recs

    def _mint_issue_id(self, domain: str) -> str:
        """Next free identifier in a domain.

        Minted against live state rather than counted locally, so two agents
        proposing in the same domain in parallel do not collide: the loser of
        the CAS race re-mints on rebase.
        """
        domain = re.sub(r"[^A-Z0-9]", "", domain.upper()) or "GEN"
        used = {i["id"] for i in self.rt.state.get("issues", []) or []}
        n = 1
        while f"{domain}-{n:03d}" in used:
            n += 1
        return f"{domain}-{n:03d}"

    def _mint_evidence_ids(self, existing: set[str], count: int) -> list[str]:
        out, n = [], 1
        while len(out) < count:
            candidate = f"EV-{n:03d}"
            if candidate not in existing:
                out.append(candidate)
                existing.add(candidate)
            n += 1
        return out

    def _fit(self, text: str, key: str) -> str:
        limit = {**DEFAULT_TEXT_BUDGETS, **self.rt.text_budgets}.get(key)
        if limit is None or len(text) <= limit:
            return text
        return text[: limit - 10].rstrip() + " [clipped]"

    # ---- §13.1 gathering ---------------------------------------------

    def gather(self, *, tokens: int = 0, findings: list[Finding] | None = None) -> list[Result]:
        """Propose findings, or record a declination if there are none."""
        if findings is None:
            findings, err = self.ask("gather", self.substrate_view(),
                                     self.rt.read(self.name))
            if err is not None:
                return [err]

        if not findings:
            return [self.decline("nothing to report from this perspective")]

        results = []
        for f in findings:
            issue_id = self._mint_issue_id(f.domain)
            ev_ids = self._mint_evidence_ids(set(), len(f.evidence))
            results.append(self._submit("gather", {"issues": [{
                "id": issue_id,
                "title": self._fit(f.title, "issue.title"),
                "severity": f.severity,
                "status": "proposed",
                "evidence": [{
                    "id": eid,
                    "claim": self._fit(e.claim, "evidence.claim"),
                    "source": {"type": e.source_type, "ref": e.source_ref},
                    "submitted_by": self.name,
                } for eid, e in zip(ev_ids, f.evidence)],
            }]}, tokens=tokens))
        return results

    def decline(self, reason: str = "nothing to report") -> Result:
        """§13.1 — an agent with nothing to say must still say so, or block the phase."""
        n = len(self.rt.state.get("decisions", []) or []) + 1
        return self._submit("decline", {"decisions": [{
            "id": f"DEC-{n:03d}", "type": "declination",
            "subject": f"AGENT:{self.name}", "outcome": "declined",
            "rationale": self._fit(reason, "decision.rationale"), "basis": self.name,
        }]})

    # ---- §13.3 analysis ----------------------------------------------

    def evaluate(self, *, tokens: int = 0,
                 assessments: list[Assessment] | None = None) -> list[Result]:
        """Confirm or contest existing issues, attaching any new evidence."""
        if assessments is None:
            assessments, err = self.ask("evaluate", self.substrate_view(),
                                        self.rt.read(self.name))
            if err is not None:
                return [err]

        results = []
        by_id = st.issues_by_id(self.rt.state)
        for a in assessments:
            issue = by_id.get(a.issue_id)
            if issue is None:
                results.append(reject(Cause.SCHEMA_VIOLATION,
                                      f"{self.name} assessed an issue that does not exist: "
                                      f"{a.issue_id}", version=self.rt.version))
                continue
            if a.position == "abstain":
                continue

            patch: dict[str, Any] = {"id": a.issue_id}
            if a.added_evidence:
                existing = {e["id"] for e in issue.get("evidence", []) or []}
                ev_ids = self._mint_evidence_ids(set(existing), len(a.added_evidence))
                patch["evidence"] = [{
                    "id": eid, "claim": self._fit(e.claim, "evidence.claim"),
                    "source": {"type": e.source_type, "ref": e.source_ref},
                    "submitted_by": self.name,
                } for eid, e in zip(ev_ids, a.added_evidence)]

            if a.position == "confirm":
                patch["confirmed_by"] = [self.name]
                # Only propose the status change when the gate can pass. An
                # agent confirming an ungrounded issue is refused outright, and
                # the endorsement is lost with it.
                grounded = any(e.get("verified") for e in issue.get("evidence", []) or [])
                if grounded and issue["status"] in ("proposed", "contested"):
                    patch["status"] = "confirmed"
            elif a.position == "contest":
                patch["contested_by"] = [self.name]
                if issue["status"] == "proposed":
                    patch["status"] = "contested"

            body: dict[str, Any] = {"issues": [patch]}
            if a.position == "contest" and a.rationale:
                body["conflict_record"] = [{
                    "issue_id": a.issue_id,
                    "positions": [{
                        "agent": self.name,
                        "claim": self._fit(a.rationale, "conflict_record.positions.claim"),
                        "evidence": [e["id"] for e in patch.get("evidence", [])],
                    }],
                }]
            results.append(self._submit("evaluate", body, tokens=tokens))
        return results

    # ---- §13.4 consensus ---------------------------------------------

    def cast_votes(self, *, tokens: int = 0) -> list[Result]:
        results = []
        for vote in self.rt.state.get("votes", []) or []:
            if vote.get("outcome") != "open":
                continue
            if any(c["agent"] == self.name for c in vote.get("cast", []) or []):
                continue
            position, err = self.ask("vote", vote["subject"], self.rt.read(self.name))
            if err is not None:
                results.append(err)
                continue
            if position not in ("confirm", "reject", "abstain"):
                position = "abstain"
            results.append(self._submit("vote", {"votes": [{
                **vote, "cast": list(vote.get("cast", []) or []) +
                                [{"agent": self.name, "position": position}],
            }]}, tokens=tokens))
        return results

    # ---- §13.5 actions -----------------------------------------------

    def propose_actions(self, *, tokens: int = 0) -> list[Result]:
        proposals, err = self.ask("propose_actions", self.rt.read(self.name))
        if err is not None:
            return [err]
        results = []
        for n, p in enumerate(proposals, start=1):
            existing = {a["id"] for a in self.rt.state.get("actions", []) or []}
            k = 1
            while f"ACT-{k:03d}" in existing:
                k += 1
            results.append(self._submit("action", {"actions": [{
                "id": f"ACT-{k:03d}",
                "description": self._fit(p.description, "action.description"),
                "owner": p.owner or self.name,
                "status": "proposed",
                "outcome_criteria": self._fit(p.outcome_criteria, "action.outcome_criteria"),
                "addresses": list(p.addresses),
            }]}, tokens=tokens))
        return results

    # ---- convenience --------------------------------------------------

    def run_for_phase(self, *, tokens: int = 0) -> list[Result]:
        phase = self.rt.phase
        if phase == "gathering":
            return self.gather(tokens=tokens)
        if phase == "analysis":
            return self.evaluate(tokens=tokens)
        if phase == "consensus":
            return self.cast_votes(tokens=tokens)
        if phase == "actions":
            return self.propose_actions(tokens=tokens)
        return []


def build_roster(runtime: Runtime, backend: AgentBackend,
                 roles: tuple[AgentRole, ...] = ONTOLOGY_ROSTER) -> list[Agent]:
    return [Agent(runtime, role, backend) for role in roles]
