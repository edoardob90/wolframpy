# Spec: Phase 1, packaging and tooling

Plan: [`docs/MODERNIZATION_PLAN.md`](../../docs/MODERNIZATION_PLAN.md), Part B, Phase 1.
Tracking issue: #1. Branch: `claude/modest-franklin-r6zb1h`. One PR.

## Goal

`uv sync && uv run pytest` works, CI is green, nothing user-facing changes in library
behaviour. Phases 2–4 are out of scope (no bug fixes from A3, no `six` removal, no
performance work) except where tooling forces a mechanical change.

## Decisions from planning

- **Python**: `requires-python = ">=3.12"`, classifiers and CI for 3.12 / 3.13 / 3.14.
- **Names**: import and distribution name stay `wolframclient`. README states it is a fork.
- **Build backend**: hatchling; version is dynamic from `wolframclient/about.py`
  (`[tool.hatch.version] path`). Version bumps to `1.5.0.dev0`.
- **Dependencies**: core `numpy>=1.26`, `certifi`. Extras: `kernel = pyzmq>=25`,
  `cloud = requests>=2.31, oauthlib>=3.2`, `async = aiohttp>=3.9`,
  `pandas = pandas>=2.1, pyarrow>=14`, `pillow = Pillow>=10`, `all` = union.
  `pytz` dropped from runtime deps; tests use `zoneinfo`. (`utils/api.py` keeps its lazy
  `pytz` reference until Phase 2: it is only resolved if a caller passes a pytz tzinfo.)
- **Dependency groups**: `dev` (pytest, pytest-asyncio, pytest-cov, ruff, pre-commit,
  mypy), `docs` (sphinx and friends; replaces `docs/requirements.txt`, no astropy).
- **Console script**: `wolframclient = "wolframclient.cli.dispatch:execute_from_command_line"`;
  `python -m wolframclient` keeps working.
- **Wheel contents**: no tests, no test data; `initkernel.m` must ship.
- **Ruff**: `line-length = 95`, `target-version = "py312"`, rules `E, F, W, I, UP, B, SIM, RUF`
  with ignores carried from the old `refactor` command (`E501, E731, SIM105, SIM118, B006`).
  The mechanical pass applies only what tooling forces: `UP` (removes `__future__`),
  `I`, `F401`. Any other rule that fires on existing code is ignored in config for now,
  with a comment pointing to the phase that will clean it up.
- **`externalevaluate.py`**: its `__future__` import is removed together with the
  `unicode_literals.compiler_flag` use at line ~212 (one-line change, flag is 0 on py3).
- **Tests**: move `wolframclient/tests/**` → `tests/**`, files renamed `test_*.py`,
  `unittest.TestCase` bodies unchanged. `tests/conftest.py` provides data-dir helpers;
  `wolframclient/utils/tests.py` deleted. Config is read lazily from
  `WOLFRAMCLIENT_PY_JSON_CONFIG`; the three `configure.py` bugs (A2) are fixed;
  `local_config_sample.json` becomes valid JSON. Markers `kernel` and `cloud` auto-skip
  when unconfigured. Jython / PY2-only tests are deleted. Coroutine tests move to
  `IsolatedAsyncioTestCase`/pytest-asyncio without changing `wolframclient/utils/asyncio.py`.
- **Deleted**: `setup.py`, `setup.cfg`, `MANIFEST.in`, `.coveragerc`, `run.py`,
  `wolframclient/utils/tests.py`, `cli/commands/{setup,refactor,test}.py`, `scripts/`,
  `docs/deploy.m`, `docs/README.md`, `docs/requirements.txt`, `docs/build_docs.sh`,
  `README.rst` (→ `README.md`), `wolframclient/tests/log/`.
- **Kept**: `PacletInfo.m` (version synced to `1.4.1`, the last released version;
  user to confirm in the PR whether the paclet is still deployed). `run.sh` reduced to
  `uv run --module wolframclient "$@"`.
- **CI**: `.github/workflows/ci.yml` (lint job + test matrix 3.12/3.13/3.14 on ubuntu,
  plus 3.12 on macOS and Windows; `pytest -m "not kernel and not cloud" --cov`),
  `.github/workflows/docs.yml` (`sphinx-build -W`). No release workflow in this phase.
- **Pre-commit**: ruff (check + format), `uv-lock`, trailing-whitespace, end-of-file-fixer,
  check-toml. Plus `.editorconfig`.

## Verification gates

1. Baseline (old runner, py3.12, all deps): 294 run, 15 errors, 105 skipped.
   9 errors are kernel/coroutine `setUpClass` without a kernel (expected); 5 pandas and
   1 Pillow error are pre-existing test-harness incompatibilities with pandas 3.1 /
   Pillow 13 (fixed in the test move, see progress rulings).
2. After: `uv run pytest -m "not kernel and not cloud"` green, with at least the same
   serializer/deserializer/externalevaluate test count as the baseline.
3. `ruff check`, `ruff format --check`, `pre-commit run --all-files` clean.
4. `uv build`; wheel has 0 test files and contains `initkernel.m`.
5. `uv run wolframclient` lists commands; `export(wl.Range(3))` → `b'Range[3]'`.
6. `uv run --group docs sphinx-build -W docs docs/_build` succeeds.
7. CI green on the pushed branch (after the user approves the push).
