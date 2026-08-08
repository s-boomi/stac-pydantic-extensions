from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions.compat.stac_pydantic import Collection, Item, Link
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)
from stac_pydantic_extensions.model_annotations import ValidateDoi

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import StacObject, StacSecondaryObject


DOI_URL_BASE = "https://doi.org/"


class Publication(StacBaseModel):
    doi: ValidateDoi | None = None
    citation: str | None = None

    def doi_as_url(self) -> str | None:
        if self.doi is not None:
            from urllib import parse

            return DOI_URL_BASE + parse.quote(self.doi)


class ScientificCitationFields(BaseExtraFields):
    """https://github.com/stac-extensions/scientific"""

    doi: ValidateDoi | None = None
    citation: str | None = None
    publications: list[Publication] | None = None

    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="sci")
    )

    def doi_as_url(self) -> str | None:
        if self.doi is not None:
            from urllib import parse

            return DOI_URL_BASE + parse.quote(self.doi)


FIELD_MODELS = {"v1.0.0": ScientificCitationFields}


class ScientificCitationExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/scientific/v1.0.0/schema.json"
    )
    prefix: ClassVar[Literal["sci"]] = "sci"
    fields: ScientificCitationFields
    version: ClassVar[Literal["v1.0.0"]] = "v1.0.0"
    allowed_objects: ClassVar[set[str]] = {"Item", "Collection"}

    def create_sci_link(self, stac_item: Item | Collection) -> Item | Collection:
        doi_url = self.fields.doi_as_url()
        if doi_url is not None:
            stac_item.links.append(Link(href=doi_url, rel="cite-as"))
        return stac_item

    @classmethod
    def from_stac_object(
        cls, stac_object: StacObject, migrate: bool = False
    ) -> ScientificCitationExtension | None:
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
    ) -> ScientificCitationExtension | None:
        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=ScientificCitationFields.model_validate(obj_properties))
