"""Pure scientific feature calculations shared by batch and API workflows."""

import math


ESI_WEIGHTS = {
    "radius": 0.57,
    "density": 1.07,
    "escape": 0.70,
    "temperature": 5.58,
}


def _similarity(value, earth_value):
    return 1 - abs(value - earth_value) / (value + earth_value)


def calculate_esi_values(radius, mass, equilibrium_temperature):
    """Calculate the project's Earth Similarity Index; return None if incomplete."""
    try:
        radius = float(radius)
        mass = float(mass)
        equilibrium_temperature = float(equilibrium_temperature)
    except (TypeError, ValueError):
        return None

    values = (radius, mass, equilibrium_temperature)
    if not all(math.isfinite(value) and value > 0 for value in values):
        return None

    density = mass / radius**3
    escape_velocity = math.sqrt(mass / radius)
    components = {
        "radius": _similarity(radius, 1.0),
        "density": _similarity(density, 1.0),
        "escape": _similarity(escape_velocity, 1.0),
        "temperature": _similarity(equilibrium_temperature, 255.0),
    }
    total_weight = sum(ESI_WEIGHTS.values())
    product = math.prod(
        components[key] ** weight for key, weight in ESI_WEIGHTS.items()
    )
    return product ** (1 / total_weight)
