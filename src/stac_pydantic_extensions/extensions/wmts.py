"""Webmap links extension"""

from typing import Any, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict, Field

from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    MaturityLevel,
    prefix_alias,
)


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


class WebMapLinksExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/web-map-links/v1.3.0/schema.json"
    )
    prefix: ClassVar[Literal["wmts"]] = "wmts"
    fields: WebMapLinksFields
    version: ClassVar[Literal["v1.3.0"]] = "v1.3.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Catalog", "Collection"}
    maturity_level: ClassVar[MaturityLevel] = MaturityLevel.PROPOSAL
