"""Greenlandic morphology: a word's root and derivation stems as extra terms.

Greenlandic (Kalaallisut) is polysynthetic: a word is a root followed by a
chain of derivational suffixes and an inflection, so most word forms occur
once. In our Greenlandic content three in four word forms occur only once
(2026-10-23), and a search for one finds only the document it is in.
Danish-style compound splitting finds nothing to split: the suffixes are not
words.

GiellaLT's analyser (giellalt.py, morphology/README.md) reduces a word to its root and
derivations. "ilinniarfissuarmi" (at the big school) analyses as
ilinniar+...+VIK+Der/vn+SUAQ+Der/nn+N+Lok+Sg: the root "ilinniar" (learn),
VIK (place for) and SUAQ (big). The word is indexed, besides itself, with
its root and with each successive derivation stem:

    ilinniar, ilinniar0vik, ilinniar0vik0suaq

so a search matches every word sharing the root, and BM25 ranks documents
sharing more of the derivation higher: the stems are rarer than the root.
Queries are analysed alike. Stems are joined with "0": the text-search
parser that reads the token column keeps a word with a digit in it whole
("ilinniar+vik" would split into two terms), and no Greenlandic word has a
digit, so a stem cannot collide with a word.

The analyser knows 90% of our Greenlandic word forms; the rest, mostly
Danish words and names it does not list, are indexed as written only. Words
are looked up capitalised too, so a name with an ending ("danmarkimi")
is found.

A third of words have several readings. A word is indexed with the stems of
the likeliest ones:

- those without error or alternative-spelling tags, when there are any;
- for a word that is itself a lemma ("aamma", and), that lemma, not an
  inflected form of another word (the noun "aak");
- those with the fewest derivations: the analyser also derives lexicalised
  stems further ("ilinniar", learn, as "ilip" + NIAR), and the further
  reading would connect unrelated words;
- unless none of those has a root in Oqaasileriffik's Greenlandic-English
  dictionary (dictionaries/greenlandic_roots.txt.gz) while a deeper reading
  has one of at least MIN_DICTIONARY_ROOT_LENGTH letters: then that one. The
  fewest derivations sometimes means a lexicalised derived word rather than
  its base ("silageqaaq", the weather is fine, as "silage" rather than
  "sila", weather; "atuartitsissut", teaching material, rather than
  "atuar", read), and the base is what connects the word to others.

Checked against that dictionary (2026-10-24): the analyser knows 96.8% of
its headwords, and the root indexed for 91% of our analysed Greenlandic
words is one of its roots before the last rule; the rule changes 4% of
words, nearly all for a root the dictionary lists.
"""

from __future__ import annotations

import gzip
from functools import lru_cache
from importlib import resources

from internetbook_analysis import giellalt

#: Bumped with the bundled analyser (morphology/README.md) or with a change
#: to how its analyses become terms. Part of Greenlandic's analyzer version
#: (analyzer.analyzer_version).
KAL_ANALYSER_VERSION = "1"

#: Joins a root and its derivations into one term (see the module docstring).
SEPARATOR = "0"

#: Derivations kept per analysis, and terms per word across analyses: a
#: long, ambiguous word should not swamp its document's length.
MAX_DERIVATIONS = 6
MAX_TERMS = 12

#: Tags of analyses that read the word as a misspelling or an alternative
#: spelling of something else.
_DISPREFERRED_TAGS = ("Err/", "Orth/")

#: A deeper reading is preferred for a dictionary root only if the root is
#: at least this long: two- and three-letter roots ("su", what; "aki",
#: price) would connect a word to far too much.
MIN_DICTIONARY_ROOT_LENGTH = 4


@lru_cache(maxsize=1)
def dictionary_roots() -> frozenset[str]:
    """The roots Oqaasileriffik's dictionary attests (built by
    scripts/build_greenlandic_roots.py; CC BY-SA 4.0, see NOTICE)."""
    path = resources.files("internetbook_analysis") / "dictionaries" / "greenlandic_roots.txt.gz"
    with gzip.open(path.open("rb"), "rt", encoding="utf-8") as f:
        return frozenset(line.strip() for line in f if line.strip())


def stems(analysis: str) -> list[str]:
    """The root and each successive derivation stem of one analysis.

    "ilinniar+Gram/IV+VIK+Der/vn+SUAQ+Der/nn+N+Lok+Sg" gives
    ["ilinniar", "ilinniar0vik", "ilinniar0vik0suaq"]: a derivation is the
    morpheme a "Der/" tag follows. [] when the root is not a word.
    """
    parts = analysis.split("+")
    root = parts[0].lower()
    if not root.isalpha():
        return []
    derivations = [
        parts[i - 1].lower()
        for i in range(2, len(parts))
        if parts[i].startswith("Der/") and parts[i - 1].isalpha() and parts[i - 1].isupper()
    ]
    out = [root]
    for derivation in derivations[:MAX_DERIVATIONS]:
        out.append(out[-1] + SEPARATOR + derivation)
    return out


class GreenlandicMorphology:
    """A Decompounder (analyzer.Decompounder) for Greenlandic: a word's root
    and derivation stems."""

    def split(self, word: str) -> list[str]:
        return list(_terms(word))


@lru_cache(maxsize=200_000)
def _terms(word: str) -> tuple[str, ...]:
    analyses = giellalt.lookup("kal", word)
    preferred = [a for a in analyses if not any(tag in a for tag in _DISPREFERRED_TAGS)] or analyses
    readings = [s for s in (stems(a) for a in preferred) if s]
    if not readings:
        return ()
    # A word that is itself a lemma ("aamma", and) is that word, not an
    # inflected form of an unrelated one (the noun "aak").
    if any(r[0] == word for r in readings):
        readings = [r for r in readings if r[0] == word]
    fewest = min(len(r) for r in readings)
    roots = dictionary_roots()
    if not any(r[0] in roots for r in readings if len(r) == fewest):
        attested = [
            r for r in readings
            if r[0] in roots and len(r[0]) >= MIN_DICTIONARY_ROOT_LENGTH
        ]
        if attested:
            readings = attested
            fewest = min(len(r) for r in readings)
    out: dict[str, None] = {}
    for reading in readings:
        if len(reading) != fewest:
            continue
        for term in reading:
            if term != word:
                out.setdefault(term)
    return tuple(out)[:MAX_TERMS]
