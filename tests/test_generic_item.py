from stac_pydantic.collection import Range

from stac_pydantic_extensions import Collection, ExtendedItem, Item


def test_all_extensions_parse(extended_item: Item):
    extended = ExtendedItem(stac_object=extended_item)

    assert extended.ext.eo.cloud_cover == 1.2
    assert extended.ext.eo.snow_cover == 0
    assert extended.ext.proj.code == "EPSG:32659"
    assert extended.ext.view.sun_elevation == 54.9
    assert extended.ext.rd.type == "scene"
    assert extended.ext.sci.doi == "10.5061/dryad.s2v81.2/27.2"


def test_shared_band_names_stay_scoped_to_their_asset(extended_item: Item):
    analytic = extended_item.assets["analytic"]
    visual = extended_item.assets["visual"]

    ext_analytic = ExtendedItem(stac_object=analytic).model_dump()
    ext_visual = ExtendedItem(stac_object=visual).model_dump()

    assert len(ext_analytic["bands"]) == 4
    assert len(ext_visual["bands"]) == 3
    # band1 in each asset is independently "blue" — confirm no cross-asset bleed
    assert ext_analytic["bands"][0]["eo:common_name"] == "blue"
    # band1 is last in visual's list
    assert ext_visual["bands"][2]["eo:common_name"] == "blue"


def test_migrate_is_noop_when_already_current(extended_item: Item):
    before = extended_item.model_dump()

    migrated = ExtendedItem(stac_object=extended_item).migrate()
    after = migrated.model_dump()

    assert before == after


def test_extension_on_plain_collection(extended_collection: Collection):
    extended = ExtendedItem(stac_object=extended_collection)
    extended.add_extension("eo")
    extended.ext.eo.cloud_cover = Range(minimum=0.0, maximum=15.0)

    dumped = extended.model_dump()
    assert dumped["summaries"]["eo:cloud_cover"] == {"minimum": 0.0, "maximum": 15.0}
