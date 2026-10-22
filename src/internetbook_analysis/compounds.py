"""Compound splitting from a frozen dictionary of corpus words.

Danish forms compounds freely ("antibiotikabehandling" = "antibiotika" +
"behandling"), so a search for one part misses text that only has the
compound. The decompounder adds a compound's parts as extra terms; the whole
word is always kept too (see Analyzer.analyze).

The method is Koehn & Knight's (2003): split a word into known words and
keep the split when its parts are more common, on average, than the word
itself. Plain, it is far too eager for Danish, where frequent words double as
endings ("lige", "ende", "gerne", "ingen"), so it also requires:

- the word is rare (fewer than MAX_WORD_FREQUENCY occurrences) and at least
  MIN_WORD_LENGTH letters: frequent words are searchable as they are, and
  frequent compounds tend to be the opaque ones ("fremtiden" is not about
  "tiden");
- exactly two parts, each a known word of at least MIN_PART_LENGTH letters
  that is neither a stopword nor a common ending, optionally joined by a
  linking "s" or "e" ("sundhed-s-pleje", "barn-e-vogn");
- not an inflection: the whole word must not stem to its first part
  ("patienterne" is "patient" + an ending the stemmer already handles).

Measured on the Danish corpus (2026-10-22): about half of all word forms
split, 4% of word occurrences, about 9 in 10 splits good in a random sample;
the remaining errors are mostly names and English words. See
docs/search-migration/README.md in core-infrastructure-modules.

The dictionary is data, not code: rebuilt with scripts/build_compound_dictionary.py
and shipped with the package. A new dictionary changes analysis output, so
it means a new ANALYZER_VERSION and a re-index.
"""

from __future__ import annotations

import gzip
from collections.abc import Callable
from functools import lru_cache
from importlib import resources

MIN_WORD_LENGTH = 8
MIN_PART_LENGTH = 4
MAX_WORD_FREQUENCY = 50
LINKS = ("", "s", "e")

#: Endings that are also words, or look like parts; never a part on their
#: own. Applied when building the dictionary.
DANISH_ENDINGS = frozenset({
    "erne", "ernes", "ene", "enes", "ens", "ende", "endes", "lige", "ligt", "lig",
    "elle", "else", "elser", "ingen", "inger", "ere", "eres", "eret", "erede",
    "eren", "erens", "est", "este", "mest", "gerne", "hed", "heder", "skab",
    "skaber", "sker", "redes", "rede", "ning", "ninger", "isk", "iske", "elig",
    "ige", "ighed",
})

#: Dictionary file per Snowball language name, in the package's
#: `dictionaries` directory: "word<TAB>frequency" lines, gzipped.
_FILES = {"danish": "danish_compounds.tsv.gz"}


@lru_cache(maxsize=None)
def load_dictionary(language: str) -> dict[str, int] | None:
    """The word frequencies for a language, or None if it has none."""
    name = _FILES.get(language)
    if name is None:
        return None
    path = resources.files("internetbook_analysis") / "dictionaries" / name
    words: dict[str, int] = {}
    with gzip.open(path.open("rb"), "rt", encoding="utf-8") as f:
        for line in f:
            word, _, frequency = line.rstrip("\n").partition("\t")
            words[word] = int(frequency)
    return words


class DictionaryDecompounder:
    """Splits compounds into two known words; see the module docstring."""

    def __init__(self, words: dict[str, int], stem: Callable[[str], str]) -> None:
        self._words = words
        self._stem = stem
        self._split = lru_cache(maxsize=200_000)(self._split_uncached)

    def split(self, word: str) -> list[str]:
        return list(self._split(word))

    def _split_uncached(self, word: str) -> tuple[str, ...]:
        if (
            len(word) < MIN_WORD_LENGTH
            or not word.isalpha()
            or self._words.get(word, 0) >= MAX_WORD_FREQUENCY
        ):
            return ()
        best: tuple[float, str, str] | None = None
        for i in range(MIN_PART_LENGTH, len(word) - MIN_PART_LENGTH + 1):
            head = word[:i]
            head_frequency = self._words.get(head)
            if head_frequency is None:
                continue
            for link in LINKS:
                tail = word[i + len(link):]
                if link and not word.startswith(link, i):
                    continue
                if len(tail) < MIN_PART_LENGTH:
                    continue
                tail_frequency = self._words.get(tail)
                if tail_frequency is None:
                    continue
                score = (head_frequency * tail_frequency) ** 0.5
                if best is None or score > best[0]:
                    best = (score, head, tail)
        if best is None or best[0] <= self._words.get(word, 0):
            return ()
        _, head, tail = best
        if self._stem(word) == self._stem(head):
            return ()
        return (head, tail)
