from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from stac_pydantic.extensions import validate_extensions

from stac_pydantic_extensions import ExtendedItem, Item
from stac_pydantic_extensions.extensions.eo import ElectroOpticalExtension
from stac_pydantic_extensions.extensions.raster import (
    Histogram,
    RasterExtension,
    RasterSampling,
)
from tests.conftest import read_json

if TYPE_CHECKING:
    from stac_pydantic_extensions.compat.stac_pydantic import Asset, Band


@pytest.fixture
def test_files(extension_data_files: Path) -> Path:
    return extension_data_files / "raster"


@pytest.fixture
def planet_item(test_files: Path) -> dict:
    """PlanetScope item: raster fields live on the asset + nested per-band,
    bands also carry eo: fields (good for coexistence tests)."""
    return read_json(test_files / "item-planet.json")


@pytest.fixture
def sentinel_item(test_files: Path) -> dict:
    """Sentinel-2 item: raster fields live directly on top-level assets,
    with no per-band nesting."""
    return read_json(test_files / "item-sentinel2.json")


@pytest.fixture
def planet_item_v1_raster_only(test_files: Path) -> dict:
    """PlanetScope item: raster fields live on the asset + nested per-band,
    bands also carry eo: fields (good for coexistence tests)."""
    return read_json(test_files / "old" / "item-planet-raster-only-v1_0_0.json")


@pytest.fixture
def sentinel_item_v1(test_files: Path) -> dict:
    """Sentinel-2 item: raster fields live directly on top-level assets,
    with no per-band nesting."""
    return read_json(test_files / "old" / "item-sentinel2-v1_0_0.json")


def test_extension_on_asset_with_nested_bands(planet_item):
    validate_extensions(planet_item)

    item = Item.model_validate(planet_item)
    item_dump = item.model_dump()
    assert item_dump

    extended_item = ExtendedItem(stac_object=item)
    assert extended_item is not None

    data_asset = cast(Item, extended_item.stac_object).assets["data"]
    extended_asset = ExtendedItem(stac_object=data_asset)

    assert isinstance(extended_asset.ext.raster, RasterExtension)
    assert extended_asset.ext.raster.sampling == RasterSampling.AREA
    assert extended_asset.ext.raster.spatial_resolution == 3

    assert data_asset.bands is not None
    assert len(data_asset.bands) == 4

    red_band: "Band" = data_asset.bands[0]
    assert red_band.name == "band-1"

    extended_band = ExtendedItem(stac_object=red_band)
    assert isinstance(extended_band.ext.raster, RasterExtension)
    assert extended_band.ext.raster.scale == 0.01
    assert extended_band.ext.raster.offset == 0

    histogram = extended_band.ext.raster.histogram
    assert isinstance(histogram, Histogram)
    assert histogram.count == 256
    assert len(histogram.buckets) == 256
    assert histogram.min == pytest.approx(1901.288235294118)
    assert histogram.max == pytest.approx(32985.71176470588)


def test_eo_and_raster_coexist_on_bands(planet_item):
    item = Item.model_validate(planet_item)
    red_band = item.assets["data"].bands[0]

    extended_band = ExtendedItem(stac_object=red_band)

    assert isinstance(extended_band.ext.eo, ElectroOpticalExtension)
    assert extended_band.ext.eo.common_name == "red"
    assert extended_band.ext.eo.center_wavelength == 0.63

    assert isinstance(extended_band.ext.raster, RasterExtension)
    assert extended_band.ext.raster.scale == 0.01
    assert extended_band.ext.raster.offset == 0


def test_extension_directly_on_asset_without_band_nesting(sentinel_item):
    """Sentinel-2 assets carry raster: fields directly, no bands list."""
    item = Item.model_validate(sentinel_item)

    b01: "Asset" = item.assets["B01"]
    extended_b01 = ExtendedItem(stac_object=b01)

    assert isinstance(extended_b01.ext.raster, RasterExtension)
    assert extended_b01.ext.raster.spatial_resolution == 60
    assert extended_b01.ext.raster.bits_per_sample == 15

    b04: "Asset" = item.assets["B04"]
    extended_b04 = ExtendedItem(stac_object=b04)

    assert extended_b04.ext.raster.spatial_resolution == 10
    assert extended_b04.ext.raster.bits_per_sample == 15


def test_modify_raster_fields_in_asset(planet_item):
    item = Item.model_validate(planet_item)
    data_asset = item.assets["data"]

    extended_asset = ExtendedItem(stac_object=data_asset)
    extended_asset.ext.raster.spatial_resolution = 5.0

    new_asset_dict = extended_asset.model_dump()
    assert new_asset_dict["raster:spatial_resolution"] == 5.0
    assert new_asset_dict["raster:sampling"] == "area"


def test_remove_raster_extension(planet_item):
    item = Item.model_validate(planet_item)
    extended_item = ExtendedItem(stac_object=item)

    extended_item.remove_extension("raster")

    remaining_extensions = extended_item.stac_object.stac_extensions or []
    assert not any("raster" in str(ext) for ext in remaining_extensions)

    item_obj = extended_item.model_dump()
    data_asset = item_obj["assets"]["data"]

    assert "raster:sampling" not in data_asset
    assert "raster:spatial_resolution" not in data_asset

    band_1 = data_asset["bands"][0]
    assert "raster:scale" not in band_1
    assert "raster:offset" not in band_1
    assert "raster:histogram" not in band_1
    # eo: fields on the band should be untouched
    assert band_1.get("eo:common_name") == "red"
    assert band_1.get("name") == "band-1"

    assert not isinstance(extended_item.ext.raster, RasterExtension)


def test_apply_raster_extension_on_plain_item(simple_item: Item):
    assert simple_item.stac_extensions is None or len(simple_item.stac_extensions) == 0

    extended_item = ExtendedItem(stac_object=simple_item)
    assert isinstance(extended_item.ext.raster, RasterExtension) is False

    extended_item.add_extension("raster")
    assert isinstance(extended_item.ext.raster, RasterExtension)

    extended_item.ext.raster.sampling = RasterSampling.POINT
    extended_item.ext.raster.spatial_resolution = 10

    assert extended_item.ext.raster.sampling == RasterSampling.POINT
    assert extended_item.ext.raster.spatial_resolution == 10

    extended_obj = extended_item.model_dump()
    assert len(extended_obj["stac_extensions"]) == 1
    assert extended_obj["properties"]["raster:sampling"] == "point"
    assert extended_obj["properties"]["raster:spatial_resolution"] == 10


def test_serialization_roundtrip(planet_item):
    item = Item.model_validate(planet_item)
    extended_item = ExtendedItem(stac_object=item)

    serialized = extended_item.model_dump_json()
    assert isinstance(serialized, str)

    deserialized = ExtendedItem(stac_object=Item.model_validate_json(serialized))
    data_asset = deserialized.stac_object.assets["data"]
    extended_asset = ExtendedItem(stac_object=data_asset)

    assert extended_asset.ext.raster.spatial_resolution == 3
    assert extended_asset.ext.raster.sampling == RasterSampling.AREA


def test_manual_band_creation():
    from stac_pydantic_extensions import Band

    band_data = {
        "name": "nir",
        "raster:spatial_resolution": 20,
        "raster:scale": 0.0001,
        "raster:offset": 0,
        "raster:sampling": "area",
    }
    band = Band(**band_data)
    extended_band = ExtendedItem(stac_object=band)

    assert isinstance(extended_band.ext.raster, RasterExtension)
    assert extended_band.ext.raster.spatial_resolution == 20
    assert extended_band.ext.raster.scale == 0.0001
    assert extended_band.ext.raster.sampling == RasterSampling.AREA


def test_migrate_raster_v1_0_0_item_to_v2_0_0(planet_item_v1_raster_only):

    item = Item.model_validate(planet_item_v1_raster_only)
    extended_item = ExtendedItem(stac_object=item)

    assert (
        extended_item.stac_object.stac_extensions is not None
        and len(extended_item.stac_object.stac_extensions) == 1
    )
    assert (
        str(extended_item.stac_object.stac_extensions[0])
        == "https://stac-extensions.github.io/raster/v1.0.0/schema.json"
    )

    migrated_item = ExtendedItem(
        stac_object=Item(**planet_item_v1_raster_only)
    ).migrate()

    assert (
        migrated_item.stac_object.stac_extensions is not None
        and len(migrated_item.stac_object.stac_extensions) == 1
    )
    assert (
        str(migrated_item.stac_object.stac_extensions[0])
        == "https://stac-extensions.github.io/raster/v2.0.0/schema.json"
    )

    migrated = migrated_item.model_dump()
    example_asset = migrated["assets"]["example"]

    assert "raster:bands" not in example_asset
    assert "bands" in example_asset
    assert len(example_asset["bands"]) == 2

    assert example_asset["bands"][0]["raster:spatial_resolution"] == 10
    assert example_asset["bands"][0]["raster:scale"] == 0.0001
    assert example_asset["bands"][1]["raster:spatial_resolution"] == 20
