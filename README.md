# stac-pydantic-extensions

[![CI](https://github.com/s-boomi/stac-pydantic-extensions/actions/workflows/cicd.yml/badge.svg)](https://github.com/s-boomi/stac-pydantic-extensions/actions/workflows/cicd.yml)
[![PyPI version](https://img.shields.io/pypi/v/stac-pydantic-extensions.svg)](https://pypi.org/project/stac-pydantic-extensions/)
[![Python versions](https://img.shields.io/pypi/pyversions/stac-pydantic-extensions.svg)](https://pypi.org/project/stac-pydantic-extensions/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Pydantic data models for [STAC extensions](https://github.com/stac-extensions), built on top of
[`stac-pydantic`](https://github.com/stac-utils/stac-pydantic).

`stac-pydantic-extensions` lets you attach, read, modify, and migrate STAC extension fields
(`eo`, `raster`, `proj`, `view`, `sat`, `sci`, `rd`, `ssys`, `wmts`, ...) on Items, Collections,
Assets and Bands, with validation and version migration handled for you.

## Features

- **Typed access to extension fields** — `item.ext.eo.cloud_cover`, `item.ext.raster.spatial_resolution`, etc.
- **Add / remove extensions** on the fly, recursively across assets and bands.
- **Version migration** — upgrade Items written against older extension schemas (e.g. `eo/v1.0.0`,
  `raster/v1.1.0`) to the current ones, including the `eo:bands` / `raster:bands` → `bands` merge
  introduced in the `v2.0.0` extensions.
- **Multiple extensions at once**, without them clobbering each other's fields.
- Works with plain STAC Items that don't declare any extensions yet.

## Installation

```bash
pip install stac-pydantic-extensions
```

or, with [uv](https://docs.astral.sh/uv/):

```bash
uv add stac-pydantic-extensions
```

Requires Python 3.13+.

## Quickstart

```python
import json

from stac_pydantic_extensions import ExtendedItem, Item

with open("item-sentinel2.json") as f:
    raw_item = json.load(f)

item = Item.model_validate(raw_item)
extended_item = ExtendedItem(stac_object=item)

# Read extension fields declared on the item
print(extended_item.ext.eo.cloud_cover)          # 21.22
print(extended_item.show_ext_names())            # {'eo', 'view', 'proj', 'raster'}

# Extensions declared on assets/bands are available the same way
red_band = extended_item.stac_object.assets["B04"]
extended_band = ExtendedItem(stac_object=red_band)
print(extended_band.ext.eo.common_name)           # "red"
print(extended_band.ext.raster.spatial_resolution)  # 10

# Add a new extension to an item that doesn't have it yet
extended_item.add_extension("raster")
extended_item.ext.raster.spatial_resolution = 10

# Serialize back out
updated = extended_item.model_dump()
```

### Migrating older extension versions

```python
from stac_pydantic_extensions import ExtendedItem, Item

old_item = Item.model_validate(raw_item_with_v1_extensions)

migrated = ExtendedItem(stac_object=old_item).migrate()
# stac_extensions now point at the latest schema versions, and any
# eo:bands / raster:bands entries have been merged into `bands`.
```

## Supported extensions

| Extension              | Prefix   |
|-------------------------|----------|
| Electro-Optical          | `eo`     |
| Projection                | `proj`   |
| Raster                    | `raster` |
| View Geometry              | `view`   |
| Satellite                  | `sat`    |
| Scientific Citation         | `sci`    |
| Remote Data                  | `rd`     |
| Solar System                    | `ssys`   |
| Web Map Tile Service              | `wmts`   |

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/s-boomi/stac-pydantic-extensions.git
cd stac-pydantic-extensions
uv sync --group dev
```

Run the test suite:

```bash
uv run pytest --cov stac_pydantic_extensions --cov-report term-missing
```

Run linting, formatting and type checks:

```bash
uv run pre-commit run --all-files
uv run ty check
```

> [!WARNING]
> The `ty` check is still relatively new and can be prone to some errors, especially in test files. To skip type-checking, you can use the following command:

```console
SKIP=ty uv run pre-commit run --all-files
```

## Releasing

Releases are published to PyPI via [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/)
from the `.github/workflows/release.yml` workflow. To cut a release:

1. Bump `version` in `pyproject.toml`.
2. Tag the commit with the matching version (e.g. `v0.2.0`) and push the tag, or create a
   GitHub Release — this triggers the `release` job.
3. The workflow verifies the tag matches the package version, builds the sdist/wheel with
   `uv build`, and publishes with `uv publish`.

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
