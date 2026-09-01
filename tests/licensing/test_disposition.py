# SPDX-License-Identifier: Apache-2.0
"""Every tracked file has exactly one licensing disposition.

"Exactly one" is the whole property. Zero means a file arrived and nobody
said what may be done with it. Two means the answer depends on which rule
was written first, which is not an answer.

The disposition is derived from provenance the repository already holds
and audited before this work existed, so the question "may I reuse this
file?" is one a reader can check rather than trust.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess

import pytest

from marep import layout

REPO = layout.repository_root()


def _module():
    path = REPO / "tools/licensing/disposition.py"
    spec = importlib.util.spec_from_file_location("disposition", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


D = _module()


#: Computed once, at import, the way the other suites in this
#: repository bind their evidence. A module-scoped fixture collided
#: with the function-scoped monkeypatch in the refusal test below.
ROWS = D.classify()


def test_every_tracked_file_has_exactly_one_disposition():
    """`classify` raises if any file matches zero or two rules, so reaching
    here at all is most of the assertion. The rest is that it covered
    everything git tracks, rather than quietly returning a subset."""
    tracked = set(subprocess.run(
        ["git", "ls-files"], cwd=str(REPO),
        capture_output=True, text=True).stdout.splitlines())
    classified = {r.path for r in ROWS}
    assert classified == tracked, (
        "classified and tracked sets differ: %s"
        % sorted(tracked ^ classified)[:8])
    assert len(ROWS) == len(classified), "a path was classified twice"


def test_no_file_matches_two_rules():
    """Checked directly rather than inferred from classify() not raising.

    A later rule that overlapped an existing one would otherwise be caught
    only by whichever file happened to trigger it.
    """
    for row in ROWS:
        matched = D.rules(row.path, row.origin)
        assert len(matched) == 1, (
            "%s matches %d rules: %s"
            % (row.path, len(matched), [m[0] for m in matched]))


def test_a_file_matching_no_rule_is_refused():
    """The failure mode that produced this design.

    Two root dotfiles matched nothing when the classifier was first run,
    and it refused rather than defaulting. Defaulting is how a file with
    unknown terms acquires a licence nobody chose.
    """
    assert D.rules("nowhere/mystery.bin", "fork") == []


def test_an_unknown_origin_yields_no_disposition():
    """A provenance value nothing maps to must not fall through to a
    project licence."""
    assert D.rules("some/file.ttl", "origin-that-does-not-exist") == []


def test_upstream_material_is_never_given_a_project_licence():
    """The load-bearing safety property, with one adjudicated exception.

    Original ValueNet material has no identified licence. Classifying any
    of it as project content would relicense somebody else's work by
    omission -- the opposite of the permissive intent behind the project
    licences.

    Exactly one file descended from upstream carries a project licence,
    and only because the owner ruled on it by name. Everything else stays
    unresolved.
    """
    adjudicated = set(D.ADJUDICATIONS)
    leaked = [r.path for r in ROWS
              if r.origin == "upstream-valuenet"
              and r.disposition in (D.CONTENT, D.SOFTWARE)
              and r.path not in adjudicated]
    assert not leaked, (
        "upstream material relicensed under project terms without an "
        "adjudication: " + str(leaked[:8]))

    for row in ROWS:
        if row.origin == "upstream-valuenet" and row.path not in adjudicated:
            assert row.licence is None, row.path
            assert row.disposition == D.EXCLUDED, row.path


def test_the_adjudication_applies_to_exactly_one_file():
    """The exception must not generalize.

    A similarity threshold would have applied itself to files nobody
    ruled on. The adjudication table names one file, and this requires it
    to stay that way -- and requires the file it names to be the one the
    ruling was about.
    """
    assert set(D.ADJUDICATIONS) == {"README.md"}, sorted(D.ADJUDICATIONS)

    disposition, licence, why = D.ADJUDICATIONS["README.md"]
    assert disposition == D.CONTENT and licence == "CC-BY-4.0"
    assert "39a8001" in why, (
        "an adjudication has to name the evidence it rests on; a ruling "
        "with no cited commit is an assertion")

    row = next(r for r in ROWS if r.path == "README.md")
    assert row.disposition == D.CONTENT and row.licence == "CC-BY-4.0"
    assert row.origin == "upstream-valuenet", (
        "the historical provenance must be preserved, not rewritten to "
        "match the ruling")


def test_the_folk_fragments_did_not_inherit_the_exception():
    """Named explicitly, because they are what a threshold rule would have
    swept up.

    They descend from upstream and were locally repaired, so a rule keyed
    on "has been modified here" would relicense them. They retain most of
    their upstream text and remain unresolved.
    """
    folk = [r for r in ROWS if r.path.startswith("ThatsAllFolks/folk_")]
    assert len(folk) > 50, "the folk fragments are not being examined at all"
    for row in folk:
        assert row.disposition == D.EXCLUDED, row.path
        assert row.licence is None, row.path


def test_every_upstream_file_but_one_is_excluded():
    """Counted, so the exception cannot quietly acquire company."""
    upstream = [r for r in ROWS if r.origin == "upstream-valuenet"]
    excluded = [r for r in upstream if r.disposition == D.EXCLUDED]
    assert len(upstream) - len(excluded) == 1, (
        "%d upstream file(s) are not excluded; exactly one adjudication "
        "exists" % (len(upstream) - len(excluded)))


def test_third_party_material_keeps_its_own_licence():
    """BFO and CCO are redistributed, not relicensed."""
    seen = {}
    for row in ROWS:
        if row.disposition == D.THIRD_PARTY:
            seen.setdefault(row.origin, set()).add(row.licence)
    assert seen, "no third-party material was classified at all"
    assert seen.get("external-bfo") == {"CC-BY-4.0"}
    assert seen.get("external-cco") == {"BSD-3-Clause"}


def test_every_declared_licence_has_its_full_text():
    """A licence named with no text is a reference to nothing."""
    named = {r.licence for r in ROWS if r.licence}
    assert named, "nothing carries a licence"
    for licence in sorted(named):
        path = REPO / "LICENSES" / (licence + ".txt")
        assert path.is_file(), "no full text for " + licence
        assert path.stat().st_size > 1000, licence + " text looks truncated"


def test_the_licence_texts_are_the_ones_they_claim_to_be():
    """Fetched verbatim, so a summary cannot sit where an
    instrument should."""
    markers = {
        "Apache-2.0.txt": "Apache License",
        "CC-BY-4.0.txt": "Creative Commons Attribution 4.0 International",
        "BSD-3-Clause.txt": "Redistribution and use in source and binary",
    }
    for name, marker in markers.items():
        text = (REPO / "LICENSES" / name).read_text(encoding="utf-8")
        assert marker in text, name + " does not contain its own text"


def test_no_licence_text_is_an_unfilled_template():
    """The check the first version of this file did not make.

    BSD-3-Clause was shipped as the SPDX *template*, reading
    "Copyright (c) <year> <owner>", and the only assertion on it was that
    it contained the phrase every BSD variant contains. A template passed
    a test for a licence, because the test asked a question the template
    answers.

    A copyright line with an unfilled placeholder names no holder, so the
    notice grants nothing traceable. Apache's placeholders are excluded
    deliberately: they sit in its "How to apply" appendix and are part of
    the canonical instrument rather than a blank nobody completed.
    """
    placeholders = ("<year>", "<owner>", "<copyright holder>", "<name>",
                    "[year]", "[yyyy]", "[name of copyright owner]",
                    "[fullname]", "[copyright holder]")
    for path in sorted((REPO / "LICENSES").glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        instrument = text.split("APPENDIX:")[0]
        for line in instrument.splitlines():
            if not line.strip().lower().startswith("copyright"):
                continue
            found = [ph for ph in placeholders if ph in line.lower()]
            assert not found, (
                path.name + " has an unfilled copyright placeholder "
                + str(found) + " on: " + line.strip())


def test_the_bsd_text_is_the_pinned_ccos_own_notice():
    """Not a generic BSD-3-Clause.

    The clause text is identical across every BSD-3-Clause work; the
    copyright line is what makes this notice CCO's. The extract's
    manifest points at the v2.2 LICENSE, and this is that file."""
    text = (REPO / "LICENSES/BSD-3-Clause.txt").read_text(encoding="utf-8")
    assert "Copyright (c) 2017, CUBRC, INC" in text, (
        "the BSD notice does not name CUBRC, the copyright holder CCO declares")
    manifest = json.loads((REPO /
        "ontology/bfo/vendor/cco/cco-valuenet-extract.manifest.json"
        ).read_text(encoding="utf-8"))
    assert manifest["license"]["spdx"] == "BSD-3-Clause"
    assert "v2.2" in manifest["license"]["url"]


def test_no_licence_text_carries_trailing_whitespace():
    """Reproduced instruments are reproduced exactly."""
    for path in sorted((REPO / "LICENSES").glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        offenders = [i + 1 for i, line in enumerate(text.splitlines())
                     if line != line.rstrip()]
        assert not offenders, (
            path.name + " has trailing whitespace on line(s) "
            + str(offenders[:5]))

def test_project_software_carries_an_spdx_identifier():
    """A file has to say what it is without a reader consulting a table."""
    missing = []
    for row in ROWS:
        if row.disposition != D.SOFTWARE or not row.path.endswith(".py"):
            continue
        head = (REPO / row.path).read_text(encoding="utf-8",
                                           errors="replace")[:400]
        if "SPDX-License-Identifier: Apache-2.0" not in head:
            missing.append(row.path)
    assert not missing, (
        "%d project-authored Python file(s) carry no SPDX identifier: %s"
        % (len(missing), missing[:8]))


def test_no_excluded_file_was_given_an_spdx_identifier():
    """The inverse. Stamping Apache-2.0 onto upstream material would assert
    a grant this repository cannot make."""
    stamped = []
    for row in ROWS:
        if row.disposition != D.EXCLUDED or not row.path.endswith(".py"):
            continue
        head = (REPO / row.path).read_text(encoding="utf-8",
                                           errors="replace")[:400]
        if "SPDX-License-Identifier" in head:
            stamped.append(row.path)
    assert not stamped, stamped


def test_the_governance_files_exist_and_cross_reference():
    """The root notice, the third-party notices, and the citation record
    have to agree with each other and with the tool."""
    licence = (REPO / "LICENSE").read_text(encoding="utf-8")
    notices = (REPO / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    citation = (REPO / "CITATION.cff").read_text(encoding="utf-8")

    assert "CC-BY-4.0" in licence and "Apache-2.0" in licence
    assert "tools/licensing/disposition.py" in licence, (
        "the notice must point at the tool that derives the answer")
    assert "no rights are granted" in licence.lower()
    assert "not identified" in notices.lower()
    assert "BSD-3-Clause" in notices and "CC BY 4.0" in notices
    assert "cff-version" in citation and "CC-BY-4.0" in citation


def test_the_classifier_refuses_without_upstream(monkeypatch):
    """Absence of the remote must not read as evidence of fork authorship.

    The upstream check is the only thing separating "we wrote this" from
    "we did not look", so losing it has to stop the classification rather
    than quietly widen it.
    """
    monkeypatch.setattr(D, "upstream_paths", lambda: set())
    with pytest.raises(SystemExit) as exc:
        D.classify()
    assert "upstream" in str(exc.value)


def test_the_pinned_site_requirements_name_only_what_is_used():
    """A pinned file that lists what the build does not import stops
    describing the environment it claims to reproduce."""
    text = (REPO / "requirements-site.txt").read_text(encoding="utf-8")
    pins = [l.strip() for l in text.splitlines()
            if l.strip() and not l.startswith("#")]
    names = sorted(p.split("==")[0].lower() for p in pins)

    # Established by installing this file into an empty environment and
    # running the site suite there. The first version named pytest alone
    # and the suite could not import its own conftest: the tests reach
    # marep.layout for component resolution, and importing anything from
    # `marep` executes a package __init__ that loads the MAREP runtime.
    assert names == ["jsonschema", "pytest", "pyyaml"], names
    assert all("==" in p for p in pins), (
        "a floor reproduces whatever was newest that day, not this "
        "environment")
    # Against the pins, not the file text: the comment names rdflib to say
    # when it will be added, and a substring search over the whole file
    # cannot tell an explanation from a dependency.
    assert "rdflib" not in names, (
        "rdflib is not imported by the Phase 2 build, checker or tests; it "
        "joins this file when Phase 3 introduces the class-index generator")


# ======================================================================
# the citation record, against its own schema
# ======================================================================

CFF_SCHEMA = REPO / "tools/licensing/vendor/citation-file-format-1.2.0.schema.json"


def test_the_citation_record_validates_against_the_cff_schema():
    """Against the schema, not against substrings.

    A substring test passes on a file with an empty `name-particle`, which
    CFF 1.2 rejects: the field is defined with a minimum length, so
    supplying it empty is worse than omitting it. Asking whether the text
    contains "cff-version" cannot see that.

    The schema is vendored so this needs no network. It is the 1.2.0
    schema from the citation-file-format project, itself CC BY 4.0 and
    classified as third-party.
    """
    import yaml
    from jsonschema import Draft7Validator

    schema = json.loads(CFF_SCHEMA.read_text(encoding="utf-8"))
    doc = yaml.safe_load((REPO / "CITATION.cff").read_text(encoding="utf-8"))
    errors = sorted(Draft7Validator(schema).iter_errors(doc),
                    key=lambda e: list(e.path))
    assert not errors, "CFF 1.2 validation failed: " + "; ".join(
        "%s: %s" % ("/".join(str(x) for x in e.path) or "(root)",
                    e.message[:120]) for e in errors[:5])


def test_the_cff_gate_rejects_the_defect_it_was_added_for():
    """Forced, so the gate is known to be capable of failing.

    An empty `name-particle` is what shipped, and the substring test that
    preceded this one passed on it.
    """
    import copy

    import yaml
    from jsonschema import Draft7Validator

    schema = json.loads(CFF_SCHEMA.read_text(encoding="utf-8"))
    doc = yaml.safe_load((REPO / "CITATION.cff").read_text(encoding="utf-8"))

    broken = copy.deepcopy(doc)
    broken["authors"][0]["name-particle"] = ""
    assert list(Draft7Validator(schema).iter_errors(broken)), (
        "the schema accepts an empty name-particle, so this gate would not "
        "have caught what shipped")

    missing = copy.deepcopy(doc)
    del missing["cff-version"]
    assert list(Draft7Validator(schema).iter_errors(missing))


def test_the_vendored_schema_is_the_cff_one_and_is_third_party():
    """A vendored schema is somebody else's file; claiming authorship of it
    would be the same error this classifier exists to prevent."""
    schema = json.loads(CFF_SCHEMA.read_text(encoding="utf-8"))
    assert schema.get("title") == "Citation File Format"
    assert set(schema.get("required", [])) == {
        "authors", "cff-version", "message", "title"}

    row = next(r for r in ROWS
               if r.path.endswith("citation-file-format-1.2.0.schema.json"))
    assert row.disposition == D.THIRD_PARTY
    assert row.licence == "CC-BY-4.0"


def test_the_citation_record_claims_no_release():
    """The repository's tags mark measurement checkpoints. Citing one as a
    version would imply an ontology release that has not been made."""
    text = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    import yaml
    doc = yaml.safe_load(text)
    assert "version" not in doc, (
        "a version is claimed but no ontology release has been tagged")
    assert "date-released" not in doc
    assert doc["license"] == "CC-BY-4.0"
