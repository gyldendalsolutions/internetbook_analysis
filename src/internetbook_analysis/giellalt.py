"""GiellaLT's morphological analysers, bundled in morphology/.

Loading and lookup shared by the languages that use one (greenlandic.py,
faroese.py). Each analyser is loaded on first use, once per process, and
shared; loading takes a second or two. See morphology/README.md for the
files, where they come from and their licence.
"""

from __future__ import annotations

import threading
from importlib import resources

#: Analyser file per GiellaLT language code.
_FILES = {
    "kal": "kal-analyser-gt-desc.hfstol",
    "fao": "fao-analyser-gt-desc.hfstol",
}

_lock = threading.Lock()
_analysers: dict[str, object] = {}


def _analyser(code: str):
    with _lock:
        if code not in _analysers:
            import pyhfst

            resource = resources.files("internetbook_analysis") / "morphology" / _FILES[code]
            with resources.as_file(resource) as path:
                _analysers[code] = pyhfst.HfstInputStream(str(path)).read()
        return _analysers[code]


def lookup(code: str, word: str) -> list[str]:
    """The analyses of `word`, in order, without repeats.

    Words reach the analyser lower-cased, but it lists proper nouns
    capitalised: "føroyum" is unknown, or worse, read as a compound of
    unrelated words ("ísland" as "ísur" + "land"), where "Føroyum" and
    "Ísland" are found. So the capitalised form is looked up too when the
    word as written has no analysis, or only compound ones ("#"). Not
    otherwise: "ilinniarfissuarmi" (at the big school) is a common word,
    not a form of the name "Ilinniarfissuaq".
    """
    analyser = _analyser(code)
    out = list(dict.fromkeys(a for a, _weight in analyser.lookup(word)))
    capitalised = word[:1].upper() + word[1:]
    if capitalised != word and all("#" in a for a in out):
        out.extend(a for a, _weight in analyser.lookup(capitalised) if a not in out)
    return out
