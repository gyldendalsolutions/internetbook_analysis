"""Tests for text analysis and the BM25 split between documents and queries."""

from __future__ import annotations

import math

import pytest

from internetbook_analysis import (
    SPARSE_DIMENSIONS,
    Analyzer,
    analyzer_for,
    document_weights,
    idf,
    normalize_language,
    term_frequencies,
    to_sparsevec,
)


class TestNormalizeLanguage:
    @pytest.mark.parametrize("tag, expected", [
        ("da", "da"), ("da-DK", "da"), ("en_GB", "en"), (" DE ", "de"), ("", ""),
    ])
    def test_primary_subtag(self, tag, expected):
        assert normalize_language(tag) == expected


class TestAnalyzer:
    def test_danish_matches_postgres_danish_stems(self):
        """The stems Postgres's `danish` config produced in the evaluation."""
        terms = analyzer_for("da").analyze("Planterne fotosyntesen sygeplejersken patienterne")
        assert terms == ["plant", "fotosyntes", "sygeplejersk", "patient"]

    def test_stopwords_dropped_and_repeats_kept(self):
        terms = analyzer_for("da").analyze("Planten og planterne i haven")
        assert terms == ["plant", "plant", "hav"]

    def test_case_and_width_folded(self):
        assert analyzer_for("en").analyze("ＥＣＯＮＯＭＩＣＳ Economics") == ["econom", "econom"]

    def test_digits_kept(self):
        """ISBNs, years and chapter numbers stay searchable."""
        assert analyzer_for("da").analyze("ISBN 9788702388244, 1864") == [
            "isbn", "9788702388244", "1864",
        ]

    def test_overlong_tokens_dropped(self):
        assert analyzer_for("da").analyze("a" * 41 + " ord") == ["ord"]

    def test_unknown_language_is_unstemmed(self):
        """Faroese, Icelandic and Greenlandic have no Snowball stemmer."""
        analyzer = analyzer_for("kl")
        assert not analyzer.stems
        assert analyzer.analyze("Kalaallisut oqaatsit") == ["kalaallisut", "oqaatsit"]

    def test_regional_tag_uses_language_stemmer(self):
        assert analyzer_for("da-DK").analyze("planterne") == ["plant"]

    def test_decompounder_adds_parts_after_the_word(self):
        class Splitter:
            def split(self, word):
                return ["sygepleje", "praksis"] if word == "sygeplejepraksis" else []

        analyzer = Analyzer("da", decompounder=Splitter())
        assert analyzer.analyze("Sygeplejepraksis") == [
            analyzer_for("da").analyze("sygeplejepraksis")[0], "sygeplej", "praksis",
        ]

    def test_empty_text(self):
        assert analyzer_for("da").analyze("") == []


class TestBM25:
    def test_term_frequencies(self):
        assert term_frequencies(["a", "b", "a"]) == {"a": 2, "b": 1}

    def test_document_weights_saturate_and_normalise(self):
        k1, b = 1.2, 0.75
        weights = document_weights({1: 1, 2: 3}, document_length=10, average_length=10)
        norm = k1 * (1 - b + b * 10 / 10)
        assert weights[1] == pytest.approx(1 * (k1 + 1) / (1 + norm))
        assert weights[2] == pytest.approx(3 * (k1 + 1) / (3 + norm))
        assert weights[2] < 3 * weights[1]  # saturation

    def test_longer_documents_weigh_less(self):
        short = document_weights({1: 1}, document_length=5, average_length=10)[1]
        long = document_weights({1: 1}, document_length=20, average_length=10)[1]
        assert short > long

    def test_first_document_of_a_language_has_no_average(self):
        weights = document_weights({1: 1}, document_length=4, average_length=0)
        assert weights[1] == pytest.approx(1.0)

    def test_idf_never_negative(self):
        assert idf(document_frequency=100, document_count=100) > 0
        assert idf(1, 1000) == pytest.approx(math.log(1 + 999.5 / 1.5))

    def test_sparsevec_text_is_sorted_and_dimensioned(self):
        assert to_sparsevec({17: 1.5, 3: 0.25}) == f"{{3:0.25,17:1.5}}/{SPARSE_DIMENSIONS}"


class TestStopwords:
    """Snowball's stop.txt lists, as published (see NOTICE)."""

    @pytest.mark.parametrize("language, count", [
        ("da", 94), ("de", 231), ("en", 174), ("es", 308), ("fr", 154),
        ("it", 279), ("no", 172), ("sv", 114),
    ])
    def test_snowball_list_sizes(self, language, count):
        assert len(analyzer_for(language).stopwords) == count

    @pytest.mark.parametrize("language", ["fo", "is", "kl"])
    def test_no_list_without_a_stemmer(self, language):
        """As in Solr today, which uses the empty generic set for these."""
        assert analyzer_for(language).stopwords == frozenset()

    def test_norwegian_variants_share_one_list(self):
        assert analyzer_for("nb").stopwords == analyzer_for("nn").stopwords == analyzer_for("no").stopwords

    @pytest.mark.parametrize("language, text, kept", [
        ("de", "Die Pflanzen und der Baum", ["pflanz", "baum"]),
        ("fr", "Les plantes et la photosynthèse", ["plant", "photosynthes"]),
        ("sv", "Växterna och bladen", ["växt", "blad"]),
    ])
    def test_stopwords_removed(self, language, text, kept):
        assert analyzer_for(language).analyze(text) == kept

    def test_comments_are_not_words(self):
        from internetbook_analysis.analyzer import _parse_stopwords

        assert _parse_stopwords(" | a comment\nog   | and\n\ni | in\n") == {"og", "i"}
