# AGENTS.md

## Cursor Cloud specific instructions

This is a freshly initialized Python repository (AGPL-3.0 licensed). There is no application code, no dependency manifests, and no services to run yet.

### Environment

- **Python**: 3.12.3 (system, `/usr/bin/python3`). `python3.12-venv` must be installed for `python3 -m venv` to work (the system image does not include it by default).
- **Virtual env**: `.venv` at the repo root. Activate with `source .venv/bin/activate`.
- **Dev tools installed in venv**: `pytest`, `ruff` (linter/formatter).

### Common commands

| Task | Command |
|------|---------|
| Activate venv | `source .venv/bin/activate` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Run tests | `pytest` |

### Gotchas

- The system Python does not have the `python` alias — use `python3` outside the venv, or activate the venv first.
- `python3-venv` / `python3.12-venv` is required but not pre-installed on the base image. The update script handles this.
