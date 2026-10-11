from flask import Blueprint, request, jsonify
from db import get_db_connection
import time

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/overview', methods=['GET'])
def get_catalog_overview():
    """
    Returns aggregate stats for Mission Control HUD Cards:
    Total planets, Total stars, Habitable worlds, Avg ESI, Drift alerts, Closest candidate, Planet types.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Main counts
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM exoplanets) AS total_planets,
            (SELECT COUNT(*) FROM stars) AS total_stars,
            (SELECT COUNT(*) FROM exoplanets WHERE predicted_habitability >= 0.5) AS habitable_candidates,
            (SELECT ROUND(AVG(esi_score), 3) FROM exoplanets WHERE esi_score IS NOT NULL) AS avg_esi_score,
            (SELECT COUNT(*) FROM habitability_log WHERE is_drift_alert = 1) AS total_drift_alerts
    """)
    summary = cursor.fetchone()

    # 2. Nearest habitable candidate
    cursor.execute("""
        SELECT 
            e.planet_id, e.name AS planet_name, s.name AS star_name, 
            ROUND(s.distance_from_earth, 2) AS distance_ly,
            e.predicted_habitability, e.esi_score
        FROM exoplanets e
        JOIN stars s ON e.star_id = s.star_id
        WHERE e.predicted_habitability >= 0.5 AND s.distance_from_earth IS NOT NULL
        ORDER BY s.distance_from_earth ASC
        LIMIT 1
    """)
    nearest = cursor.fetchone()

    # 3. Planet type breakdown
    cursor.execute("""
        SELECT planet_type, COUNT(*) AS count
        FROM exoplanets
        GROUP BY planet_type
        ORDER BY count DESC
    """)
    type_distribution = cursor.fetchall()

    # 4. Habitability Score Tiers
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN predicted_habitability >= 0.70 THEN 1 ELSE 0 END) AS tier_prime_habitable,
            SUM(CASE WHEN predicted_habitability >= 0.45 AND predicted_habitability < 0.70 THEN 1 ELSE 0 END) AS tier_optimistic_habitable,
            SUM(CASE WHEN predicted_habitability >= 0.15 AND predicted_habitability < 0.45 THEN 1 ELSE 0 END) AS tier_marginal,
            SUM(CASE WHEN predicted_habitability < 0.15 THEN 1 ELSE 0 END) AS tier_hostile
        FROM exoplanets
    """)
    tiers = cursor.fetchone()

    conn.close()

    return jsonify({
        "status": "success",
        "summary": summary,
        "nearest_habitable": nearest,
        "type_distribution": type_distribution,
        "habitability_tiers": tiers
    })

@analytics_bp.route('/drift-radar', methods=['GET'])
def get_drift_radar():
    """
    Returns recent Confidence Drift alerts from v_confidence_drift_alerts.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM v_confidence_drift_alerts
        LIMIT 50
    """)
    alerts = cursor.fetchall()
    conn.close()
    return jsonify({"status": "success", "count": len(alerts), "alerts": alerts})

@analytics_bp.route('/earth-twins', methods=['GET'])
def get_earth_twins():
    """
    Returns top 25 Earth twins from v_top_earth_twins.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM v_top_earth_twins")
    twins = cursor.fetchall()
    conn.close()
    return jsonify({"status": "success", "twins": twins})

@analytics_bp.route('/audit-log', methods=['GET'])
def get_audit_log():
    """
    Returns recent DML audit logs from system_audit_trail.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM system_audit_trail
        ORDER BY performed_at DESC
        LIMIT 30
    """)
    logs = cursor.fetchall()
    conn.close()
    return jsonify({"status": "success", "logs": logs})

@analytics_bp.route('/sql-workbench', methods=['POST'])
def run_sql_workbench():
    """
    Safe DBMS workbench runner for demonstrating Stored Procedures, Views,
    and EXPLAIN query plans during presentations and viva evaluations.
    """
    data = request.json or {}
    query = data.get('query', '').strip()

    if not query:
        return jsonify({"error": "No SQL query provided"}), 400

    # Whitelist safety: only allow SELECT, CALL, EXPLAIN, SHOW, DESCRIBE
    first_word = query.split()[0].upper() if query.split() else ''
    allowed_words = ['SELECT', 'CALL', 'EXPLAIN', 'SHOW', 'DESCRIBE', 'DESC']

    if first_word not in allowed_words:
        return jsonify({
            "error": f"Security restriction: Direct '{first_word}' statements disabled in console. Use the UI CRUD forms for modifications."
        }), 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    start_time = time.time()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        exec_ms = round((time.time() - start_time) * 1000, 2)
        columns = list(rows[0].keys()) if rows else []

        conn.close()
        return jsonify({
            "status": "success",
            "query": query,
            "execution_time_ms": exec_ms,
            "row_count": len(rows),
            "columns": columns,
            "rows": rows[:100] # Cap output at 100 rows for display
        })
    except Exception as err:
        conn.close()
        return jsonify({
            "status": "error",
            "error": str(err),
            "execution_time_ms": round((time.time() - start_time) * 1000, 2)
        }), 400

# Research Bookmarks Endpoints
@analytics_bp.route('/bookmarks', methods=['GET'])
def get_bookmarks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            b.*,
            e.name AS planet_name,
            e.planet_type,
            e.predicted_habitability,
            e.esi_score,
            s.name AS star_name,
            s.distance_from_earth
        FROM research_bookmarks b
        JOIN exoplanets e ON b.planet_id = e.planet_id
        JOIN stars s ON e.star_id = s.star_id
        ORDER BY b.created_at DESC
    """)
    bookmarks = cursor.fetchall()
    conn.close()
    return jsonify({"status": "success", "bookmarks": bookmarks})

@analytics_bp.route('/bookmarks', methods=['POST'])
def add_bookmark():
    data = request.json or {}
    planet_id = data.get('planet_id')
    if not planet_id:
        return jsonify({"error": "planet_id is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO research_bookmarks (planet_id, researcher_name, notes, priority)
        VALUES (%s, %s, %s, %s)
    """, (
        planet_id,
        data.get('researcher_name', 'Mission Specialist'),
        data.get('notes', 'Flagged for priority investigation.'),
        data.get('priority', 'HIGH')
    ))
    conn.commit()
    bm_id = cursor.lastrowid
    conn.close()
    return jsonify({"status": "success", "message": "Planet pinned to research bookmarks.", "bookmark_id": bm_id}), 201

@analytics_bp.route('/bookmarks/<int:id>', methods=['DELETE'])
def remove_bookmark(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM research_bookmarks WHERE bookmark_id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Bookmark removed."})
