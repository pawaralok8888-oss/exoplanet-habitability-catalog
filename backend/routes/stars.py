from flask import Blueprint, jsonify, request

import repositories
import services
from services import ValidationError


stars_bp = Blueprint("stars", __name__)


@stars_bp.route("/", methods=["GET"])
def get_stars():
    return jsonify(repositories.list_stars())


@stars_bp.route("/<int:star_id>", methods=["GET"])
def get_star(star_id):
    star = repositories.get_star(star_id)
    if star is None:
        return jsonify({"error": "Star not found"}), 404
    return jsonify(star)


@stars_bp.route("/", methods=["POST"])
def create_star():
    try:
        star_id = repositories.create_star(services.validate_star(request.get_json(silent=True)))
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"message": "Star created", "star_id": star_id}), 201


@stars_bp.route("/<int:star_id>", methods=["PUT"])
def update_star(star_id):
    try:
        data = services.validate_star(request.get_json(silent=True))
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    if not repositories.update_star(star_id, data):
        return jsonify({"error": "Star not found"}), 404
    return jsonify({"message": "Star updated"})


@stars_bp.route("/<int:star_id>", methods=["DELETE"])
def delete_star(star_id):
    if not repositories.delete_star(star_id):
        return jsonify({"error": "Star not found"}), 404
    return jsonify({"message": "Star deleted"})
