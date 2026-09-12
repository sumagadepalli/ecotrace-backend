from flask import Blueprint, request, jsonify
from database import db
from models import Alert, SmartBin
import uuid

alerts_bp = Blueprint(
    "alerts",
    __name__,
    url_prefix="/api/v1/alerts"
)


@alerts_bp.post("")
def create_alert():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request body is required."
            }
        }), 400

    required_fields = [
        "organization_id",
        "bin_id",
        "alert_type",
        "severity",
        "trigger_condition",
        "message",
        "recipient_group"
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
                "message": f"Missing fields: {', '.join(missing)}"
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
                "message": "Smart bin not found."
            }
        }), 404

    alert = Alert(
        alert_uid=data.get(
            "alert_uid",
            f"ALT-{uuid.uuid4().hex[:12].upper()}"
        ),
        organization_id=data["organization_id"],
        bin_id=data["bin_id"],
        detection_id=data.get("detection_id"),
        alert_type=data["alert_type"],
        severity=data["severity"],
        status=data.get("status", "OPEN"),
        trigger_condition=data["trigger_condition"],
        message=data["message"],
        recipient_group=data["recipient_group"],
        email_delivery_status=data.get(
            "email_delivery_status",
            "PENDING"
        )
    )

    db.session.add(alert)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "alert_id": str(alert.alert_id),
            "alert_uid": alert.alert_uid,
            "organization_id": str(alert.organization_id),
            "bin_id": str(alert.bin_id),
            "detection_id": (
                str(alert.detection_id)
                if alert.detection_id
                else None
            ),
            "alert_type": alert.alert_type,
            "severity": (
                alert.severity.value
                if hasattr(alert.severity, "value")
                else str(alert.severity)
            ),
            "status": (
                alert.status.value
                if hasattr(alert.status, "value")
                else str(alert.status)
            ),
            "trigger_condition": alert.trigger_condition,
            "message": alert.message,
            "recipient_group": alert.recipient_group
        }
    }), 201


@alerts_bp.get("")
def get_alerts():
    alerts = Alert.query.order_by(
        Alert.created_at.desc()
    ).all()

    return jsonify({
        "success": True,
        "data": [
            {
                "alert_id": str(alert.alert_id),
                "alert_uid": alert.alert_uid,
                "organization_id": str(alert.organization_id),
                "bin_id": str(alert.bin_id),
                "detection_id": (
                    str(alert.detection_id)
                    if alert.detection_id
                    else None
                ),
                "alert_type": alert.alert_type,
                "severity": (
                    alert.severity.value
                    if hasattr(alert.severity, "value")
                    else str(alert.severity)
                ),
                "status": (
                    alert.status.value
                    if hasattr(alert.status, "value")
                    else str(alert.status)
                ),
                "trigger_condition": alert.trigger_condition,
                "message": alert.message,
                "recipient_group": alert.recipient_group,
                "email_delivery_status": (
                    alert.email_delivery_status.value
                    if hasattr(
                        alert.email_delivery_status,
                        "value"
                    )
                    else str(alert.email_delivery_status)
                ),
                "created_at": (
                    alert.created_at.isoformat()
                    if alert.created_at
                    else None
                )
            }
            for alert in alerts
        ]
    })