"""Tests for the query side of BM25."""

import pytest

from internetbook_analysis import TermStatistics, analyzer_for, idf, query_weights


def test_idf_per_known_term():
    stats = {
        "plant": TermStatistics(term_id=3, document_frequency=10),
        "fotosyntes": TermStatistics(term_id=8, document_frequency=2),
    }
    weights = query_weights(analyzer_for("da").analyze("Planterne og fotosyntesen"), stats, 1000)
    assert weights == {3: pytest.approx(idf(10, 1000)), 8: pytest.approx(idf(2, 1000))}
    assert weights[8] > weights[3]  # rarer weighs more


def test_unknown_and_absent_terms_dropped():
    stats = {"plant": TermStatistics(term_id=3, document_frequency=0)}
    assert query_weights(["plant", "ukendt"], stats, 1000) == {}


def test_repeated_query_term_counts_once():
    stats = {"plant": TermStatistics(term_id=3, document_frequency=10)}
    assert query_weights(["plant", "plant"], stats, 1000) == query_weights(["plant"], stats, 1000)
