from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict

from stac_pydantic_extensions.compat.stac_pydantic import Collection, Item
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    MaturityLevel,
    OldBaseExtension,
    prefix_alias,
)
from stac_pydantic_extensions.model_annotations import PercentageValue
from stac_pydantic_extensions.types import (
    StacObject,
    StacSecondaryObject,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import (
        ExtendableStacObject,
    )


class EoAssetRoles(StrEnum):
    """https://github.com/stac-extensions/eo/blob/v2.0.0/README.md#best-practices"""

    REFLECTANCE = "reflectance"
    TEMPERATURE = "temperature"
    SATURATION = "saturation"
    CLOUD = "cloud"
    CLOUD_SHADOW = "cloud-shadow"


class BandCommonNames(StrEnum):
    """https://github.com/stac-extensions/eo/blob/v2.0.0/README.md#common-band-names"""

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


class OldElectroOpticalExtension(OldBaseExtension):
    prefix: str = "eo"
    maturity_level: MaturityLevel = MaturityLevel.STABLE


class ElectroOpticalExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/eo/v2.0.0/schema.json"
    )
    prefix: ClassVar[Literal["eo"]] = "eo"
    old_stac_extensions: ClassVar[list[OldElectroOpticalExtension]] = [
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
    fields: ElectroOpticalFields
    version: ClassVar[Literal["v2.0.0"]] = "v2.0.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Asset", "Collection", "Band"}

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

    @classmethod
    def add_extension(
        cls, stac_object: ExtendableStacObject, **ext_fields
    ) -> BaseExtension:
        """Returns an instantiated form of the ElectroOpticalExtension with the corresponding fields"""
        if isinstance(stac_object, StacObject) and not cls.has_extension(stac_object):
            if stac_object.stac_extensions is None:
                stac_object.stac_extensions = []
            stac_object.stac_extensions.append(cls.stac_extension)
            return cls(fields=ElectroOpticalFields(**ext_fields))

        if isinstance(stac_object, StacSecondaryObject):
            return cls(fields=ElectroOpticalFields(**ext_fields))

        raise ValueError("This type of file isn't taken into account")
