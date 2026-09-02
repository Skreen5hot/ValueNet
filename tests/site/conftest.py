# SPDX-License-Identifier: Apache-2.0
"""Shared fixtures for the site tests.

The class index is built here rather than read from `_site/`. That
directory is a gitignored build artifact: reading it makes a test pass or
fail depending on whether somebody ran the build first, which is a
dependency on execution order and on local residue rather than on the
repository. In a clean clone the same tests would skip, and a skip reads
as a pass.
"""

from __future__ import annotations

import importlib.util
import json

import pytest

from marep import layout

REPO = layout.repository_root()


@pytest.fixture(scope="session")
def class_index(tmp_path_factory):
    """The class index, generated for the test session."""
    path = layout.component("tool.build-class-index").resolve()
    spec = importlib.util.spec_from_file_location("class_index_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    out = tmp_path_factory.mktemp("shared-index")
    assert module.main(["--index", str(out / "class-index.json"),
                        "--coverage", str(out / "coverage.json")]) == 0
    return json.loads(
        (out / "class-index.json").read_text(encoding="utf-8"))
