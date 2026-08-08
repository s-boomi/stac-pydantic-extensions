import json
from pathlib import Path
from typing import Any

import pytest

from stac_pydantic_extensions import Collection
from stac_pydantic_extensions.compat.stac_pydantic import Item

TEST_PATH = Path(__file__).parent
EXTENSION_TEST_PATH = TEST_PATH / "extensions"
EXTENSION_DATA_FILES = EXTENSION_TEST_PATH / "data-files"


def read_json(file: Path) -> dict[str, Any]:
    return json.loads(file.read_text(encoding="utf-8"))


@pytest.fixture
def extension_data_files() -> Path:
    return EXTENSION_DATA_FILES


@pytest.fixture
def simple_item(extension_data_files: Path) -> Item:
    """A basic STAC item"""
    _simple_item = read_json(extension_data_files / "simple-item.json")

    return Item.model_validate(_simple_item)


@pytest.fixture
def core_item(extension_data_files: Path) -> Item:
    """A more complex Item example"""
    _core_item = read_json(extension_data_files / "core-item.json")

    return Item.model_validate(_core_item)


@pytest.fixture
def extended_item(extension_data_files: Path) -> Item:
    """An Item example with extensions"""
    _core_item = read_json(extension_data_files / "common" / "item.json")

    return Item.model_validate(_core_item)


@pytest.fixture
def extended_collection(extension_data_files: Path) -> Collection:
    """A Collection example with extensions"""
    _core_collection = read_json(extension_data_files / "common" / "collection.json")

    return Collection.model_validate(_core_collection)
