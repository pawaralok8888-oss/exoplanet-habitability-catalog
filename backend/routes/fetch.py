from flask import Blueprint, jsonify
from db import get_db_connection
import requests

fetch_bp = Blueprint('fetch', __name__)

@fetch_bp.route('/fetch-new', methods=['POST'])
def fetch_new_planets():
    # Example logic to query NASA TAP API
    # Since this is a course project, we simulate or do a basic pull
    try:
        url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+top+5+pl_name,pl_radj,pl_bmassj,pl_orbper,disc_year+from+ps&format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        inserted = 0
        for row in data:
            # basic insert logic, skip if exists
            cursor.execute("SELECT planet_id FROM exoplanets WHERE name = %s", (row.get('pl_name'),))
            if cursor.fetchone():
                continue
                
            cursor.execute("""
                INSERT INTO exoplanets (name, radius, mass, orbital_period, discovery_year)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                row.get('pl_name'),
                row.get('pl_radj'),
                row.get('pl_bmassj'),
                row.get('pl_orbper'),
                row.get('disc_year')
            ))
            inserted += 1
            
        conn.commit()
        conn.close()
        
        return jsonify({"message": f"Successfully fetched and inserted {inserted} new planets."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
