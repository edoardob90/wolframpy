# CLAUDE.md

Guidance for Claude Code (and humans) working in this repository.

## Project

`wolframpy` is a fork of Wolfram Research's `WolframClientForPython` 1.4.1. The import
name and distribution name stay `wolframclient`. Public API that must not break:
`wolframclient` import name, `export`, `binary_deserialize`, `wl`, the evaluation
sessions, `Dispatch`. Internals may change freely.

The modernization roadmap lives in [`docs/MODERNIZATION_PLAN.md`](docs/MODERNIZATION_PLAN.md),
tracked by issue #1.

## Commands

```bash
uv sync --all-extras          # install the package, all extras and the dev group
uv run pytest                 # tests; kernel/cloud tests auto-skip without config
uv run ruff check             # lint
uv run ruff format            # format
uv run pre-commit run --all-files
uv build                      # sdist + wheel
uv run wolframclient          # CLI (benchmark, start_externalevaluate)
```

Never edit `pyproject.toml` dependency lists or `uv.lock` by hand: use `uv add`,
`uv add --optional <extra>`, `uv add --group <group>`, `uv remove`, `uv lock`.

Kernel tests need `WOLFRAMCLIENT_PY_JSON_CONFIG` pointing to a JSON file with a
`"kernel"` key; cloud tests need `cloud_credentials`/`server` in the same file
(see `tests/local_config_sample.json`).

## Workflow

**One plan = one tracking issue = one or more sessions = one PR.**

1. **Plan.** Every plan gets a document under `docs/` (e.g. `docs/MODERNIZATION_PLAN.md`)
   and one GitHub tracking issue that links to it.
2. **Split only when needed.** If a plan is too large for one reviewable PR, split it
   into sub-issues of the tracking issue, one PR per sub-issue. Do not split a plan
   that fits in one PR.
3. **Sessions.** A plan (or sub-issue) may take several sessions; each session works
   through one or more tasks and keeps these folders current:

   | Folder | Contents |
   |---|---|
   | `.claude/todo/` | What is left to do for the current plan/phase, as a checklist. |
   | `.claude/progress/` | What has been done: one line per completed task with commits and the test command/result, plus every `Ruling:` (a decision that deviates from or fills a gap in the plan, with why and the cost if wrong). This is the ledger a new session resumes from. |
   | `.claude/specs/` | The decisions taken during planning that shape the code: scope, constraints, interfaces, chosen tools and versions, and what was explicitly ruled out. The binding authority when the plan is ambiguous. |

   Name files after the plan or phase (`phase-1.md`, `phase-2.md`, ...). Update
   `todo` and `progress` in the same commit as the work they describe.
4. **Resume.** A new session reads `specs/`, then `progress/`, then `todo/`, then
   `git log`, and continues at the first open item. Trust `progress/` and git over
   memory.
5. **Close.** When the PR is opened, tick the phase in the tracking issue and link
   the PR. When the PR merges, the `todo/` file for that phase can be emptied; the
   `progress/` and `specs/` files stay as the record.

## Conventions

- Python >= 3.12; CI matrix 3.12 / 3.13 / 3.14.
- Tests live in top-level `tests/`, named `test_*.py`, run by pytest. Existing
  `unittest.TestCase` bodies are fine. Bug fixes come with a regression test written
  first (red, then green).
- Ruff is the only linter/formatter (`line-length = 95`).
- Commits: conventional prefixes (`build:`, `test:`, `ci:`, `docs:`, `fix:`, `refactor:`,
  `perf:`, `chore:`).
