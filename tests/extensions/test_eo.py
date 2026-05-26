from pathlib import Path

import pytest
from stac_pydantic.extensions import validate_extensions

from stac_pydantic_extensions import Item
from tests.conftest import read_json


@pytest.fixture
def test_files(extension_data_files: Path) -> Path:
    return extension_data_files / "eo"


def test_validate_extension(test_files):
    test_item = read_json(test_files / "item.json")

    validate_extensions(test_item)

    test_item = Item(**test_item).model_dump()
    assert test_item
