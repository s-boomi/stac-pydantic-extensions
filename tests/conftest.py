import json
from pathlib import Path
from typing import Any

import pytest

import stac_pydantic_extensions  # noqa: F401

TEST_PATH = Path(__file__).parent
EXTENSION_TEST_PATH = TEST_PATH / "extensions"
EXTENSION_DATA_FILES = EXTENSION_TEST_PATH / "data-files"


@pytest.fixture
def extension_data_files() -> Path:
    return EXTENSION_DATA_FILES


def read_json(file: Path) -> dict[str, Any]:
    return json.loads(file.read_text(encoding="utf-8"))
