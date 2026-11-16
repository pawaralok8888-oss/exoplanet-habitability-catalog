import pandas as pd
import numpy as np
from science import calculate_esi_values

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
# 1. CONSERVATIVE HABITABLE-ZONE FLAG
# ---------------------------------------------------------
# P_HABZONE_CON is the catalog's precomputed conservative-zone flag.
# S_HZ_CON_MIN/MAX are orbital-distance boundaries (AU), while P_FLUX is
# incident flux (Earth = 1); comparing those values directly mixes units.
df["habitable_zone_flag"] = pd.to_numeric(df["P_HABZONE_CON"], errors="coerce")


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
    return calculate_esi_values(
        row["P_RADIUS"], row["P_MASS"], row["P_TEMP_EQUIL"]
    )


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
