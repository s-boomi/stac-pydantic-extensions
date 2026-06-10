"""
Simplified Pydantic v2 model for PROJJSON v0.7.
Replaces the datamodel-codegen output (~1200 lines) with ~250 lines by:
  - Using a shared CommonFields base instead of the Xxx1/Xxx2 mixin explosion
  - Replacing numbered enums with descriptive Literal or str-Enum types
  - Collapsing RootModel wrappers into plain type aliases
  - Replacing the empty OneAndOnlyOneOfDatumOrDatumEnsemble base with a model_validator
  - Using discriminated unions on the `type` field where possible
"""

from __future__ import annotations

from enum import StrEnum, auto
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

# ---------------------------------------------------------------------------
# Small value types
# ---------------------------------------------------------------------------


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StrictBaseModelByName(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Bbox(StrictBaseModel):
    east_longitude: float
    west_longitude: float
    south_latitude: float
    north_latitude: float


class VerticalExtent(StrictBaseModel):
    minimum: float
    maximum: float
    unit: Unit | None = None


class TemporalExtent(StrictBaseModel):
    start: str
    end: str


class Usage(StrictBaseModel):
    scope: str | None = None
    area: str | None = None
    bbox: Bbox | None = None
    vertical_extent: VerticalExtent | None = None
    temporal_extent: TemporalExtent | None = None


class Id(StrictBaseModel):
    authority: str
    code: str | int
    version: str | float | None = None
    authority_citation: str | None = None
    uri: str | None = None


# ---------------------------------------------------------------------------
# Unit
# ---------------------------------------------------------------------------


class UnitType(StrEnum):
    LinearUnit = auto()
    AngularUnit = auto()
    ScaleUnit = auto()
    TimeUnit = auto()
    ParametricUnit = auto()
    Unit = auto()


class UnitObject(StrictBaseModel):
    type: UnitType
    name: str
    conversion_factor: float | None = None
    id: Id | None = None
    ids: list[Id] | None = None


# A unit can be a well-known string shorthand or a full object.
Unit = str | UnitObject


class ValueAndUnit(StrictBaseModel):
    value: float
    unit: Unit


# A value expressed in degrees (plain float) or with an explicit unit.
ValueInDegree = float | ValueAndUnit
# A value expressed in metres (plain float) or with an explicit unit.
ValueInMetre = float | ValueAndUnit


# ---------------------------------------------------------------------------
# Shared base for almost every PROJJSON object
# ---------------------------------------------------------------------------


class CommonFields(StrictBaseModelByName):
    """
    Fields that appear on nearly every object in the schema.
    Concrete classes inherit from this instead of the Xxx1/Xxx2 mixin pattern.
    """

    field_schema: str | None = Field(None, alias="$schema")
    scope: str | None = None
    area: str | None = None
    bbox: Bbox | None = None
    vertical_extent: VerticalExtent | None = None
    temporal_extent: TemporalExtent | None = None
    usages: list[Usage] | None = None
    remarks: str | None = None
    id: Id | None = None
    ids: list[Id] | None = None


# ---------------------------------------------------------------------------
# Supporting objects
# ---------------------------------------------------------------------------


class Direction(StrEnum):
    NORTH = auto()
    NORTH_NORTH_EAST = "northNorthEast"
    NORTH_EAST = "northEast"
    EAST_NORTH_EAST = "eastNorthEast"
    EAST = auto()
    EAST_SOUTH_EAST = "eastSouthEast"
    SOUTH_EAST = "southEast"
    SOUTH_SOUTH_EAST = "southSouthEast"
    SOUTH = auto()
    SOUTH_SOUTH_WEST = "southSouthWest"
    SOUTH_WEST = "southWest"
    WEST_SOUTH_WEST = "westSouthWest"
    WEST = auto()
    WEST_NORTH_WEST = "westNorthWest"
    NORTH_WEST = "northWest"
    NORTH_NORTH_WEST = "northNorthWest"
    UP = auto()
    DOWN = auto()
    GEOCENTRIC_X = "geocentricX"
    GEOCENTRIC_Y = "geocentricY"
    GEOCENTRIC_Z = "geocentricZ"
    COLUMN_POSITIVE = "columnPositive"
    COLUMN_NEGATIVE = "columnNegative"
    ROW_POSITIVE = "rowPositive"
    ROW_NEGATIVE = "rowNegative"
    DISPLAY_RIGHT = "displayRight"
    DISPLAY_LEFT = "displayLeft"
    DISPLAY_UP = "displayUp"
    DISPLAY_DOWN = "displayDown"
    FORWARD = auto()
    AFT = auto()
    PORT = auto()
    STARBOARD = auto()
    CLOCKWISE = auto()
    COUNTER_CLOCKWISE = "counterClockwise"
    TOWARDS = auto()
    AWAY_FROM = "awayFrom"
    FUTURE = auto()
    PAST = auto()
    UNSPECIFIED = auto()


class RangeMeaning(StrEnum):
    exact = auto()
    wraparound = auto()


class CoordinateSystemSubtype(StrEnum):
    Cartesian = auto()
    spherical = auto()
    ellipsoidal = auto()
    vertical = auto()
    ordinal = auto()
    parametric = auto()
    affine = auto()
    TemporalDateTime = auto()
    TemporalCount = auto()
    TemporalMeasure = auto()


class Meridian(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["Meridian"] | None = None
    longitude: ValueInDegree
    id: Id | None = None
    ids: list[Id] | None = None


class Axis(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["Axis"] | None = None
    name: str
    abbreviation: str
    direction: Direction
    meridian: Meridian | None = None
    unit: Unit | None = None
    minimum_value: float | None = None
    maximum_value: float | None = None
    range_meaning: RangeMeaning | None = None
    id: Id | None = None
    ids: list[Id] | None = None


class CoordinateSystem(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["CoordinateSystem"] | None = None
    name: str | None = None
    subtype: CoordinateSystemSubtype
    axis: list[Axis]
    id: Id | None = None
    ids: list[Id] | None = None


class PrimeMeridian(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["PrimeMeridian"] | None = None
    name: str
    longitude: ValueInDegree | None = None
    id: Id | None = None
    ids: list[Id] | None = None


class Ellipsoid(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["Ellipsoid"] | None = None
    name: str
    # For a sphere, only radius is used. For a spheroid, semi_major_axis is
    # required and the shape is given by either semi_minor_axis or
    # inverse_flattening (but not both).
    semi_major_axis: ValueInMetre | None = None
    semi_minor_axis: ValueInMetre | None = None
    inverse_flattening: float | None = None
    radius: ValueInMetre | None = None
    id: Id | None = None
    ids: list[Id] | None = None

    @model_validator(mode="after")
    def check_shape(self) -> "Ellipsoid":
        if self.radius is not None:
            # Sphere — semi_major_axis should not be set
            return self
        if self.semi_major_axis is None:
            raise ValueError(
                "semi_major_axis is required for a non-spherical ellipsoid"
            )
        has_minor = self.semi_minor_axis is not None
        has_inv = self.inverse_flattening is not None
        if has_minor == has_inv:
            raise ValueError(
                "Exactly one of semi_minor_axis or inverse_flattening must be provided"
            )
        return self


class Member(StrictBaseModel):
    name: str
    id: Id | None = None
    ids: list[Id] | None = None


class DatumEnsemble(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["DatumEnsemble"] | None = None
    name: str
    members: list[Member]
    ellipsoid: Ellipsoid | None = None
    accuracy: str
    id: Id | None = None
    ids: list[Id] | None = None


class Method(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["OperationMethod"] | None = None
    name: str
    id: Id | None = None
    ids: list[Id] | None = None


class ParameterValue(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["ParameterValue"] | None = None
    name: str
    value: str | float
    unit: Unit | None = None
    id: Id | None = None
    ids: list[Id] | None = None


class DeformationModel(StrictBaseModel):
    name: str
    id: Id | None = None


# ---------------------------------------------------------------------------
# Datums
# ---------------------------------------------------------------------------


class GeodeticReferenceFrame(CommonFields):
    type: Literal["GeodeticReferenceFrame"] | None = None
    name: str
    anchor: str | None = None
    datum_epoch: float | None = None  # v0.6+
    ellipsoid: Ellipsoid
    prime_meridian: PrimeMeridian | None = None


class DynamicGeodeticReferenceFrame(CommonFields):
    type: Literal["DynamicGeodeticReferenceFrame"] | None = None
    name: str
    anchor: str | None = None
    datum_epoch: float | None = None  # v0.6+
    ellipsoid: Ellipsoid
    prime_meridian: PrimeMeridian | None = None
    frame_reference_epoch: float


class VerticalReferenceFrame(CommonFields):
    type: Literal["VerticalReferenceFrame"] | None = None
    name: str
    anchor: str | None = None
    datum_epoch: float | None = None  # v0.6+


class DynamicVerticalReferenceFrame(CommonFields):
    type: Literal["DynamicVerticalReferenceFrame"] | None = None
    name: str
    anchor: str | None = None
    datum_epoch: float | None = None  # v0.6+
    frame_reference_epoch: float


class TemporalDatum(CommonFields):
    type: Literal["TemporalDatum"] | None = None
    name: str
    calendar: str
    time_origin: str | None = None


class ParametricDatum(CommonFields):
    type: Literal["ParametricDatum"] | None = None
    name: str
    anchor: str | None = None


class EngineeringDatum(CommonFields):
    type: Literal["EngineeringDatum"] | None = None
    name: str
    anchor: str | None = None


Datum = (
    GeodeticReferenceFrame
    | DynamicGeodeticReferenceFrame
    | VerticalReferenceFrame
    | DynamicVerticalReferenceFrame
    | TemporalDatum
    | ParametricDatum
    | EngineeringDatum
)


# ---------------------------------------------------------------------------
# CRS types  (forward-referenced via string annotations where needed)
# ---------------------------------------------------------------------------


def _datum_xor_ensemble_validator(self: Any) -> Any:
    """Shared validator: exactly one of datum / datum_ensemble must be set."""
    has_datum = self.datum is not None
    has_ensemble = self.datum_ensemble is not None
    if has_datum == has_ensemble:  # both set or neither set
        raise ValueError("Exactly one of datum or datum_ensemble must be provided")
    return self


class GeodeticCrs(CommonFields):
    type: Literal["GeodeticCRS", "GeographicCRS"] | None = None
    name: str
    datum: GeodeticReferenceFrame | DynamicGeodeticReferenceFrame | None = None
    datum_ensemble: DatumEnsemble | None = None
    coordinate_system: CoordinateSystem | None = None
    deformation_models: list[DeformationModel] | None = None

    check_datum = model_validator(mode="after")(_datum_xor_ensemble_validator)


class VerticalCrs(CommonFields):
    type: Literal["VerticalCRS"] | None = None
    name: str
    datum: VerticalReferenceFrame | DynamicVerticalReferenceFrame | None = None
    datum_ensemble: DatumEnsemble | None = None
    coordinate_system: CoordinateSystem | None = None
    geoid_model: GeoidModel | None = None
    geoid_models: list[GeoidModel] | None = None
    deformation_models: list[DeformationModel] | None = None

    check_datum = model_validator(mode="after")(_datum_xor_ensemble_validator)


class ProjectedCrs(CommonFields):
    type: Literal["ProjectedCRS"] | None = None
    name: str
    base_crs: GeodeticCrs
    conversion: Conversion
    coordinate_system: CoordinateSystem


class EngineeringCrs(CommonFields):
    type: Literal["EngineeringCRS"] | None = None
    name: str
    datum: EngineeringDatum
    coordinate_system: CoordinateSystem | None = None


class ParametricCrs(CommonFields):
    type: Literal["ParametricCRS"] | None = None
    name: str
    datum: ParametricDatum
    coordinate_system: CoordinateSystem | None = None


class TemporalCrs(CommonFields):
    type: Literal["TemporalCRS"] | None = None
    name: str
    datum: TemporalDatum
    coordinate_system: CoordinateSystem | None = None


class CompoundCrs(CommonFields):
    type: Literal["CompoundCRS"] | None = None
    name: str
    components: list[Crs]


class BoundCrs(CommonFields):
    type: Literal["BoundCRS"] | None = None
    name: str | None = None
    source_crs: Crs
    target_crs: Crs
    transformation: AbridgedTransformation


# Derived CRS types -----------------------------------------------------------


class DerivedGeodeticCrs(CommonFields):
    type: Literal["DerivedGeodeticCRS", "DerivedGeographicCRS"] | None = None
    name: str
    base_crs: GeodeticCrs
    conversion: Conversion
    coordinate_system: CoordinateSystem


class DerivedProjectedCrs(CommonFields):
    type: Literal["DerivedProjectedCRS"] | None = None
    name: str
    base_crs: ProjectedCrs
    conversion: Conversion
    coordinate_system: CoordinateSystem


class DerivedVerticalCrs(CommonFields):
    type: Literal["DerivedVerticalCRS"] | None = None
    name: str
    base_crs: VerticalCrs
    conversion: Conversion
    coordinate_system: CoordinateSystem


class DerivedEngineeringCrs(CommonFields):
    type: Literal["DerivedEngineeringCRS"] | None = None
    name: str
    base_crs: EngineeringCrs
    conversion: Conversion
    coordinate_system: CoordinateSystem


class DerivedParametricCrs(CommonFields):
    type: Literal["DerivedParametricCRS"] | None = None
    name: str
    base_crs: ParametricCrs
    conversion: Conversion
    coordinate_system: CoordinateSystem


class DerivedTemporalCrs(CommonFields):
    type: Literal["DerivedTemporalCRS"] | None = None
    name: str
    base_crs: TemporalCrs
    conversion: Conversion
    coordinate_system: CoordinateSystem


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


class Conversion(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["Conversion"] | None = None
    name: str
    method: Method
    parameters: list[ParameterValue] | None = None
    id: Id | None = None
    ids: list[Id] | None = None


class AbridgedTransformation(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["AbridgedTransformation"] | None = None
    name: str
    source_crs: Crs | None = None
    method: Method
    parameters: list[ParameterValue]
    id: Id | None = None
    ids: list[Id] | None = None


class Transformation(CommonFields):
    type: Literal["Transformation"] | None = None
    name: str
    source_crs: Crs
    target_crs: Crs
    interpolation_crs: Crs | None = None
    method: Method
    parameters: list[ParameterValue]
    accuracy: str | None = None


class PointMotionOperation(CommonFields):
    type: Literal["PointMotionOperation"] | None = None
    name: str
    source_crs: Crs
    method: Method
    parameters: list[ParameterValue]
    accuracy: str | None = None


class ConcatenatedOperation(CommonFields):
    type: Literal["ConcatenatedOperation"] | None = None
    name: str
    source_crs: Crs
    target_crs: Crs
    steps: list[SingleOperation]
    accuracy: str | None = None


class GeoidModel(StrictBaseModel):
    name: str
    interpolation_crs: Crs | None = None
    id: Id | None = None


class CoordinateMetadata(StrictBaseModelByName):
    field_schema: str | None = Field(None, alias="$schema")
    type: Literal["CoordinateMetadata"] | None = None
    crs: Crs
    coordinateEpoch: float | None = None


# ---------------------------------------------------------------------------
# Union aliases
# ---------------------------------------------------------------------------

SingleOperation = Conversion | Transformation | PointMotionOperation

Crs = (
    BoundCrs
    | CompoundCrs
    | DerivedEngineeringCrs
    | DerivedGeodeticCrs
    | DerivedParametricCrs
    | DerivedProjectedCrs
    | DerivedTemporalCrs
    | DerivedVerticalCrs
    | EngineeringCrs
    | GeodeticCrs
    | ParametricCrs
    | ProjectedCrs
    | TemporalCrs
    | VerticalCrs
)

Model = Annotated[
    Crs
    | Datum
    | DatumEnsemble
    | Ellipsoid
    | PrimeMeridian
    | SingleOperation
    | ConcatenatedOperation
    | CoordinateMetadata,
    Field(description="Schema for PROJJSON (v0.7)"),
]


class ProjJson(
    RootModel[
        Crs
        | Datum
        | DatumEnsemble
        | Ellipsoid
        | PrimeMeridian
        | SingleOperation
        | ConcatenatedOperation
        | CoordinateMetadata,
    ]
):
    """Root type for any PROJJSON v0.7 doStrictcument."""


# ---------------------------------------------------------------------------
# Rebuild models that have forward references
# ---------------------------------------------------------------------------

for _cls in [
    GeoidModel,
    VerticalCrs,
    BoundCrs,
    CompoundCrs,
    AbridgedTransformation,
    Transformation,
    PointMotionOperation,
    ConcatenatedOperation,
    CoordinateMetadata,
    DerivedVerticalCrs,
    DerivedGeodeticCrs,
    DerivedProjectedCrs,
    DerivedEngineeringCrs,
    DerivedParametricCrs,
    DerivedTemporalCrs,
]:
    _cls.model_rebuild()
