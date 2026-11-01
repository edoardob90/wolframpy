#!/bin/bash
# Build the HTML documentation into docs/_build/html.
# Requires uv; the theme stylesheet is recompiled only if npx (Node.js) is available.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# API pages for every module; the two below need optional deps (matplotlib, astropy).
uv run --all-extras --group docs sphinx-apidoc --force --no-toc -o api ../wolframclient \
    ../wolframclient/language/hooks/matplotlib_backend.py \
    ../wolframclient/serializers/encoders/astropy.py
# The API root is reachable by URL only, not from the hand-written toctree.
{ printf ':orphan:\n\n'; cat api/wolframclient.rst; } > api/.root.rst && mv api/.root.rst api/wolframclient.rst
uv run --all-extras --group docs sphinx-build -W --keep-going -b html . _build/html

if command -v npx >/dev/null 2>&1; then
    npx sass ./wri_theme/static/mma.scss > ./_build/html/_static/mma.css
fi
