import pandas as pd
import mysql.connector
import os
import sys

def load_data():
    csv_path = '../data/processed/exoplanets_features.csv'
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        sys.exit(1)

    print("Loading exoplanet features CSV...")
    df = pd.read_csv(csv_path)

    # Database connection
    # Modify credentials as needed or use environment variables
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_name = os.environ.get('DB_NAME', 'exoplanets_db')

    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        print("Please ensure MySQL is running and credentials are correct.")
        sys.exit(1)

    print("Connected to MySQL. Inserting data...")

    # We will insert dummy stars to satisfy the foreign key constraint
    # Or set star_id to NULL. For simplicity, let's just insert one dummy star
    # and link all planets to it if we don't have real star data in this CSV.
    # We can check if 'S_NAME' exists in the dataframe, but let's just create a generic one.
    
    cursor.execute("INSERT INTO stars (name, temperature, radius, mass, distance_from_earth) VALUES ('Generic Star', 5000, 1.0, 1.0, 100)")
    star_id = cursor.lastrowid
    
    # Process dataframe and insert
    # Mapping CSV columns to DB columns. (P_NAME -> name, P_RADIUS -> radius, etc.)
    
    insert_query = """
    INSERT INTO exoplanets 
    (star_id, name, radius, mass, orbital_period, equilibrium_temp, esi_score, habitable_zone_flag, predicted_habitability, discovery_year)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    count = 0
    for _, row in df.iterrows():
        # Handle potential NaNs
        def get_val(col_name):
            val = row.get(col_name)
            if pd.isna(val):
                return None
            return float(val) if not isinstance(val, str) else val

        name = row.get('P_NAME', f'Planet_{count}')
        if pd.isna(name):
            name = f'Planet_{count}'
            
        radius = get_val('P_RADIUS')
        mass = get_val('P_MASS')
        period = get_val('P_PERIOD')
        temp = get_val('P_TEMP_EQUIL')
        esi = get_val('esi_score')
        hz_flag = row.get('habitable_zone_flag', 0)
        
        # We assume predicted_habitability might be computed later, or we can leave it NULL to let the backend score it.
        # But if we have predictions we could put them here. We leave it NULL.
        
        values = (
            star_id,
            name,
            radius,
            mass,
            period,
            temp,
            esi,
            int(hz_flag) if not pd.isna(hz_flag) else 0,
            None,
            None # discovery_year
        )
        
        try:
            cursor.execute(insert_query, values)
            count += 1
        except Exception as e:
            print(f"Error inserting {name}: {e}")
            
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Successfully loaded {count} exoplanets into the database.")

if __name__ == '__main__':
    load_data()
