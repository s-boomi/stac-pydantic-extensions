from pathlib import Path

import pytest
from stac_pydantic import Catalog
from stac_pydantic.extensions import validate_extensions

from stac_pydantic_extensions import Collection, ExtendedItem, Item
from stac_pydantic_extensions.extensions.ssys import SolSysExtension, SolSysTargets
from tests.conftest import read_json


@pytest.fixture
def test_files(extension_data_files: Path) -> Path:
    return extension_data_files / "ssys"


def test_extension_on_item(test_files):
    test_item = read_json(test_files / "item.json")

    validate_extensions(test_item)

    item_dump = Item(**test_item).model_dump()
    assert item_dump

    extended_item = ExtendedItem(stac_object=Item(**test_item))
    assert extended_item is not None
    assert isinstance(extended_item.ext.ssys, SolSysExtension)
    assert extended_item.ext.ssys.targets == ["Europa"]
    assert extended_item.ext.ssys.target_class == SolSysTargets.PLANET


def test_extension_on_collection(test_files):
    test_collection = read_json(test_files / "collection.json")

    validate_extensions(test_collection)

    collection_dump = Collection(**test_collection).model_dump()
    assert collection_dump

    extended_collection = ExtendedItem(stac_object=Collection(**test_collection))
    assert extended_collection is not None
    assert isinstance(extended_collection.ext.ssys, SolSysExtension)
    assert extended_collection.ext.ssys.targets == ["Europa"]
    assert extended_collection.ext.ssys.target_class is None


def test_extension_on_catalog(test_files):
    test_catalog = read_json(test_files / "catalog.json")

    catalog_dump = Catalog(**test_catalog).model_dump()
    assert catalog_dump

    extended_catalog = ExtendedItem(stac_object=Catalog(**test_catalog))
    assert extended_catalog is not None
    assert isinstance(extended_catalog.ext.ssys, SolSysExtension)
    assert extended_catalog.ext.ssys.targets == ["Europa"]
    assert extended_catalog.ext.ssys.target_class is None


def test_modify_fields_on_item(test_files):
    test_item = read_json(test_files / "item.json")
    extended_item = ExtendedItem(stac_object=Item(**test_item))

    extended_item.ext.ssys.target_class = SolSysTargets.SATELLITE
    extended_item.ext.ssys.local_time = "12:00"

    new_item_dict = extended_item.model_dump()
    assert new_item_dict["properties"]["ssys:target_class"] == "satellite"
    assert new_item_dict["properties"]["ssys:local_time"] == "12:00"
    # Untouched field should survive
    assert new_item_dict["properties"]["ssys:targets"] == ["Europa"]


def test_apply_extension_on_plain_item(simple_item: Item):
    assert simple_item.stac_extensions is None or (
        simple_item.stac_extensions is not None
        and len(simple_item.stac_extensions) == 0
    )

    extended_item = ExtendedItem(stac_object=simple_item)
    assert isinstance(extended_item.ext.ssys, SolSysExtension) is False

    # Add ssys extension with no fields
    extended_item.add_extension("ssys")
    assert isinstance(extended_item.ext.ssys, SolSysExtension)

    extended_item.ext.ssys.targets = ["Mars"]
    extended_item.ext.ssys.target_class = SolSysTargets.PLANET

    assert extended_item.ext.ssys.targets == ["Mars"]
    assert extended_item.ext.ssys.target_class == SolSysTargets.PLANET

    extended_obj = extended_item.model_dump()
    assert len(extended_obj["stac_extensions"]) == 1
    assert extended_obj["properties"]["ssys:targets"] == ["Mars"]
    assert extended_obj["properties"]["ssys:target_class"] == "planet"


def test_remove_ssys_extension(test_files):
    test_item = read_json(test_files / "item.json")

    extended_item = ExtendedItem(stac_object=Item(**test_item))
    assert isinstance(extended_item.ext.ssys, SolSysExtension)
    assert extended_item.ext.ssys.targets == ["Europa"]

    extended_item.remove_extension("ssys")
    assert extended_item.stac_object.stac_extensions is None

    item_obj = extended_item.model_dump()
    assert item_obj.get("stac_extensions") is None
    assert item_obj.get("properties") is not None

    assert item_obj["properties"].get("ssys:targets") is None
    assert item_obj["properties"].get("ssys:target_class") is None

    assert not isinstance(extended_item.ext.ssys, SolSysExtension)


def test_serialization_roundtrip(test_files):
    test_item = read_json(test_files / "item.json")
    extended_item = ExtendedItem(stac_object=Item(**test_item))

    serialized = extended_item.model_dump_json()
    assert isinstance(serialized, str)

    deserialized = ExtendedItem(stac_object=Item.model_validate_json(serialized))
    assert deserialized.ext.ssys.targets == ["Europa"]
    assert deserialized.ext.ssys.target_class == SolSysTargets.PLANET


def test_manual_targets_list_mutation(test_files):
    """Targets is a plain list field; confirm append-style edits round-trip."""
    test_item = read_json(test_files / "item.json")
    extended_item = ExtendedItem(stac_object=Item(**test_item))

    extended_item.ext.ssys.targets = [*extended_item.ext.ssys.targets, "Io"]

    new_item_dict = extended_item.model_dump()
    assert new_item_dict["properties"]["ssys:targets"] == ["Europa", "Io"]
