import json
from pathlib import Path

from stac_pydantic_extensions import Item
from stac_pydantic_extensions.extended import ExtendedItem

example = Path(
    "/home/sboomi/PythonProjects/stac-pydantic-extensions/tests/extensions/data-files/common/item.json"
)


def main():
    ex_obj = json.loads(example.read_text(encoding="utf-8"))
    print(ex_obj)
    stac_item = Item(**ex_obj)
    extended_stac = ExtendedItem(stac_object=stac_item)
    print(extended_stac)
    print(extended_stac.show_ext_names())
    print(extended_stac.ext.eo.cloud_cover)


if __name__ == "__main__":
    main()
