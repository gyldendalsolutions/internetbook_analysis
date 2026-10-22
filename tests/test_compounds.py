"""Compound splitting rules, on a small dictionary."""

from internetbook_analysis.compounds import DictionaryDecompounder

import snowballstemmer

STEM = snowballstemmer.stemmer("danish").stemWord
WORDS = {
    "sundhed": 900, "pleje": 700, "vand": 800, "kraftværk": 60, "patient": 500,
    "person": 400, "fremtid": 300, "tiden": 2000, "frem": 1500, "antibiotika": 80,
    "behandling": 600, "antibiotikabehandling": 205, "barn": 300, "vogn": 90,
}


def split(word, words=WORDS):
    return DictionaryDecompounder(words, STEM).split(word)


def test_two_known_words():
    assert split("vandkraftværk") == ["vand", "kraftværk"]


def test_linking_s_and_e():
    assert split("sundhedspleje") == ["sundhed", "pleje"]
    assert split("barnevogn") == ["barn", "vogn"]


def test_frequent_words_stay_whole():
    """Frequent compounds tend to be opaque, and are searchable as they are."""
    assert split("antibiotikabehandling") == []


def test_short_words_and_parts_stay_whole():
    assert split("frempeg") == []          # under 8 letters


def test_inflection_is_not_compounding():
    """'patienterne' stems to 'patient': the ending is the stemmer's job,
    even with 'erne' in the dictionary."""
    assert split("patienterne", {**WORDS, "erne": 5000}) == []


def test_parts_must_beat_the_whole_word():
    assert split("fremtiden", {**WORDS, "fremtiden": 5}) == ["frem", "tiden"]
    assert split("fremtiden", {**WORDS, "fremtiden": 49, "frem": 10, "tiden": 10}) == []


def test_unknown_parts():
    assert split("xyzzyplugh") == []
