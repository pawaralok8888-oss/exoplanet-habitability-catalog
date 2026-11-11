from typing import Literal


from pydantic import BaseModel, ConfigDict, Field, field_validator

class RequestModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        allow_inf_nan=False,
    )


class PlanetRequest(RequestModel):
    name: str = Field(min_length=1, max_length=100)

    star_id: int | None = Field(default=None, gt=0)
    radius: float | None = Field(default=None, gt=0)
    mass: float | None = Field(default=None, gt=0)
    orbital_period: float | None = Field(default=None, gt=0)
    orbital_distance: float | None = Field(default=None, gt=0)
    stellar_flux: float | None = Field(default=None, ge=0)
    equilibrium_temp: float | None = Field(default=None, gt=0)
    esi_score: float | None = Field(default=None, ge=0, le=1)

    habitable_zone_flag: Literal[0, 1] | None = None
    habitable_zone_optimistic_flag: Literal[0, 1] | None = None
    discovery_year: int | None = Field(default=None, ge=0)

    density: float | None = Field(default=None, ge=0)
    gravity: float | None = Field(default=None, ge=0)
    escape_velocity: float | None = Field(default=None, ge=0)

    detection_method: str | None = Field(default=None, max_length=100)
    planet_type: str | None = Field(default=None, max_length=64)
    data_source: str | None = Field(default=None, max_length=100)
    @field_validator("detection_method", "planet_type", "data_source", mode="before")
    @classmethod
    def blank_optional_text_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

class StarRequest(RequestModel):
    name: str = Field(min_length=1, max_length=100)

    temperature: float | None = Field(default=None, gt=0)
    radius: float | None = Field(default=None, gt=0)
    mass: float | None = Field(default=None, gt=0)
    distance_from_earth: float | None = Field(default=None, ge=0)
    age: float | None = Field(default=None, ge=0)
    luminosity: float | None = Field(default=None, ge=0)

    hz_conservative_inner_au: float | None = Field(default=None, ge=0)
    hz_conservative_outer_au: float | None = Field(default=None, ge=0)
    stellar_type: str | None = Field(default=None, max_length=64)

    @field_validator("stellar_type", mode="before")
    @classmethod
    def blank_optional_text_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value