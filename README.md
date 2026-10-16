# internetbook-analysis

Text analysis and BM25 weighting shared by internetbook indexing and search.

The internetbook indexer and the search API must turn text into terms the same way: a query term the indexer spelled differently matches nothing, and nothing reports it. This package is the one implementation both use.

## What it does

- **Analysis:** tokenises, case-folds, drops stopwords, optionally adds compound-word parts, and stems with Snowball. Supported: Danish, English, German, Spanish, French, Italian, Norwegian and Swedish. Faroese, Icelandic and Greenlandic have no Snowball stemmer or stopword list; they are left unstemmed and keep every word, rather than borrowing a neighbour's rules.
- **BM25, split between documents and queries:**
  - The document side stores saturated, length-normalised term frequencies.
  - The query side applies IDF.
  - Their dot product is the BM25 score. Document vectors don't change when document frequencies do.
- **pgvector sparse vectors:** produces the text form of `sparsevec` values.

```python
from internetbook_analysis import (
    TermStatistics, analyzer_for, document_weights, query_weights,
    term_frequencies, to_sparsevec,
)

terms = analyzer_for("da").analyze("Planterne laver fotosyntese")
# ['plant', 'lav', 'fotosyntes']

# Document side: term ids come from the indexer's term dictionary.
ids = {"plant": 1, "lav": 2, "fotosyntes": 3}
doc = to_sparsevec(document_weights(
    term_frequencies(ids[t] for t in terms), len(terms), average_length=120.0,
))

# Query side: IDF from document frequencies.
stats = {"plant": TermStatistics(term_id=1, document_frequency=420)}
query = to_sparsevec(query_weights(analyzer_for("da").analyze("planter"), stats, 3_500_000))
```

## Versioning

`ANALYZER_VERSION` names the analysis output. It changes whenever the same input would produce different terms: a new stopword, tokeniser rule, decompounder or stemmer version. A change means re-indexing everything, so:

- Consumers pin this package exactly (`==`).
- `snowballstemmer` is pinned exactly here, and upgrading it is a new `ANALYZER_VERSION`.
- `tests/golden/` holds expected output for real sentences. A change to it is a change to `ANALYZER_VERSION`.

The package version is separate. Releases that don't change output (documentation, new helpers) keep `ANALYZER_VERSION`.

## Stopwords

The lists in `src/internetbook_analysis/stopwords/` are the Snowball project's `stop.txt` files, copied unmodified; their licence is in `NOTICE`. Solr's EXT:solr configsets use slightly edited copies of the same lists (English swaps `a` for `us`, Swedish has `sitta` for `sitt`, French adds ten forms). This package follows Snowball, not those edits.

## Constants that must match elsewhere

- `BM25_K1`, `BM25_B`: the `k1`/`b` options of the pg_textsearch BM25 index.
- `SPARSE_DIMENSIONS`: the dimension of every `sparsevec` written or queried.
