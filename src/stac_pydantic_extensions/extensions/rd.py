from enum import StrEnum
from typing import ClassVar, Literal

from pydantic import AnyUrl, ConfigDict, Field

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)


class ProductLevel(StrEnum):
    LV1A = "LV1A"
    LV1B = "LV1B"
    LV2A = "LV2A"
    LV2B = "LV2B"
    LV3A = "LV3A"
    LV3B = "LV3B"


class RemoteDataFields(BaseExtraFields):
    """https://github.com/stac-extensions/remote-data"""

    type: str = Field(default="scene")
    product_level: ProductLevel = Field(...)
    sat_id: str = Field(...)
    runs: list[str] | None = None
    parsecs: list[int | float] | None = None
    anomalous_pixels: float | None = None
    earth_sun_distance: int | float | None = None
    flux_capacitor: bool | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="rd")
    )


class RemoteDataExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/remote-data/v1.0.0/schema.json"
    )
    prefix: ClassVar[Literal["rd"]] = "rd"
    fields: RemoteDataFields
    version: ClassVar[Literal["v1.0.0"]] = "v1.0.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}
