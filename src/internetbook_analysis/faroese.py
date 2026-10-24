"""Faroese morphology: a word's lemma and compound parts as extra terms.

Faroese has no Snowball stemmer, so it was indexed as written: "skúli"
(school) did not match "skúlanum" (the school, dative). Nouns inflect for
case, number and definiteness, and compounds are formed as in Danish
("arbeiðsuppgávur" = "arbeið" + "uppgávur"). GiellaLT's analyser
(giellalt.py, morphology/README.md) gives each word's lemma, and a
compound's parts each with its lemma ("skúli+N+...+Cmp#bók+N+...").

A word is indexed, besides itself, with the lemma of its likeliest
reading, or with the lemmas of its parts if that reading is a compound:

    skúlanum          -> skúli
    arbeiðsuppgávur   -> arbeið, uppgáva
    skúlabøkurnar     -> skúlabók, skúli, bók

Which reading is likeliest:

- Readings marked as errors, and compound readings with a part shorter
  than MIN_PART_LENGTH letters, are dropped. The analyser forces foreign
  words into compounds of short, unrelated parts ("største" as "størur" +
  "te"); our Faroese content has much Danish and English in it. A word's
  own lemma may be short: "ár" (year), "á" (river).
- Of the rest, those with the fewest parts: a lexicalised compound or a
  name ("Ísland") over a split into unrelated words ("ísur" + "land").
- A lexicalised compound keeps the parts of its split reading too, so a
  search for one part finds it ("skúlabók" for "bók"), but only when the
  whole lemma ends with the split's last part. A split that does not
  ("málið", the language, as "máur" + "lið") reads a different word, and a
  name is not split at all ("Ísland" is not "ísur" + "land").

Measured on our Faroese content (2026-10-23, 186k word forms): the analyser
knows 57% of word forms and 81% of occurrences; the rest is mostly Danish
and English text, indexed as written. Checked against the hand-annotated
lemmas of the UD_Faroese-OFT treebank (2026-10-24, 8,136 words of Faroese
Wikipedia): a word's terms include its lemma, or a compound's parts, for
99% of words; most misses need the sentence to resolve ("fæst": "fáa" or
"fæstur").
"""

from __future__ import annotations

from functools import lru_cache

from internetbook_analysis import giellalt

#: Bumped with the bundled analyser (morphology/README.md) or with a change
#: to how its analyses become terms. Part of Faroese's analyzer version
#: (analyzer.analyzer_version).
FAO_ANALYSER_VERSION = "1"

MIN_PART_LENGTH = 3
MAX_TERMS = 8


def reading(analysis: str) -> list[str]:
    """The lemmas of one analysis: one, or one per compound part.

    "skúli+N+Msc+Sg+Gen+Indef+Cmp#bók+N+Fem+Sg+Nom+Indef" gives
    ["skúli", "bók"]. [] when a lemma is not a word.
    """
    lemmas = [segment.split("+")[0].lower() for segment in analysis.split("#")]
    return lemmas if all(lemma.isalpha() for lemma in lemmas) else []


class FaroeseMorphology:
    """A Decompounder (analyzer.Decompounder) for Faroese: a word's lemma or
    compound parts (see the module docstring)."""

    def split(self, word: str) -> list[str]:
        return list(_terms(word))


@lru_cache(maxsize=200_000)
def _terms(word: str) -> tuple[str, ...]:
    analyses = [a for a in giellalt.lookup("fao", word) if "Err/" not in a]
    readings = [
        r for r in (reading(a) for a in analyses)
        if r and (len(r) == 1 or all(len(lemma) >= MIN_PART_LENGTH for lemma in r))
    ]
    if not readings:
        return ()
    fewest = min(len(r) for r in readings)
    best = [r for r in readings if len(r) == fewest]
    terms = [lemma for r in best for lemma in r]
    names = {r[0] for a in analyses if "#" not in a and "+Prop" in a and (r := reading(a))}
    if fewest == 1:
        wholes = {r[0] for r in best} - names
        for r in readings:
            if len(r) > 1 and any(whole.endswith(r[-1]) for whole in wholes):
                terms.extend(r)
    out = dict.fromkeys(t for t in terms if t != word)
    return tuple(out)[:MAX_TERMS]
