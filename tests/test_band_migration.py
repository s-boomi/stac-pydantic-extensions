from stac_pydantic_extensions import ExtendedItem
from stac_pydantic_extensions.compat.stac_pydantic import Item


def test_band_migration_to_2_0(simple_item: Item):
    item_obj = simple_item.model_dump()
    item_obj["stac_extensions"] = [
        "https://stac-extensions.github.io/raster/v1.1.0/schema.json",
        "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
    ]

    stac_assets_1_0 = {
        "assets": {
            "example": {
                "href": "example.tif",
                "eo:bands": [
                    {"name": "r", "common_name": "red"},
                    {"name": "g", "common_name": "green"},
                    {"name": "b", "common_name": "blue"},
                    {"name": "nir", "common_name": "nir"},
                ],
                "raster:bands": [
                    {
                        "data_type": "uint16",
                        "spatial_resolution": 10,
                        "sampling": "area",
                    },
                    {
                        "data_type": "uint16",
                        "spatial_resolution": 10,
                        "sampling": "area",
                    },
                    {
                        "data_type": "uint16",
                        "spatial_resolution": 10,
                        "sampling": "area",
                    },
                    {
                        "data_type": "uint16",
                        "spatial_resolution": 30,
                        "sampling": "area",
                    },
                ],
            }
        }
    }
    item_obj["assets"] = stac_assets_1_0["assets"]
    item_with_assets_1_0 = Item.model_validate(item_obj)

    stac_assets_2_0 = {
        "assets": {
            "example": {
                "href": "example.tif",
                "data_type": "uint16",
                "raster:sampling": "area",
                "raster:spatial_resolution": 10,
                "bands": [
                    {"name": "r", "eo:common_name": "red"},
                    {"name": "g", "eo:common_name": "green"},
                    {"name": "b", "eo:common_name": "blue"},
                    {
                        "name": "nir",
                        "eo:common_name": "nir",
                        "raster:spatial_resolution": 30,
                    },
                ],
            }
        }
    }

    item_obj["stac_extensions"] = [
        "https://stac-extensions.github.io/raster/v2.0.0/schema.json",
        "https://stac-extensions.github.io/eo/v2.0.0/schema.json",
    ]
    item_obj["assets"] = stac_assets_2_0["assets"]
    item_with_assets_2_0 = Item.model_validate(item_obj)

    extended_item = ExtendedItem(stac_object=item_with_assets_1_0)
    migrated_ext_item = extended_item.migrate()

    migrated_obj = migrated_ext_item.model_dump()

    example_asset = migrated_obj["assets"]["example"]
    assert example_asset["raster:spatial_resolution"] == 10
    assert example_asset["raster:sampling"] == "area"
    assert example_asset["data_type"] == "uint16"
    assert (
        example_asset["bands"][3]["raster:spatial_resolution"] == 30
    )  # nir override survives
    assert (
        "raster:spatial_resolution" not in example_asset["bands"][0]
    )  # r had it hoisted away
