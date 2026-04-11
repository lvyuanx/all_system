# Task Specification

> Scope anchor for the task. Update only when goals or constraints change, and log the reason in PROGRESS.md.

## Task Shape

- **Shape**: `single-full`

## Goals

- Add a field data source metadata API for the form designer in `flow_engine`.
- Return registered field data source metadata in a designer-friendly JSON shape.
- Preserve backward compatibility for legacy `default_config` and `options_config` behavior.
- Cover the new endpoint and metadata export with focused tests.

## Non-Goals

- No changes to `docs/**`, `prd.txt`, `tasks\\表单设计器数据源类机制实施任务.md`, `.ralphy/progress.txt`, `.ralphy-worktrees`, or `.ralphy-sandboxes`.
- No unrelated refactors outside `flow_engine` and files directly related to the form designer data source mechanism.
- No redesign of the existing designer UI.

## Constraints

- Keep changes minimal and scoped to the field data source mechanism.
- The metadata response must expose `key`, `label`, `data_type`, `support_components`, `support_default`, `support_options`, and `params_schema`.
- Tests and lint/check commands must pass before completion.

## Environment

- **Project root**: `D:\projects\all_system`
- **Language/runtime**: `Python / Django`
- **Package manager**: `pip`
- **Test framework**: `django test`
- **Build command**: `.venv\Scripts\python.exe manage.py test`
- **Existing test count**: `flow_engine tests in a single module`

## Deliverables

- Metadata export helper for registered field data sources.
- JSON endpoint for the form designer to fetch field data source metadata.
- Tests covering metadata export and the new API response.

## Done-When

- [ ] Registered data source metadata can be listed programmatically.
- [ ] A read-only endpoint returns the metadata payload for the designer.
- [ ] Legacy `default_config` and `options_config` flows remain untouched.
- [ ] Tests pass.
- [ ] Lint/check passes.
- [ ] Changes are committed with a descriptive message.

## Final Validation Command

```bash
.venv\Scripts\python.exe manage.py test flow_engine && .venv\Scripts\python.exe -m ruff check flow_engine
```
