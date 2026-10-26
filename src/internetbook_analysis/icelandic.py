"""Icelandic morphology: a word's lemma and compound parts as extra terms.

Icelandic has no Snowball stemmer, so it was indexed as written: "skóli"
(school) did not match "skólanum" (the school, dative). Nouns inflect for
case, number and definiteness, verbs and adjectives heavily too, and
compounds are formed freely. BÍN, the Database of Icelandic Morphology
(Árni Magnússon Institute), lists the inflections of the language's
vocabulary; the islenska package (Miðeind) looks words up in it and guesses
the structure of compounds BÍN does not list.

A word is indexed, besides itself, with its lemmas, and with a compound's
parts:

    skólanum         -> skóli
    kennslubókinni   -> kennslubók, kennsla, bók
    myndbandið       -> myndband, mynd, band

islenska splits only compounds BÍN does not list, and BÍN lists most, so a
listed compound is split here: at the longest ending that is a noun of the
compound's own gender (a compound takes its head's), after a beginning that
is a form of a word in BÍN, both at least MIN_PART_LENGTH letters. A head
one letter shorter ("bók", "mál", "rit") is accepted after a genitive
joint, a beginning ending in -s, -a or -u ("kennslu|bók", "orða|bók"):
splits inside a stem ("kenn|ari", "mill|jón") have none. A head that is
itself a compound is split in turn: "landbúnaðarráðherra" gives "land",
"búnaður" and "ráðherra". Names are
not split ("Reykjavík" is not "reykur" + "vík"), and islenska's guesses are
used only for words BÍN does not list: it guesses at known words too.

Measured on our Icelandic content (2026-10-23, 113k word forms): BÍN knows
83% of word forms and 92% of occurrences; the rest is mostly English and
abbreviations, indexed as written. About a third of words get compound
parts, about nine in ten of them sensible; the rest are etymological or
wrong ("einstaklingur" as "einstak" + "lingur").
"""

from __future__ import annotations

import threading
from functools import lru_cache

#: Bumped with the pinned islenska or islenska-data (BÍN) version, or with a
#: change to how lookups become terms. Part of Icelandic's analyzer version
#: (analyzer.analyzer_version).
ISL_ANALYSIS_VERSION = "1"

MIN_PART_LENGTH = 4
MAX_TERMS = 8
#: Endings of a compound's beginning that join it in the genitive.
_GENITIVE_JOINTS = ("s", "a", "u")

#: BÍN's noun classes: masculine, feminine, neuter.
_NOUNS = frozenset({"kk", "kvk", "hk"})


def _is_name(lemma: str) -> bool:
    """BÍN capitalises names' lemmas ("Reykjavík", "Jón"). Its sections
    cannot tell: they also divide words by subject ("orðabók" is filed under
    linguistics, not the general vocabulary)."""
    return lemma[:1].isupper()


_lock = threading.Lock()
_bin = None


def _db():
    global _bin
    with _lock:
        if _bin is None:
            from islenska import Bin

            _bin = Bin()
    return _bin


@lru_cache(maxsize=200_000)
def _listed(form: str) -> frozenset[tuple[str, str]]:
    """(lemma, class) of the words, not names, BÍN lists `form` as."""
    return frozenset(
        (e.ord.lower(), e.ofl) for e in _db().lookup(form)[1]
        if e.bin_id != 0 and "-" not in e.ord and not _is_name(e.ord)
    )


def split(lemma: str, word_class: str, depth: int = 2) -> list[str]:
    """A listed noun compound's parts: [beginning's lemmas..., head], or []."""
    if word_class not in _NOUNS or depth == 0:
        return []
    for i in range(MIN_PART_LENGTH, len(lemma) - MIN_PART_LENGTH + 2):  # longest head first
        head = lemma[i:]
        if len(head) < MIN_PART_LENGTH and not lemma[:i].endswith(_GENITIVE_JOINTS):
            continue
        if (head, word_class) in _listed(head):
            # The beginning as written is long enough (the loop's start); its
            # lemma may be shorter ("orða", genitive plural of "orð").
            candidates = {(l, c) for l, c in _listed(lemma[:i]) if len(l) >= MIN_PART_LENGTH - 1}
            # A beginning is usually a noun: its noun lemmas, when it has any,
            # rather than every word it could be a form of.
            nouns = {l for l, c in candidates if c in _NOUNS}
            beginning = sorted(nouns or {l for l, _ in candidates})
            if beginning:
                return [*beginning, *(split(head, word_class, depth - 1) or [head])]
    return []


class IcelandicMorphology:
    """A Decompounder (analyzer.Decompounder) for Icelandic: a word's lemmas
    and compound parts (see the module docstring)."""

    def split(self, word: str) -> list[str]:
        return list(_terms(word))


@lru_cache(maxsize=200_000)
def _terms(word: str) -> tuple[str, ...]:
    entries = _db().lookup(word, auto_uppercase=True)[1]
    listed = [e for e in entries if e.bin_id != 0]
    terms: list[str] = []
    for entry in listed or entries:
        lemma = entry.ord.lower()
        if "-" in lemma:
            # islenska's guess at a compound BÍN does not list: its parts,
            # the beginnings as their lemmas where BÍN lists them.
            parts = lemma.split("-")
            terms.append("".join(parts))
            if all(len(p) >= MIN_PART_LENGTH for p in parts):
                for part in parts[:-1]:
                    lemmas = sorted(l for l, _ in _listed(part) if len(l) >= MIN_PART_LENGTH)
                    terms.extend(lemmas or [part])
                terms.append(parts[-1])
        elif lemma.isalpha():
            terms.append(lemma)
            if not _is_name(entry.ord):
                terms.extend(split(lemma, entry.ofl))
    out = dict.fromkeys(t for t in terms if t != word and t.isalpha())
    return tuple(out)[:MAX_TERMS]
