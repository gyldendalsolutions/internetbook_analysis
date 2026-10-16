"""Analysis output must not change without a new ANALYZER_VERSION.

A failure here means the same text now produces different terms. If that was
intended, bump ANALYZER_VERSION and run tests/regenerate_golden.py.
"""

import json
from pathlib import Path

import pytest

from internetbook_analysis import ANALYZER_VERSION, analyzer_for

GOLDEN = sorted((Path(__file__).parent / "golden").glob("*.json"))


def test_golden_files_exist():
    assert {p.stem for p in GOLDEN} >= {"da", "en"}


@pytest.mark.parametrize("path", GOLDEN, ids=lambda p: p.stem)
def test_output_unchanged(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["analyzer_version"] == ANALYZER_VERSION, (
        "Golden files are from another ANALYZER_VERSION: regenerate them"
    )
    analyzer = analyzer_for(path.stem)
    for case in data["cases"]:
        assert analyzer.analyze(case["text"]) == case["terms"], case["text"]
