"""The query side of BM25.

A query's sparse vector holds the IDF of each query term, so that its dot
product with a document's vector (see bm25.document_weights) is the BM25
score. Terms absent from the corpus are dropped: they match nothing.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from internetbook_analysis.bm25 import idf


@dataclass(frozen=True)
class TermStatistics:
    """What the query side needs to know about one term in one language."""

    term_id: int
    document_frequency: int


def query_weights(
    terms: Iterable[str],
    statistics: Mapping[str, TermStatistics],
    document_count: int,
) -> dict[int, float]:
    """IDF weight per term id for an analysed query.

    A term repeated in the query counts once: BM25 weighs query terms by
    rarity, not by how often the user typed them.

    Args:
        terms: The query's terms, from Analyzer.analyze().
        statistics: Dictionary entries for those terms, by term.
        document_count: Documents in the language's corpus.
    """
    weights: dict[int, float] = {}
    for term in set(terms):
        stats = statistics.get(term)
        if stats is None or stats.document_frequency <= 0:
            continue
        weights[stats.term_id] = idf(stats.document_frequency, document_count)
    return weights
