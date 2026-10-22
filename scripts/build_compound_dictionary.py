"""Build a compound-splitting dictionary from a corpus word list.

Input: a CSV of "word,frequency" lines, words as written (lower-cased,
unstemmed). For the internetbook corpus, that is the search database's
`word` table, exported from a database instance with:

    \\copy (SELECT word, frequency FROM word WHERE language = 'da'
            ORDER BY frequency DESC) TO STDOUT WITH CSV

Output: src/internetbook_analysis/dictionaries/<language>_compounds.tsv.gz,
the words that may be compound parts (and the frequencies the splitter
compares against): at least MIN_PART_LENGTH letters, letters only, at least
--min-frequency occurrences, neither stopwords nor common endings.

A new dictionary changes analysis output: bump ANALYZER_VERSION, regenerate
the golden files (tests/regenerate_golden.py), review their diff, release,
and re-index.

    python scripts/build_compound_dictionary.py words_da.csv --language danish
"""

from __future__ import annotations

import argparse
import csv
import gzip
from pathlib import Path

from internetbook_analysis.analyzer import _stopwords
from internetbook_analysis.compounds import DANISH_ENDINGS, MIN_PART_LENGTH

ENDINGS = {"danish": DANISH_ENDINGS}
OUT = Path(__file__).resolve().parent.parent / "src" / "internetbook_analysis" / "dictionaries"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("words", type=Path, help="CSV of word,frequency")
    parser.add_argument("--language", default="danish", help="Snowball language name")
    parser.add_argument("--min-frequency", type=int, default=5)
    args = parser.parse_args()

    stopwords = _stopwords(args.language)
    endings = ENDINGS.get(args.language, frozenset())
    kept: dict[str, int] = {}
    with args.words.open(encoding="utf-8") as f:
        for word, frequency in csv.reader(f):
            n = int(frequency)
            if (
                n >= args.min_frequency and len(word) >= MIN_PART_LENGTH and word.isalpha()
                and word not in stopwords and word not in endings
            ):
                kept[word] = kept.get(word, 0) + n

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{args.language}_compounds.tsv.gz"
    # mtime=0: the same input gives a byte-identical file.
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        for word in sorted(kept):
            gz.write(f"{word}\t{kept[word]}\n".encode("utf-8"))
    print(f"wrote {path}: {len(kept)} words, {path.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
