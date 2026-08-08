"""Webmap links extension"""

from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict, Field

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    MaturityLevel,
    prefix_alias,
)
from stac_pydantic_extensions.types import StacObject, StacSecondaryObject


class WebMapLinks3DTilesFields(BaseExtraFields):
    """
    https://github.com/stac-extensions/web-map-links#3d-tiles
    """

    rel: str = Field(..., alias="rel")
    href: str = Field(..., alias="href")
    type: str | None = None
    model_config = ConfigDict(extra="ignore")


class WebMapLinksOgcWmsFields(BaseExtraFields):
    """
    https://github.com/stac-extensions/web-map-links#ogc-wms
    """

    rel: str = Field(..., alias="rel")
    href: str = Field(..., alias="href")
    type: str | None = Field(None, alias="type")

    layers: list[str] = Field(...)
    styles: list[str] | None
    dimensions: dict[str, str] | None = None
    transparent: bool | None = False
    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="wmts")
    )


class WebMapLinksOgcWmtsFields(BaseExtraFields):
    """
    https://github.com/stac-extensions/web-map-links#ogc-wmts
    """

    rel: str = Field(..., alias="rel")
    href: str = Field(..., alias="href")
    href_servers: list[str] | None = Field(None, alias="href:servers")
    wmts_layer: str | list[str] = Field(..., alias="wmts:layer")
    wmts_encoding: str | None = Field(None, alias="wmts:encoding")
    model_config = ConfigDict(extra="ignore")


class WebMapLinksKvpFields(BaseExtraFields):
    """
    https://github.com/stac-extensions/web-map-links#kvp
    """

    type: str | None = Field(None, alias="type")
    encoding: str | None = None
    dimensions: dict[str, str] | None
    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="wmts")
    )


class WebMapLinksRestFields(BaseExtraFields):
    """
    https://github.com/stac-extensions/web-map-links#rest
    """

    type: str | None = Field(None, alias="type")
    encoding: str = Field(default="rest", alias="wmts:encoding")
    uri_template: str | None = Field(None, alias="uriTemplate")
    variables: dict[str, Any] | None = Field(None, alias="variables")


class WebMapLinksPmTilesFields(BaseExtraFields):
    """
    https://github.com/stac-extensions/web-map-links#tilejson
    """

    rel: str = Field("pmtiles", alias="rel")
    href: str = Field(..., alias="href")
    type: str | None = None
    layers: list[str] | None = Field(None, alias="pmtiles:layers")


class WebMapLinksXyzFields(BaseExtraFields):
    """
    https://github.com/stac-extensions/web-map-links#tilejson
    """

    rel: str = Field("xyz", alias="rel")
    href: str = Field(..., alias="href")
    type: str | None = None
    href_servers: list[str] | None = Field(None, alias="href:layers")


class WebMapLinksTileJsonFields(BaseExtraFields):
    """
    https://github.com/stac-extensions/web-map-links#tilejson
    """

    rel: str = Field("tilejson", alias="rel")
    href: str = Field(..., alias="href")
    type: str | None = None


class WebMapLinksFields(BaseExtraFields):
    """https://github.com/stac-extensions/web-map-links"""

    href_servers: list[str] | None = Field(None, alias="href:servers")
    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="wmts")
    )


FIELD_MODELS = {"v1.3.0": WebMapLinksFields}


class WebMapLinksExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/web-map-links/v1.3.0/schema.json"
    )
    prefix: ClassVar[Literal["wmts"]] = "wmts"
    fields: WebMapLinksFields
    version: ClassVar[Literal["v1.3.0"]] = "v1.3.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Catalog", "Collection"}
    maturity_level: ClassVar[MaturityLevel] = MaturityLevel.PROPOSAL

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> WebMapLinksExtension | None:
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
    ) -> WebMapLinksExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=WebMapLinksFields.model_validate(obj_properties))
