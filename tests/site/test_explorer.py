# SPDX-License-Identifier: Apache-2.0
"""The explorer, and the four things it must not do.

Ranking is exercised by running the shipped `ranking.js` under node, not
by re-implementing it here. A test that reimplements the algorithm proves
the reimplementation works and says nothing about what the site serves,
which is the failure this whole project keeps finding in other forms.

The DOM code cannot be run without a browser, so it is checked
structurally: that ontology text has exactly one path into the page and
that path is `textContent`, that the page carries the controls and states
the plan requires, and that IRIs are never anchors. Those are properties
of the source, and the source is what ships.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest

from marep import layout

REPO = layout.repository_root()
SRC = layout.component("site.source").resolve()
EXPLORER_JS = (SRC / "assets/js/explorer.js").read_text(encoding="utf-8")
RANKING_JS_PATH = SRC / "assets/js/ranking.js"
RANKING_JS = RANKING_JS_PATH.read_text(encoding="utf-8")
EXPLORE_HTML = (SRC / "explore/index.html").read_text(encoding="utf-8")

NODE = shutil.which("node")

#: The tested JavaScript engine. Node is a build-test dependency of this
#: repository, not a convenience: the ranking that ships is JavaScript,
#: and the only way to test what ships is to run it.
#:
#: A supported LTS line. This pinned 25.2.1 for one commit, which Node
#: lists as end-of-life -- a release that receives no security fix, chosen
#: because it was the one already installed. What is on a machine is not
#: an argument for what a project should depend on.
NODE_PIN = (REPO / ".nvmrc").read_text(encoding="utf-8").strip()


def node_version():
    out = subprocess.run([NODE, "--version"], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-200:]
    return out.stdout.strip().lstrip("v")


def require_node():
    """Absence is a failure, not a skip.

    This was a skipif. A skip is indistinguishable from a pass in a
    summary line, so on a machine without node every behavioural test in
    this file reported success while running none of the shipped code --
    the same fail-open shape as a checker that reads the wrong files.

    The complete version is what is pinned, not the major. .nvmrc names an
    exact release and actions/setup-node installs exactly that, so a check
    that accepted any 25.x would have been claiming results for releases
    nothing here had ever run.
    """
    assert NODE is not None, (
        "node is not on PATH. It is required to test the shipped ranking "
        "module: the pinned version is %s, declared in .nvmrc. Install it "
        "rather than skipping -- a skip here hides the entire behavioural "
        "half of this file." % NODE_PIN)
    running = node_version()
    assert running == NODE_PIN, (
        "node %s is on PATH but the tested version is %s (.nvmrc). Install "
        "the pinned release; results are only claimed for it."
        % (running, NODE_PIN))


@pytest.fixture(scope="module")
def index(tmp_path_factory):
    """The real index, built for the test."""
    import importlib.util

    path = layout.component("tool.build-class-index").resolve()
    spec = importlib.util.spec_from_file_location("bci_for_explorer", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path_factory.mktemp("idx")
    assert mod.main(["--index", str(out / "i.json"),
                     "--coverage", str(out / "c.json")]) == 0
    return json.loads((out / "i.json").read_text(encoding="utf-8"))


def run_ranking(index, query, filters=None, with_modules=True):
    """Search using the file the browser loads.

    `with_modules` passes the index module list, exactly as explorer.js
    does. Setting it False is how the tests show that module titles come
    from that list and are not hidden in the class records.
    """
    require_node()
    script = """
const R = require(process.argv[2]);
const index = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
const modules = process.argv[6] === 'yes' ? index.modules : undefined;
const hits = R.search(index.classes, process.argv[4],
                      JSON.parse(process.argv[5]), modules);
process.stdout.write(JSON.stringify(
    hits.map(h => ({id: h.record.id, score: h.score}))));
"""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        runner = Path(tmp) / "run.js"
        runner.write_text(script, encoding="utf-8")
        payload = Path(tmp) / "index.json"
        payload.write_text(json.dumps(index), encoding="utf-8")
        result = subprocess.run(
            [NODE, str(runner), str(RANKING_JS_PATH), str(payload), query,
             json.dumps(filters or {}), "yes" if with_modules else "no"],
            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-400:]
    return json.loads(result.stdout)


# ======================================================================
# the toolchain this file depends on
# ======================================================================


def test_the_node_pin_is_declared_where_the_toolchain_reads_it():
    """.nvmrc is the file nvm and actions/setup-node both read.

    It must stay bare: nvm reads the whole file, so a comment explaining
    the pin would become part of the version string.
    """
    raw = (REPO / ".nvmrc").read_text(encoding="utf-8")
    assert raw.endswith("\n"), ".nvmrc needs a trailing newline"
    assert re.fullmatch(r"\d+\.\d+\.\d+", raw.strip()), (
        "expected a bare version, got %r" % raw)


def test_the_running_node_matches_the_pin():
    """Named on its own so the toolchain failure is legible as a
    toolchain failure rather than as eight ranking tests going red."""
    require_node()


def test_the_python_requirements_name_the_node_dependency():
    """requirements-site.txt is where somebody sets this repository up.

    A reader who installs exactly what it lists and runs the suite must
    not be the one to discover that half of it needs a JavaScript engine.
    """
    text = (REPO / "requirements-site.txt").read_text(encoding="utf-8")
    assert ".nvmrc" in text, (
        "the pinned Python requirements say nothing about node, which the "
        "site tests require")


def test_no_workflow_states_a_node_version_of_its_own():
    """A forward guard: inert until .github/workflows/ exists, binding on
    the day it does.

    A workflow naming its own node version would be a second pin, free to
    drift from .nvmrc, and drift between two pins is not visible from
    either one. `node-version-file` reads the single pin instead.

    This test cannot yet have caught anything -- there is no workflow
    directory -- and that is stated rather than implied by a green tick.
    """
    workflows = REPO / ".github/workflows"
    if not workflows.is_dir():
        assert not workflows.exists(), (
            ".github/workflows exists but is not a directory")
        return
    import yaml

    offenders = []
    for path in sorted(workflows.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        if "pytest" not in text:
            continue
        # Parsed rather than pattern-matched, for the reason the sibling
        # guard in tests/licensing carries: a comment mentioning the
        # setting is not the setting.
        document = yaml.safe_load(text) or {}
        setups = []
        # Per job, not per workflow. Aggregating across the file let one
        # job's setup-node satisfy a different job that ran pytest with
        # no node at all.
        for job_name, job in (document.get("jobs") or {}).items():
            steps = job.get("steps") or []
            if not any("pytest" in str(step.get("run", "")) for step in steps):
                continue
            here = [step for step in steps
                    if "actions/setup-node" in str(step.get("uses", ""))]
            if not here:
                offenders.append(
                    "%s/%s: runs pytest without setting up the pinned node"
                    % (path.name, job_name))
            for step in here:
                setups.append(("%s/%s" % (path.name, job_name),
                               step.get("with") or {}))
        for name, options in setups:
            if options.get("node-version") is not None:
                offenders.append(
                    "%s: states node-version %r inline, a second pin free "
                    "to drift from .nvmrc" % (name, options["node-version"]))
            if options.get("node-version-file") != ".nvmrc":
                offenders.append(
                    "%s: node-version-file is %r, not .nvmrc"
                    % (name, options.get("node-version-file")))
    assert not offenders, offenders


# ======================================================================
# every documented search field, isolated on synthetic records
# ======================================================================

#: One record per field, with a nonsense token unique to each field, so a
#: query can only match through the field under test. Built here rather
#: than drawn from the corpus: a corpus test says the fields work on
#: today's data, and says nothing about which field did the work.
FIXTURE = {
    "id": "syn:Fixture",
    "iri": "https://synthetic.invalid/m#Fixture",
    "label": "Marmoset Threshold",
    "definition": "Mentions pomegranate, and otherwise says little.",
    "synonyms": ["Basalt Clef"],
    "category": "disposition",
    "module": "syn-alpha",
    "source": "synthetic.ttl",
    "parents": [],
    "mappings": [],
}

#: A second record that names the first one's IRI in its prose. It exists
#: so the exact-IRI test has something to outrank.
MENTIONS = dict(FIXTURE,
                id="syn:Mentions",
                iri="https://synthetic.invalid/m#Mentions",
                label="Aardvark Mention",
                definition="Cross-references "
                           "https://synthetic.invalid/m#Fixture in prose.",
                synonyms=[])

SYNTHETIC = {
    "format_version": 1,
    "generated_by": "tests/site/test_explorer.py",
    "source_commit": "0" * 40,
    "modules": [{"key": "syn-alpha",
                 "title": "Quartzite Reference Compendium",
                 "classes": 2}],
    "classes": [FIXTURE, MENTIONS],
}

EXACT, PREFIX, TOKEN, SYNONYM, SUBSTRING = 0, 1, 2, 3, 4


@pytest.mark.parametrize("field,query,score", [
    ("exact compact id", "syn:Fixture", EXACT),
    ("exact full IRI", "https://synthetic.invalid/m#Fixture", EXACT),
    ("label prefix", "marmoset", PREFIX),
    ("label token", "threshold", TOKEN),
    ("synonym", "basalt", SYNONYM),
    ("definition", "pomegranate", SUBSTRING),
    ("module key", "syn-alpha", SUBSTRING),
    ("module title", "quartzite", SUBSTRING),
])
def test_each_documented_search_field_is_reachable(field, query, score):
    """The plan lists the fields a reader can search. Each is claimed
    here on its own, at the tier the plan gives it."""
    hits = run_ranking(SYNTHETIC, query)
    ids = [h["id"] for h in hits]
    assert "syn:Fixture" in ids, (
        "%s is not searchable: %r returned %s" % (field, query, ids))
    hit = [h for h in hits if h["id"] == "syn:Fixture"][0]
    assert hit["score"] == score, (
        "%s matched at tier %s, expected %s" % (field, hit["score"], score))


def test_an_exact_iri_outranks_a_definition_that_quotes_it():
    """The defect this test was written for: a full IRI scored SUBSTRING,
    so pasting an IRI ranked the class it names below anything whose
    label merely started with the same characters."""
    hits = run_ranking(SYNTHETIC, "https://synthetic.invalid/m#Fixture")
    assert [h["id"] for h in hits] == ["syn:Fixture", "syn:Mentions"]
    assert [h["score"] for h in hits] == [EXACT, SUBSTRING]


def test_the_module_title_comes_from_the_module_list_not_the_records():
    """Titles are passed to search(), not stamped onto 187 records.

    Searching a title with the module list withheld must find nothing --
    if it still matched, the title would be living in the record after
    all, in a second place free to disagree with the first.
    """
    assert run_ranking(SYNTHETIC, "quartzite"), "the title is not searchable"
    assert run_ranking(SYNTHETIC, "quartzite", with_modules=False) == [], (
        "a module title matched without the module list, so it is "
        "duplicated into the class records")


def test_no_generated_class_record_carries_a_module_title(index):
    """The same claim against the real index."""
    titles = {m["title"] for m in index["modules"]}
    for record in index["classes"]:
        for key, value in record.items():
            if not isinstance(value, str):
                continue
            assert value not in titles, (
                "%s.%s holds a module title" % (record["id"], key))


# ======================================================================
# ranking, run as shipped
# ======================================================================


@pytest.mark.parametrize("query,expected", [
    ("value disposition", "core:ValueDisposition"),
    ("benevolence disposition", "schwartz-values:BenevolenceDisposition"),
    ("honesty", "folk:HonestyDisposition"),
    ("betrayal", "moral-foundations:BetrayalProcess"),
    ("rash judgment", "moral-epistemics:RashJudgmentAct"),
])
def test_a_representative_search_in_each_module_finds_its_class(
        index, query, expected):
    """One per module, so a module dropping out of the index shows up as a
    search that stops working rather than as a smaller number.

    Each term is unambiguous on purpose. "care" would not be: six labels
    are shared between modules, and the test below covers those.
    """
    ids = [h["id"] for h in run_ranking(index, query)]
    assert expected in ids, (
        "%r is not in the index; the term this test searches for no longer "
        "names anything" % expected)
    assert ids[0] == expected, ids[:4]


def test_classes_sharing_a_label_are_ordered_by_iri(index):
    """Six labels are shared across modules -- folk and moral-foundations
    both have a care disposition, folk and schwartz both have power.

    They are distinct classes and both should be findable, so the search
    cannot prefer one on merit. The tie break decides, and this records
    which way: normalised label first, then IRI. Without it the winner
    would be whichever the array happened to hold first.
    """
    by_label = {}
    for record in index["classes"]:
        by_label.setdefault(record["label"].lower(), []).append(record)
    shared = {k: v for k, v in by_label.items() if len(v) > 1}
    assert shared, "no label is shared, so this test is watching nothing"

    for label, records in sorted(shared.items()):
        hits = run_ranking(index, label)
        ids = [h["id"] for h in hits]
        expected = [r["id"] for r in sorted(records, key=lambda r: r["iri"])]
        assert ids[:len(expected)] == expected, (label, ids[:4])
        top = [h for h in hits if h["score"] == hits[0]["score"]]
        assert len(top) >= 2, (
            "%r is shared but only one class scored best" % label)


def test_an_exact_identifier_ranks_first(index):
    """Searching a compact id must land on that class, not on whatever
    else mentions the string."""
    for record in index["classes"][:25]:
        hits = run_ranking(index, record["id"])
        assert hits, record["id"]
        assert hits[0]["id"] == record["id"], (record["id"], hits[:3])
        assert hits[0]["score"] == 0, "an exact id did not score EXACT"


def test_an_exact_label_ranks_first(index):
    for record in index["classes"][:25]:
        hits = run_ranking(index, record["label"])
        assert hits[0]["score"] == 0, (record["label"], hits[:2])


def test_ranking_is_deterministic_and_tie_broken(index):
    """Two runs must agree, and equal scores must be ordered by label then
    IRI rather than by whatever order the array held."""
    first = run_ranking(index, "disposition")
    second = run_ranking(index, "disposition")
    assert first == second

    by_label = {r["id"]: r["label"].lower() for r in index["classes"]}
    by_iri = {r["id"]: r["iri"] for r in index["classes"]}
    previous = None
    for hit in first:
        key = (hit["score"], by_label[hit["id"]], by_iri[hit["id"]])
        if previous is not None:
            assert previous <= key, "results are not in score/label/IRI order"
        previous = key


def test_filters_narrow_without_changing_order(index):
    """A filter removes rows; it does not reorder the ones that remain."""
    everything = run_ranking(index, "disposition")
    folk_only = run_ranking(index, "disposition", {"module": "valuenet-folk"})
    folk_ids = [h["id"] for h in folk_only]
    assert folk_ids, "the folk filter returned nothing"
    assert folk_ids == [h["id"] for h in everything
                        if h["id"].startswith("folk:")]


def test_an_empty_query_returns_the_filtered_set(index):
    """So the corpus is browsable without typing."""
    hits = run_ranking(index, "")
    assert len(hits) == len(index["classes"])
    roles = run_ranking(index, "", {"category": "role"})
    assert len(roles) == sum(1 for r in index["classes"]
                             if r["category"] == "role")


def test_a_query_matching_nothing_returns_nothing(index):
    assert run_ranking(index, "zzzzz-no-such-term-zzzzz") == []


# ======================================================================
# the DOM code, checked as source
# ======================================================================


def test_ontology_text_never_becomes_markup():
    """One path into the page, and it is textContent.

    A definition is authored text in a file anyone can edit. innerHTML
    anywhere on that path turns an ontology edit into a script injection,
    and the review that would catch it is the one nobody does on a
    Turtle file.
    """
    def code_only(source):
        """Comments stripped, because a substring scan over source cannot
        tell code from prose -- this test failed on the comment in
        explorer.js explaining why innerHTML is forbidden."""
        source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
        return re.sub(r"(?m)//.*$", "", source)

    for name, source in (("explorer.js", code_only(EXPLORER_JS)),
                         ("ranking.js", code_only(RANKING_JS))):
        assert "innerHTML" not in source, name
        assert "outerHTML" not in source, name
        assert "insertAdjacentHTML" not in source, name
        assert "document.write" not in source, name
        assert not re.search(r"\beval\s*\(", source), name
        assert "new Function" not in source, name


def test_the_explorer_requires_no_third_party_origin():
    """The site must render with no external request."""
    for source in (EXPLORER_JS, RANKING_JS, EXPLORE_HTML):
        assert not re.search(r"https?://(?!www\.w3\.org)", source), (
            "an external origin is referenced")


def test_iris_are_rendered_as_text_and_never_as_anchors():
    """They identify entities and do not resolve. An anchor would send a
    reader to a 404 and imply the ontology is broken."""
    assert 'el("code", "iri-value", value)' in EXPLORER_JS
    # The only anchors the explorer creates are result links, whose href
    # is a query string on this same page.
    anchors = re.findall(r'createElement\("a"\)', EXPLORER_JS)
    assert len(anchors) == 1, "the explorer creates %d anchors" % len(anchors)
    assert "link.href = paramsFor(" in EXPLORER_JS


def test_the_copy_button_reports_refusal(index):
    """The clipboard refuses without a secure context. A button that
    silently does nothing is worse than one that says it could not."""
    assert "navigator.clipboard" in EXPLORER_JS
    assert "Clipboard unavailable" in EXPLORER_JS
    assert "Copy refused by the browser" in EXPLORER_JS


def test_the_page_states_every_condition_the_plan_requires():
    """Loading, failure, no results, and an unknown class identifier are
    distinct states with distinct text."""
    assert "Loading the class index" in EXPLORER_JS
    assert "could not be loaded" in EXPLORER_JS
    assert "No class matches" in EXPLORER_JS
    assert "No class has the identifier" in EXPLORER_JS


def test_a_malformed_filter_parameter_is_dropped_not_obeyed():
    """A filter naming something that does not exist would return an
    empty set, which reads as a corpus with no such classes."""
    assert "modules.indexOf(params.module) === -1" in EXPLORER_JS
    assert "categories.indexOf(params.category) === -1" in EXPLORER_JS


def test_the_url_carries_the_query_and_the_selection():
    for key in ('p.set("q"', 'p.set("module"', 'p.set("category"',
                'p.set("class"'):
        assert key in EXPLORER_JS, key
    assert 'p.get("class")' in EXPLORER_JS
    assert "window.history.pushState" in EXPLORER_JS
    assert 'addEventListener("popstate"' in EXPLORER_JS


def test_modified_clicks_are_left_to_the_browser():
    """Ctrl/Cmd/shift-click and middle-click must open a tab, which is
    the point of using a real anchor."""
    assert "event.metaKey" in EXPLORER_JS
    assert "event.ctrlKey" in EXPLORER_JS
    assert "event.shiftKey" in EXPLORER_JS
    assert "event.button !== 0" in EXPLORER_JS


def test_focus_moves_deliberately_when_a_class_is_opened():
    """Otherwise a keyboard user is left at the top of a list that
    changed underneath them."""
    assert '$("detail").focus()' in EXPLORER_JS
    assert 'focusDetail' in EXPLORER_JS


def test_every_control_is_labelled_and_the_status_is_live():
    for control in ("q", "module", "category"):
        assert 'for="%s"' % control in EXPLORE_HTML, control
        assert 'id="%s"' % control in EXPLORE_HTML, control
    assert 'aria-live="polite"' in EXPLORE_HTML
    assert 'role="status"' in EXPLORE_HTML
    assert 'id="detail"' in EXPLORE_HTML and 'tabindex="-1"' in EXPLORE_HTML


def test_without_javascript_the_page_says_so_and_offers_routes():
    """Navigation, explanatory content and downloads keep working; the
    search does not pretend to."""
    assert "<noscript>" in EXPLORE_HTML
    for target in ("../modules/", "../downloads/", "../data/class-index.json"):
        assert target in EXPLORE_HTML, target


def test_no_form_appears_functional_without_javascript():
    """A form that submits would reload the page and look broken
    rather than unavailable.

    Three independent reasons it cannot, so no single one carries the
    claim alone: the form ships hidden and is revealed only after the
    index loads, it names no action and carries no submit control, and
    the script cancels submission on the same synchronous line that
    reveals it.

    This test used to assert the literal string onsubmit="return
    false;", which writes the fix down rather than checking it. The
    attribute has since become a bound listener -- strictly better,
    being the only inline script on the site -- and the old assertion
    failed while every property it existed to protect still held.
    """
    assert "<form" in EXPLORE_HTML
    assert "action=" not in EXPLORE_HTML
    assert 'type="submit"' not in EXPLORE_HTML
    form_tag = EXPLORE_HTML[EXPLORE_HTML.index("<form"):]
    form_tag = form_tag[:form_tag.index(">") + 1]
    assert " hidden" in form_tag, form_tag
    assert re.search(r'addEventListener\(\s*"submit"', EXPLORER_JS), (
        "nothing cancels form submission")
    assert "preventDefault" in EXPLORER_JS


def test_the_page_carries_no_inline_event_handler():
    """An inline handler is script inside the markup: the one thing a
    content-security policy cannot permit without permitting all of
    it, and invisible to every check that reads the .js files."""
    assert not re.findall(r"\son[a-z]+\s*=", EXPLORE_HTML)


def test_the_explorer_is_the_only_page_that_needs_a_script():
    """Navigating the rest of the site must not depend on JavaScript."""
    for page in sorted(SRC.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        if page.parent.name == "explore":
            assert "<script" in text
        else:
            assert "<script" not in text, page.name


def test_the_shipped_ranking_is_the_module_the_page_loads():
    """explorer.js delegates rather than carrying a second copy; two
    implementations of an order is two orders."""
    assert "window.ValueNetRanking" in EXPLORER_JS
    assert "ranking.search(" in EXPLORER_JS
    assert 'src="../assets/js/ranking.js"' in EXPLORE_HTML
    assert 'src="../assets/js/explorer.js"' in EXPLORE_HTML
    # The ranking constants live in one place.
    assert "var EXACT = 0" in RANKING_JS
    assert "var EXACT = 0" not in EXPLORER_JS
