from flask import Blueprint, request, jsonify
from database import db
from models import WasteDetection, SmartBin


detections_bp = Blueprint(
    "detections",
    __name__,
    url_prefix="/api/v1/detections"
)


CLASS_MAPPING = {
    "dry": {
        "waste_stream": "DRY",
        "compartment": 1
    },
    "wet": {
        "waste_stream": "WET",
        "compartment": 2
    },
    "pcb_development": {
        "waste_stream": "E_WASTE",
        "compartment": 3
    },
    "pcb_consumer": {
        "waste_stream": "E_WASTE",
        "compartment": 3
    },
    "battery": {
        "waste_stream": "BATTERY",
        "compartment": 4
    }
}


@detections_bp.post("")
def create_detection():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request body is required"
            }
        }), 400

    required_fields = [
        "organization_id",
        "bin_id",
        "model_class",
        "confidence"
    ]

    missing = [
        field for field in required_fields
        if field not in data
    ]

    if missing:
        return jsonify({
            "success": False,
            "error": {
                "code": "MISSING_FIELDS",
                "message": "Required fields are missing",
                "details": missing
            }
        }), 400

    model_class = data["model_class"]

    if model_class not in CLASS_MAPPING:
        return jsonify({
            "success": False,
            "error": {
                "code": "UNSUPPORTED_CLASS",
                "message": f"Unsupported YOLO class: {model_class}"
            }
        }), 400

    try:
        confidence = float(data["confidence"])
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_CONFIDENCE",
                "message": "Confidence must be a number between 0 and 1"
            }
        }), 400

    if confidence < 0 or confidence > 1:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_CONFIDENCE",
                "message": "Confidence must be between 0 and 1"
            }
        }), 400

    bin_record = SmartBin.query.filter_by(
        bin_id=data["bin_id"],
        organization_id=data["organization_id"]
    ).first()

    if not bin_record:
        return jsonify({
            "success": False,
            "error": {
                "code": "BIN_NOT_FOUND",
                "message": "Bin does not exist for this organization"
            }
        }), 404

    mapping = CLASS_MAPPING[model_class]

    status = "CLASSIFIED"

    if confidence < 0.50:
        status = "LOW_CONFIDENCE_REVIEW"

    detection = WasteDetection(
    organization_id=data["organization_id"],
    bin_id=data["bin_id"],
    presentation_session_id=data.get("presentation_session_id"),
    frame_reference_id=data.get("frame_reference_id"),
    model_class=model_class,
    confidence=confidence,
    waste_stream=mapping["waste_stream"],
    target_compartment=mapping["compartment"],
    bounding_box=data.get("bounding_box"),
    image_storage_path=data.get("image_path"),          # ← renamed
    image_mime_type=data.get("image_mime", "image/jpeg"),# ← renamed
    image_size_bytes=data.get("image_size_bytes"),
    image_checksum_sha256=data.get("image_checksum"),    # ← renamed
    model_version=data.get("model_version", "YOLOv8n"),
    status=status
)

    db.session.add(detection)
    db.session.commit()

    return jsonify({
    "success": True,
    "data": {
        "detection_id": str(detection.detection_id),
        "model_class": detection.model_class,
        "confidence": float(detection.confidence),
        "waste_stream": detection.waste_stream,
        "target_compartment": detection.target_compartment,
        "status": detection.status
    }
}), 201