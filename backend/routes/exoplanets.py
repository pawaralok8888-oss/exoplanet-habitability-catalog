from flask import Blueprint, request, jsonify
from db import get_db_connection
import pickle
import os
import json
import numpy as np

exoplanets_bp = Blueprint('exoplanets', __name__)

# Load Machine Learning Model
model_path = os.path.join(os.path.dirname(__file__), '../../model.pkl')
try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    print("Random Forest model loaded successfully into exoplanets route.")
except Exception as e:
    model = None
    print(f"Warning: Could not load model from {model_path}: {e}")

def compute_model_score(data, star_data=None):
    """
    Computes habitability probability (0.0 to 1.0) using trained RandomForestClassifier.
    Features: [esi_score, habitable_zone_flag, P_RADIUS, P_MASS, P_TEMP_EQUIL, 
               P_PERIOD, P_FLUX, S_TEMPERATURE, S_RADIUS, S_MASS]
    """
    if not model:
        return 0.5000

    def safe_f(v, default=0.0):
        try:
            return float(v) if v is not None and not np.isnan(float(v)) else default
        except:
            return default

    # Stellar fallbacks
    s_temp = safe_f(star_data.get('temperature') if star_data else data.get('star_temperature'), 5778.0)
    s_rad = safe_f(star_data.get('radius') if star_data else data.get('star_radius'), 1.0)
    s_mass = safe_f(star_data.get('mass') if star_data else data.get('star_mass'), 1.0)

    # Estimate flux if missing using semi-major axis (AU)
    dist = safe_f(data.get('orbital_distance'), 1.0)
    s_lum = (s_rad ** 2) * ((s_temp / 5778.0) ** 4) if s_temp and s_rad else 1.0
    calc_flux = s_lum / (dist ** 2) if dist > 0 else 1.0

    features = [
        safe_f(data.get('esi_score'), 0.5),
        safe_f(data.get('habitable_zone_flag'), 0.0),
        safe_f(data.get('radius'), 1.0),
        safe_f(data.get('mass'), 1.0),
        safe_f(data.get('equilibrium_temp'), 255.0),
        safe_f(data.get('orbital_period'), 365.25),
        safe_f(data.get('stellar_flux'), calc_flux),
        s_temp,
        s_rad,
        s_mass
    ]

    try:
        prob = model.predict_proba([features])[0][1]
        return round(float(prob), 4)
    except Exception as err:
        print("Model inference error:", err)
        return 0.0

@exoplanets_bp.route('', methods=['GET'], strict_slashes=False)
@exoplanets_bp.route('/', methods=['GET'], strict_slashes=False)
def get_exoplanets():
    """
    Paginated, searchable, and filterable exoplanets endpoint.
    Query params: page, limit, search, sort, order, filter, star_id, planet_type
    """
    page = max(1, int(request.args.get('page', 1)))
    limit = min(100, max(5, int(request.args.get('limit', 20))))
    offset = (page - 1) * limit

    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'habitability').lower()
    order = request.args.get('order', 'desc').upper()
    filter_tier = request.args.get('filter', 'all').lower()
    star_id = request.args.get('star_id', None)
    planet_type = request.args.get('type', None)

    # Order validation
    if order not in ['ASC', 'DESC']:
        order = 'DESC'

    # Column mapping for sorting
    sort_column_map = {
        'habitability': 'e.predicted_habitability',
        'esi': 'e.esi_score',
        'name': 'e.name',
        'distance': 's.distance_from_earth',
        'year': 'e.discovery_year',
        'period': 'e.orbital_period',
        'radius': 'e.radius',
        'mass': 'e.mass'
    }
    sort_col = sort_column_map.get(sort_by, 'e.predicted_habitability')

    conditions = []
    params = []

    if search:
        conditions.append("(e.name LIKE %s OR s.name LIKE %s OR s.constellation LIKE %s)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    if star_id:
        conditions.append("e.star_id = %s")
        params.append(int(star_id))

    if planet_type and planet_type != 'all':
        conditions.append("e.planet_type = %s")
        params.append(planet_type)

    if filter_tier == 'habitable':
        conditions.append("e.predicted_habitability >= 0.5")
    elif filter_tier == 'optimistic':
        conditions.append("(e.predicted_habitability >= 0.35 OR e.habitable_zone_flag = 1)")
    elif filter_tier == 'earth_like':
        conditions.append("(e.esi_score >= 0.70 AND e.planet_type IN ('Terran', 'Superterran'))")
    elif filter_tier == 'extreme':
        conditions.append("(e.equilibrium_temp > 1000 OR e.equilibrium_temp < 150)")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Count total
    count_sql = f"""
    SELECT COUNT(*) AS total 
    FROM exoplanets e
    JOIN stars s ON e.star_id = s.star_id
    {where_clause}
    """
    cursor.execute(count_sql, tuple(params))
    total_count = cursor.fetchone()['total']

    # Fetch paginated rows with joined star info and latest drift info
    query_sql = f"""
    SELECT 
        e.planet_id,
        e.name,
        e.star_id,
        s.name AS star_name,
        s.spectral_type,
        s.temperature AS star_temperature,
        s.distance_from_earth AS distance_ly,
        s.constellation,
        e.planet_type,
        e.radius,
        e.mass,
        e.orbital_period,
        e.orbital_distance,
        e.equilibrium_temp,
        e.stellar_flux,
        e.esi_score,
        e.habitable_zone_flag,
        e.predicted_habitability,
        e.discovery_year,
        dm.name AS discovery_method,
        e.last_updated,
        hl.score_delta AS latest_drift_delta,
        hl.is_drift_alert AS latest_drift_alert,
        hl.notes AS latest_drift_notes
    FROM exoplanets e
    JOIN stars s ON e.star_id = s.star_id
    LEFT JOIN discovery_methods dm ON e.discovery_method_id = dm.method_id
    LEFT JOIN habitability_log hl ON hl.log_id = (
        SELECT MAX(sub_hl.log_id) FROM habitability_log sub_hl WHERE sub_hl.planet_id = e.planet_id
    )
    {where_clause}
    ORDER BY {sort_col} {order}
    LIMIT %s OFFSET %s
    """
    cursor.execute(query_sql, tuple(params + [limit, offset]))
    planets = cursor.fetchall()
    conn.close()

    total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

    return jsonify({
        "status": "success",
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "planets": planets
    })

@exoplanets_bp.route('/<int:id>', methods=['GET'])
def get_exoplanet_detail(id):
    """
    Returns complete exoplanet record with host star, parsed JSON telemetry,
    and complete drift timeline.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    planet_sql = """
    SELECT 
        e.*,
        s.name AS star_name,
        s.spectral_type,
        s.temperature AS star_temp,
        s.radius AS star_radius,
        s.mass AS star_mass,
        s.luminosity AS star_luminosity,
        s.distance_from_earth AS distance_ly,
        s.constellation,
        dm.name AS discovery_method,
        dm.description AS discovery_method_desc
    FROM exoplanets e
    JOIN stars s ON e.star_id = s.star_id
    LEFT JOIN discovery_methods dm ON e.discovery_method_id = dm.method_id
    WHERE e.planet_id = %s
    """
    cursor.execute(planet_sql, (id,))
    planet = cursor.fetchone()

    if not planet:
        conn.close()
        return jsonify({"error": "Exoplanet not found in catalog"}), 404

    # Parse telemetry_json
    if planet.get('telemetry_json'):
        try:
            if isinstance(planet['telemetry_json'], str):
                planet['telemetry_json'] = json.loads(planet['telemetry_json'])
        except:
            pass

    # Fetch drift history
    drift_sql = """
    SELECT 
        log_id,
        old_score,
        new_score,
        score_delta,
        change_type,
        is_drift_alert,
        notes,
        prediction_timestamp
    FROM habitability_log
    WHERE planet_id = %s
    ORDER BY prediction_timestamp ASC
    """
    cursor.execute(drift_sql, (id,))
    planet['drift_history'] = cursor.fetchall()

    conn.close()
    return jsonify(planet)

@exoplanets_bp.route('/<int:id>/drift', methods=['GET'])
def get_planet_drift(id):
    """
    Returns full drift history for a specific planet.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT log_id, old_score, new_score, score_delta, change_type, is_drift_alert, notes, prediction_timestamp
        FROM habitability_log
        WHERE planet_id = %s
        ORDER BY prediction_timestamp ASC
    """, (id,))
    drift_history = cursor.fetchall()
    conn.close()
    return jsonify(drift_history)

@exoplanets_bp.route('', methods=['POST'], strict_slashes=False)
@exoplanets_bp.route('/', methods=['POST'], strict_slashes=False)
def create_exoplanet():
    """
    Creates a new exoplanet. Runs live ML habitability prediction before insert.
    Triggers automatically create initial audit log record.
    """
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"error": "Planet name is required"}), 400

    star_id = data.get('star_id')
    if not star_id:
        return jsonify({"error": "Host star ID is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch star data for high-fidelity ML inference
    cursor.execute("SELECT * FROM stars WHERE star_id = %s", (star_id,))
    star_data = cursor.fetchone()
    if not star_data:
        conn.close()
        return jsonify({"error": f"Star with ID {star_id} not found"}), 404

    # Compute live ML score
    predicted_score = compute_model_score(data, star_data)

    # Auto-derive habitable zone flag if not provided
    hz_flag = data.get('habitable_zone_flag')
    if hz_flag is None:
        eq_temp = float(data.get('equilibrium_temp', 0) or 0)
        hz_flag = 1 if 180 <= eq_temp <= 310 else 0

    # Auto-derive ESI if not provided
    esi_val = data.get('esi_score')
    if esi_val is None:
        rad = float(data.get('radius', 1.0) or 1.0)
        mass = float(data.get('mass', 1.0) or 1.0)
        esi_val = round(max(0.0, 1.0 - 0.5 * abs((rad - 1) / (rad + 1)) - 0.5 * abs((mass - 1) / (mass + 1))), 4)

    # Telemetry JSON
    telemetry = {
        "mission_source": "User Catalog Submission",
        "spectroscopy": {
            "biosignature_status": "PENDING_VERIFICATION",
            "water_vapor_confidence": round(float(esi_val) * 0.8, 2),
            "spectroscopy_grade": "A" if predicted_score > 0.5 else "B"
        },
        "submitted_at": "User Manual Entry"
    }

    insert_sql = """
    INSERT INTO exoplanets (
        star_id, name, planet_type, radius, mass, orbital_period, orbital_distance,
        equilibrium_temp, stellar_flux, esi_score, habitable_zone_flag,
        predicted_habitability, discovery_year, discovery_method_id, telemetry_json
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(insert_sql, (
            star_id,
            name,
            data.get('planet_type', 'Terran'),
            data.get('radius'),
            data.get('mass'),
            data.get('orbital_period'),
            data.get('orbital_distance'),
            data.get('equilibrium_temp'),
            data.get('stellar_flux'),
            esi_val,
            int(hz_flag),
            predicted_score,
            data.get('discovery_year', 2026),
            data.get('discovery_method_id', 1),
            json.dumps(telemetry)
        ))
        conn.commit()
        planet_id = cursor.lastrowid
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Exoplanet successfully catalogued with ML Habitability Score.",
            "planet_id": planet_id,
            "predicted_habitability": predicted_score,
            "esi_score": esi_val
        }), 201

    except Exception as err:
        conn.close()
        return jsonify({"error": str(err)}), 400

@exoplanets_bp.route('/<int:id>', methods=['PUT'])
def update_exoplanet(id):
    """
    Updates an exoplanet. Re-runs ML prediction.
    The database trigger automatically detects score drift and creates an alert if delta >= 15%.
    """
    data = request.json or {}
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch existing
    cursor.execute("SELECT * FROM exoplanets WHERE planet_id = %s", (id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Planet not found"}), 404

    # Fetch star
    star_id = data.get('star_id', existing['star_id'])
    cursor.execute("SELECT * FROM stars WHERE star_id = %s", (star_id,))
    star_data = cursor.fetchone()

    # Re-run ML model
    updated_score = compute_model_score(data, star_data)

    update_sql = """
    UPDATE exoplanets SET
        star_id = %s,
        name = %s,
        planet_type = %s,
        radius = %s,
        mass = %s,
        orbital_period = %s,
        orbital_distance = %s,
        equilibrium_temp = %s,
        stellar_flux = %s,
        esi_score = %s,
        habitable_zone_flag = %s,
        predicted_habitability = %s,
        discovery_year = %s
    WHERE planet_id = %s
    """
    try:
        cursor.execute(update_sql, (
            star_id,
            data.get('name', existing['name']),
            data.get('planet_type', existing['planet_type']),
            data.get('radius', existing['radius']),
            data.get('mass', existing['mass']),
            data.get('orbital_period', existing['orbital_period']),
            data.get('orbital_distance', existing['orbital_distance']),
            data.get('equilibrium_temp', existing['equilibrium_temp']),
            data.get('stellar_flux', existing['stellar_flux']),
            data.get('esi_score', existing['esi_score']),
            data.get('habitable_zone_flag', existing['habitable_zone_flag']),
            updated_score,
            data.get('discovery_year', existing['discovery_year']),
            id
        ))
        conn.commit()

        # Check if drift trigger fired an alert
        cursor.execute("""
            SELECT * FROM habitability_log 
            WHERE planet_id = %s 
            ORDER BY prediction_timestamp DESC 
            LIMIT 1
        """, (id,))
        latest_log = cursor.fetchone()

        conn.close()

        return jsonify({
            "status": "success",
            "message": "Exoplanet telemetry updated and re-scored.",
            "predicted_habitability": updated_score,
            "drift_event": latest_log
        })

    except Exception as err:
        conn.close()
        return jsonify({"error": str(err)}), 400

@exoplanets_bp.route('/<int:id>', methods=['DELETE'])
def delete_exoplanet(id):
    """
    Deletes exoplanet. Trigger logs into system_audit_trail.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exoplanets WHERE planet_id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Planet #{id} removed from catalog."})
