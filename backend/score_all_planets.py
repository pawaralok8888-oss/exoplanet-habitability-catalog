from db import get_db_connection
import pickle
import os

print("Loading model...")
model_path = os.path.join(os.path.dirname(__file__), '../model.pkl')
with open(model_path, 'rb') as f:
    model = pickle.load(f)

def safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except:
        return default

print("Connecting to database...")
conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

print("Fetching unscored planets...")
cursor.execute("SELECT * FROM exoplanets WHERE predicted_habitability IS NULL")
planets = cursor.fetchall()

print(f"Found {len(planets)} planets to score. Scoring...")
update_cursor = conn.cursor()
count = 0
for data in planets:
    features = [
        safe_float(data.get('esi_score'), 0.5),
        safe_float(data.get('habitable_zone_flag'), 0.0),
        safe_float(data.get('radius'), 1.0),
        safe_float(data.get('mass'), 1.0),
        safe_float(data.get('equilibrium_temp'), 250),
        safe_float(data.get('orbital_period'), 365),
        safe_float(data.get('orbital_distance', 1.0)),
        5000.0, # star_temperature (default proxy)
        1.0,    # star_radius (default proxy)
        1.0     # star_mass (default proxy)
    ]
    
    # Predict probability of being habitable (class 1)
    prob = float(model.predict_proba([features])[0][1])
    
    update_cursor.execute(
        "UPDATE exoplanets SET predicted_habitability = %s WHERE planet_id = %s", 
        (prob, data['planet_id'])
    )
    count += 1
    if count % 500 == 0:
        print(f"Scored {count} planets...")

conn.commit()
conn.close()
print(f"Done! Successfully scored and updated {count} planets in the database.")
