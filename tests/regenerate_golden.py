"""Rewrite tests/golden/*.json from the current analyzer.

Only after a deliberate change to analysis output, with the analyzer version
bumped (ANALYZER_VERSION, or the language's own: see analyzer_version). Review the diff: every changed line is a term that indexed
documents and queries will disagree on until the corpus is re-indexed.
"""

import json
from pathlib import Path

from golden_sentences import SENTENCES

from internetbook_analysis import analyzer_for, analyzer_version

GOLDEN = Path(__file__).parent / "golden"

for language, sentences in SENTENCES.items():
    data = {
        "analyzer_version": analyzer_version(language),
        "cases": [
            {"text": text, "terms": analyzer_for(language).analyze(text)}
            for text in sentences
        ],
    }
    path = GOLDEN / f"{language}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
