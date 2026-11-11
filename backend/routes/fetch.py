from flask import Blueprint, jsonify
import requests

import repositories


fetch_bp = Blueprint("fetch", __name__)
NASA_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
NASA_QUERY = "select top 5 pl_name,pl_rade,pl_bmasse,pl_orbper,pl_orbsmax,pl_insol,pl_eqt,disc_year from ps"


@fetch_bp.route("/fetch-new", methods=["POST"])
def fetch_new_planets():
    try:
        response = requests.get(
            NASA_TAP_URL,
            params={"query": NASA_QUERY, "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        records = response.json()
        inserted = 0
        for row in records:
            name = row.get("pl_name")
            if not name or repositories.find_planet_by_name(name):
                continue
            repositories.import_planet({
                "name": name,
                "radius": row.get("pl_rade"),
                "mass": row.get("pl_bmasse"),
                "orbital_period": row.get("pl_orbper"),
                "orbital_distance": row.get("pl_orbsmax"),
                "stellar_flux": row.get("pl_insol"),
                "equilibrium_temp": row.get("pl_eqt"),
                "discovery_year": row.get("disc_year"),
            })
            inserted += 1
        return jsonify({"message": f"Successfully fetched and inserted {inserted} new planets."})
    except (requests.RequestException, ValueError) as exc:
        return jsonify({"error": f"NASA data could not be fetched: {exc}"}), 502
