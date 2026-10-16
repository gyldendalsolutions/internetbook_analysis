"""Rewrite tests/golden/*.json from the current analyzer.

Only after a deliberate change to analysis output, with ANALYZER_VERSION
bumped. Review the diff: every changed line is a term that indexed
documents and queries will disagree on until the corpus is re-indexed.
"""

import json
from pathlib import Path

from golden_sentences import SENTENCES

from internetbook_analysis import ANALYZER_VERSION, analyzer_for

GOLDEN = Path(__file__).parent / "golden"

for language, sentences in SENTENCES.items():
    data = {
        "analyzer_version": ANALYZER_VERSION,
        "cases": [
            {"text": text, "terms": analyzer_for(language).analyze(text)}
            for text in sentences
        ],
    }
    path = GOLDEN / f"{language}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
