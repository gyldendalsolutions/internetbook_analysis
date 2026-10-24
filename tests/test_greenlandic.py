"""Greenlandic morphology: roots and derivation stems from the bundled analyser."""

import pytest

from internetbook_analysis import analyzer_for, analyzer_version
from internetbook_analysis.greenlandic import KAL_ANALYSER_VERSION, SEPARATOR, stems


class TestStems:
    def test_root_then_each_derivation(self):
        analysis = "ilinniar+Gram/IV+Gram/IV+VIK+Der/vn+SUAQ+Der/nn+N+Lok+Sg"
        assert stems(analysis) == ["ilinniar", "ilinniar0vik", "ilinniar0vik0suaq"]

    def test_inflection_and_enclitics_are_not_derivations(self):
        # N, Abs, Sg and the enclitic MI follow no Der/ tag.
        assert stems("ilinniar+VIK+Der/vn+N+Abs+Sg+MI") == ["ilinniar", "ilinniar0vik"]

    def test_a_root_that_is_not_a_word_gives_nothing(self):
        assert stems("2010+Num+Lok") == []

    def test_stems_survive_the_text_search_parser(self):
        # One token each: letters and the digit separator only.
        for term in stems("ilinniar+VIK+Der/vn+SUAQ+Der/nn+N+Lok+Sg"):
            assert all(c.isalpha() or c == SEPARATOR for c in term)


class TestAnalysis:
    @pytest.fixture(scope="class")
    def kl(self):
        return analyzer_for("kl")

    def test_words_sharing_a_root_share_terms(self, kl):
        school, big_school = kl.analyze("ilinniarfik"), kl.analyze("ilinniarfissuarmi")
        assert "ilinniar0vik" in school and "ilinniar0vik" in big_school
        assert "ilinniar0vik0suaq" in big_school and "ilinniar0vik0suaq" not in school

    def test_the_word_itself_comes_first(self, kl):
        assert kl.analyze("oqaatsit") == ["oqaatsit", "oqaaseq"]

    def test_the_lexicalised_reading_wins(self, kl):
        # Not also "ilip" + NIAR: that further derivation would connect
        # unrelated words.
        assert not any(t.startswith("ilip") for t in kl.analyze("ilinniarfissuarmi"))

    def test_a_lemma_is_not_read_as_another_word_inflected(self, kl):
        # "aamma" (and), not a possessive form of the noun "aak".
        assert kl.analyze("aamma") == ["aamma"]

    def test_unknown_words_are_kept_as_written(self, kl):
        assert kl.analyze("Hans Lynge") == ["hans", "lynge"]

    def test_names_with_endings_are_found_capitalised(self, kl):
        assert kl.analyze("danmarkimi") == ["danmarkimi", "danmark"]

    def test_a_common_word_is_not_read_as_a_name(self, kl):
        # Not the university "Ilinniarfissuaq", which would win on having no
        # derivations.
        assert "ilinniar0vik0suaq" in kl.analyze("ilinniarfissuarmi")

    def test_a_dictionary_root_beats_a_lexicalised_derivation(self, kl):
        # "silageqaaq" (the weather is fine): "sila", weather, not "silage";
        # "atuartitsissut" (teaching material): "atuar", read.
        assert kl.analyze("silageqaaq")[1] == "sila"
        assert kl.analyze("atuartitsissutitut")[1] == "atuar"

    def test_the_dictionary_does_not_override_an_attested_choice(self, kl):
        assert kl.analyze("ilinniarfik") == ["ilinniarfik", "ilinniar", "ilinniar0vik"]

    def test_dictionary_roots_are_bundled(self):
        from internetbook_analysis.greenlandic import dictionary_roots

        roots = dictionary_roots()
        assert len(roots) > 10_000 and {"sila", "inuk", "atuar"} <= roots

    def test_other_languages_are_unaffected(self):
        assert analyzer_for("da").analyze("ilinniarfik") == ["ilinniarfik"]


def test_version_per_language():
    assert analyzer_version("kl") == analyzer_version("kl-GL") == f"2+kal{KAL_ANALYSER_VERSION}"
    assert analyzer_version("da") == "2"
