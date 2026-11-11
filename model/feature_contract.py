"""Canonical model input order shared by training and inference."""

FEATURE_COLUMNS = [
    "esi_score",
    "habitable_zone_flag",
    "P_RADIUS",
    "P_MASS",
    "P_TEMP_EQUIL",
    "P_PERIOD",
    "P_FLUX",
    "S_TEMPERATURE",
    "S_RADIUS",
    "S_MASS",
]

FEATURE_CONTRACT_VERSION = "1"



def to_model_row(data):
    """Translate API/database names to the catalog's trained feature names."""
    return {
        "esi_score": data.get("esi_score"),
        "habitable_zone_flag": data.get("habitable_zone_flag"),
        "P_RADIUS": data.get("radius"),
        "P_MASS": data.get("mass"),
        "P_TEMP_EQUIL": data.get("equilibrium_temp"),
        "P_PERIOD": data.get("orbital_period"),
        "P_FLUX": data.get("stellar_flux"),
        "S_TEMPERATURE": data.get("star_temperature"),
        "S_RADIUS": data.get("star_radius"),
        "S_MASS": data.get("star_mass"),
    }
