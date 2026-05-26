from enum import auto
from typing import Any, Dict, List, Optional, Union

from pydantic import ConfigDict
from stac_pydantic import Collection as OldCollection
from stac_pydantic import Item as OldItem
from stac_pydantic.links import Link as OldLink
from stac_pydantic.shared import StacBaseModel
from stac_pydantic.shared import StacCommonMetadata as OldStacCommonMetadata
from stac_pydantic.utils import AutoValueEnum

STAC_VERSION = "1.1.0"


class NoDataTypes(str, AutoValueEnum):
    nan = auto()
    inf = auto()
    minus_inf = "-inf"


class DataTypes(str, AutoValueEnum):
    int8 = auto()
    int16 = auto()
    int32 = auto()
    int64 = auto()
    uint8 = auto()
    uint16 = auto()
    uint32 = auto()
    uint64 = auto()
    float16 = auto()
    float32 = auto()
    float64 = auto()
    cint16 = auto()
    cint32 = auto()
    cfloat32 = auto()
    cfloat64 = auto()
    other = auto()


class Band(StacBaseModel):
    """
    https://github.com/radiantearth/stac-spec/blob/v1.1.0/commons/common-metadata.md#band-object
    """

    name: Optional[str]
    description: Optional[str]
    # For extensions related to bands
    model_config = ConfigDict(use_enum_values=True, extra="allow")


class Statistics(StacBaseModel):
    """
    https://github.com/radiantearth/stac-spec/blob/v1.1.0/commons/common-metadata.md#statistics-object
    """

    minimum: Optional[float] = None
    maximum: Optional[float] = None
    mean: Optional[float] = None
    stddev: Optional[float] = None
    count: Optional[int] = None
    valid_percent: Optional[float] = None


class StacCommonMetadata(OldStacCommonMetadata):
    keywords: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    # Bands
    bands: Optional[List[Band]] = None
    # Data
    nodata: Optional[float | str] = None
    data_type: Optional[str] = None
    statistics: Optional[Statistics] = None
    unit: Optional[str] = None


class Link(OldLink):
    method: str = "GET"
    headers: Optional[Dict[str, Union[str, List[str]]]] = None
    body: Optional[Any] = None


class ItemAsset(StacBaseModel):
    """
    https://github.com/radiantearth/stac-spec/blob/v1.1.0/collection-spec/collection-spec.md#item-asset-definition-object
    """

    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    roles: Optional[List[str]] = None

    model_config = ConfigDict(
        populate_by_name=True, use_enum_values=True, extra="allow"
    )


class Collection(OldCollection):
    """
    https://github.com/radiantearth/stac-spec/blob/v1.1.0/collection-spec/collection-spec.md
    """

    item_assets: Optional[Dict[str, ItemAsset]] = None


class ItemProperties(StacCommonMetadata):
    """
    https://github.com/radiantearth/stac-spec/blob/v1.1.0/item-spec/item-spec.md#properties-object
    """

    model_config = ConfigDict(extra="allow")


class Item(OldItem):
    """
    https://github.com/radiantearth/stac-spec/blob/v1.1.0/item-spec/item-spec.md
    """

    properties: ItemProperties
