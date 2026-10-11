from flask import Blueprint, request, jsonify
from db import get_db_connection
import math

stars_bp = Blueprint('stars', __name__)

@stars_bp.route('', methods=['GET'], strict_slashes=False)
@stars_bp.route('/', methods=['GET'], strict_slashes=False)
def get_stars():
    """
    Paginated, searchable star systems list using v_star_systems_summary.
    Query params: page, limit, search, sort, order, min_planets
    """
    page = max(1, int(request.args.get('page', 1)))
    limit = min(100, max(5, int(request.args.get('limit', 24))))
    offset = (page - 1) * limit

    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'planets').lower()
    order = request.args.get('order', 'desc').upper()
    min_planets = int(request.args.get('min_planets', 0))

    if order not in ['ASC', 'DESC']:
        order = 'DESC'

    sort_map = {
        'planets': 'total_planets',
        'habitable': 'habitable_planets',
        'distance': 'distance_from_earth',
        'name': 'star_name',
        'temp': 'star_temp'
    }
    sort_col = sort_map.get(sort_by, 'total_planets')

    conditions = []
    params = []

    if search:
        conditions.append("(star_name LIKE %s OR constellation LIKE %s)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard])

    if min_planets > 0:
        conditions.append("total_planets >= %s")
        params.append(min_planets)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Count total
    count_sql = f"SELECT COUNT(*) AS total FROM v_star_systems_summary {where_clause}"
    cursor.execute(count_sql, tuple(params))
    total_count = cursor.fetchone()['total']

    # Fetch paginated stars
    query_sql = f"""
    SELECT * FROM v_star_systems_summary
    {where_clause}
    ORDER BY {sort_col} {order}
    LIMIT %s OFFSET %s
    """
    cursor.execute(query_sql, tuple(params + [limit, offset]))
    stars = cursor.fetchall()
    conn.close()

    total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

    return jsonify({
        "status": "success",
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "stars": stars
    })

@stars_bp.route('/<int:id>', methods=['GET'])
def get_star_detail(id):
    """
    Returns full star system details: host star physical properties,
    all orbiting planets, and calculated Kopparapu Habitable Zone boundaries in AU.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM stars WHERE star_id = %s", (id,))
    star = cursor.fetchone()

    if not star:
        conn.close()
        return jsonify({"error": "Star not found"}), 404

    # Fetch orbiting planets
    cursor.execute("""
        SELECT 
            planet_id, name, planet_type, radius, mass, 
            orbital_period, orbital_distance, equilibrium_temp, 
            stellar_flux, esi_score, habitable_zone_flag, predicted_habitability,
            discovery_year
        FROM exoplanets
        WHERE star_id = %s
        ORDER BY orbital_distance ASC, orbital_period ASC
    """, (id,))
    planets = cursor.fetchall()
    conn.close()

    # Calculate Habitable Zone Boundaries (Kopparapu et al. simplified)
    # Luminosity L = (R/R_sun)^2 * (T/T_sun)^4
    lum = float(star.get('luminosity') or 1.0)
    if lum <= 0:
        lum = 1.0

    hz_inner_au = round(math.sqrt(lum / 1.1), 4)  # Runaway greenhouse boundary
    hz_outer_au = round(math.sqrt(lum / 0.53), 4) # Maximum greenhouse boundary

    star['orbiting_planets'] = planets
    star['habitable_zone'] = {
        "inner_boundary_au": hz_inner_au,
        "outer_boundary_au": hz_outer_au,
        "unit": "Astronomical Units (AU)"
    }

    return jsonify(star)

@stars_bp.route('', methods=['POST'], strict_slashes=False)
@stars_bp.route('/', methods=['POST'], strict_slashes=False)
def create_star():
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"error": "Star name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stars (name, spectral_type, temperature, radius, mass, luminosity, distance_from_earth, constellation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        name,
        data.get('spectral_type', 'G2 V'),
        data.get('temperature', 5778.0),
        data.get('radius', 1.0),
        data.get('mass', 1.0),
        data.get('luminosity', 1.0),
        data.get('distance_from_earth', 10.0),
        data.get('constellation', 'Solar Neighborhood')
    ))
    conn.commit()
    star_id = cursor.lastrowid
    conn.close()
    return jsonify({"status": "success", "message": "Host star catalogued.", "star_id": star_id}), 201

@stars_bp.route('/<int:id>', methods=['PUT'])
def update_star(id):
    data = request.json or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE stars SET 
            name = %s, spectral_type = %s, temperature = %s, radius = %s, 
            mass = %s, luminosity = %s, distance_from_earth = %s, constellation = %s
        WHERE star_id = %s
    """, (
        data.get('name'), data.get('spectral_type'), data.get('temperature'),
        data.get('radius'), data.get('mass'), data.get('luminosity'),
        data.get('distance_from_earth'), data.get('constellation'), id
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Star updated."})

@stars_bp.route('/<int:id>', methods=['DELETE'])
def delete_star(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stars WHERE star_id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Star deleted."})
