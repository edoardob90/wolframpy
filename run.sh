#!/bin/bash
# Run the wolframclient CLI from this checkout (same as `uv run wolframclient`).
exec uv run --directory "$(dirname "${BASH_SOURCE[0]}")" --module wolframclient "$@"
