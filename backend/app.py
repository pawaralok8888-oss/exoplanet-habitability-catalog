import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask
from routes.stars import stars_bp
from routes.exoplanets import exoplanets_bp
from routes.fetch import fetch_bp
from flask_cors import CORS

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/.*": {
            "origins": [
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ]
        }
    },
)

# Register Blueprints
app.register_blueprint(stars_bp, url_prefix='/api/stars')
app.register_blueprint(exoplanets_bp, url_prefix='/api/exoplanets')
app.register_blueprint(fetch_bp, url_prefix='/api')

@app.route('/')
def home():
    return "Exoplanet Habitability API is running."

if __name__ == '__main__':
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5000)
