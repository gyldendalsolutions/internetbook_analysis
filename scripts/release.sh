#!/usr/bin/env bash
# Build internetbook-analysis, upload it to PyPI, and tag the release.
#
# Authentication is the same as for systime-stackapi: twine reads a
# project-scoped PyPI token from ~/.pypirc. Nothing secret is kept in the
# repository or in CI.
#
#   [distutils]
#     index-servers =
#       pypi
#       internetbook-analysis
#
#   [internetbook-analysis]
#     repository = https://upload.pypi.org/legacy/
#     username = __token__
#     password = pypi-...   # project-scoped token for internetbook-analysis
#
# The very first upload creates the project on PyPI, which a project-scoped
# token cannot do: use an account-scoped token for that one upload, then
# create the project token and switch to it.
#
# Usage:
#   scripts/release.sh            # test, build, check, ask, upload, tag
#   scripts/release.sh --dry-run  # test, build and check only
#   scripts/release.sh --yes      # don't ask before uploading
#
# Requires: git, uv (twine is run through uvx).

set -euo pipefail

REPOSITORY="internetbook-analysis"
PACKAGE="internetbook-analysis"

dry_run=false
assume_yes=false
for arg in "$@"; do
    case "$arg" in
        --dry-run) dry_run=true ;;
        --yes) assume_yes=true ;;
        -h|--help) sed -n '2,29p' "$0"; exit 0 ;;
        *) echo "Unknown option: $arg" >&2; exit 2 ;;
    esac
done

cd "$(git rev-parse --show-toplevel)"

fail() { echo "release: $*" >&2; exit 1; }

# ─── Preconditions ──────────────────────────────────────────────────────────

[[ -z "$(git status --porcelain)" ]] || fail "working tree is not clean"

branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "main" ]] || fail "releases are made from main, not $branch"

git fetch --quiet --tags origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] \
    || fail "local main differs from origin/main; pull or push first"

version="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' src/internetbook_analysis/__init__.py)"
[[ -n "$version" ]] || fail "could not read __version__"
tag="v$version"

git rev-parse -q --verify "refs/tags/$tag" >/dev/null \
    && fail "tag $tag already exists; bump __version__ first"

status="$(curl -s -o /dev/null -w '%{http_code}' "https://pypi.org/pypi/$PACKAGE/$version/json")"
[[ "$status" == "404" ]] || fail "$PACKAGE $version is already on PyPI (HTTP $status)"

analyzer_version="$(sed -n 's/^ANALYZER_VERSION = "\(.*\)"$/\1/p' src/internetbook_analysis/analyzer.py)"
echo "Releasing $PACKAGE $version (ANALYZER_VERSION $analyzer_version) from $(git rev-parse --short HEAD)"

# ─── Test, build, check ─────────────────────────────────────────────────────

# The lowest and highest supported Pythons; CI covers the ones between.
for python in 3.12 3.14; do
    echo "Testing on Python $python"
    uv run --quiet --isolated --python "$python" --with pytest --with-editable . \
        python -m pytest -q
done

rm -rf dist
uv build --quiet
uvx --quiet twine check --strict dist/*
ls -l dist

if $dry_run; then
    echo "Dry run: not uploading or tagging."
    exit 0
fi

# ─── Upload and tag ─────────────────────────────────────────────────────────

if ! $assume_yes; then
    read -r -p "Upload $PACKAGE $version to PyPI and push tag $tag? [y/N] " answer
    [[ "$answer" == "y" || "$answer" == "Y" ]] || fail "aborted"
fi

uvx twine upload --repository "$REPOSITORY" dist/*

# Tagged only after a successful upload: a tag must always name a version
# that exists on PyPI.
git tag -a "$tag" -m "$PACKAGE $version (ANALYZER_VERSION $analyzer_version)"
git push origin "$tag"

echo "Released $PACKAGE $version: https://pypi.org/project/$PACKAGE/$version/"
