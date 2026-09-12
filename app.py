from flask import Flask, jsonify
from database import db, init_db
from models import Organization
from routes.bins import bins_bp
from routes.detections import detections_bp
from routes.ewaste import ewaste_bp
from routes.agencies import agencies_bp
from routes.sensors import sensors_bp
from routes.alerts import alerts_bp
from routes.agent import agent_bp

def create_app():
    app = Flask(__name__)
    init_db(app)

    app.register_blueprint(bins_bp)
    app.register_blueprint(detections_bp)
    app.register_blueprint(ewaste_bp)
    app.register_blueprint(agencies_bp)
    app.register_blueprint(sensors_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(agent_bp)

    @app.get("/")
    def home():
        return jsonify({
            "name": "EcoTrace Backend",
            "status": "running"
        })

    @app.get("/health")
    def health():
        return jsonify({
            "status": "healthy"
        })

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )