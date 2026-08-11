import pandas as pd
import numpy as np

# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------

INPUT_FILE = "data/raw/phl_exoplanet_catalog_2019_cleaned.csv"
OUTPUT_FILE = "data/processed/exoplanets_features.csv"


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

df = pd.read_csv(INPUT_FILE)


# ---------------------------------------------------------
# Create output directory
# ---------------------------------------------------------

import os
os.makedirs("data/processed", exist_ok=True)


# ---------------------------------------------------------
# 1. HABITABLE ZONE FLAG
# ---------------------------------------------------------
# A planet is considered to be in the conservative
# habitable zone when its incident stellar flux lies
# between the conservative HZ minimum and maximum.

def calculate_habitable_zone(row):

    flux = row["P_FLUX"]
    hz_min = row["S_HZ_CON_MIN"]
    hz_max = row["S_HZ_CON_MAX"]

    if pd.isna(flux) or pd.isna(hz_min) or pd.isna(hz_max):
        return np.nan

    if hz_min <= flux <= hz_max:
        return 1

    return 0


df["habitable_zone_flag"] = df.apply(
    calculate_habitable_zone,
    axis=1
)


# ---------------------------------------------------------
# 2. EARTH SIMILARITY INDEX (ESI)
# ---------------------------------------------------------
# ESI compares a planet with Earth using:
# - radius
# - density
# - escape velocity
# - equilibrium temperature
#
# Earth values are normalized to 1.
#
# The commonly used weighting exponents are:
# radius      = 0.57
# density     = 1.07
# escape vel. = 0.70
# temperature = 5.58


def similarity(value, earth_value):
    """
    Calculate similarity between a planetary value
    and the corresponding Earth value.
    """
    return 1 - abs(value - earth_value) / (value + earth_value)


def calculate_esi(row):

    radius = row["P_RADIUS"]
    mass = row["P_MASS"]
    temperature = row["P_TEMP_EQUIL"]

    if pd.isna(radius) or pd.isna(mass) or pd.isna(temperature):
        return np.nan

    # Earth-normalized values
    earth_radius = 1.0
    earth_mass = 1.0
    earth_temperature = 255.0

    # Planet density relative to Earth.
    # Density is proportional to mass / radius^3.
    density = mass / (radius ** 3)
    earth_density = 1.0

    # Escape velocity relative to Earth.
    # Escape velocity is proportional to sqrt(M / R).
    escape_velocity = np.sqrt(mass / radius)
    earth_escape_velocity = 1.0

    # Individual similarity values
    radius_similarity = similarity(
        radius,
        earth_radius
    )

    density_similarity = similarity(
        density,
        earth_density
    )

    escape_similarity = similarity(
        escape_velocity,
        earth_escape_velocity
    )

    temperature_similarity = similarity(
        temperature,
        earth_temperature
    )

    # Weighted geometric mean
    weights = {
        "radius": 0.57,
        "density": 1.07,
        "escape": 0.70,
        "temperature": 5.58
    }

    total_weight = sum(weights.values())

    esi = (
        radius_similarity ** weights["radius"]
        * density_similarity ** weights["density"]
        * escape_similarity ** weights["escape"]
        * temperature_similarity ** weights["temperature"]
    ) ** (1 / total_weight)

    return esi


df["esi_score"] = df.apply(
    calculate_esi,
    axis=1
)


# ---------------------------------------------------------
# Save feature-engineered dataset
# ---------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# Report
# ---------------------------------------------------------

print("Feature engineering complete!")
print()
print(f"Input file:  {INPUT_FILE}")
print(f"Output file: {OUTPUT_FILE}")
print()
print("New features:")
print(" - habitable_zone_flag")
print(" - esi_score")
print()
print("Rows processed:", len(df))
print("Habitability-zone values:", df["habitable_zone_flag"].notna().sum())
print("ESI values:", df["esi_score"].notna().sum())