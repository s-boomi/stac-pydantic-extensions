# Contributing to stac-pydantic-extensions

Thanks for taking the time to contribute! This document covers how to get set up, the
conventions the codebase follows, and how to submit changes.

## Getting started

The project uses [uv](https://docs.astral.sh/uv/) for dependency management and packaging.

```bash
git clone https://github.com/s-boomi/stac-pydantic-extensions.git
cd stac-pydantic-extensions
uv sync --group dev
```

This creates a `.venv` and installs the package plus all dev dependencies (pytest, ruff, ty,
pre-commit, ...).

Install the pre-commit hooks so linting/formatting run automatically on each commit:

```bash
uv run pre-commit install
```

## Running the test suite

```bash
uv run pytest --cov stac_pydantic_extensions --cov-report term-missing
```

Tests live under `tests/`, mirroring the extensions they cover (`test_eo.py`, `test_raster.py`,
...). Test fixtures and sample STAC items live under `tests/extensions/data-files/`.

When adding a new extension or a new migration path, add:

- a fixture item under `tests/extensions/data-files/<extension>/`,
- tests covering read access (`extended_item.ext.<prefix>.<field>`), adding/removing the
  extension, and — if relevant — migration from older schema versions.

## Linting, formatting and type checking

```bash
uv run pre-commit run --all-files   # ruff lint + format, tombi (toml), etc.
uv run ty check                     # static type checking
```

Both run in CI on every pull request and must pass before merging.

## Code conventions

- Extensions follow the pattern in `stac_pydantic_extensions/extensions/`: one module per
  extension, with a `..._V1_0_0`-style field model per historical schema version, a current
  `XyzFields` model, and an `XyzExtension` subclassing `BaseExtension`. If you're adding a new
  extension, `eo.py` and `raster.py` are the most complete examples to copy from, since they also
  implement band merging and migration.
- New extensions must be registered in `stac_pydantic_extensions/_registry.py`
  (`AVAILABLE_EXTENSIONS`).
- Field models use Pydantic's `alias_generator` (via `prefix_alias`) to add the extension's
  namespace prefix (`eo:`, `raster:`, ...) automatically — don't hardcode prefixed field names
  in the model itself.
- Validators for cross-cutting rules (percentages, azimuth/elevation ranges, projection codes,
  DOIs, ...) belong in `validators.py` rather than being duplicated per-extension.
- Prefer `from __future__ import annotations` and modern typing (`X | None`, PEP 604 unions) —
  this matches the rest of the codebase and the `requires-python = ">=3.13"` target.

## Migrations between extension versions

If a STAC extension you're implementing has had breaking schema changes (most have), each old
field model should implement `migrate(stac_object, version)` to produce the next version's
field model, and `_add_bands_to_obj` (or an equivalent) if fields moved to/from `bands`. See
`ElectroOpticalFields_V1_0_0._migrate_to_1_1_0` / `_migrate_to_2_0_0` in `eo.py` for the
reference implementation. Add a corresponding test in `tests/test_band_migration.py` or a
dedicated `test_<extension>.py`.

## Submitting changes

1. Fork the repo and create a branch off `main`.
2. Make your changes, with tests for any new behavior.
3. Bump the version in `pyproject.toml` if the change should be released (maintainers may also
   do this at release time — ask if unsure).
4. Open a pull request against `main`. CI (tests across supported Python versions, pre-commit,
   type checks) must pass.
5. Keep PRs focused — one extension or one fix per PR makes review much easier.

## Reporting bugs / requesting features

Please open an issue at
[github.com/s-boomi/stac-pydantic-extensions/issues](https://github.com/s-boomi/stac-pydantic-extensions/issues)
with a minimal reproducible example (a STAC item snippet plus the code you ran) for bugs, or a
short description of the use case for feature requests.

## Code of conduct

Be respectful and constructive. Disagreements about code are fine; personal attacks aren't.
