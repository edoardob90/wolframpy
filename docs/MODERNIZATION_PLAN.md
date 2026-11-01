# wolframpy: code review and modernization plan

Review performed on commit a5762a4 (2026-11-01). Tracking issue: see repository issues.


## Context

`wolframpy` (github.com/edoardob90/wolframpy) is a fork of Wolfram Research's `WolframClientForPython` v1.4.1, ~15k lines of Python. The code still carries its Python 2.7 / 3.5 heritage: `from __future__` in 119 files, a vendored `six` shim with Jython branches, `pytz`, deprecated asyncio patterns. Packaging is a legacy `setup.py` (`python_requires>=3.5.3`, universal wheel), there is no `pyproject.toml`, no CI, no linter config, and the tests ship inside the wheel. `run.sh` already shells out to `uv run`, so the move to uv is half-started.

Decisions taken with the user:

- Minimum Python: **3.12** (test matrix 3.12 / 3.13 / 3.14). Every dependency has 3.12 and 3.13 wheels; no 3.13-only feature is needed, and 3.12 is the Ubuntu 24.04 default with EOL Oct 2028.
- Compatibility: keep the public API (`wolframclient` import name, `export`, `binary_deserialize`, `wl`, sessions, `Dispatch`); internals may be rewritten or deleted.
- Implementation scope on this branch: **Phase 1 only** (packaging + tooling). Phases 2–4 are the roadmap.

---

## Part A: Review findings

### A1. Packaging and repo hygiene (facts)

- `setup.py`: `python_requires>=3.5.3`, classifiers stop at 3.7, `test_suite='setup.load_tests'` (removed from setuptools), `url` points to wolfram.com, project URLs point to upstream. `setup.cfg` has `universal=1` and the deprecated `license_file` key.
- Version drift: `about.py` says 1.4.1, `PacletInfo.m` says 1.4.0, `CHANGELOG.md` ends at 1.1.10.
- Hard dependencies that are only imported lazily: `numpy`, `pytz` (used by nothing in library code, only tests), `aiohttp`/`requests`/`oauthlib` (cloud only), `pyzmq` (kernel only). `pandas`, `pyarrow`, `Pillow` are undeclared but have encoders and tests. A second, divergent dependency list lives in `cli/commands/setup.py` (dead command, no `handle`).
- `run.sh`: `--with zmq` installs the PyPI stub `zmq`, not `pyzmq`.
- `MANIFEST.in` + `find_packages()` ship `wolframclient/tests/**` and ~800 KB of binary test data in the wheel.
- No `.github/`, no pre-commit, no ruff/black/isort config, no lockfile. `.coveragerc` uses `timid=True`. `.gitignore` lacks `.venv`, `.ruff_cache`, `.pytest_cache`, `docs/_build`.
- Wolfram-internal artifacts committed: `scripts/re_build_WolframClient.xml` (Ant, needs `RE_ANTLIBRARY_HOME`), `docs/deploy.m`, `PacletInfo.m`.
- Docs: Sphinx 7.3 with custom `wri_theme`, SCSS compiled with `npx sass`, two divergent build scripts (`docs/build.sh` uv-based on py3.10, `docs/build_docs.sh` assumes tools on PATH). `docs/README.md` is self-described as AI-generated and factually wrong about both scripts. `docpages/install.rst` says "Python 3.5 or higher". `docs/requirements.txt` pins astropy, which the library does not use.

### A2. Test infrastructure (facts)

- Tests are `unittest.TestCase` under `wolframclient/tests/`; most files are not named `test_*.py` (`serializers/wxf_numpy.py`, `deserializers/wxf_deserialize.py`, ...). Discovery works only through the custom runner `cli/commands/test.py` with `pattern="*"`; plain pytest would find a fraction.
- `tests/configure.py` reads `WOLFRAMCLIENT_PY_JSON_CONFIG` at import time. Bugs: `_parse_config` reads the global instead of its argument (`configure.py:84,86`), `logger.warning("...", e)` with no placeholder (`:58,68,82`), only `OSError` caught around `json.load`. `local_config_sample.json` has `//` comments and is not valid JSON.
- Kernel tests (`test_kernel.py`, `test_coroutine.py`) have no skip for a missing kernel; cloud tests are gated by `skip_for_missing_config`.
- Flaky/wrong patterns: `test_coroutine.py:49-85` asserts timing before tasks run; `assertTrue(res, 2)` instead of `assertEqual`; fixed ports 12345-12347 in `externalevaluate/ev_loop.py` with no socket cleanup or recv timeout; module-level `LOOP = get_event_loop()`.

### A3. Confirmed bugs (reproduced in this session)

| # | Where | Symptom |
|---|-------|---------|
| 1 | `serializers/utils.py:33` `py_encode_text` encodes with `iso-8859-1` | `export('日本')` raises `UnicodeEncodeError` (default `wl` format) |
| 2 | `serializers/wxf.py:72-74` writes `len(name)` (chars) then `force_bytes(name)` | `export(wl.café, target_format='wxf')` produces corrupt WXF |
| 3 | `serializers/wl.py:58` `b"%.13f" % number` | `export(1e-20)` is `b'0.'`; `1.5e300` becomes a 40-digit garbage integer |
| 4 | `serializers/base.py:83` regex `^([A-Za-z]+/[A-Za-z]+?\|UTC)$` | `America/New_York` is exported as fixed offset `-5.`, DST lost |
| 5 | `utils/datastructures.py:52` undefined `hashdict` | `immutabledict + immutabledict` raises `NameError` |
| 6 | `evaluation/cloud/asynccloudsession.py:65-66`, `asyncoauth.py:35-38` use bare `ssl.SSLContext()` | With a custom `certificate`, `verify_mode=CERT_NONE` and no hostname check: TLS verification is silently disabled |
| 7 | `evaluation/cloud/oauth.py:43-50` `raise` inside its own `except Exception` | Server error messages never reach the user |
| 8 | `evaluation/kernel/kernelcontroller.py:289` `kill()` without `wait()` | Zombie kernel processes |

Other bugs reported by the audit and judged credible from the code (not individually executed): `wxfnumpyencoder.py:90` builds a `TypeError` but never raises it; `DefaultWXFEncoder.encode` tests `int` before `is True` so `True` becomes integer 1; `utils/encoding.py:86` iterates an Exception; `language/array.py:39` packs complex with scalar format; `pool.py:122-146` can kill a kernel loop when the caller's future was cancelled; `pool.stop()` never resets `_kernel_evaluation_loop_tasks`; `result.py:357,418` defines async `is_message_failure` twice and awaits a method object; `logging.disable()` used globally and without `finally` in `oauth.py`; mutable default dicts mutated in `cloudsession._post` and `oauth.signed_request`; `externalevaluate.py:212` depends on the `unicode_literals` name bound by the `__future__` import (must be removed together); `numpy.tostring` fallbacks (removed in NumPy 2).

### A4. Performance hot spots (for Phase 3)

- `utils/dispatch.py:123-134` `Dispatch.resolve` caches by the MRO class that matched, not by `type(arg)`; subclass instances walk the MRO on every call. Cache `type(arg) -> impl`.
- Each object encoded goes through `composition` → `partial` → `as_method` closure → `resolve` → generator; nested `chain.from_iterable` makes deep trees O(n·depth) to drain.
- `wxfencoder/utils.py:25` `varint_bytes` allocates `bytearray(9)` and slices per call; no fast path for `< 128`. `float_to_bytes` uses `pack_into` on a fresh bytearray instead of `Struct.pack`.
- `Encoder.__init__` calls `update_dispatch()` which takes a process-wide `multiprocessing.Lock` on every `export()`.
- Parser reads one byte at a time through `ExactSizeReader`; `ZipCompressedReader.read` is wrapped by `decorate(concatenate_bytes)` so every `read(1)` builds a generator and a `join`. Each token does `getattr(self, "token_for_…")`.
- `KernelLogger` thread wakes every 10 ms (`kernelcontroller.py:62-74`); use `poll(timeout)`.
- `wrap_response` in `request_adapter.py` imports both `requests` and `aiohttp` for every isinstance check.

### A5. Hygiene

- Two parallel WXF encoding stacks: generator-based `serializers/wxf.py` (used by `export`) and object-based `wxfencoder/{wxfexpr,wxfencoder,wxfexprprovider,serializer}.py` (used by tests and documented upstream). Keep for now; candidate for deprecation in Phase 4.
- Dead: `WolframDispatch.register_plugins/_update_plugins` (registry never filled), `cli/commands/setup.py`, `_KernelProcessDied`, Jython branches, `six.PY_35/36/37`, commented-out code in `wxfconsumer.py:249` and `result.py:379-410`.
- Duplicated: `serialize_mapping`/`serialize_association`; `consume_rule`/`consume_rule_delayed`; `consume_integer8/16/32/64`; functions redefined under the same name (ruff F811) in `builtin.py`, `numpy.py`, `encoding.py`.
- Typos: `__slot__` (`wxfexpr.py:261`), `__all__` lists `WXFConsumer` twice, base `_serialize_to_wxf(context, stream)` has swapped argument order vs subclasses, `Exception("...({}).", value_type)` never formatted.
- No type hints anywhere. `about.py` overrides the module's `__name__`.

---

## Part B: Roadmap

### Phase 1 (this branch): packaging and tooling

Goal: `uv sync && uv run pytest` works, CI is green, nothing user-facing changes.

1. **`pyproject.toml`** (new, replaces `setup.py`, `setup.cfg`, `MANIFEST.in`):
   - `[build-system]` = `hatchling` (simple, handles `include`/`exclude` and dynamic version from `wolframclient/about.py` via `[tool.hatch.version] path`). Package name stays `wolframclient` (distribution name: keep `wolframclient` too unless the user wants `wolframpy` on PyPI; note in README that it is a fork).
   - `requires-python = ">=3.12"`, classifiers 3.12/3.13/3.14, license `MIT`, URLs pointing to this fork.
   - Core deps: `numpy>=1.26` (used by deserializer fast path and documented as prerequisite), `certifi`. Optional groups (`[project.optional-dependencies]`): `kernel = ["pyzmq>=25"]`, `cloud = ["requests>=2.31", "oauthlib>=3.2"]`, `async = ["aiohttp>=3.9"]`, `pandas = ["pandas>=2.1", "pyarrow>=14"]`, `pillow = ["Pillow>=10"]`, `all = [...]`. Drop `pytz` entirely from runtime deps (tests that use it switch to `zoneinfo`, see step 4).
   - `[dependency-groups]`: `dev = ["pytest", "pytest-asyncio", "pytest-cov", "ruff", "pre-commit", "mypy"]`, `docs = [sphinx, pygments-mathematica, ...]` (replaces `docs/requirements.txt`).
   - `[project.scripts] wolframclient = "wolframclient.cli.dispatch:execute_from_command_line"` so `start_externalevaluate` stays reachable; `python -m wolframclient` keeps working via `__main__.py`.
   - `[tool.hatch.build]` exclude `wolframclient/tests/**` from the wheel (tests move anyway, step 4).
   - `[tool.ruff]`: `line-length = 95` (matches the existing black setting), `target-version = "py312"`, rule set `E, F, I, UP, B, SIM, RUF` plus `W`; `[tool.ruff.format]` replaces black. Carry over the sensible ignores from `cli/commands/refactor.py` (E501, E731, SIM105, SIM118, B006 for now).
   - `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `python_files = ["test_*.py", "*_test.py"]`, `asyncio_mode = "auto"`, markers `kernel`, `cloud`.
   - `[tool.coverage.run]` replaces `.coveragerc` (drop `timid`).
2. **uv**: `uv lock` committed; `run.sh` reduced to `uv run --module wolframclient "$@"` (or deleted; `uv run wolframclient` covers it). Fix the `zmq`→`pyzmq` mistake by deleting the `--with` list. Delete `run.py`, `setup.py`, `setup.cfg`, `MANIFEST.in`, `.coveragerc`, `cli/commands/setup.py`, `cli/commands/refactor.py` (replaced by ruff config), `scripts/re_build_WolframClient.xml`, `docs/deploy.m`. Keep `PacletInfo.m` only if the user still deploys it as a paclet; sync its version to `about.py` (ask in PR description; default: keep and bump to 1.4.1).
3. **Pre-commit** (`.pre-commit-config.yaml`): `ruff` (check + format), `uv-lock` hook, trailing-whitespace/end-of-file, `check-toml`. Add `.editorconfig`.
4. **Tests → top-level `tests/`**, run by pytest:
   - Move `wolframclient/tests/**` to `tests/`, rename modules to `test_*.py` (`serializers/wxf_numpy.py` → `tests/serializers/test_wxf_numpy.py`, etc.). Keep `unittest.TestCase` bodies unchanged; pytest runs them.
   - Replace `wolframclient/utils/tests.py` with `tests/conftest.py` providing `data_dir` (path to `tests/data`) and `path_to_file_in_data_dir`; delete `utils/tests.py` and the `module_path`-based lookup.
   - Rewrite `tests/configure.py` as conftest fixtures: read `WOLFRAMCLIENT_PY_JSON_CONFIG` lazily, fix the three bugs listed in A2, turn `local_config_sample.json` into valid JSON (comments moved to a README line).
   - Add `pytest.mark.kernel` / `pytest.mark.cloud` with auto-skip when no kernel path / credentials are configured, so `uv run pytest` is green on a machine without Mathematica. Replace `skip_for_jython` and the `PY2`-only skips (dead tests) with deletion.
   - Replace `pytz` usage in `tests/serializers/test_wl_serialization.py` with `zoneinfo.ZoneInfo`.
   - Replace module-level `LOOP`/`run_in_loop` in coroutine tests with `pytest-asyncio` (or `IsolatedAsyncioTestCase`). Only the test harness changes, not `wolframclient/utils/asyncio.py` (Phase 2).
   - Delete `cli/commands/test.py` (pytest replaces it) and the `wolframclient/tests/log/` placeholder.
5. **GitHub Actions** (`.github/workflows/ci.yml`): matrix 3.12/3.13/3.14 on ubuntu + one macOS + one Windows job; steps: `astral-sh/setup-uv`, `uv sync --all-extras --dev`, `uv run ruff check`, `uv run ruff format --check`, `uv run pytest -m "not kernel and not cloud" --cov`. Separate `docs.yml` building Sphinx with `uv run --group docs sphinx-build -W`. Optional `release.yml` publishing to PyPI via trusted publishing on tags.
6. **Mechanical ruff pass** limited to what tooling forces: `ruff check --fix` with `UP` (drops `from __future__`, `%`-format → f-strings is left for Phase 2), `I` (import sorting), `F401` (unused imports). Exception: `wolframclient/utils/externalevaluate.py` must keep its `__future__` import until line 212's `unicode_literals.compiler_flag` is removed (do both together, it is a one-line change). Run the full test suite before and after; the suite is the regression gate.
7. **Docs and metadata**: `README.rst` → `README.md` with fork notice, install (`uv add wolframclient[kernel]`), quickstart, dev setup (`uv sync`, `pre-commit install`, `uv run pytest`). Fix `docpages/install.rst` Python version. Delete the inaccurate `docs/README.md`, keep one build script (`docs/build.sh`, uv-based, target 3.12). Add `CHANGELOG.md` entries for 1.2–1.4 (from git log) and a new "Unreleased" section. Update `CONTRIBUTING.md` with the dev workflow. `.gitignore` additions. Bump `about.py` to `1.5.0.dev0` and add `__version__` as the single source (hatch dynamic).

### Phase 2: legacy removal and confirmed bug fixes

- Delete `utils/six.py`; replace `six.string_types`→`str`, `binary_type`→`bytes`, `buffer_types`→`(bytes, bytearray, memoryview)`, `BytesIO`→`io.BytesIO`, `iterable_types`→`collections.abc.Iterable` where used as a dispatch key; move `WINDOWS/LINUX/MACOS` flags into `utils/environment.py`. Drop all `PY2`/`JYTHON`/`PY_3x` branches (`wxfencoder/utils.py`, `constants.py`, `builtin.py`, `encoding.py`, `functional.py` `map` shim, `wxfparser.py`, `externalevaluate.py:142-154`).
- Delete `pytz` from `utils/api.py`; `serialize_tzinfo` handles `ZoneInfo` and `datetime.timezone` only. Replace `datetime.utcnow()`.
- `utils/asyncio.py`: use `asyncio.run` / `asyncio.get_running_loop`; `pool.py` use `loop.create_future()` and `create_task` consistently.
- Fix bugs 1–8 from A3 with regression tests: utf-8 in `py_encode_text`; encode name before measuring length in `WXFSerializer.serialize_symbol`; `repr(float)`-based WL float formatting (handles exponents, `inf`/`nan` → `Infinity`/`Indeterminate`); timezone regex accepting `[A-Za-z0-9_+\-]+(/[A-Za-z0-9_+\-]+)*`; `hashdict` → `immutabledict`; `ssl.create_default_context(cafile=...)`; restructure `_check_response`; `kill()` then `wait()`.
- Fix the credible-but-unexecuted items in A3 (uint64 raise, `True` vs `int` ordering, exception iteration, complex pack format, pool cancellation/restart, duplicate async `is_message_failure`, `logging.disable` → a logging filter on the oauth logger, mutable defaults, `numpy.tostring`).
- `%`-formatting and `.format` → f-strings (ruff UP031/UP032) now that six is gone.

### Phase 3: performance (measure with `wolframclient benchmark` before and after; keep that command)

- `Dispatch.resolve`: cache by concrete `type(arg)`; make `register` invalidate the cache under a `threading.Lock`; drop the per-`export()` `multiprocessing.Lock` by doing `update_dispatch` once after the registry changes (`sys.modules` check only when a new module appears).
- `varint_bytes`: single-byte fast path and `bytes` return; `float_to_bytes` → `STRUCT.pack`.
- Flatten the encoder call chain: `Encoder.encode` resolves once per object and calls the handler directly instead of `composition`+`partial`+`as_method`.
- Parser: read the whole buffer into `bytes`/`memoryview` when the input is in memory and index with an offset instead of `read(1)`; dispatch tokens via a dict of bound methods built once per instance; `parse_varint` on the memoryview; remove `decorate(concatenate_bytes)` from `ZipCompressedReader.read`.
- `KernelLogger`: `socket.poll()` instead of 10 ms sleep. `kernelcontroller`: default stdout/stderr to `DEVNULL` unless logging is enabled; register an `atexit` cleanup.
- `request_adapter.wrap_response`: check `sys.modules` before importing the other HTTP library.

### Phase 4: structure, typing, docs (optional, larger)

- Type hints on the public API (`export`, `binary_deserialize`, sessions, `Dispatch`) and `py.typed`; mypy in CI on those modules first.
- Deprecate the object-based `wxfencoder` stack (`WXFExprSerializer`, `WXFEncoder`, `WXFExprProvider`) with warnings for one minor release, then remove.
- Replace `utils/legacy.py` global flag with an explicit serializer option / `contextvars`.
- Consolidate duplicate `serialize_mapping`/`serialize_association`, `consume_rule*`, `consume_integerN`.
- `externalevaluate`: optional IPC transport (`ipc://` on POSIX) or ZMQ CURVE for shared hosts; document the trust model. Fix the `matplotlib_backend` hook (close figures, correct usage docstring) or drop it.
- Docs: `sphinx-autodoc-typehints`, move the hand-written `docpages` to MyST Markdown, deploy via GitHub Pages workflow.

---

## Critical files (Phase 1)

- New: `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml`, `.editorconfig`, `.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `tests/conftest.py`, `README.md`.
- Moved: `wolframclient/tests/**` → `tests/**` (renamed to `test_*.py`); `wolframclient/tests/data/` → `tests/data/`.
- Deleted: `setup.py`, `setup.cfg`, `MANIFEST.in`, `.coveragerc`, `run.py`, `wolframclient/utils/tests.py`, `wolframclient/cli/commands/{setup,refactor,test}.py`, `scripts/`, `docs/deploy.m`, `docs/README.md`, `docs/requirements.txt`, `docs/build_docs.sh`, `README.rst`.
- Edited: `wolframclient/about.py` (version), `run.sh`, `.gitignore`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/conf.py` (version via `importlib.metadata`), `docs/docpages/install.rst`, `docs/build.sh`, `PacletInfo.m` (version), `wolframclient/utils/externalevaluate.py` (one line, with its `__future__` import), plus the mechanical ruff edits across the package.

Reused as-is: `wolframclient/cli/dispatch.py` + `cli/utils.py` command discovery (console script target), `cli/commands/benchmark.py`, `cli/commands/start_externalevaluate.py`, the existing unittest bodies.

## Verification (Phase 1)

1. Baseline before touching code: `PYTHONDONTWRITEBYTECODE=1 python -m wolframclient test` with pandas/pyarrow/Pillow/pyzmq installed; record pass/fail counts (kernel and cloud tests are expected to error without a kernel/credentials; note the counts).
2. After: `uv sync --all-extras --dev`, then `uv run pytest -m "not kernel and not cloud"` must pass with the same number of serializer/deserializer/externalevaluate tests collected as the baseline (compare collected counts, not only "green").
3. `uv run ruff check` and `uv run ruff format --check` clean; `uv run pre-commit run --all-files` clean.
4. `uv build` then inspect the wheel: `unzip -l dist/*.whl | grep -c tests` must be 0; `initkernel.m` must be present.
5. `uv run wolframclient` prints the command list; `uv run python -c "from wolframclient.language import wl; from wolframclient.serializers import export; print(export(wl.Range(3)))"` prints `b'Range[3]'`.
6. `uv run --group docs sphinx-build -W docs docs/_build` succeeds.
7. Push the branch and confirm the GitHub Actions matrix is green on 3.12/3.13/3.14.
