"""Text analysis shared by internetbook indexing and search.

Turns text into the terms both BM25 mechanisms score: a sparse vector per
document (book-scoped search, brute force) and the token array a
pg_textsearch index reads (global search). The indexer and the search API
must analyse with the same version of this package. A query tokenised
differently from the documents it is matched against finds nothing for the
terms that differ, and nothing reports it.

`ANALYZER_VERSION` names the analysis output. It changes whenever the same
input would produce different terms, and a change means re-indexing.
"""

from internetbook_analysis.analyzer import (
    ANALYZER_VERSION,
    Analyzer,
    Decompounder,
    NoDecompounder,
    analyzer_for,
    analyzer_version,
    normalize_language,
)
from internetbook_analysis.bm25 import (
    BM25_B,
    BM25_K1,
    SPARSE_DIMENSIONS,
    document_weights,
    idf,
    term_frequencies,
    to_sparsevec,
)
from internetbook_analysis.query import TermStatistics, query_weights

__version__ = "0.3.0"

__all__ = [
    "ANALYZER_VERSION",
    "Analyzer",
    "BM25_B",
    "BM25_K1",
    "Decompounder",
    "NoDecompounder",
    "SPARSE_DIMENSIONS",
    "TermStatistics",
    "analyzer_for",
    "analyzer_version",
    "document_weights",
    "idf",
    "normalize_language",
    "query_weights",
    "term_frequencies",
    "to_sparsevec",
]
