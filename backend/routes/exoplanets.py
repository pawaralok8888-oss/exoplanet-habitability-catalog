from flask import Blueprint, jsonify, request
import math

import repositories
import services
from services import ValidationError


exoplanets_bp = Blueprint("exoplanets", __name__)




@exoplanets_bp.route("/drifted", methods=["GET"])
def get_drifted_exoplanets():
    try:
        threshold = float(request.args.get("threshold", "0.15"))
    except ValueError:
        return jsonify({"error": "threshold must be a number"}), 400
    if not math.isfinite(threshold) or threshold < 0 or threshold > 1:
        return jsonify({"error": "threshold must be between 0 and 1"}), 400
    return jsonify(repositories.list_drifted_planets(threshold))


@exoplanets_bp.route("/", methods=["GET"])
def get_exoplanets():
    return jsonify(repositories.list_planets())


@exoplanets_bp.route("/search", methods=["GET"])
def search_exoplanets():
    try:
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "12"))
    except ValueError:
        return jsonify({"error": "page and per_page must be whole numbers"}), 400

    if page < 1:
        return jsonify({"error": "page must be at least 1"}), 400

    if per_page < 1 or per_page > 100:
        return jsonify({"error": "per_page must be between 1 and 100"}), 400

    search_term = request.args.get("q", "").strip()
    hz = request.args.get("hz", "all")
    score = request.args.get("score", "all")
    drift_value = request.args.get("drift_only", "false").lower()

    if len(search_term) > 100:
        return jsonify({"error": "q must be 100 characters or fewer"}), 400
    if hz not in {"all", "1", "0", "unknown"}:
        return jsonify({"error": "hz must be all, 1, 0, or unknown"}), 400
    if score not in {"all", "high", "medium", "low", "unscored"}:
        return jsonify({"error": "score must be all, high, medium, low, or unscored"}), 400
    if drift_value not in {"true", "false"}:
        return jsonify({"error": "drift_only must be true or false"}), 400

    drift_only = drift_value == "true"
    total = repositories.count_matching_planets(search_term, hz, score, drift_only)
    pages = math.ceil(total / per_page)
    items = repositories.search_planets_page(search_term, hz, score, drift_only, page, per_page)

    return jsonify({
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    })

@exoplanets_bp.route("/<int:planet_id>/drift", methods=["GET"])
def get_exoplanet_drift(planet_id):
    if repositories.get_planet(planet_id) is None:
        return jsonify({"error": "Exoplanet not found"}), 404
    return jsonify(repositories.get_drift_history(planet_id))


@exoplanets_bp.route("/", methods=["POST"])
def create_exoplanet():
    try:
        planet_id, score = services.create_planet(request.get_json(silent=True))
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify({"message": "Exoplanet created", "planet_id": planet_id,
                    "predicted_habitability": score}), 201


@exoplanets_bp.route("/<int:planet_id>", methods=["PUT"])
def update_exoplanet(planet_id):
    if repositories.get_planet(planet_id) is None:
        return jsonify({"error": "Exoplanet not found"}), 404
    try:
        updated, score = services.update_planet(planet_id, request.get_json(silent=True))
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify({"message": "Exoplanet updated", "predicted_habitability": score})


@exoplanets_bp.route("/<int:planet_id>", methods=["DELETE"])
def delete_exoplanet(planet_id):
    if not repositories.delete_planet(planet_id):
        return jsonify({"error": "Exoplanet not found"}), 404
    return jsonify({"message": "Exoplanet deleted"})
