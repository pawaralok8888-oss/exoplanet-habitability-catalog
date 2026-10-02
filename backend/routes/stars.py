from flask import Blueprint, request, jsonify
from db import get_db_connection

stars_bp = Blueprint('stars', __name__)

@stars_bp.route('/', methods=['GET'])
def get_stars():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM stars")
    stars = cursor.fetchall()
    conn.close()
    return jsonify(stars)

@stars_bp.route('/<int:id>', methods=['GET'])
def get_star(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM stars WHERE star_id = %s", (id,))
    star = cursor.fetchone()
    conn.close()
    if star:
        return jsonify(star)
    return jsonify({"error": "Star not found"}), 404

@stars_bp.route('/', methods=['POST'])
def create_star():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stars (name, temperature, radius, mass, distance_from_earth)
        VALUES (%s, %s, %s, %s, %s)
    """, (data.get('name'), data.get('temperature'), data.get('radius'), data.get('mass'), data.get('distance_from_earth')))
    conn.commit()
    star_id = cursor.lastrowid
    conn.close()
    return jsonify({"message": "Star created", "star_id": star_id}), 201

@stars_bp.route('/<int:id>', methods=['PUT'])
def update_star(id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE stars SET name=%s, temperature=%s, radius=%s, mass=%s, distance_from_earth=%s
        WHERE star_id = %s
    """, (data.get('name'), data.get('temperature'), data.get('radius'), data.get('mass'), data.get('distance_from_earth'), id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Star updated"})

@stars_bp.route('/<int:id>', methods=['DELETE'])
def delete_star(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stars WHERE star_id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Star deleted"})
