"""Input validation and application-level operations."""

from pydantic import ValidationError as PydanticValidationError

from schemas import PlanetRequest, StarRequest

import repositories
from model.feature_contract import to_model_row
from predictor import predict_habitability


class ValidationError(ValueError):
    pass


def _validation_message(error):
    first_error = error.errors(include_url=False)[0]
    field = ".".join(str(part) for part in first_error["loc"]) or "request"
    return f"{field}: {first_error['msg']}"


def validate_planet(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")

    try:
        request_data = PlanetRequest.model_validate(payload)
    except PydanticValidationError as error:
        raise ValidationError(_validation_message(error)) from error

    return request_data.model_dump()


def validate_star(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")

    try:
        request_data = StarRequest.model_validate(payload)
    except PydanticValidationError as error:
        raise ValidationError(_validation_message(error)) from error

    return request_data.model_dump()

def prediction_for(data):
    model_data = dict(data)
    if data.get("star_id") is not None:
        star = repositories.get_star(data["star_id"])
        if star is None:
            raise ValidationError("star_id does not refer to an existing star")
        model_data.update({
            "star_temperature": star.get("temperature"),
            "star_radius": star.get("radius"),
            "star_mass": star.get("mass"),
        })
    return predict_habitability(to_model_row(model_data))


def create_planet(payload):
    data = validate_planet(payload)
    score = prediction_for(data)
    data["predicted_habitability"] = score
    planet_id = repositories.create_planet(data)
    return planet_id, score


def update_planet(planet_id, payload):
    data = validate_planet(payload)
    existing = repositories.get_planet(planet_id)
    # The current editor does not expose these science/provenance fields yet.
    # Preserve them when a normal edit submits only the fields visible in that form.
    for field in (
        "density", "gravity", "escape_velocity", "habitable_zone_optimistic_flag",
        "detection_method", "planet_type", "data_source",
    ):
        if field not in payload:
            data[field] = existing.get(field)
    score = prediction_for(data)
    data["predicted_habitability"] = score
    updated = repositories.update_planet(planet_id, data)
    return updated, score



request_data = PlanetRequest.model_validate(payload)