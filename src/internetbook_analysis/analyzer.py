"""Tokenisation, stopwords, compound splitting and stemming per language."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

import snowballstemmer

#: Bumped whenever analysis output changes for the same input, including a
#: change of snowballstemmer version (pinned exactly for that reason). The
#: indexer puts it in every document's content hash, so a change re-indexes
#: the corpus, and the search API refuses statistics built with another one.
ANALYZER_VERSION = "1"

#: Snowball algorithm per primary language subtag. Languages missing here
#: (Faroese, Icelandic, Greenlandic) have no Snowball stemmer, and are indexed
#: unstemmed rather than with a neighbouring language's rules, which would
#: conflate unrelated words.
_STEMMERS = {
    "da": "danish",
    "de": "german",
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "it": "italian",
    "nb": "norwegian",
    "nn": "norwegian",
    "no": "norwegian",
    "sv": "swedish",
}

#: Stopword lists, as files named after the Snowball algorithm. They are the
#: Snowball project's stop.txt lists, copied unmodified (see NOTICE), for every
#: language with a stemmer. Faroese, Icelandic and Greenlandic have none,
#: as in Solr today. Removing stopwords keeps posting lists and sparse
#: vectors small; BM25 would weight them near zero anyway.
_STOPWORD_DIR = "stopwords"


def _parse_stopwords(text: str) -> frozenset[str]:
    """Words of a Snowball stop.txt: everything after "|" is a comment.

    Words go through the same normalisation as tokens, so a list word and a
    text word compare equal whenever the text word would be removed.
    Entries with an apostrophe (English contractions) never match, because
    the tokeniser splits on apostrophes; they are kept so the file stays
    exactly as published.
    """
    words: set[str] = set()
    for line in text.splitlines():
        for word in line.split("|", 1)[0].split():
            words.add(unicodedata.normalize("NFKC", word).casefold())
    return frozenset(words)


@lru_cache(maxsize=None)
def _stopwords(algorithm: str) -> frozenset[str]:
    from importlib import resources

    path = resources.files("internetbook_analysis") / _STOPWORD_DIR / f"{algorithm}.txt"
    if not path.is_file():
        return frozenset()
    return _parse_stopwords(path.read_text(encoding="utf-8"))

#: A token is a run of letters and digits. Digits are kept so that ISBNs,
#: years and chapter numbers stay searchable.
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)

#: Tokens longer than this are not words (hashes, base64, run-together
#: garbage) and only bloat the dictionary.
_MAX_TOKEN_LENGTH = 40


def normalize_language(language: str) -> str:
    """The primary subtag of a BCP 47 tag, lower-cased: "da-DK" -> "da"."""
    return language.strip().replace("_", "-").split("-")[0].lower()


class Decompounder(Protocol):
    """Splits a compound word into its parts.

    Danish forms compounds freely ("sygeplejepraksis" = "sygepleje" +
    "praksis"), so a query for one part misses documents that only contain
    the compound. A decompounder returns the parts to index *in addition to*
    the whole word, never instead of it.
    """

    def split(self, word: str) -> list[str]:
        """Parts of `word`, excluding the word itself; [] if not a compound."""
        ...


class NoDecompounder:
    """The default: no compound splitting."""

    def split(self, word: str) -> list[str]:
        return []


@dataclass
class Analyzer:
    """Analysis for one language."""

    language: str
    decompounder: Decompounder = field(default_factory=NoDecompounder)

    def __post_init__(self) -> None:
        self.language = normalize_language(self.language)
        algorithm = _STEMMERS.get(self.language)
        self._stemmer = snowballstemmer.stemmer(algorithm) if algorithm else None
        self._stopwords = _stopwords(algorithm) if algorithm else frozenset()

    @property
    def stems(self) -> bool:
        """Whether this language has a stemmer."""
        return self._stemmer is not None

    @property
    def stopwords(self) -> frozenset[str]:
        """The words this language drops, normalised like tokens."""
        return self._stopwords

    def words(self, text: str) -> list[str]:
        """Lower-cased words of `text`, before stopwords and stemming."""
        if not text:
            return []
        # NFKC folds ligatures and full-width forms; casefold handles ß etc.
        normalized = unicodedata.normalize("NFKC", text).casefold()
        return [
            t for t in _TOKEN_RE.findall(normalized)
            if len(t) <= _MAX_TOKEN_LENGTH
        ]

    def analyze(self, text: str) -> list[str]:
        """The index terms of `text`, in order, with repeats.

        Stopwords are dropped; compound parts follow their compound; every
        term is stemmed. Repeats are kept because term frequency is part of
        the BM25 weight.
        """
        terms: list[str] = []
        for word in self.words(text):
            if word in self._stopwords:
                continue
            terms.append(word)
            terms.extend(
                part for part in self.decompounder.split(word)
                if part and part not in self._stopwords
            )
        if self._stemmer is None:
            return terms
        return self._stemmer.stemWords(terms)


@lru_cache(maxsize=32)
def analyzer_for(language: str) -> Analyzer:
    """The shared analyzer for a language. Unknown languages are unstemmed."""
    return Analyzer(language)
