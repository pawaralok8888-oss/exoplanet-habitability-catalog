from flask import Blueprint, jsonify
import requests

import repositories
import services
from services import ValidationError


fetch_bp = Blueprint("fetch", __name__)
NASA_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
NASA_QUERY = "select top 5 pl_name,pl_rade,pl_bmasse,pl_orbper,pl_orbsmax,pl_insol,pl_eqt,disc_year,disc_method from ps"


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
        if not isinstance(records, list):
            return jsonify({"error": "NASA TAP returned an unexpected response format."}), 502
        inserted = 0
        skipped_existing = 0
        rejected = 0
        for row in records:
            if not isinstance(row, dict):
                rejected += 1
                continue
            name = row.get("pl_name")
            if not name:
                rejected += 1
                continue
            if repositories.find_planet_by_name(name):
                skipped_existing += 1
                continue
            try:
                services.import_planet({
                    "name": name,
                    "radius": row.get("pl_rade"),
                    "mass": row.get("pl_bmasse"),
                    "orbital_period": row.get("pl_orbper"),
                    "orbital_distance": row.get("pl_orbsmax"),
                    "stellar_flux": row.get("pl_insol"),
                    "equilibrium_temp": row.get("pl_eqt"),
                    "discovery_year": row.get("disc_year"),
                    "detection_method": row.get("disc_method"),
                    "data_source": "NASA TAP",
                })
            except ValidationError:
                rejected += 1
                continue
            inserted += 1
        return jsonify({
            "message": f"NASA TAP returned {len(records)} records; {inserted} imported.",
            "inserted": inserted,
            "skipped_existing": skipped_existing,
            "rejected": rejected,
        })
    except (requests.RequestException, ValueError) as exc:
        return jsonify({"error": f"NASA data could not be fetched: {exc}"}), 502
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
