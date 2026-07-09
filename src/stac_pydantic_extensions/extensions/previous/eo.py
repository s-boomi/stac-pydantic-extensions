from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import AnyUrl, ConfigDict
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions.extensions._base import (
    BaseExtraFields,
    MaturityLevel,
    OldBaseExtension,
    prefix_alias,
)
from stac_pydantic_extensions.model_annotations import PercentageValue

if TYPE_CHECKING:
    pass


class EoAssetRoles(StrEnum):
    """https://github.com/stac-extensions/eo/blob/v2.0.0/README.md#best-practices"""

    REFLECTANCE = "reflectance"
    TEMPERATURE = "temperature"
    SATURATION = "saturation"
    CLOUD = "cloud"
    CLOUD_SHADOW = "cloud-shadow"


class BandCommonNames_V1_0_0(StrEnum):
    """https://github.com/stac-extensions/eo/blob/v2.0.0/README.md#common-band-names"""

    COASTAL = "coastal"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    PAN = "pan"
    REDEDGE = "rededge"
    NIR = "nir"
    NIR08 = "nir08"
    NIR09 = "nir09"
    CIRRUS = "cirrus"
    SWIR16 = "swir16"
    SWIR22 = "swir22"
    LWIR = "lwir"
    LWIR11 = "lwir11"
    LWIR12 = "lwir12"


class EoBand_V1_0_0(StacBaseModel):
    common_name: BandCommonNames_V1_0_0 | None = None
    center_wavelength: float | None = None
    full_width_half_max: float | None = None


class EoBand_V1_1_0(EoBand_V1_0_0):
    solar_illumination: float | None = None


class ElectroOpticalFields_V1_0_0(BaseExtraFields):
    """https://github.com/stac-extensions/eo"""

    cloud_cover: PercentageValue | None = None
    bands: list[EoBand_V1_0_0] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="eo")
    )


class ElectroOpticalFields_V1_1_0(ElectroOpticalFields_V1_0_0):
    snow_cover: PercentageValue | None = None


class OldElectroOpticalExtension(OldBaseExtension):
    prefix: str = "eo"
    maturity_level: MaturityLevel = MaturityLevel.STABLE


old_stac_extensions: list[OldElectroOpticalExtension] = [
    OldElectroOpticalExtension(
        stac_extension=AnyUrl(
            "https://stac-extensions.github.io/eo/v1.0.0/schema.json"
        ),
        version="v1.0.0",
        allowed_objects={
            "Item",
            "Asset",
            "Collection",
        },
    ),
    OldElectroOpticalExtension(
        stac_extension=AnyUrl(
            "https://stac-extensions.github.io/eo/v1.1.0/schema.json"
        ),
        version="v1.1.0",
        allowed_objects={
            "Item",
            "Asset",
            "Collection",
        },
    ),
    OldElectroOpticalExtension(
        stac_extension=AnyUrl(
            "https://stac-extensions.github.io/eo/v2.0.0-beta.1/schema.json"
        ),
        version="v2.0.0-beta.1",
        allowed_objects={"Item", "Asset", "Collection", "Band"},
    ),
]
