"""Input validation and application-level operations."""

from pydantic import ValidationError as PydanticValidationError

from schemas import PlanetRequest, StarRequest

import repositories
from model.feature_contract import to_model_row
from predictor import get_model_version, predict_habitability
from science import calculate_esi_values


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
    data["esi_score"] = calculate_esi_values(
        data.get("radius"), data.get("mass"), data.get("equilibrium_temp")
    )
    score = prediction_for(data)
    data["predicted_habitability"] = score
    data["model_version"] = get_model_version()
    planet_id = repositories.create_planet(data)
    return planet_id, score


def import_planet(payload):
    """Validate and score an imported catalog record before saving it."""
    data = validate_planet(payload)
    data["data_source"] = data.get("data_source") or "NASA TAP"
    data["esi_score"] = calculate_esi_values(
        data.get("radius"), data.get("mass"), data.get("equilibrium_temp")
    )
    score = prediction_for(data)
    data["predicted_habitability"] = score
    data["model_version"] = get_model_version()
    planet_id = repositories.create_planet(data)
    return planet_id, score


def update_planet(planet_id, payload):
    data = validate_planet(payload)
    existing = repositories.get_planet(planet_id)
    # A PUT can omit fields; retain those values while allowing explicit nulls.
    for field in data:
        if field not in payload:
            data[field] = existing.get(field)
    data["esi_score"] = calculate_esi_values(
        data.get("radius"), data.get("mass"), data.get("equilibrium_temp")
    )
    score = prediction_for(data)
    data["predicted_habitability"] = score
    data["model_version"] = get_model_version()
    updated = repositories.update_planet(planet_id, data)
    return updated, score
