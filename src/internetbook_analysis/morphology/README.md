# GiellaLT morphological analysers

GiellaLT's descriptive analysers, compiled to HFST's optimised-lookup format
and used unmodified by `internetbook_analysis.giellalt` (loading and lookup),
`greenlandic` and `faroese` (what each language indexes).

| File | Language | Source | Debian package (Apertium nightly) | SHA-256 |
|---|---|---|---|---|
| `kal-analyser-gt-desc.hfstol` | Greenlandic | https://github.com/giellalt/lang-kal (with Oqaasileriffik) | `giella-kal` `0.2.0+g10802~347a8a87-1~sid1` | `770df352e3a6fe6e4f05dbf1aacb94e31eba1d0d9edd96287d9ff6279f818770` |
| `fao-analyser-gt-desc.hfstol` | Faroese | https://github.com/giellalt/lang-fao | `giella-fao` `0.2.0+g3968~2211c935-1~sid1` | `371da6bbb0da4ff46e89031c4846f75c91ebc85495fbb07da4682694607f4812` |

Each is `/usr/share/giella/<code>/analyser-gt-desc.hfstol` from its package.

Copyright 2005 The University of Tromsø. Licence: GNU General Public
License, version 3 or later; the full text is in `COPYING.giellalt`. These
files are under that licence, not the package's MIT licence.

Replacing one changes that language's analysis: bump its version
(`KAL_ANALYSER_VERSION` in `greenlandic.py`, `FAO_ANALYSER_VERSION` in
`faroese.py`), regenerate the golden files and re-index that language.
