# SDD ledger — plan: docs/MODERNIZATION_PLAN.md (Phase 1)

Spec: `.claude/specs/phase-1.md`. Todo: `.claude/todo/phase-1.md`.

Baseline (old runner, `python -m wolframclient test`, py3.12, all optional deps): 294 run, errors=15, skipped=105.
Kernel/coroutine setUpClass errors: 9 (no kernel). Pandas subTest errors: 5. Pillow test_mode_L: 1.

Pre-flight: Task 3's ruff pass consumes the pytest setup from Task 2 as its regression gate; Task 4's CI consumes the commands from Tasks 1–3; Task 5's docs build consumes the `docs` group from Task 1. No conflicts.

Ruling: the plan is a phased roadmap, not a task/brief-formatted plan; Phase 1's seven steps are regrouped into Tasks 1–6 in `.claude/todo/phase-1.md` — order follows dependencies (packaging → tests → lint) — cost if wrong: none, same scope.
Ruling: this file is the executing-plans ledger (instead of `.superpowers/sdd/`) — the user's workflow puts progress in `.claude/progress/` — cost if wrong: none.
Ruling: GitHub sub-issues not created; Phase 1 fits one PR and the plan already scopes this branch to Phase 1 — cost if wrong: Phases 2–4 get sub-issues later.

Task 0: complete (workflow docs; no tests)
Task 1: Ruling: `certifi` lower bound kept at `>=2017.4.17` (setup.py's floor) instead of the `>=2026.10.23` uv added by default — a library should not force a this-week certifi — cost if wrong: none.
Task 1: Ruling: `pytz` added to the dev group temporarily so the unchanged tests run; removed in Task 2 with the `zoneinfo` switch — cost if wrong: none.
Task 1: Ruling: `README.rst` stays as `readme` until Task 5 converts it — cost if wrong: none.
Task 1: complete (commits e813292..41f044d, tests: uv run python -m wolframclient test → 294 run, errors=15, skipped=105, identical to baseline)
Task 2: Kernel baseline (old runner + local Wolfram 14 kernel): 46 kernel/coroutine ok; 3 FAIL in test_kernel (test_many_failures_wrap, test_one_eval_many_msg_wrap, test_many_failures_wrap_async: newer kernels emit an extra syntax message) — pre-existing, out of Phase 1 scope. InvalidStateError traces from kernel threads on cancelled futures are pre-existing (pool cancellation bug, Phase 2).
Task 2: Ruling: data-dir helpers (`DATA_DIR`, `path_to_file_in_data_dir`) live in `tests/configure.py` and conftest exposes a `data_dir` fixture — unittest bodies call the helper as a function and importing from conftest is a pytest anti-pattern — cost if wrong: one move.
Task 2: Ruling: config stays a module (`tests/configure.py`) with a cached `get_config()` and PEP 562 `__getattr__`, not pure fixtures — keeps the unittest bodies' `from tests.configure import kernel_path` unchanged while reading the env var lazily — cost if wrong: small refactor if tests move to pytest style.
Task 2: Ruling: `cloud` gate = SAK present (not merely "a config file exists") — the old `skip_for_missing_config` ran 70 cloud tests into failure whenever a kernel-only config was set — cost if wrong: none.
Task 2: Ruling: `test_coroutine.py` moved to `IsolatedAsyncioTestCase` with per-test session/pool in asyncSetUp/asyncTearDown (verified against a local kernel: all pass); `test_async_cloud.py` keeps `run_in_loop` because it cannot be verified without credentials and `run_in_loop` already creates a loop on 3.14 — cost if wrong: async cloud tests may need the same conversion in Phase 2.
Task 2: Ruling: fixed two pre-existing harness bugs that were red in the baseline — `test_pandas` evaluated cases through the lazy `api.pandas` proxy that lacks `date_range`/`Index`/`Timestamp` (now uses the real module); `test_wl_pil.test_mode_L` used `fromarray(int8, mode="L")`, rejected by Pillow 13 (now uint8, asserts mode L, same expected bytes) — cost if wrong: none, library untouched.
Task 2: Ruling: PY2-only tests (`test_all_str_py2` ×2) and their data files (`allbytes.wl`, `allbytes.wxf`) deleted; `pytz` cases replaced by `datetime.timezone` fixed offsets (the pytz Europe/Rome case duplicated the existing ZoneInfo case); module helper `test_datetime()` renamed `sample_datetime()` so pytest stops collecting it — cost if wrong: none.
Task 2: complete (commits 41f044d..29b15d9, tests: uv run pytest → 186 passed, 163 skipped, 34 subtests passed; with local kernel: pytest -m kernel → 57 passed, 3 failed (pre-existing), 12 skipped (cloud))
Task 3: Ruling: mechanical fixes limited to UP (minus UP031/UP032, deferred to Phase 2 per plan), I001, F401 and W291/W292/W293 (the whitespace the pre-commit hooks force anyway); `ruff format` applied repo-wide (black-compatible, semantics-preserving) — cost if wrong: none, suite unchanged.
Task 3: Ruling: leftover findings are split — pervasive style rules (UP031, UP032, B904, B905, RUF012, RUF021, RUF022, RUF023) ignored globally with the phase that removes them; bug-signalling rules (F811, F821 incl. bug #5 `hashdict`, E722, RUF068, B008/B018/B020/B028, E741, SIM*) pinned in per-file-ignores so new code is still checked — the spec said "ignored in config", a 72-file per-file list would hide the signal — cost if wrong: config churn only.
Task 3: Ruling: `unicode_literals.compiler_flag` (0x200000) dropped from `compile()` flags in `externalevaluate.py` together with its `__future__` import — verified identical AST on py3 — cost if wrong: none.
Task 3: Ruling: pre-commit excludes `tests/data/` and `docs/wri_theme/`; trailing-whitespace keeps Markdown hard breaks; hooks stripped trailing whitespace after commas in `.m` files (outside strings) — cost if wrong: none.
Task 3: complete (commits 29b15d9..effd660, tests: uv run pytest → 186 passed, 163 skipped, 34 subtests passed; ruff check/format --check and pre-commit run --all-files clean)
Task 4: Ruling: added a `build` job asserting the wheel has no tests and ships `initkernel.m` (plan verification step 4, kept as a CI guard) and `uv lock --check` in lint; docs workflow builds and uploads an artifact only (Pages deploy is Phase 4); no release workflow (optional in plan) — cost if wrong: one more workflow later.
Task 4: Ruling: action versions taken from the current release tags (checkout v7, setup-uv v10, upload-artifact v7) — cost if wrong: none.
