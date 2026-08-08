from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import AnyUrl, ConfigDict, computed_field
from stac_pydantic.shared import StacBaseModel

from stac_pydantic_extensions import Collection, Item
from stac_pydantic_extensions.types import (
    BaseExtraFieldsType,
    StacObject,
    StacSecondaryObject,
)

if TYPE_CHECKING:
    from stac_pydantic_extensions.types import (
        ExtendableStacObject,
    )


def prefix_alias(field_name: str, prefix: str) -> str:
    return prefix + ":" + field_name


class MaturityLevel(IntEnum):
    PROPOSAL = 0
    PILOT = 1
    CANDIDATE = 3
    STABLE = 6
    DEPRECATED = -1


class BaseExtraFields(StacBaseModel):
    model_config = ConfigDict(
        extra="ignore", alias_generator=lambda s: prefix_alias(s, prefix="")
    )

    @classmethod
    def downgrade(
        cls, stac_object: ExtendableStacObject, ext_vers: str
    ) -> OldBaseExtraFields | None:
        """Only called if the user doesn't wish to migrate"""
        pass

    def migrate(
        self, stac_object: ExtendableStacObject, version: str
    ) -> BaseExtraFieldsType:
        """Common method for all BaseExtraFields and OldBaseExtraFields types

        - If the class derives from BaseExtraFields, always return self
        - If the class derives from OldBaseExtraFields, implement strategy

        If the stac_object in question is an Item, look for Assets and Bands and
        apply migrations.

        If the stact_object is a Collection, look in Assets and ItemAssets. Do not attempt to
        migrate items
        """
        return self


class OldBaseExtraFields(BaseExtraFields):
    pass


class _BaseExtension(StacBaseModel):
    stac_extension: AnyUrl
    prefix: str
    version: str
    allowed_objects: set[str]
    # No maturity level is considered as WIP
    maturity_level: MaturityLevel | None = None


class _BaseClassExtension(StacBaseModel):
    stac_extension: ClassVar[AnyUrl]
    prefix: ClassVar[str]
    version: ClassVar[str]
    allowed_objects: ClassVar[set[str]]
    maturity_level: ClassVar[MaturityLevel | None] = None


class OldBaseExtension(_BaseExtension):
    fields: OldBaseExtraFields | None = None


FIELD_MODELS = {"old": OldBaseExtraFields}


class BaseExtension(_BaseClassExtension):
    """Base model for extensions"""

    # List of previous STAC extensions
    # Can be left empty some extensions are at their first version
    old_stac_extensions: ClassVar[list[OldBaseExtension]] = []

    fields: BaseExtraFieldsType
    _loaded_version: str | None = None

    @classmethod
    def schema_uris(cls) -> list[AnyUrl]:
        """List the schema URIs of the extension"""
        return [cls.stac_extension] + [
            old_ext.stac_extension for old_ext in cls.old_stac_extensions
        ]

    @classmethod
    def available_versions(cls) -> list[str]:
        """List the available versions of the extension"""
        return [cls.version] + [old_ext.version for old_ext in cls.old_stac_extensions]

    @computed_field
    @property
    def loaded_version(self) -> str:
        if self._loaded_version is None:
            return self.version
        return self._loaded_version

    @classmethod
    def add_extension(
        cls, stac_object: ExtendableStacObject, **ext_fields
    ) -> BaseExtension:
        """Returns an instantiated form of the extension with fields"""
        if isinstance(stac_object, StacObject) and not cls.has_extension(stac_object):
            if stac_object.stac_extensions is None:
                stac_object.stac_extensions = []
            stac_object.stac_extensions.append(cls.stac_extension)
            return cls(fields=BaseExtraFields(**ext_fields))

        if isinstance(stac_object, StacSecondaryObject):
            return cls(fields=BaseExtraFields(**ext_fields))

        raise ValueError("This type of file isn't taken into account")

    def remove_extension(
        self, stac_object: ExtendableStacObject
    ) -> ExtendableStacObject:
        """Removes any variation of the extension to the object"""
        if (
            isinstance(stac_object, StacObject)
            and stac_object.stac_extensions is not None
        ):
            ext_to_remove = set(stac_object.stac_extensions).intersection(
                set(self.schema_uris())
            )
            stac_object.stac_extensions = [
                uri for uri in stac_object.stac_extensions if uri not in ext_to_remove
            ]

            if len(stac_object.stac_extensions) == 0:
                stac_object.stac_extensions = None

        # next remove fields
        fields_to_remove = self.fields.model_dump()
        stac_dict = stac_object.model_dump()

        if isinstance(stac_object, Item):
            stac_dict["properties"] = {
                k: v
                for k, v in stac_dict["properties"].items()
                if k not in fields_to_remove
            }
        elif isinstance(stac_object, Collection):
            stac_dict["summaries"] = {
                k: v
                for k, v in (stac_dict.get("summaries") or {}).items()
                if k not in fields_to_remove
            }
        else:
            stac_dict = {
                k: v for k, v in stac_dict.items() if k not in fields_to_remove
            }

        return stac_object.__class__.model_validate(stac_dict)

    @classmethod
    def has_extension(cls, stac_object: ExtendableStacObject) -> bool:
        """Checks if any variation of the schema exists"""
        if isinstance(stac_object, StacObject):
            if stac_object.stac_extensions is not None:
                return (
                    len(
                        set(stac_object.stac_extensions).intersection(
                            set(cls.schema_uris())
                        )
                    )
                    > 0
                )

        elif isinstance(stac_object, StacSecondaryObject):
            return any(
                field.startswith(cls.prefix)
                for field in stac_object.model_fields.keys()
            )

        return False

    def is_from_github(self) -> bool:
        return self.stac_extension.host == "stac-extensions.github.io"

    @staticmethod
    def _extract_properties(stac_object: StacObject) -> dict[str, Any]:
        if isinstance(stac_object, Item):
            return stac_object.properties.to_dict()
        if isinstance(stac_object, Collection):
            return stac_object.summaries or {}

        return stac_object.to_dict()

    @classmethod
    def from_stac_object(
        cls,
        stac_object: StacObject,
        migrate: bool = False,
    ) -> "BaseExtension | None":
        """Creates an instance of the extension from a STAC item

        Args:
            stac_object: the STAC item (Item, Collection, etc.).
            migrate: If True, migrate data towars extension's current version

        Returns:
            An extension instance or None if the extension isn't present
        """
        if not cls.has_extension(stac_object=stac_object):
            return None

        properties = cls._extract_properties(stac_object=stac_object)

        stac_ext_version = (
            cls.version
            if cls.stac_extension in stac_object.stac_extensions
            else next(
                stac_ext_info.version
                for stac_ext_info in cls.old_stac_extensions
                if stac_ext_info.stac_extension in stac_object.stac_extensions
            )
        )

        model = FIELD_MODELS[stac_ext_version]
        fields = model.model_validate(properties or {})

        if migrate and stac_ext_version != cls.version:
            stac_object.stac_extensions = [
                stac_extension
                for stac_extension in stac_object.stac_extensions
                if stac_extension not in cls.schema_uris()
            ]
            stac_object.stac_extensions.append(cls.stac_extension)
            # Applique la migration sur les champs
            fields = fields.migrate(
                stac_object=stac_object,
                version=cls.version,
            )

        return cls(
            fields=fields,
            _loaded_version=None if migrate else stac_ext_version,
        )

    @classmethod
    def from_stac_secondary_object(
        cls, stac_object: StacSecondaryObject
    ) -> BaseExtension | None:
        """Creates an instance from Asset, ItemAsset and Band objects

        Since these objects don't possess a schema URI, they're automatically assumed
        to be under the latest version"""
        if not cls.has_extension(stac_object=stac_object):
            return None

        obj_properties = stac_object.to_dict()
        if any(field.startswith(cls.prefix + ":") for field in obj_properties.keys()):
            return cls(fields=BaseExtraFields.model_validate(obj_properties))

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

        self.fields = self.fields.migrate(
            stac_object=stac_object,
            version=_version,
        )

        return stac_object

    def __getattr__(self, name: str):
        allowed_fields = list(self.fields.__dict__.keys())
        if name not in allowed_fields:
            raise AttributeError(
                f"{name} not allowed as a field. Possible fields are {allowed_fields}"
            )
        return getattr(self.fields, name)

    def __setattr__(self, name, value):
        model_fields = type(self).model_fields

        # If it's one of my own fields, set it normally.
        if name in model_fields or name.startswith("_"):
            return super().__setattr__(name, value)

        # Otherwise, if it's a field on the inner model, delegate.
        fields = object.__getattribute__(self, "fields")
        if name in type(fields).model_fields:
            setattr(fields, name, value)
            return

        raise AttributeError(name)
