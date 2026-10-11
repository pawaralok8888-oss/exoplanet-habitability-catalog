from flask import Flask
from routes.stars import stars_bp
from routes.exoplanets import exoplanets_bp
from routes.fetch import fetch_bp
from routes.analytics import analytics_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for all frontend requests

# Register Modular REST API Blueprints
app.register_blueprint(stars_bp, url_prefix='/api/stars')
app.register_blueprint(exoplanets_bp, url_prefix='/api/exoplanets')
app.register_blueprint(fetch_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

@app.route('/')
def root_status():
    return {
        "system": "EXOPLANET HABITABILITY CATALOG // DBMS MISSION CONTROL",
        "status": "OPERATIONAL",
        "endpoints": {
            "catalog": "/api/exoplanets",
            "star_systems": "/api/stars",
            "analytics_overview": "/api/analytics/overview",
            "drift_radar": "/api/analytics/drift-radar",
            "earth_twins": "/api/analytics/earth-twins",
            "sql_workbench": "/api/analytics/sql-workbench",
            "nasa_tap_sync": "/api/fetch-new"
        }
    }

if __name__ == '__main__':
    print("=================================================================")
    print("  EXOPLANET MISSION CONTROL BACKEND API ACTIVE ON PORT 5000      ")
    print("=================================================================")
    app.run(debug=True, host='0.0.0.0', port=5000)
