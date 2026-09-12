from flask import Blueprint, jsonify
from database import db
from models import WasteDetection, KnowledgeBase, EWastePrediction


ewaste_bp = Blueprint(
    "ewaste",
    __name__,
    url_prefix="/api/v1/ewaste"
)


@ewaste_bp.post("/enrich/<detection_id>")
def enrich_detection(detection_id):

    detection = WasteDetection.query.filter_by(
        detection_id=detection_id
    ).first()

    if not detection:
        return jsonify({
            "success": False,
            "error": {
                "code": "DETECTION_NOT_FOUND",
                "message": "Detection not found"
            }
        }), 404

    if detection.waste_stream.value not in ["E_WASTE", "BATTERY"]:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_EWASTE",
                "message": "Detection is not an e-waste or battery item"
            }
        }), 400

    kb = KnowledgeBase.query.filter_by(
        model_class=detection.model_class
    ).order_by(
        KnowledgeBase.created_at.desc()
    ).first()

    if not kb:
        detection.status = "KNOWLEDGE_UNAVAILABLE"
        db.session.commit()

        return jsonify({
            "success": False,
            "error": {
                "code": "KNOWLEDGE_UNAVAILABLE",
                "message": "No knowledge-base record found"
            }
        }), 404

    existing = EWastePrediction.query.filter_by(
        detection_id=detection.detection_id
    ).first()

    if existing:
        prediction = existing
    else:
        prediction = EWastePrediction(
            detection_id=detection.detection_id,
            kb_id=kb.kb_id,
            version_id=kb.version_id,
            component_group=kb.component_group,
            material_profile=kb.material_profile,
            estimated_metals=kb.estimated_metals,
            recovery_category=kb.recovery_category,
            provenance_source=kb.provenance_source
        )

        db.session.add(prediction)

    detection.status = "ENRICHED"

    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "detection_id": str(detection.detection_id),
            "prediction_id": str(prediction.prediction_id),
            "model_class": detection.model_class,
            "component_group": prediction.component_group,
            "material_profile": prediction.material_profile,
            "estimated_metals": prediction.estimated_metals,
            "recovery_category": prediction.recovery_category,
            "provenance_source": prediction.provenance_source,
            "kb_version_id": str(prediction.version_id)
        }
    }), 201