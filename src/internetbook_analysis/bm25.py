"""BM25 weighting split between documents and queries.

The score of a document for a query is a dot product: the document side holds
the saturated, length-normalised term frequency, and the query side holds the
IDF. Keeping IDF out of the stored vectors means a change in document
frequencies needs no rewrite of the corpus.

pg_textsearch computes the same formula over the same tokens for the global
search path, so the constants must match the BM25 index options (k1, b).
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Mapping

#: BM25 term-frequency saturation. pg_textsearch's default; the BM25 index
#: options must use the same value.
BM25_K1 = 1.2
#: BM25 length normalisation. pg_textsearch's default; the BM25 index
#: options must use the same value.
BM25_B = 0.75

#: Dimension count of every BM25 sparse vector. Term ids index into it, so it
#: must exceed the largest id; pgvector's maximum is 10^9. Queries must build
#: their vectors with the same dimension, or the dot product is rejected.
SPARSE_DIMENSIONS = 1_000_000_000


def term_frequencies(terms: Iterable[str]) -> Counter[str]:
    """How often each term occurs."""
    return Counter(terms)


def document_weights(
    frequencies: Mapping[int, int],
    document_length: int,
    average_length: float,
    *,
    k1: float = BM25_K1,
    b: float = BM25_B,
) -> dict[int, float]:
    """The document side of BM25 for each term id.

    `average_length` is the language's average document length when the
    document is written. It drifts as the corpus changes, which skews the
    length normalisation slightly until the stats are recomputed and the
    vectors rewritten.
    """
    if average_length <= 0:
        average_length = max(document_length, 1)
    norm = k1 * (1 - b + b * document_length / average_length)
    return {
        term: tf * (k1 + 1) / (tf + norm)
        for term, tf in frequencies.items()
        if tf > 0
    }


def idf(document_frequency: int, document_count: int) -> float:
    """The query side of BM25 (the Lucene variant, which is never negative)."""
    return math.log(
        1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
    )


def to_sparsevec(weights: Mapping[int, float]) -> str:
    """pgvector's text form of a sparse vector, e.g. "{3:0.5,17:1.2}/1000000000".

    Indices are 1-based in pgvector and must be sorted and unique, which term
    ids (identity, starting at 1) are.
    """
    body = ",".join(
        f"{term}:{weight:.6g}" for term, weight in sorted(weights.items())
    )
    return f"{{{body}}}/{SPARSE_DIMENSIONS}"
