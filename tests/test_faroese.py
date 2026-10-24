"""Faroese morphology: lemmas and compound parts from the bundled analyser."""

import pytest

from internetbook_analysis import analyzer_for, analyzer_version
from internetbook_analysis.faroese import FAO_ANALYSER_VERSION, reading


def test_reading_gives_each_parts_lemma():
    assert reading("skúli+N+Msc+Sg+Gen+Indef+Cmp#bók+N+Fem+Sg+Nom+Indef") == ["skúli", "bók"]
    assert reading("skúli+N+Msc+Sg+Dat+Def") == ["skúli"]
    assert reading("2010+Num") == []


class TestAnalysis:
    @pytest.fixture(scope="class")
    def fo(self):
        return analyzer_for("fo")

    def test_inflected_forms_share_their_lemma(self, fo):
        assert fo.analyze("skúlanum") == ["skúlanum", "skúli"]
        assert "skúli" in fo.analyze("skúli")

    def test_compounds_add_their_parts(self, fo):
        assert fo.analyze("arbeiðsuppgávur") == ["arbeiðsuppgávur", "arbeið", "uppgáva"]

    def test_a_lexicalised_compound_keeps_its_parts(self, fo):
        assert fo.analyze("skúlabøkurnar") == ["skúlabøkurnar", "skúlabók", "skúli", "bók"]

    def test_a_split_reading_another_word_is_not_used(self, fo):
        # "málið" (the language), not "máur" + "lið".
        terms = fo.analyze("málið")
        assert "mál" in terms and "lið" not in terms and "máur" not in terms

    def test_names_are_found_capitalised_and_not_split(self, fo):
        assert fo.analyze("føroyum") == ["føroyum", "føroyar"]
        assert fo.analyze("ísland") == ["ísland"]

    def test_a_short_lemma_is_kept(self, fo):
        # The length minimum is for compound parts, not a word's own lemma.
        assert fo.analyze("ársins") == ["ársins", "ár"]
        assert fo.analyze("áin") == ["áin", "á"]

    def test_short_part_splits_of_foreign_words_are_dropped(self, fo):
        # Danish "største", which the analyser reads as "størur" + "te".
        assert fo.analyze("største") == ["største"]

    def test_unknown_words_are_kept_as_written(self, fo):
        assert fo.analyze("the") == ["the"]


def test_version():
    assert analyzer_version("fo") == f"2+fao{FAO_ANALYSER_VERSION}"
