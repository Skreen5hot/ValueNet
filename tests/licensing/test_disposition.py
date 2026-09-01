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
    """The load-bearing safety property.

    Original ValueNet material has no identified licence. Classifying any
    of it as project content would relicense somebody else's work by
    omission -- the precise opposite of the permissive intent behind the
    project licences.
    """
    leaked = [r.path for r in ROWS
              if r.origin == "upstream-valuenet"
              and r.disposition in (D.CONTENT, D.SOFTWARE)]
    assert not leaked, (
        "upstream material relicensed under project terms: " + str(leaked[:8]))

    for row in ROWS:
        if row.origin == "upstream-valuenet":
            assert row.licence is None, row.path
            assert row.disposition == D.EXCLUDED, row.path


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
    """Fetched verbatim from canonical sources; checked so a placeholder or
    a summary cannot sit where a licence should be."""
    markers = {
        "Apache-2.0.txt": "Apache License",
        "CC-BY-4.0.txt": "Creative Commons Attribution 4.0 International",
        "BSD-3-Clause.txt": "Redistribution and use in source and binary",
    }
    for name, marker in markers.items():
        text = (REPO / "LICENSES" / name).read_text(encoding="utf-8")
        assert marker in text, name + " does not contain its own licence text"


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
