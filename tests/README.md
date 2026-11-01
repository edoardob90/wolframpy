# Tests

Run with `uv run pytest`. Tests marked `kernel` need a local Wolfram kernel and tests
marked `cloud` need Wolfram Cloud credentials; both are skipped unless configured.

To enable them, copy `local_config_sample.json` to `local_config.json` (git-ignored),
fill in the values you have, and point `WOLFRAMCLIENT_PY_JSON_CONFIG` at it:

```bash
WOLFRAMCLIENT_PY_JSON_CONFIG=tests/local_config.json uv run pytest -m kernel
```

Keys: `kernel` (path to `WolframKernel`) enables kernel tests; `cloud_credentials.SAK`
enables cloud tests; `server` and `ApiOwner` are needed by some cloud tests.
Set `WOLFRAMCLIENT_PY_LOG_FILE` to also log to a file.
