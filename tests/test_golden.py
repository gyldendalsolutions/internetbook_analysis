"""Analysis output must not change without a new analyzer version.

A failure here means the same text now produces different terms. If that was
intended, bump ANALYZER_VERSION (or the language's own version, see
analyzer_version) and run tests/regenerate_golden.py.
"""

import json
from pathlib import Path

import pytest

from internetbook_analysis import analyzer_for, analyzer_version

GOLDEN = sorted((Path(__file__).parent / "golden").glob("*.json"))


def test_golden_files_exist():
    assert {p.stem for p in GOLDEN} >= {"da", "en"}


@pytest.mark.parametrize("path", GOLDEN, ids=lambda p: p.stem)
def test_output_unchanged(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["analyzer_version"] == analyzer_version(path.stem), (
        "Golden file is from another analyzer version: regenerate it"
    )
    analyzer = analyzer_for(path.stem)
    for case in data["cases"]:
        assert analyzer.analyze(case["text"]) == case["terms"], case["text"]
