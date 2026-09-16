from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError
from stac_pydantic.extensions import validate_extensions

from stac_pydantic_extensions import Asset, Collection, ExtendedItem, Item
from stac_pydantic_extensions.extensions.eo import ElectroOpticalExtension
from stac_pydantic_extensions.extensions.proj import ProjectionExtension
from tests.conftest import read_json

if TYPE_CHECKING:
    pass


@pytest.fixture
def test_files(extension_data_files: Path) -> Path:
    return extension_data_files / "proj"


@pytest.fixture
def item_assets_data(test_files: Path) -> dict:
    """Item where proj fields live both on the item and on individual assets,
    one of which (thumbnail) only carries a subset of fields (and an explicit
    proj:code: null)."""
    return read_json(test_files / "assets.json")


@pytest.fixture
def proj_eo_item(test_files: Path) -> dict:
    """Item exercising the full proj field set (wkt2, projjson, geometry, bbox,
    centroid, shape, transform) alongside the eo extension on assets/bands."""
    return read_json(test_files / "item_with_eo.json")


def test_extension_on_item(test_files):
    test_item = read_json(test_files / "item.json")

    validate_extensions(test_item)

    item = Item(**test_item)
    assert item.model_dump()

    extended_item = ExtendedItem(stac_object=item)
    assert isinstance(extended_item.ext.proj, ProjectionExtension)
    assert extended_item.ext.proj.code == "EPSG:32659"
    assert extended_item.ext.proj.shape == [5558, 9559]
    assert extended_item.ext.proj.transform == [
        0.5,
        0,
        712710,
        0,
        -0.5,
        151406,
        0,
        0,
        1,
    ]


def test_item_assets_reject_summary_style_list(test_files):
    """item_assets entries are Asset-shaped, not summary-shaped — a list
    should never be valid there even though it's nested inside a Collection."""
    test_collection = read_json(test_files / "collection.json")
    test_collection["item_assets"]["analytic"]["proj:code"] = [
        "EPSG:32659",
        "EPSG:4326",
    ]

    collection = Collection(**test_collection)
    analytic = collection.item_assets["analytic"]

    with pytest.raises(ValidationError):
        ExtendedItem(stac_object=analytic)


def test_extension_on_collection(test_files):
    test_collection = read_json(test_files / "collection.json")

    validate_extensions(test_collection)

    collection = Collection(**test_collection)
    assert collection.model_dump()

    extended_collection = ExtendedItem(stac_object=collection)
    assert extended_collection is not None

    # Raw summaries are untouched dict values (not run through the field model)
    assert collection.summaries is not None
    assert collection.summaries["proj:code"] == [32659, None]

    # item_assets entries are StacSecondaryObjects, so proj fields on them
    # are read the same way as on a regular Asset.
    assert collection.item_assets is not None
    analytic = collection.item_assets["analytic"]

    extended_analytic = ExtendedItem(stac_object=analytic)
    assert isinstance(extended_analytic.ext.proj, ProjectionExtension)
    assert extended_analytic.ext.proj.code == "EPSG:32659"
    assert extended_analytic.ext.proj.shape == [5558, 9559]
    assert extended_analytic.ext.proj.transform == [
        0.5,
        0,
        712710,
        0,
        -0.5,
        151406,
        0,
        0,
        1,
    ]


def test_extension_on_item_and_assets(item_assets_data):
    validate_extensions(item_assets_data)

    item = Item(**item_assets_data)
    assert item.model_dump()

    extended_item = ExtendedItem(stac_object=item)
    assert isinstance(extended_item.ext.proj, ProjectionExtension)
    assert extended_item.ext.proj.code == "EPSG:32659"

    analytic_asset: Asset = item.assets["analytic"]
    extended_analytic = ExtendedItem(stac_object=analytic_asset)
    assert isinstance(extended_analytic.ext.proj, ProjectionExtension)
    assert extended_analytic.ext.proj.code == "EPSG:32659"
    assert extended_analytic.ext.proj.shape == [5558, 9559]
    assert extended_analytic.ext.proj.transform == [
        0.5,
        0,
        712710,
        0,
        -0.5,
        151406,
        0,
        0,
        1,
    ]

    # thumbnail only carries a partial set of fields, including an explicit
    # `proj:code: null` — make sure that doesn't get confused with "absent"
    thumbnail_asset: Asset = item.assets["thumbnail"]
    extended_thumbnail = ExtendedItem(stac_object=thumbnail_asset)
    assert isinstance(extended_thumbnail.ext.proj, ProjectionExtension)
    assert extended_thumbnail.ext.proj.code is None
    assert extended_thumbnail.ext.proj.shape == [800, 800]
    assert extended_thumbnail.ext.proj.transform is None


def test_modify_proj_fields_in_asset(item_assets_data):
    item = Item(**item_assets_data)
    analytic_asset = item.assets["analytic"]

    extended_asset = ExtendedItem(stac_object=analytic_asset)
    assert isinstance(extended_asset.ext.proj, ProjectionExtension)

    extended_asset.ext.proj.code = "EPSG:4326"
    new_asset_dict = extended_asset.model_dump()

    assert new_asset_dict["proj:code"] == "EPSG:4326"
    # untouched fields survive the round trip
    assert new_asset_dict["proj:shape"] == [5558, 9559]


def test_custom_non_epsg_projection_code(test_files):
    """proj:code isn't limited to EPSG — planetary/other authorities
    (e.g. IAU_2015 for non-Earth bodies) should parse and round-trip too."""
    test_item = read_json(test_files / "item_custom_proj.json")

    item = Item(**test_item)
    extended_item = ExtendedItem(stac_object=item)

    assert isinstance(extended_item.ext.proj, ProjectionExtension)
    assert extended_item.ext.proj.code == "IAU_2015:49900"

    dumped = extended_item.model_dump()
    assert dumped["properties"]["proj:code"] == "IAU_2015:49900"


def test_full_field_set(proj_eo_item):
    validate_extensions(proj_eo_item)

    item = Item(**proj_eo_item)
    assert item.model_dump()

    extended_item = ExtendedItem(stac_object=item)
    proj_ext = extended_item.ext.proj
    assert isinstance(proj_ext, ProjectionExtension)

    assert proj_ext.code == "EPSG:32614"
    assert proj_ext.wkt2 is not None
    assert proj_ext.projjson is not None
    assert proj_ext.geometry is not None
    assert list(proj_ext.bbox) == [169200, 3712800, 403200, 3951000]
    assert proj_ext.centroid is not None
    assert proj_ext.centroid.lat == pytest.approx(34.595302781575604)
    assert proj_ext.centroid.lon == pytest.approx(-101.34448382627504)
    assert proj_ext.shape == [8391, 8311]
    assert proj_ext.transform == [30, 0, 224985, 0, -30, 6790215, 0, 0, 1]


def test_proj_and_eo_coexist_on_item_and_assets(proj_eo_item):
    item = Item(**proj_eo_item)
    extended_item = ExtendedItem(stac_object=item)

    assert isinstance(extended_item.ext.proj, ProjectionExtension)
    assert isinstance(extended_item.ext.eo, ElectroOpticalExtension)

    # B8 only carries proj fields (its own shape/transform override the item's)
    b8_asset = item.assets["B8"]
    extended_b8 = ExtendedItem(stac_object=b8_asset)
    assert isinstance(extended_b8.ext.proj, ProjectionExtension)
    assert extended_b8.ext.proj.shape == [16781, 16621]
    assert extended_b8.ext.proj.transform == [
        15,
        0,
        224992.5,
        0,
        -15,
        6790207.5,
        0,
        0,
        1,
    ]

    # B1's band carries eo: fields only — proj extension shouldn't leak in
    b1_band = item.assets["B1"].bands[0]
    extended_band = ExtendedItem(stac_object=b1_band)
    assert isinstance(extended_band.ext.eo, ElectroOpticalExtension)
    assert extended_band.ext.eo.common_name == "coastal"
    assert extended_band.ext.eo.center_wavelength == 0.44


def test_proj_and_view_extensions_coexist(extended_item: Item):
    """Uses the shared `common/item.json` fixture (proj + eo + view + rd + sci)."""
    extended = ExtendedItem(stac_object=extended_item)

    assert isinstance(extended.ext.proj, ProjectionExtension)
    assert extended.ext.proj.code == "EPSG:32659"
    assert extended.ext.proj.shape == [5558, 9559]
    assert extended.ext.view.sun_elevation == 54.9


def test_remove_projection_extension(test_files):
    test_item = read_json(test_files / "item.json")

    item = Item(**test_item)
    extended_item = ExtendedItem(stac_object=item)
    assert isinstance(extended_item.ext.proj, ProjectionExtension)

    extended_item.remove_extension("proj")
    assert extended_item.stac_object.stac_extensions is None

    item_obj = extended_item.model_dump()
    assert item_obj.get("stac_extensions") is None
    assert item_obj.get("properties") is not None

    assert "proj:code" not in item_obj["properties"]
    assert "proj:shape" not in item_obj["properties"]
    assert "proj:transform" not in item_obj["properties"]

    assert not isinstance(extended_item.ext.proj, ProjectionExtension)


def test_apply_projection_extension_on_plain_item(simple_item: Item):
    assert simple_item.stac_extensions is None or len(simple_item.stac_extensions) == 0

    extended_item = ExtendedItem(stac_object=simple_item)
    assert isinstance(extended_item.ext.proj, ProjectionExtension) is False

    extended_item.add_extension("proj")
    assert isinstance(extended_item.ext.proj, ProjectionExtension)

    extended_item.ext.proj.code = "EPSG:4326"
    extended_item.ext.proj.shape = [100, 100]

    assert extended_item.ext.proj.code == "EPSG:4326"
    assert extended_item.ext.proj.shape == [100, 100]

    extended_obj = extended_item.model_dump()
    assert len(extended_obj["stac_extensions"]) == 1
    assert extended_obj["properties"]["proj:code"] == "EPSG:4326"
    assert extended_obj["properties"]["proj:shape"] == [100, 100]


def test_serialization_roundtrip(test_files):
    test_item = read_json(test_files / "item.json")
    extended_item = ExtendedItem(stac_object=Item(**test_item))

    serialized = extended_item.model_dump_json()
    assert isinstance(serialized, str)

    deserialized = ExtendedItem(stac_object=Item.model_validate_json(serialized))
    assert deserialized.ext.proj.code == "EPSG:32659"
    assert deserialized.ext.proj.shape == [5558, 9559]
