from flask import Blueprint, request, jsonify
from db import get_db_connection
import pickle
import os
import numpy as np

exoplanets_bp = Blueprint('exoplanets', __name__)

# Load model
model_path = os.path.join(os.path.dirname(__file__), '../../model.pkl')
try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
except Exception as e:
    model = None
    print(f"Warning: Could not load model from {model_path}. Predict will fail.")

def get_prediction(data):
    if not model:
        return 0.0
    # Expected features: [esi_score, habitable_zone_flag, P_RADIUS, P_MASS, P_TEMP_EQUIL, P_PERIOD, P_FLUX, S_TEMPERATURE, S_RADIUS, S_MASS]
    # For a real implementation we would fetch star details from DB, but we do simple imputation here if missing.
    
    def safe_float(val, default=0.0):
        try:
            return float(val) if val is not None else default
        except:
            return default

    features = [
        safe_float(data.get('esi_score'), 0.5),
        safe_float(data.get('habitable_zone_flag'), 0.0),
        safe_float(data.get('radius'), 1.0),
        safe_float(data.get('mass'), 1.0),
        safe_float(data.get('equilibrium_temp'), 250),
        safe_float(data.get('orbital_period'), 365),
        safe_float(data.get('orbital_distance', 1.0)), # Proxy for P_FLUX
        safe_float(data.get('star_temperature'), 5000),
        safe_float(data.get('star_radius'), 1.0),
        safe_float(data.get('star_mass'), 1.0)
    ]
    
    try:
        # predict_proba returns [[prob_class_0, prob_class_1]]
        prob = model.predict_proba([features])[0][1]
        return float(prob)
    except Exception as e:
        print("Prediction error:", e)
        return 0.0

@exoplanets_bp.route('/', methods=['GET'])
def get_exoplanets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Get basic list
    cursor.execute("SELECT * FROM exoplanets")
    planets = cursor.fetchall()
    conn.close()
    return jsonify(planets)

@exoplanets_bp.route('/<int:id>', methods=['GET'])
def get_exoplanet(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM exoplanets WHERE planet_id = %s", (id,))
    planet = cursor.fetchone()
    if planet:
        # Fetch drift history
        cursor.execute("CALL GetDriftHistory(%s)", (id,))
        # The stored procedure returns a result set
        drift_history = cursor.fetchall()
        planet['drift_history'] = drift_history
        conn.close()
        return jsonify(planet)
    conn.close()
    return jsonify({"error": "Exoplanet not found"}), 404

@exoplanets_bp.route('/<int:id>/drift', methods=['GET'])
def get_exoplanet_drift(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("CALL GetDriftHistory(%s)", (id,))
    drift_history = cursor.fetchall()
    conn.close()
    return jsonify(drift_history)

@exoplanets_bp.route('/', methods=['POST'])
def create_exoplanet():
    data = request.json
    score = get_prediction(data)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO exoplanets 
        (star_id, name, radius, mass, orbital_period, orbital_distance, equilibrium_temp, esi_score, habitable_zone_flag, predicted_habitability, discovery_year)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get('star_id'), data.get('name'), data.get('radius'), data.get('mass'),
        data.get('orbital_period'), data.get('orbital_distance'), data.get('equilibrium_temp'),
        data.get('esi_score'), data.get('habitable_zone_flag'), score, data.get('discovery_year')
    ))
    conn.commit()
    planet_id = cursor.lastrowid
    conn.close()
    
    return jsonify({"message": "Exoplanet created", "planet_id": planet_id, "predicted_habitability": score}), 201

@exoplanets_bp.route('/<int:id>', methods=['PUT'])
def update_exoplanet(id):
    data = request.json
    score = get_prediction(data)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE exoplanets 
        SET star_id=%s, name=%s, radius=%s, mass=%s, orbital_period=%s, orbital_distance=%s, 
            equilibrium_temp=%s, esi_score=%s, habitable_zone_flag=%s, predicted_habitability=%s, discovery_year=%s
        WHERE planet_id = %s
    """, (
        data.get('star_id'), data.get('name'), data.get('radius'), data.get('mass'),
        data.get('orbital_period'), data.get('orbital_distance'), data.get('equilibrium_temp'),
        data.get('esi_score'), data.get('habitable_zone_flag'), score, data.get('discovery_year'),
        id
    ))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Exoplanet updated", "predicted_habitability": score})

@exoplanets_bp.route('/<int:id>', methods=['DELETE'])
def delete_exoplanet(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exoplanets WHERE planet_id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Exoplanet deleted"})
