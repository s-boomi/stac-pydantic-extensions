from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from stac_pydantic.extensions import validate_extensions

from stac_pydantic_extensions import Asset, Band, Collection, ExtendedItem, Item
from stac_pydantic_extensions.extensions.eo import (
    BandCommonNames,
    ElectroOpticalExtension,
)
from tests.conftest import read_json

if TYPE_CHECKING:
    from stac_pydantic_extensions.compat.stac_pydantic import Asset


@pytest.fixture
def test_files(extension_data_files: Path) -> Path:
    return extension_data_files / "eo"


def test_extension_on_simple_item_and_assets(test_files):
    test_item = read_json(test_files / "item.json")

    validate_extensions(test_item)

    test_item_dump = Item(**test_item).model_dump()
    assert test_item_dump

    test_extended_item = ExtendedItem(stac_object=Item(**test_item))
    assert test_extended_item is not None
    assert isinstance(test_extended_item.ext.eo, ElectroOpticalExtension)
    assert test_extended_item.ext.eo.cloud_cover == 1.2
    assert test_extended_item.ext.eo.snow_cover == 0

    extendable_item = cast(Item, test_extended_item.stac_object)
    assert extendable_item.assets is not None
    assert len(extendable_item.assets) == 3

    analytic_asset: Asset = extendable_item.assets["analytic"]

    assert analytic_asset.model_extra is not None
    assert len(analytic_asset.model_extra) == 2
    assert sorted(list(analytic_asset.model_extra.keys())) == sorted(
        ["eo:cloud_cover", "bands"]
    )

    assert sorted(analytic_asset.model_dump().keys()) == sorted(
        ["href", "type", "title", "roles", "eo:cloud_cover", "bands"]
    )

    analytic_bands = analytic_asset.bands
    assert analytic_bands is not None
    assert len(analytic_bands) == 4

    band_1: Band = analytic_bands[0]
    assert band_1.name == "band1"

    extended_band = ExtendedItem(stac_object=band_1)
    assert extended_band.ext.eo.common_name == BandCommonNames.BLUE
    assert extended_band.ext.eo.center_wavelength == 0.47
    assert extended_band.ext.eo.full_width_half_max == 0.07
    assert extended_band.ext.eo.solar_illumination == 1959.66


def test_extension_on_collection(test_files):
    test_collection = read_json(test_files / "collection.json")

    validate_extensions(test_collection)

    test_collection_dump = Collection(**test_collection).model_dump()
    assert test_collection_dump

    test_extended_collection = ExtendedItem(stac_object=Collection(**test_collection))
    assert test_extended_collection is not None


def test_modify_fields_in_asset(test_files):
    test_item = read_json(test_files / "item.json")
    analytic_asset = Asset.model_validate(test_item["assets"]["analytic"])

    extended_asset = ExtendedItem(stac_object=analytic_asset)
    assert isinstance(extended_asset.ext.eo, ElectroOpticalExtension)

    # Adding random snow cover value
    extended_asset.ext.eo.snow_cover = 0.7
    new_asset_dict = extended_asset.model_dump()
    assert "eo:cloud_cover" in new_asset_dict
    assert new_asset_dict["eo:cloud_cover"] == 1.2

    assert "eo:snow_cover" in new_asset_dict
    assert new_asset_dict["eo:snow_cover"] == 0.7


def test_apply_extension_on_plain_object(simple_item: Item):
    # Check if extension list is empty or non-existent
    assert simple_item.stac_extensions is None or (
        simple_item.stac_extensions is not None
        and len(simple_item.stac_extensions) == 0
    )

    extended_item = ExtendedItem(stac_object=simple_item)
    assert isinstance(extended_item.ext.eo, ElectroOpticalExtension) is False

    # Add EO extension with no fields
    extended_item.add_extension("eo")

    assert isinstance(extended_item.ext.eo, ElectroOpticalExtension)

    extended_item.ext.eo.common_name = BandCommonNames.GREEN05
    extended_item.ext.eo.full_width_half_max = 0.07

    assert extended_item.ext.eo.common_name == BandCommonNames.GREEN05
    assert extended_item.ext.eo.full_width_half_max == 0.07

    extended_eo_obj = extended_item.model_dump()
    assert len(extended_eo_obj["stac_extensions"]) == 1


def test_remove_eo_extension(test_files):
    test_item = read_json(test_files / "item.json")

    validate_extensions(test_item)

    test_item_dump = Item(**test_item).model_dump()
    assert test_item_dump

    test_extended_item = ExtendedItem(stac_object=Item(**test_item))
    assert test_extended_item is not None
    assert isinstance(test_extended_item.ext.eo, ElectroOpticalExtension)
    assert test_extended_item.ext.eo.cloud_cover == 1.2
    assert test_extended_item.ext.eo.snow_cover == 0

    # remove extension
    test_extended_item.remove_extension("eo")
    assert test_extended_item.stac_object.stac_extensions is None
    item_obj = test_extended_item.model_dump()
    assert item_obj.get("stac_extensions") is None
    assert item_obj.get("properties") is not None

    assert item_obj["properties"].get("eo:snow_cover") is None
    assert item_obj["properties"].get("eo:cloud_cover") is None

    analytic_asset = item_obj["assets"]["analytic"]
    assert analytic_asset.get("eo:cloud_cover") is None
    assert analytic_asset.get("title") == "4-Band Analytic"
    assert (
        analytic_asset.get("href")
        == "https://storage.googleapis.com/open-cogs/stac-examples/20201211_223832_CS2_analytic.tif"
    )

    band_1 = analytic_asset["bands"][0]
    assert band_1.get("eo:common_name") is None
    assert band_1.get("eo:center_wavelength") is None
    assert band_1.get("eo:full_width_half_max") is None
    assert band_1.get("eo:solar_illumination") is None
    assert band_1.get("name") == "band1"

    assert not isinstance(test_extended_item.ext.eo, ElectroOpticalExtension)


def test_extension_on_old_item(test_files):
    test_item = read_json(test_files / "old" / "item-v1_0_0.json")

    validate_extensions(test_item)

    test_item_dump = Item(**test_item).model_dump()
    assert test_item_dump
