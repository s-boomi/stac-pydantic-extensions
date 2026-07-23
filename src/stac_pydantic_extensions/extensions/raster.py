from __future__ import annotations

from enum import StrEnum, auto
from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict, Field
from stac_pydantic.shared import NumType, StacBaseModel

from stac_pydantic_extensions import DataTypes, NoDataTypes, Statistics
from stac_pydantic_extensions.compat.stac_pydantic import Asset, Band, Item
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    MaturityLevel,
    OldBaseExtension,
    prefix_alias,
)
from stac_pydantic_extensions.types import (
    RasterFieldsType,
    StacObject,
    StacSecondaryObject,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import (
        ExtendableStacObject,
    )


RASTER_BAND_FIELDS = {
    "sampling",
    "bits_per_sample",
    "spatial_resolution",
    "scale",
    "offset",
    "histogram",
}


class Histogram(StacBaseModel):
    """https://github.com/stac-extensions/raster#histogram-object"""

    count: NumType = Field(...)
    min: NumType = Field(...)
    max: NumType = Field(...)
    buckets: list[NumType] = Field(...)


class RasterBand_V1_0_0(StacBaseModel):
    """https://github.com/stac-extensions/raster/tree/v1.0.0#raster-band-object"""

    nodata: float | None = None
    data_type: DataTypes | None = None
    statistics: Statistics | None = None
    unit: str | None = None
    statistics: Statistics | None = None
    # Kept in V2.0.0
    sampling: RasterSampling | None = None
    bits_per_sample: NumType | None = None
    spatial_resolution: NumType | None = None
    scale: NumType | None = None
    offset: NumType | None = None
    histogram: Histogram | None = None

    def to_new_band(self) -> Band:
        band = RasterBand_V1_1_0.model_validate(self.model_dump())
        return Band.model_validate(
            {
                "raster:" + k if k in RASTER_BAND_FIELDS else k: v
                for k, v in band.model_dump().items()
            }
        )


class RasterBand_V1_1_0(RasterBand_V1_0_0):
    """https://github.com/stac-extensions/raster/tree/v1.1.0#raster-band-object"""

    nodata: float | NoDataTypes | None = None

    def to_new_band(self) -> Band:
        return Band.model_validate(
            {
                "raster:" + k if k in RASTER_BAND_FIELDS else k: v
                for k, v in self.model_dump().items()
            }
        )


class RasterFields_V1_0_0(BaseExtraFields):
    """https://github.com/stac-extensions/raster/tree/v1.0.0"""

    bands: list[RasterBand_V1_0_0] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="eo")
    )

    @staticmethod
    def _convert_eo_bands(
        bands: list[RasterBand_V1_1_0],
    ) -> list[Band]:
        return [b.to_new_band() for b in bands]

    def _migrate_to_1_1_0(
        self, stac_object: ExtendableStacObject
    ) -> RasterFields_V1_1_0:
        """https://github.com/stac-extensions/eo/blob/main/CHANGELOG.md#v110---2023-02-10"""
        obj = self.model_dump()
        return RasterFields_V1_1_0.model_validate(obj)

    def _add_bands_to_obj(
        self, stac_object: ExtendableStacObject
    ) -> ExtendableStacObject:
        if self.bands is not None:
            bands = self.bands

            if isinstance(stac_object, Item):
                if stac_object.properties.bands is None:
                    stac_object.properties.bands = [b.to_new_band() for b in bands]
                else:
                    stac_object.properties.bands.extend(
                        [b.to_new_band() for b in bands]
                    )
            elif isinstance(stac_object, Asset):
                asset_obj = stac_object.model_dump()
                if "bands" in asset_obj:
                    asset_obj["bands"].extend(
                        [b.to_new_band().model_dump() for b in bands]
                    )
                else:
                    asset_obj["bands"] = [b.to_new_band().model_dump() for b in bands]
                del asset_obj["eo:bands"]
                stac_object = Asset.model_validate(asset_obj)

        return stac_object

    def _migrate_to_2_0_0(
        self,
        stac_object: ExtendableStacObject,
    ) -> RasterFields:
        """Applies to 2.0.0 and 2.0.0-beta.1
        https://github.com/stac-extensions/eo/blob/main/CHANGELOG.md#v200---2024-09-09
        """

        obj = self._migrate_to_1_1_0(stac_object).model_dump()
        return RasterFields.model_validate(obj)

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> RasterFieldsType:
        if version == "1.1.0":
            return self._migrate_to_1_1_0(stac_object)
        return self._migrate_to_2_0_0(stac_object=stac_object)


class RasterFields_V1_1_0(RasterFields_V1_0_0):
    """https://github.com/stac-extensions/eo/tree/v1.1.0"""

    def _migrate_to_1_1_0(
        self, stac_object: ExtendableStacObject
    ) -> RasterFields_V1_1_0:
        return self

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> RasterFieldsType:
        return self._migrate_to_2_0_0(stac_object=stac_object)


class RasterSampling(StrEnum):
    AREA = auto()
    POINT = auto()


class RasterFields(BaseExtraFields):
    """https://github.com/stac-extensions/raster"""

    sampling: RasterSampling | None = None
    bits_per_sample: NumType | None = None
    spatial_resolution: NumType | None = None
    scale: NumType | None = None
    offset: NumType | None = None
    histogram: Histogram | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="raster")
    )

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> RasterFieldsType:
        return self

    def _add_bands_to_obj(
        self, stac_object: ExtendableStacObject
    ) -> ExtendableStacObject:
        return stac_object


class OldRasterExtension(OldBaseExtension):
    prefix: str = "eo"
    maturity_level: MaturityLevel = MaturityLevel.STABLE


FIELD_MODELS = {
    "v1.0.0": RasterFields_V1_0_0,
    "v1.1.0": RasterFields_V1_1_0,
    "v2.0.0-beta.1": RasterFields,
    "v2.0.0": RasterFields,
}


class RasterExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/raster/v2.0.0/schema.json"
    )
    prefix: ClassVar[Literal["raster"]] = "raster"
    old_stac_extensions: ClassVar[list[OldRasterExtension]] = [
        OldRasterExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/raster/v1.0.0/schema.json"
            ),
            version="v1.0.0",
            allowed_objects={
                "Item",
                "Asset",
                "Collection",
            },
        ),
        OldRasterExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
            ),
            version="v1.1.0",
            allowed_objects={
                "Item",
                "Asset",
                "Collection",
            },
        ),
        OldRasterExtension(
            stac_extension=AnyUrl(
                "https://stac-extensions.github.io/raster/v2.0.0-beta.1/schema.json"
            ),
            version="v2.0.0-beta.1",
            allowed_objects={"Item", "Asset", "Collection", "Band"},
        ),
    ]
    fields: RasterFieldsType
    version: ClassVar[Literal["v2.0.0"]] = "v2.0.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Asset", "Collection", "Band"}

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> RasterExtension | None:
        if not cls.has_extension(stac_object=stac_object):
            return None

        properties = cls._extract_properties(stac_object=stac_object)

        # Find the version
        stac_ext_version = (
            cls.version
            if cls.stac_extension in stac_object.stac_extensions
            else [
                stac_ext_info.version
                for stac_ext_info in cls.old_stac_extensions
                if stac_ext_info.stac_extension in stac_object.stac_extensions
            ][0]
        )

        model = FIELD_MODELS[stac_ext_version]
        fields = model.model_validate(properties or {})

        if migrate and stac_ext_version != cls.version:
            # First remove old schema and replace by current
            stac_object.stac_extensions = [
                stac_extension
                for stac_extension in stac_object.stac_extensions or []
                if stac_extension not in cls.schema_uris()
            ]
            stac_object.stac_extensions.append(cls.stac_extension)
            fields = fields.migrate(
                stac_object,
                cls.version,
            )

        return cls(
            fields=fields,
            _loaded_version=None if migrate else stac_ext_version,
        )

    @classmethod
    def from_stac_secondary_object(
        cls, stac_object: StacSecondaryObject
    ) -> RasterExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            if (
                stac_object.__class__.__name__.lower() == "asset"
                and "eo:bands" in obj_properties
            ):
                return cls(fields=RasterFields_V1_0_0.model_validate(obj_properties))

            return cls(fields=RasterFields.model_validate(obj_properties))

    @classmethod
    def add_extension(
        cls, stac_object: ExtendableStacObject, **ext_fields
    ) -> BaseExtension:
        """Returns an instantiated form of the RasterExtension with the corresponding fields"""
        if isinstance(stac_object, StacObject) and not cls.has_extension(stac_object):
            if stac_object.stac_extensions is None:
                stac_object.stac_extensions = []
            stac_object.stac_extensions.append(cls.stac_extension)
            return cls(fields=RasterFields(**ext_fields))

        if isinstance(stac_object, StacSecondaryObject):
            return cls(fields=RasterFields(**ext_fields))

        raise ValueError("This type of file isn't taken into account")

    def migrate(
        self, stac_object: ExtendableStacObject, version: str | None = None
    ) -> ExtendableStacObject:
        """Migrates fields to the set version given a STAC object

        Args:
            stac_object (ExtendableStacObject): The STAC object to migrate
            version (str | None, optional): The version to migrate the STAC object's
                extra fields to. If version is None, then this STAC object will be migrated
                to the latest available version supported by the package. Defaults to None.

        Raises:
            ValueError: Raises when no version matches the ones available

        Returns:
            ExtendableStacObject: The original STAC object, mutated in the case some fields
                get transferred to common metadata.
        """
        if version is not None and version not in self.available_versions():
            raise ValueError(
                f"The specified version {version} isn't available. "
                f"Available versions are {self.available_versions()}"
            )

        _version = version if version is not None else self.version

        if isinstance(stac_object, StacObject):
            stac_object.stac_extensions = [
                stac_extension
                for stac_extension in stac_object.stac_extensions or []
                if stac_extension not in self.schema_uris()
            ]

            stac_object.stac_extensions.append(self.stac_extension)

        new_stac_object = self.fields._add_bands_to_obj(stac_object)

        self.fields = self.fields.migrate(
            stac_object=stac_object,
            version=_version,
        )

        return new_stac_object
