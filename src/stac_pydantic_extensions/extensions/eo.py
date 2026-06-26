from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, ClassVar, Literal

from pydantic import AfterValidator, AnyUrl, ConfigDict

from stac_pydantic_extensions.compat.stac_pydantic import Collection, Item
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)
from stac_pydantic_extensions.validators import validate_percentage

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import StacObject, StacSecondaryObject

PercentageValue = Annotated[float, AfterValidator(validate_percentage)]


class BandCommonNames(StrEnum):
    PAN = "pan"
    COASTAL = "coastal"
    BLUE = "blue"
    GREEN = "green"
    GREEN05 = "green05"
    YELLOW = "yellow"
    RED = "red"
    REDEDGE = "rededge"
    REDEDGE071 = "rededge071"
    REDEDGE075 = "rededge075"
    REDEDGE078 = "rededge078"
    NIR = "nir"
    NIR08 = "nir08"
    NIR09 = "nir09"
    CIRRUS = "cirrus"
    SWIR16 = "swir16"
    SWIR22 = "swir22"
    LWIR = "lwir"
    LWIR11 = "lwir11"
    LWIR12 = "lwir12"


class ElectroOpticalFields(BaseExtraFields):
    """https://github.com/stac-extensions/eo"""

    cloud_cover: PercentageValue | None = None
    snow_cover: PercentageValue | None = None
    common_name: BandCommonNames | None = None
    center_wavelength: float | None = None
    full_width_half_max: float | None = None
    solar_illumination: float | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="eo")
    )


class ElectroOpticalExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/eo/v2.0.0/schema.json"
    )
    prefix: ClassVar[Literal["eo"]] = "eo"
    fields: ElectroOpticalFields
    version: ClassVar[Literal["v2.0.0"]] = "v2.0.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Asset", "Band"}

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject
    ) -> ElectroOpticalExtension | None:
        stac_obj_ext = stac_object.stac_extensions
        if stac_obj_ext is not None and cls.stac_extension in stac_obj_ext:
            if isinstance(stac_object, Item):
                properties = stac_object.properties.to_dict()
            elif isinstance(stac_object, Collection):
                properties = stac_object.summaries
            else:
                properties = stac_object.to_dict()
            return cls(fields=ElectroOpticalFields.model_validate(properties or {}))

    @classmethod
    def from_stac_secondary_object(
        cls, stac_object: StacSecondaryObject
    ) -> ElectroOpticalExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=ElectroOpticalFields.model_validate(obj_properties))
