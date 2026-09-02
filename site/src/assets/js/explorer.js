/* SPDX-License-Identifier: Apache-2.0
 *
 * The class explorer.
 *
 * Reads the generated index and searches it in the browser. No framework,
 * no third-party runtime: the site must render with no external request,
 * and the checker refuses any reference to another origin.
 *
 * THREE RULES THIS FILE IS BUILT AROUND
 *
 * Ontology text is never markup. Every value from the index reaches the
 * page through textContent or a created node -- never innerHTML, not even
 * for a value that "obviously" cannot contain a tag. A definition is
 * authored text in a file anyone can edit, and the day one contains
 * "<img onerror=...>" is not the day to discover the difference.
 *
 * Ranking is deterministic. Two classes matching equally well must come
 * back in the same order every time, so every comparison ends in a tie
 * break on normalised label and then IRI. Sorting by score alone leaves
 * the rest to whatever order the array happened to be in.
 *
 * IRIs are not links. They identify entities and do not resolve; an
 * anchor would send a reader to a 404 and imply the ontology is broken.
 * They are selectable text with a copy button, and if the clipboard
 * refuses -- it does, without a user gesture or a secure context -- the
 * refusal is visible rather than a button that silently does nothing.
 */

(function () {
  "use strict";

  var INDEX_URL = "../data/class-index.json";
  var state = { index: null, module: "", category: "", q: "", selected: "" };

  function $(id) { return document.getElementById(id); }

  /* Text only. The single place ontology-derived strings become DOM. */
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    return node;
  }

  function setStatus(message) { $("status").textContent = message; }

  /* ---------------------------------------------------------------- URL */

  function readParams() {
    var p = new URLSearchParams(window.location.search);
    return {
      q: p.get("q") || "",
      module: p.get("module") || "",
      category: p.get("category") || "",
      selected: p.get("class") || ""
    };
  }

  function paramsFor(next) {
    var p = new URLSearchParams();
    if (next.q) { p.set("q", next.q); }
    if (next.module) { p.set("module", next.module); }
    if (next.category) { p.set("category", next.category); }
    if (next.selected) { p.set("class", next.selected); }
    var query = p.toString();
    return query ? "?" + query : window.location.pathname;
  }

  function pushState(next, replace) {
    var url = paramsFor(next);
    if (replace) { window.history.replaceState(null, "", url); }
    else { window.history.pushState(null, "", url); }
  }

  /* ------------------------------------------------------------ ranking */

  /* Ranking lives in ranking.js so it can be exercised directly rather
   * than through a browser. This file holds the DOM; that one holds the
   * order, and the tests run the same code the site does. */
  var ranking = window.ValueNetRanking;

  function search() {
    return ranking.search(state.index.classes, state.q,
                          { module: state.module,
                            category: state.category },
                          state.index.modules);
  }

  /* ------------------------------------------------------------ render */

  function excerpt(text, limit) {
    if (text.length <= limit) { return text; }
    return text.slice(0, limit).replace(/\s+\S*$/, "") + "…";
  }

  function resultItem(record) {
    var item = document.createElement("li");
    var link = document.createElement("a");
    /* A real anchor: copyable, openable in a new tab, and in history. */
    link.href = paramsFor({
      q: state.q, module: state.module, category: state.category,
      selected: record.id
    });
    link.className = "result";
    link.appendChild(el("span", "result-label", record.label));
    link.appendChild(el("span", "result-id", record.id));
    link.appendChild(el("span", "result-meta",
                        record.category + " · " + record.module));
    link.appendChild(el("p", "result-definition",
                        excerpt(record.definition, 160)));
    item.appendChild(link);
    return item;
  }

  function renderResults(matches) {
    var list = $("results");
    list.textContent = "";
    if (!matches.length) {
      list.appendChild(el("li", "empty",
        state.q
          ? "No class matches that search with the current filters."
          : "No class matches the current filters."));
      setStatus("0 classes");
      return;
    }
    for (var i = 0; i < matches.length; i += 1) {
      list.appendChild(resultItem(matches[i].record));
    }
    setStatus(matches.length === 1 ? "1 class" : matches.length + " classes");
  }

  function iriRow(label, value) {
    var wrap = el("div", "iri-row");
    wrap.appendChild(el("span", "iri-label", label));
    var text = el("code", "iri-value", value);
    /* Selectable text, never an anchor: these do not resolve. */
    text.setAttribute("tabindex", "0");
    wrap.appendChild(text);

    var button = el("button", "copy", "Copy");
    button.type = "button";
    button.setAttribute("aria-label", "Copy " + label);
    var said = el("span", "copy-result");
    said.setAttribute("role", "status");
    said.setAttribute("aria-live", "polite");
    button.addEventListener("click", function () {
      /* The clipboard refuses without a secure context or a gesture it
       * recognises. A button that silently does nothing is worse than one
       * that says it could not. */
      if (!navigator.clipboard || !navigator.clipboard.writeText) {
        said.textContent = "Clipboard unavailable — select the text to copy.";
        return;
      }
      navigator.clipboard.writeText(value).then(function () {
        said.textContent = "Copied.";
      }, function () {
        said.textContent = "Copy refused by the browser — select the text.";
      });
    });
    wrap.appendChild(button);
    wrap.appendChild(said);
    return wrap;
  }

  function renderDetail(record) {
    var pane = $("detail"), body = $("detail-body");
    body.textContent = "";
    if (!record) {
      pane.hidden = true;
      return;
    }
    body.appendChild(el("h3", "detail-label", record.label));
    body.appendChild(el("p", "detail-id", record.id));
    body.appendChild(el("p", "detail-definition", record.definition));

    body.appendChild(iriRow("IRI", record.iri));

    var meta = el("dl", "detail-meta");
    meta.appendChild(el("dt", null, "Category"));
    meta.appendChild(el("dd", null, record.category));
    meta.appendChild(el("dt", null, "Module"));
    meta.appendChild(el("dd", null, record.module));
    meta.appendChild(el("dt", null, "Source"));
    meta.appendChild(el("dd", null, record.source));
    body.appendChild(meta);

    if (record.synonyms.length) {
      body.appendChild(el("h4", null, "Also known as"));
      var syn = document.createElement("ul");
      record.synonyms.forEach(function (value) {
        syn.appendChild(el("li", null, value));
      });
      body.appendChild(syn);
    }

    body.appendChild(el("h4", null, "Named parents"));
    var parents = document.createElement("ul");
    record.parents.forEach(function (value) {
      parents.appendChild(el("li", "iri-inline", value));
    });
    body.appendChild(parents);

    body.appendChild(el("h4", null, "Mappings"));
    if (!record.mappings.length) {
      body.appendChild(el("p", "muted", "None asserted."));
    } else {
      body.appendChild(el("p", "muted",
        "Published exactly as asserted. These are correspondences, not "
        + "logical equivalences."));
      var maps = document.createElement("ul");
      record.mappings.forEach(function (m) {
        var li = document.createElement("li");
        li.appendChild(el("span", "map-predicate",
                          m.predicate.split("#").pop()));
        li.appendChild(el("span", "iri-inline", m.target));
        maps.appendChild(li);
      });
      body.appendChild(maps);
    }
    pane.hidden = false;
  }

  function byId(id) {
    for (var i = 0; i < state.index.classes.length; i += 1) {
      if (state.index.classes[i].id === id) { return state.index.classes[i]; }
    }
    return null;
  }

  /* ------------------------------------------------------------ wiring */

  function fillSelect(select, values, allLabel) {
    select.textContent = "";
    var any = document.createElement("option");
    any.value = "";
    any.textContent = allLabel;
    select.appendChild(any);
    values.forEach(function (value) {
      var option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
  }

  function apply(options) {
    var matches = search();
    renderResults(matches);

    if (!state.selected) {
      renderDetail(null);
      return;
    }
    var record = byId(state.selected);
    if (!record) {
      var pane = $("detail"), body = $("detail-body");
      body.textContent = "";
      body.appendChild(el("p", "error",
        "No class has the identifier “" + state.selected + "”. It "
        + "may have been renamed, or the link may be from an older build."));
      pane.hidden = false;
      setStatus("Unknown class identifier");
      return;
    }
    renderDetail(record);
    if (options && options.focusDetail) {
      /* Deliberate: following a result link moves focus to what it
       * opened, so a keyboard or screen-reader user is not left at the
       * top of a list that changed underneath them. */
      $("detail").focus();
    }
  }

  function syncControls() {
    $("q").value = state.q;
    $("module").value = state.module;
    $("category").value = state.category;
  }

  function adoptParams(params, options) {
    state.q = params.q;
    state.module = params.module;
    state.category = params.category;
    state.selected = params.selected;
    syncControls();
    apply(options);
  }

  function start(index) {
    state.index = index;
    $("explorer-controls").hidden = false;

    var modules = index.modules.map(function (m) { return m.key; }).sort();
    var categories = [];
    index.classes.forEach(function (r) {
      if (categories.indexOf(r.category) === -1) {
        categories.push(r.category);
      }
    });
    categories.sort();
    fillSelect($("module"), modules, "All modules");
    fillSelect($("category"), categories, "All categories");

    var params = readParams();
    /* A filter value naming something that does not exist is dropped
     * rather than silently returning nothing: an empty result set would
     * look like a corpus with no such classes. */
    if (params.module && modules.indexOf(params.module) === -1) {
      params.module = "";
    }
    if (params.category && categories.indexOf(params.category) === -1) {
      params.category = "";
    }
    adoptParams(params);
    pushState(state, true);

    $("q").addEventListener("input", function () {
      state.q = $("q").value;
      state.selected = "";
      apply();
      pushState(state, true);
    });
    ["module", "category"].forEach(function (name) {
      $(name).addEventListener("change", function () {
        state[name] = $(name).value;
        apply();
        pushState(state);
      });
    });
    $("clear").addEventListener("click", function () {
      state.q = ""; state.module = ""; state.category = ""; state.selected = "";
      syncControls();
      apply();
      pushState(state);
      $("q").focus();
    });

    $("results").addEventListener("click", function (event) {
      var link = event.target.closest ? event.target.closest("a.result") : null;
      if (!link || event.metaKey || event.ctrlKey || event.shiftKey
          || event.button !== 0) {
        return;   /* let the browser open it in a tab or window */
      }
      event.preventDefault();
      var params = new URLSearchParams(link.search);
      state.selected = params.get("class") || "";
      apply({ focusDetail: true });
      pushState(state);
    });

    window.addEventListener("popstate", function () {
      adoptParams(readParams());
    });
  }

  function fail(message) {
    setStatus(message);
    var list = $("results");
    list.textContent = "";
    var item = el("li", "error", message);
    list.appendChild(item);
  }

  document.addEventListener("DOMContentLoaded", function () {
    setStatus("Loading the class index…");
    fetch(INDEX_URL, { cache: "no-cache" }).then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    }).then(function (index) {
      if (!index || !Array.isArray(index.classes) || !index.classes.length) {
        throw new Error("the index is empty");
      }
      start(index);
    }).catch(function (error) {
      fail("The class index could not be loaded (" + error.message
           + "). The module pages and downloads do not depend on it.");
    });
  });
}());
