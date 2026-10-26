# Development

    uv venv --python 3.12 .venv
    uv pip install --python .venv/bin/python -e '.[dev]'
    .venv/bin/python -m pytest

## Changing analysis output

Anything that changes the terms produced for the same input must:

1. bump `ANALYZER_VERSION` in `src/internetbook_analysis/analyzer.py`;
2. regenerate the golden files and review the diff:

       .venv/bin/python tests/regenerate_golden.py

3. bump the package's major version (0.x: minor), and say in the release
   notes that consumers must re-index.

## Compound dictionary

Danish compounds are split with a dictionary of corpus words
(`src/internetbook_analysis/dictionaries/danish_compounds.tsv.gz`; the rules
are in `compounds.py`). It is rebuilt from the search database's `word` table:

    kubectl exec -n search-db search-db-prod-1 -c postgres -- \
      psql -d search -c "\copy (SELECT word, frequency FROM word WHERE language = 'da' ORDER BY frequency DESC) TO STDOUT WITH CSV" \
      > words_da.csv
    .venv/bin/python scripts/build_compound_dictionary.py words_da.csv --language danish

A new dictionary changes analysis output: follow "Changing analysis output"
above. Rebuild occasionally (new subject areas), not routinely: compounds of
known words split without one.

## GiellaLT analysers

`morphology/kal-analyser-gt-desc.hfstol` (Greenlandic) and `morphology/fao-analyser-gt-desc.hfstol` (Faroese) come from GiellaLT's nightly Debian packages `giella-kal` and `giella-fao` (Apertium repository, `pool/main/g/`); `morphology/README.md` records the builds and their SHA-256. To update one:

1. Download the `giella-<code>_*.deb`, unpack it (`ar x`, then `tar xf data.tar.xz`), and copy `usr/share/giella/<code>/analyser-gt-desc.hfstol` over the bundled file.
2. Record the package version and SHA-256 in `morphology/README.md`.
3. Bump the language's version (`KAL_ANALYSER_VERSION` in `greenlandic.py`, `FAO_ANALYSER_VERSION` in `faroese.py`), then regenerate the golden files and review that language's file in `tests/golden/`.
4. Release; the indexer then re-indexes that language's content only.

## Greenlandic dictionary roots

`dictionaries/greenlandic_roots.txt.gz` lists the roots Oqaasileriffik's Greenlandic-English dictionary attests; `greenlandic.py` prefers them when choosing between readings. It is built from the dictionary's spreadsheets (CC BY-SA 4.0):

    git clone https://github.com/Oqaasileriffik/dicts /tmp/dicts
    .venv/bin/python scripts/build_greenlandic_roots.py "/tmp/dicts/2018 Chicago"

Rebuild it when the dictionary or the Greenlandic analyser changes: it is analysed with the bundled analyser. A new list changes analysis output: bump `KAL_ANALYSER_VERSION` and follow "Changing analysis output" above.

## Icelandic (BÍN)

Icelandic analysis reads BÍN through `islenska` and `islenska-data`, both pinned exactly in `pyproject.toml`. A new BÍN release or a new `islenska` changes the analysis: update both pins together, bump `ISL_ANALYSIS_VERSION` in `icelandic.py`, regenerate the golden files and review `tests/golden/is.json`.

## Release

1. Bump `__version__` in `src/internetbook_analysis/__init__.py` (the only
   place the version is set) and merge to `main`.
2. Publish a GitHub Release from `main` with tag `vX.Y.Z` matching it.

`.github/workflows/publish.yaml` then checks the tag against `__version__`
and that the commit is on `main`, runs the test matrix, builds, and uploads to
PyPI.

### Authentication: trusted publishing

PyPI trusts the workflow itself (OIDC), so there is no API token in the
repository or its secrets. One-time setup:

- **pypi.org:** under the project's *Publishing* settings (before the first
  release: your account's *Publishing* page, "Add a new pending publisher"),
  add a GitHub publisher with owner `gyldendalsolutions`, repository
  `internetbook_analysis` (underscore: the GitHub repository, not the PyPI
  project), workflow `publish.yaml`, environment `pypi`.
- **GitHub:** create the `pypi` environment under *Settings → Environments*.
  Add required reviewers and limit it to tags `v*`, so every upload is
  approved.

### Manual fallback

`scripts/release.sh` builds and uploads from your machine, with the same
authentication as systime-stackapi: a project-scoped token in `~/.pypirc`.

    [distutils]
      index-servers =
        pypi
        internetbook-analysis

    [internetbook-analysis]
      repository = https://upload.pypi.org/legacy/
      username = __token__
      password = # project-scoped token for internetbook-analysis

    scripts/release.sh --dry-run   # tests on 3.12 and 3.14, build, twine check
    scripts/release.sh             # the same, then upload and push tag vX.Y.Z

It refuses to release from anything but a clean `main` equal to
`origin/main`, a version already tagged, or a version already on PyPI, and
tags only after a successful upload. A GitHub Release made afterwards for that
tag does no harm: the workflow skips files already on PyPI.
