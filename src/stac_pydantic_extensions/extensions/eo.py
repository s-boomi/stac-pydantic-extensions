from enum import StrEnum
from typing import Annotated, ClassVar, Literal

from pydantic import AfterValidator, AnyUrl, ConfigDict

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)
from stac_pydantic_extensions.utils import validate_percentage

PercentageOrNoneValue = Annotated[float, AfterValidator(validate_percentage)]


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
    cloud_cover: PercentageOrNoneValue
    snow_cover: PercentageOrNoneValue
    common_name: BandCommonNames | None = None
    center_wavelength: float | None = None
    full_width_half_max: float | None = None
    solar_illumination: float | None = None

    model_config = ConfigDict(
        extra="forbid", alias_generator=lambda s: prefix_alias(s, prefix="eo")
    )


class ElectroOpticalExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/eo/v2.0.0/schema.json"
    )
    prefix: Literal["ssys"] = "ssys"
    fields: ElectroOpticalFields
    version: Literal["v2.0.0"] = "v2.0.0"
    allowed_objects: set[str] = {"Item", "Asset", "Band"}
