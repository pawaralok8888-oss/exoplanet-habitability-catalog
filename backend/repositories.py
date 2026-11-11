"""SQL operations for the API, kept out of request handlers."""

from db import call_procedure, execute, fetch_all, fetch_one


PLANET_COLUMNS = (
    "star_id, name, radius, mass, orbital_period, orbital_distance, "
    "stellar_flux, equilibrium_temp, esi_score, habitable_zone_flag, "
    "predicted_habitability, discovery_year, density, gravity, escape_velocity, "
    "habitable_zone_optimistic_flag, detection_method, planet_type, data_source"
)


def list_planets():
    return fetch_all("SELECT * FROM exoplanets ORDER BY planet_id")


def _planet_search_filters(search_term="", hz="all", score="all", drift_only=False):
    clauses = []
    params = []

    if search_term:
        pattern = f"%{search_term}%"
        clauses.append("(p.name LIKE %s OR s.name LIKE %s)")
        params.extend((pattern, pattern))

    if hz == "1":
        clauses.append("p.habitable_zone_flag = %s")
        params.append(1)
    elif hz == "0":
        clauses.append("p.habitable_zone_flag = %s")
        params.append(0)
    elif hz == "unknown":
        clauses.append("p.habitable_zone_flag IS NULL")

    if score == "high":
        clauses.append("p.predicted_habitability >= %s")
        params.append(0.7)
    elif score == "medium":
        clauses.append("p.predicted_habitability >= %s AND p.predicted_habitability < %s")
        params.extend((0.4, 0.7))
    elif score == "low":
        clauses.append("p.predicted_habitability IS NOT NULL AND p.predicted_habitability < %s")
        params.append(0.4)
    elif score == "unscored":
        clauses.append("p.predicted_habitability IS NULL")

    if drift_only:
        clauses.append(
            "p.planet_id IN ("
            "SELECT drift_rows.planet_id FROM ("
            "SELECT planet_id, ABS(predicted_habitability - LAG(predicted_habitability) "
            "OVER (PARTITION BY planet_id ORDER BY prediction_timestamp, log_id)) AS score_delta "
            "FROM habitability_log WHERE predicted_habitability IS NOT NULL"
            ") AS drift_rows WHERE drift_rows.score_delta > %s)"
        )
        params.append(0.15)

    where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_clause, params


def count_matching_planets(search_term="", hz="all", score="all", drift_only=False):
    where_clause, params = _planet_search_filters(search_term, hz, score, drift_only)
    sql = (
        "SELECT COUNT(*) AS total "
        "FROM exoplanets AS p "
        "LEFT JOIN stars AS s ON p.star_id = s.star_id"
        f"{where_clause}"
    )
    result = fetch_one(sql, tuple(params))
    return int(result["total"])


def search_planets_page(search_term, hz, score, drift_only, page, per_page):
    where_clause, params = _planet_search_filters(search_term, hz, score, drift_only)
    offset = (page - 1) * per_page
    sql = (
        "SELECT p.* "
        "FROM exoplanets AS p "
        "LEFT JOIN stars AS s ON p.star_id = s.star_id"
        f"{where_clause} "
        "ORDER BY (p.predicted_habitability IS NULL), "
        "p.predicted_habitability DESC, p.planet_id ASC "
        "LIMIT %s OFFSET %s"
    )
    return fetch_all(sql, tuple(params) + (per_page, offset))

def get_planet(planet_id):
    return fetch_one("SELECT * FROM exoplanets WHERE planet_id = %s", (planet_id,))


def get_drift_history(planet_id):
    return call_procedure("CALL GetDriftHistory(%s)", (planet_id,))


def list_drifted_planets(threshold):
    sql = (
        "SELECT DISTINCT planet_id FROM ("
        "SELECT planet_id, predicted_habitability, LAG(predicted_habitability) OVER ("
        "PARTITION BY planet_id ORDER BY prediction_timestamp, log_id) AS previous_score "
        "FROM habitability_log WHERE predicted_habitability IS NOT NULL"
        ") AS history WHERE previous_score IS NOT NULL "
        "AND ABS(predicted_habitability - previous_score) > %s"
    )
    return fetch_all(sql, (threshold,))


def create_planet(data):
    sql = f"INSERT INTO exoplanets ({PLANET_COLUMNS}) VALUES ({', '.join(['%s'] * len(PLANET_COLUMNS.split(', ')))})"
    _, planet_id = execute(sql, tuple(data[column] for column in PLANET_COLUMNS.split(", ")))
    return planet_id

def update_planet(planet_id, data):
    columns = PLANET_COLUMNS.split(", ")
    assignments = ", ".join(f"{column} = %s" for column in columns)
    count, _ = execute(
        f"UPDATE exoplanets SET {assignments} WHERE planet_id = %s",
        tuple(data[column] for column in columns) + (planet_id,),
    )
    return count > 0


def delete_planet(planet_id):
    count, _ = execute("DELETE FROM exoplanets WHERE planet_id = %s", (planet_id,))
    return count > 0


def list_stars():
    return fetch_all("SELECT * FROM stars ORDER BY star_id")


def get_star(star_id):
    return fetch_one("SELECT * FROM stars WHERE star_id = %s", (star_id,))


def create_star(data):
    _, star_id = execute(
        "INSERT INTO stars (name, temperature, radius, mass, distance_from_earth, "
        "stellar_type, age, luminosity, hz_conservative_inner_au, hz_conservative_outer_au) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (data["name"], data.get("temperature"), data.get("radius"),
         data.get("mass"), data.get("distance_from_earth"), data.get("stellar_type"),
         data.get("age"), data.get("luminosity"), data.get("hz_conservative_inner_au"),
         data.get("hz_conservative_outer_au")),
    )
    return star_id


def update_star(star_id, data):
    count, _ = execute(
        "UPDATE stars SET name=%s, temperature=%s, radius=%s, mass=%s, "
        "distance_from_earth=%s, stellar_type=%s, age=%s, luminosity=%s, "
        "hz_conservative_inner_au=%s, hz_conservative_outer_au=%s WHERE star_id=%s",
        (data["name"], data.get("temperature"), data.get("radius"),
         data.get("mass"), data.get("distance_from_earth"), data.get("stellar_type"),
         data.get("age"), data.get("luminosity"), data.get("hz_conservative_inner_au"),
         data.get("hz_conservative_outer_au"), star_id),
    )
    return count > 0


def delete_star(star_id):
    count, _ = execute("DELETE FROM stars WHERE star_id = %s", (star_id,))
    return count > 0


def find_planet_by_name(name):
    return fetch_one("SELECT planet_id FROM exoplanets WHERE name = %s", (name,))


def import_planet(data):
    """Insert a NASA catalog record; missing measurements remain NULL."""
    _, planet_id = execute(
        "INSERT INTO exoplanets (name, radius, mass, orbital_period, orbital_distance, "
        "stellar_flux, equilibrium_temp, discovery_year, detection_method, data_source) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'NASA TAP')",
        (data.get("name"), data.get("radius"), data.get("mass"),
         data.get("orbital_period"), data.get("orbital_distance"), data.get("stellar_flux"),
         data.get("equilibrium_temp"), data.get("discovery_year"), data.get("detection_method")),
    )
    return planet_id
