import pandas as pd
import mysql.connector
import os
import sys
import pickle
from pathlib import Path

def load_data():
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    if env_path.is_file():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and value and key not in os.environ:
                os.environ[key] = value

    csv_path = project_root / 'data' / 'processed' / 'exoplanets_features.csv'
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        sys.exit(1)

    print("Loading exoplanet features CSV...")
    df = pd.read_csv(csv_path)
    sys.path.insert(0, str(project_root))
    from model.feature_contract import FEATURE_COLUMNS

    model_path = project_root / "model.pkl"
    with model_path.open("rb") as model_file:
        model = pickle.load(model_file)
    predictions = model.predict_proba(df[FEATURE_COLUMNS])[:, 1]

    # Database connection
    # Modify credentials as needed or use environment variables
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_name = os.environ.get('DB_NAME', 'exoplanets_db')

    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        print("Please ensure MySQL is running and credentials are correct.")
        sys.exit(1)

    cursor = conn.cursor()

    print("Connected to MySQL. Inserting data...")

    # Process dataframe and insert
    # Store each actual host star once instead of linking every planet to a dummy.

    insert_query = """
    INSERT INTO exoplanets
    (star_id, name, radius, mass, orbital_period, orbital_distance, stellar_flux, equilibrium_temp, esi_score, habitable_zone_flag, predicted_habitability, discovery_year, density, gravity, escape_velocity, habitable_zone_optimistic_flag, detection_method, planet_type, data_source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    inserted = 0
    updated = 0
    planet_columns = [
        "star_id", "name", "radius", "mass", "orbital_period", "orbital_distance",
        "stellar_flux", "equilibrium_temp", "esi_score", "habitable_zone_flag",
        "predicted_habitability", "discovery_year", "density", "gravity", "escape_velocity",
        "habitable_zone_optimistic_flag", "detection_method", "planet_type", "data_source",
    ]
    update_query = "UPDATE exoplanets SET " + ", ".join(
        f"{column}=%s" for column in planet_columns if column != "name"
    ) + " WHERE planet_id=%s"
    for row_index, (_, row) in enumerate(df.iterrows()):
        # Handle potential NaNs
        def get_val(col_name):
            val = row.get(col_name)
            if pd.isna(val):
                return None
            if isinstance(val, str):
                return val
            numeric_value = float(val)
            # The PHL export encodes some missing stellar ages as a very large
            # negative integer. Physical catalog inputs in these columns cannot
            # be negative, so store those sentinels as SQL NULL.
            if col_name.startswith(("P_", "S_", "esi_")) and numeric_value < 0:
                return None
            return numeric_value

        def get_text(col_name):
            val = row.get(col_name)
            return None if pd.isna(val) else str(val)

        star_name = row.get('S_NAME')
        star_id = None
        if isinstance(star_name, str) and star_name.strip():
            cursor.execute("SELECT star_id FROM stars WHERE name = %s", (star_name.strip(),))
            existing_star = cursor.fetchone()
            if existing_star:
                star_id = existing_star[0]
                cursor.execute(
                    "UPDATE stars SET temperature=%s, radius=%s, mass=%s, distance_from_earth=%s, stellar_type=%s, age=%s, luminosity=%s, hz_conservative_inner_au=%s, hz_conservative_outer_au=%s WHERE star_id=%s",
                    (get_val('S_TEMPERATURE'), get_val('S_RADIUS'), get_val('S_MASS'),
                     get_val('S_DISTANCE'), get_text('S_TYPE'), get_val('S_AGE'),
                     get_val('S_LUMINOSITY'), get_val('S_HZ_CON_MIN'),
                     get_val('S_HZ_CON_MAX'), star_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO stars (name, temperature, radius, mass, distance_from_earth, stellar_type, age, luminosity, hz_conservative_inner_au, hz_conservative_outer_au) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (star_name.strip(), get_val('S_TEMPERATURE'), get_val('S_RADIUS'),
                     get_val('S_MASS'), get_val('S_DISTANCE'), get_text('S_TYPE'),
                     get_val('S_AGE'), get_val('S_LUMINOSITY'), get_val('S_HZ_CON_MIN'),
                     get_val('S_HZ_CON_MAX')),
                )
                star_id = cursor.lastrowid

        name = row.get('P_NAME', f'Planet_{row_index}')
        if pd.isna(name):
            name = f'Planet_{count}'

        radius = get_val('P_RADIUS')
        mass = get_val('P_MASS')
        period = get_val('P_PERIOD')
        orbital_distance = get_val('P_SEMI_MAJOR_AXIS')
        stellar_flux = get_val('P_FLUX')
        temp = get_val('P_TEMP_EQUIL')
        esi = get_val('esi_score')
        hz_flag = row.get('habitable_zone_flag')

        values = (
            star_id,
            name,
            radius,
            mass,
            period,
            orbital_distance,
            stellar_flux,
            temp,
            esi,
            int(hz_flag) if not pd.isna(hz_flag) else None,
            float(predictions[row_index]),
            get_val('P_YEAR'),
            get_val('P_DENSITY'), get_val('P_GRAVITY'), get_val('P_ESCAPE'),
            int(row.get('P_HABZONE_OPT')) if not pd.isna(row.get('P_HABZONE_OPT')) else None,
            get_text('P_DETECTION'), get_text('P_TYPE'), 'PHL Exoplanet Catalog 2019'
        )

        try:
            cursor.execute("SELECT planet_id FROM exoplanets WHERE name = %s ORDER BY planet_id LIMIT 1", (name,))
            existing_planet = cursor.fetchone()
            if existing_planet:
                update_values = tuple(value for column, value in zip(planet_columns, values) if column != "name")
                cursor.execute(update_query, update_values + (existing_planet[0],))
                updated += 1
            else:
                cursor.execute(insert_query, values)
                inserted += 1
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            print(f"Import stopped at CSV row {row_index + 2} ({name}); transaction rolled back: {e}")
            raise

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Import complete: {inserted} inserted, {updated} refreshed, {len(df) - inserted - updated} rows failed.")

if __name__ == '__main__':
    load_data()
