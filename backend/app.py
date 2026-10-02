from flask import Flask
from routes.stars import stars_bp
from routes.exoplanets import exoplanets_bp
from routes.fetch import fetch_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Enable CORS for frontend

# Register Blueprints
app.register_blueprint(stars_bp, url_prefix='/api/stars')
app.register_blueprint(exoplanets_bp, url_prefix='/api/exoplanets')
app.register_blueprint(fetch_bp, url_prefix='/api')

@app.route('/')
def home():
    return "Exoplanet Habitability API is running."

if __name__ == '__main__':
    app.run(debug=True, port=5000)
