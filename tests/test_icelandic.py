"""Icelandic morphology: lemmas and compound parts from BÍN (islenska)."""

import pytest

from internetbook_analysis import analyzer_for, analyzer_version
from internetbook_analysis.icelandic import ISL_ANALYSIS_VERSION, split


class TestSplit:
    def test_at_a_head_of_the_compounds_gender(self):
        assert split("myndband", "hk") == ["mynd", "band"]

    def test_a_short_head_after_a_genitive_joint(self):
        assert split("kennslubók", "kvk") == ["kennsla", "bók"]

    def test_no_short_head_inside_a_stem(self):
        assert split("kennari", "kk") == []      # not "kenn" + "ari"
        assert split("milljón", "kvk") == []     # not "mill" + "jón"

    def test_a_compound_head_is_split_in_turn(self):
        assert split("landbúnaðarráðherra", "kk") == ["land", "búnaður", "ráðherra"]

    def test_only_nouns_are_split(self):
        assert split("myndband", "so") == []


class TestAnalysis:
    @pytest.fixture(scope="class")
    def icelandic(self):
        return analyzer_for("is")

    def test_inflected_forms_share_their_lemma(self, icelandic):
        assert "skóli" in icelandic.analyze("skólanum")
        assert icelandic.analyze("hestarnir") == ["hestarnir", "hestur"]
        assert "fara" in icelandic.analyze("fóru")

    def test_listed_compounds_add_their_parts(self, icelandic):
        assert icelandic.analyze("kennslubókinni") == ["kennslubókinni", "kennslubók", "kennsla", "bók"]

    def test_subject_vocabulary_is_split_too(self, icelandic):
        # BÍN files "orðabók" under linguistics, not the general vocabulary.
        assert {"orð", "bók"} <= set(icelandic.analyze("orðabók"))

    def test_names_are_found_and_not_split(self, icelandic):
        assert icelandic.analyze("reykjavík") == ["reykjavík"]
        assert icelandic.analyze("Jóns") == ["jóns", "jón"]

    def test_unknown_words_are_kept_as_written(self, icelandic):
        assert icelandic.analyze("the") == ["the"]


def test_version():
    assert analyzer_version("is") == f"2+isl{ISL_ANALYSIS_VERSION}"
