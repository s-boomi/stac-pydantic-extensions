from typing import Annotated, ClassVar, Literal

from pydantic import AnyUrl, ConfigDict
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions import Collection, Item, Link
from stac_pydantic_extensions.extensions._base import (
    BaseExtension,
    BaseExtraFields,
    prefix_alias,
)
from stac_pydantic_extensions.validators import validate_doi

DOI_URL_BASE = "https://doi.org/"


ValidateDoiOrNone = Annotated[str, validate_doi]


class Publication(StacBaseModel):
    doi: ValidateDoiOrNone
    citation: str | None = None

    def doi_as_url(self) -> str | None:
        if self.doi is not None:
            from urllib import parse

            return DOI_URL_BASE + parse.quote(self.doi)


class ScientificCitationFields(BaseExtraFields):
    """https://github.com/stac-extensions/scientific"""

    doi: ValidateDoiOrNone
    citation: str | None = None
    publications: list[Publication] | None = None

    model_config = ConfigDict(
        extra="forbid", alias_generator=lambda s: prefix_alias(s, prefix="sci")
    )

    def doi_as_url(self) -> str | None:
        if self.doi is not None:
            from urllib import parse

            return DOI_URL_BASE + parse.quote(self.doi)


class ScientificCitationExtension(BaseExtension):
    stac_extension: ClassVar[AnyUrl] = AnyUrl(
        "https://stac-extensions.github.io/sci/v1.0.0/schema.json"
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
