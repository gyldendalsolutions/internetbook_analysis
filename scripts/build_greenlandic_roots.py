"""Build the list of Greenlandic dictionary roots from Oqaasileriffik's dictionary.

Input: the spreadsheets of the 2018 Greenlandic-English dictionary, from
https://github.com/Oqaasileriffik/dicts ("2018 Chicago/*.ods"; CC BY-SA 4.0).

Output: src/internetbook_analysis/dictionaries/greenlandic_roots.txt.gz, the
roots of every analysis of every single-word headword, one per line, sorted:
the roots the dictionary attests. greenlandic.py prefers them when choosing
between a word's readings (see its docstring).

A new list changes Greenlandic analysis: bump KAL_ANALYSER_VERSION in
greenlandic.py, regenerate the golden files (tests/regenerate_golden.py),
review tests/golden/kl.json, release, and re-index.

    git clone https://github.com/Oqaasileriffik/dicts /tmp/dicts
    python scripts/build_greenlandic_roots.py "/tmp/dicts/2018 Chicago"
"""

from __future__ import annotations

import argparse
import gzip
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from internetbook_analysis import giellalt
from internetbook_analysis.greenlandic import stems

OUT = Path(__file__).resolve().parent.parent / "src" / "internetbook_analysis" / "dictionaries"

_TABLE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
_TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
_REPEAT = f"{{{_TABLE}}}number-columns-repeated"
#: The header row's first cell ("word to look up").
_HEADER = "Ujartugassaq"


def first_cells(path: Path):
    """The first cell of each row of an OpenDocument spreadsheet."""
    root = ET.fromstring(zipfile.ZipFile(path).read("content.xml"))
    for row in root.iter(f"{{{_TABLE}}}table-row"):
        cell = row.find(f"{{{_TABLE}}}table-cell")
        if cell is not None:
            yield "".join("".join(p.itertext()) for p in cell.findall(f"{{{_TEXT}}}p"))


def headwords(directory: Path) -> set[str]:
    """Single-word headwords, lower-cased."""
    words = set()
    for path in sorted(directory.glob("*.ods")):
        for text in first_cells(path):
            word = text.strip().lower().rstrip("!?.,")
            if word and word != _HEADER.lower() and word.isalpha():
                words.add(word)
    return words


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", type=Path, help='the dictionary\'s "2018 Chicago" directory')
    args = parser.parse_args()

    words = headwords(args.directory)
    roots = {r[0] for w in words for a in giellalt.lookup("kal", w) if (r := stems(a))}

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "greenlandic_roots.txt.gz"
    # mtime=0: the same input gives a byte-identical file.
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        for root in sorted(roots):
            gz.write(f"{root}\n".encode("utf-8"))
    print(f"wrote {path}: {len(roots)} roots from {len(words)} headwords")


if __name__ == "__main__":
    main()
