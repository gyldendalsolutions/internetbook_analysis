# internetbook-analysis

Text analysis and BM25 weighting shared by internetbook indexing and search.

The internetbook indexer and the search API must turn text into terms the same way: a query term the indexer spelled differently matches nothing, and nothing reports it. This package is the one implementation both use.

## What it does

- **Analysis:** tokenises, case-folds, drops stopwords, optionally adds compound-word parts, and stems with Snowball. Supported: Danish, English, German, Spanish, French, Italian, Norwegian and Swedish. Faroese, Icelandic and Greenlandic have no Snowball stemmer or stopword list; they keep every word, rather than borrowing a neighbour's rules.
- **Greenlandic, Faroese and Icelandic morphology:** Greenlandic and Faroese from GiellaLT's analysers, which are bundled (see below); Icelandic from BÍN, the Database of Icelandic Morphology, through the [islenska](https://github.com/mideind/BinPackage) package. Greenlandic words also get their root and derivation stems: `ilinniarfissuarmi` adds `ilinniar`, `ilinniar0vik` and `ilinniar0vik0suaq` (`greenlandic.py`). Faroese words also get their lemma, or a compound's parts: `skúlanum` adds `skúli`, `arbeiðsuppgávur` adds `arbeið` and `uppgáva` (`faroese.py`). Icelandic likewise: `skólanum` adds `skóli`, `kennslubókinni` adds `kennslubók`, `kennsla` and `bók` (`icelandic.py`). BÍN is licensed CC BY-SA 4.0 (Árni Magnússon Institute); see `NOTICE`.
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

`analyzer_version(language)` is the version a language's terms are written with: `ANALYZER_VERSION`, plus a language's own analysis version where it has one (Greenlandic: `2+kal1`, Faroese: `2+fao1`, Icelandic: `2+isl1`). Changing one language's analysis then re-indexes only that language's content.

## GiellaLT analysers and their licence

`src/internetbook_analysis/morphology/` holds GiellaLT's Greenlandic ([lang-kal](https://github.com/giellalt/lang-kal)) and Faroese ([lang-fao](https://github.com/giellalt/lang-fao)) analysers, bundled unmodified. It is licensed under the GNU GPL, version 3 or later, not under this package's MIT licence; see `NOTICE` and `morphology/README.md`, which also records the build it came from. It is read with [pyhfst](https://github.com/Rootroo-ltd/pyhfst), pinned exactly like snowballstemmer.

## Stopwords

The lists in `src/internetbook_analysis/stopwords/` are the Snowball project's `stop.txt` files, copied unmodified; their licence is in `NOTICE`. Solr's EXT:solr configsets use slightly edited copies of the same lists (English swaps `a` for `us`, Swedish has `sitta` for `sitt`, French adds ten forms). This package follows Snowball, not those edits.

## Constants that must match elsewhere

- `BM25_K1`, `BM25_B`: the `k1`/`b` options of the pg_textsearch BM25 index.
- `SPARSE_DIMENSIONS`: the dimension of every `sparsevec` written or queried.
