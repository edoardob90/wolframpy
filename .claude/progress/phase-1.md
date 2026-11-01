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
Task 1: complete (commits e813292..d9bbff7, tests: uv run python -m wolframclient test → 294 run, errors=15, skipped=105, identical to baseline)
