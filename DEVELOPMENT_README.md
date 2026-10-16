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

## Release

Same authentication as systime-stackapi: a project-scoped PyPI token in
`~/.pypirc`, used by twine on the releasing machine. Nothing secret is kept
in the repository or in CI.

    [distutils]
      index-servers =
        pypi
        internetbook-analysis

    [internetbook-analysis]
      repository = https://upload.pypi.org/legacy/
      username = __token__
      password = # project-scoped token for internetbook-analysis

The first upload creates the project on PyPI, which a project-scoped token
cannot do: use an account-scoped token for it, then create the project token.

To release:

1. Bump `__version__` in `src/internetbook_analysis/__init__.py` (the only
   place the version is set) and merge to `main`.
2. From an up-to-date, clean `main`:

       scripts/release.sh --dry-run   # tests on 3.12 and 3.14, build, twine check
       scripts/release.sh             # the same, then upload and push tag vX.Y.Z

The script refuses to release from anything but a clean `main` equal to
`origin/main`, a version already tagged, or a version already on PyPI. It tags
only after the upload succeeds, so every tag names a published version.
