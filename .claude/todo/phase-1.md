# Todo: Phase 1, packaging and tooling

Spec: [`../specs/phase-1.md`](../specs/phase-1.md). Ledger: [`../progress/phase-1.md`](../progress/phase-1.md).

- [x] Task 0: workflow docs (`CLAUDE.md`, `.claude/{todo,progress,specs}`)
- [x] Task 1: `pyproject.toml` (hatchling, extras, groups, scripts), `uv.lock`, version `1.5.0.dev0`; delete `setup.py`, `setup.cfg`, `MANIFEST.in`, `.coveragerc`, `run.py`; slim `run.sh`; `.gitignore`
- [ ] Task 2: tests → top-level `tests/` with pytest, conftest, lazy config, `kernel`/`cloud` markers, `zoneinfo`, async tests; delete `utils/tests.py`, `cli/commands/test.py`
- [ ] Task 3: ruff config + mechanical pass, `.pre-commit-config.yaml`, `.editorconfig`; delete `cli/commands/{refactor,setup}.py`
- [ ] Task 4: GitHub Actions `ci.yml` and `docs.yml`
- [ ] Task 5: docs and metadata (`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, Sphinx config/build script, `install.rst`, `PacletInfo.m`; delete Wolfram-internal build files)
- [ ] Task 6: full verification (wheel contents, CLI, docs build), final review, PR
