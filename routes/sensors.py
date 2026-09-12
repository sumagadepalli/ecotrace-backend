from flask import Blueprint, request, jsonify
from database import db
from models import SmartBin, SensorReading
from datetime import datetime, timezone

sensors_bp = Blueprint("sensors", __name__, url_prefix="/api/v1/sensors")


@sensors_bp.route("/readings", methods=["POST"])
def add_sensor_reading():
    data = request.get_json() or {}

    required = ["bin_id", "compartment"]

    for field in required:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    bin_obj = SmartBin.query.get(data["bin_id"])

    if not bin_obj:
        return jsonify({
            "error": "Bin not found"
        }), 404

    reading = SensorReading(
        bin_id=data["bin_id"],
        compartment=data["compartment"],
        recorded_at=datetime.now(timezone.utc),
        fill_percentage=data.get("fill_percentage"),
        temperature_celsius=data.get("temperature_celsius"),
        humidity_percentage=data.get("humidity_percentage"),
        gas_index=data.get("gas_index"),
        raw_sensor_payload=data.get("raw_sensor_payload")
    )

    db.session.add(reading)
    db.session.commit()

    return jsonify({
        "message": "Sensor reading stored successfully",
        "reading_id": str(reading.reading_id)
    }), 201


@sensors_bp.route("/readings/<bin_id>", methods=["GET"])
def get_sensor_readings(bin_id):
    readings = (
        SensorReading.query
        .filter_by(bin_id=bin_id)
        .order_by(SensorReading.recorded_at.desc())
        .limit(20)
        .all()
    )

    return jsonify([
        {
            "reading_id": str(r.reading_id),
            "bin_id": str(r.bin_id),
            "compartment": r.compartment,
            "recorded_at": r.recorded_at.isoformat(),
            "fill_percentage": float(r.fill_percentage) if r.fill_percentage is not None else None,
            "temperature_celsius": float(r.temperature_celsius) if r.temperature_celsius is not None else None,
            "humidity_percentage": float(r.humidity_percentage) if r.humidity_percentage is not None else None,
            "gas_index": float(r.gas_index) if r.gas_index is not None else None
        }
        for r in readings
    ])