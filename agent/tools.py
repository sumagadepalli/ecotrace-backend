import math
import uuid

import networkx as nx

from database import db
from models import (
    WasteDetection,
    SmartBin,
    Agency,
    SensorReading,
    SensorThresholdConfig,
    Alert
)


CLASS_MAPPING = {
    "dry": {
        "waste_stream": "DRY",
        "category": "Dry Waste",
        "subcategory": "General Dry Waste"
    },
    "wet": {
        "waste_stream": "WET",
        "category": "Wet Waste",
        "subcategory": "Organic Waste"
    },
    "pcb_development": {
        "waste_stream": "E_WASTE",
        "category": "E-Waste",
        "subcategory": "Development PCB"
    },
    "pcb_consumer": {
        "waste_stream": "E_WASTE",
        "category": "E-Waste",
        "subcategory": "Consumer PCB"
    },
    "battery": {
        "waste_stream": "BATTERY",
        "category": "Battery",
        "subcategory": "Waste Battery"
    }
}


def classify_waste_type(
    model_class,
    confidence,
    compartment=None,
    model_version=None
):
    if model_class not in CLASS_MAPPING:
        return {
            "status": "UNSUPPORTED",
            "reason": "Unsupported YOLO model class.",
            "model_class": model_class
        }

    mapping = CLASS_MAPPING[model_class]

    status = "CLASSIFIED"

    if float(confidence) < 0.50:
        status = "LOW_CONFIDENCE_REVIEW"

    return {
        "status": status,
        "model_class": model_class,
        "confidence": float(confidence),
        "waste_stream": mapping["waste_stream"],
        "category": mapping["category"],
        "subcategory": mapping["subcategory"],
        "compartment": compartment,
        "model_version": model_version
    }


def check_environmental_risk(
    bin_id,
    compartment,
    temperature=None,
    humidity=None,
    gas_index=None
):
    readings = SensorReading.query.filter_by(
        bin_id=bin_id,
        compartment=compartment
    ).order_by(
        SensorReading.recorded_at.desc()
    ).limit(10).all()

    latest_temperature = temperature
    latest_humidity = humidity
    latest_gas = gas_index

    if readings:
        latest = readings[0]

        if latest_temperature is None:
            latest_temperature = latest.temperature_celsius

        if latest_humidity is None:
            latest_humidity = latest.humidity_percentage

        if latest_gas is None:
            latest_gas = latest.gas_index

    configs = SensorThresholdConfig.query.filter(
        (SensorThresholdConfig.bin_id == bin_id) |
        (SensorThresholdConfig.bin_id.is_(None))
    ).all()

    result = {
        "status": "NORMAL",
        "reason": "No configured environmental threshold exceeded.",
        "temperature_celsius": (
            float(latest_temperature)
            if latest_temperature is not None
            else None
        ),
        "humidity_percentage": (
            float(latest_humidity)
            if latest_humidity is not None
            else None
        ),
        "gas_index": (
            float(latest_gas)
            if latest_gas is not None
            else None
        ),
        "threshold_reference": None
    }

    severity_rank = {
        "NORMAL": 0,
        "WARNING": 1,
        "CRITICAL": 2
    }

    for config in configs:
        if config.threshold_value is None:
            continue

        metric = config.metric
        threshold = float(config.threshold_value)

        if metric == "DHT11_TEMPERATURE":
            value = latest_temperature
        elif metric == "MQ135_GAS_INDEX":
            value = latest_gas
        elif metric == "ULTRASONIC_FILL":
            value = None
        else:
            continue

        if value is None:
            continue

        value = float(value)
        operator = config.operator

        exceeded = False

        if operator == ">":
            exceeded = value > threshold
        elif operator == ">=":
            exceeded = value >= threshold
        elif operator == "<":
            exceeded = value < threshold
        elif operator == "<=":
            exceeded = value <= threshold
        elif operator == "=":
            exceeded = value == threshold

        if exceeded:
            severity = (
                config.severity.value
                if hasattr(config.severity, "value")
                else str(config.severity)
            )

            if severity_rank.get(
                severity,
                0
            ) > severity_rank[result["status"]]:

                result["status"] = severity
                result["reason"] = (
                    f"{metric} value {value} "
                    f"exceeded configured threshold "
                    f"{threshold}."
                )

                result["threshold_reference"] = {
                    "metric": metric,
                    "operator": operator,
                    "threshold": threshold,
                    "unit": config.unit
                }

    return result


def get_agency_options(
    detection_id,
    waste_stream=None,
    category=None
):
    detection = WasteDetection.query.filter_by(
        detection_id=detection_id
    ).first()

    if not detection:
        return {
            "status": "FAILED",
            "reason": "Detection not found.",
            "candidates": []
        }

    stream = (
        waste_stream
        or detection.waste_stream.value
    )

    model_class = detection.model_class

    agencies = Agency.query.filter_by(
        verification_status="VERIFIED",
        is_active=True
    ).all()

    candidates = []

    for agency in agencies:
        accepted_streams = [
            item.value
            if hasattr(item, "value")
            else str(item)
            for item in (agency.accepted_streams or [])
        ]

        if stream not in accepted_streams:
            continue

        tags = [
            str(tag).lower()
            for tag in (agency.capability_tags or [])
        ]

        capability_match = True

        if stream == "BATTERY":
            capability_match = any(
                keyword in tag
                for tag in tags
                for keyword in [
                    "battery",
                    "lithium"
                ]
            )

        elif stream == "E_WASTE":
            if model_class in [
                "pcb_development",
                "pcb_consumer"
            ]:
                capability_match = any(
                    keyword in tag
                    for tag in tags
                    for keyword in [
                        "pcb",
                        "electronic",
                        "e-waste"
                    ]
                )

        if not capability_match:
            continue

        candidates.append({
            "agency_id": str(agency.agency_id),
            "facility_name": agency.facility_name,
            "verification_status": (
                agency.verification_status.value
                if hasattr(
                    agency.verification_status,
                    "value"
                )
                else str(
                    agency.verification_status
                )
            ),
            "capability_tags": agency.capability_tags or [],
            "latitude": float(agency.latitude),
            "longitude": float(agency.longitude),
            "contact_phone": agency.contact_phone,
            "contact_email": agency.contact_email
        })

    return {
        "status": "SUCCESS",
        "waste_stream": stream,
        "category": category,
        "candidate_count": len(candidates),
        "candidates": candidates
    }


def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    radius = 6371.0

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


def calculate_route_priority(
    bin_id,
    candidates
):
    bin_record = SmartBin.query.filter_by(
        bin_id=bin_id
    ).first()

    if not bin_record:
        return {
            "status": "FAILED",
            "reason": "Bin not found.",
            "ranked_agencies": []
        }

    if not candidates:
        return {
            "status": "NO_ELIGIBLE_AGENCY",
            "reason": "No suitable agency candidates.",
            "ranked_agencies": []
        }

    graph = nx.Graph()

    graph.add_node(
        "BIN",
        latitude=float(bin_record.latitude),
        longitude=float(bin_record.longitude)
    )

    for candidate in candidates:
        agency_id = candidate["agency_id"]

        graph.add_node(
            agency_id,
            latitude=candidate["latitude"],
            longitude=candidate["longitude"]
        )

        distance = calculate_distance_km(
            bin_record.latitude,
            bin_record.longitude,
            candidate["latitude"],
            candidate["longitude"]
        )

        graph.add_edge(
            "BIN",
            agency_id,
            weight=distance
        )

    distances = nx.single_source_dijkstra_path_length(
        graph,
        "BIN",
        weight="weight"
    )

    ranked = []

    for candidate in candidates:
        agency_id = candidate["agency_id"]

        distance = distances.get(
            agency_id
        )

        if distance is None:
            continue

        ranked.append({
            **candidate,
            "distance_km": round(
                distance,
                3
            )
        })

    ranked.sort(
        key=lambda item: item["distance_km"]
    )

    if ranked:
        nearest = ranked[0]["distance_km"]

        for rank, item in enumerate(
            ranked,
            start=1
        ):
            if nearest == 0:
                score = 1.0
            else:
                score = nearest / item["distance_km"]

            item["route_score"] = round(
                min(score, 1.0),
                4
            )

            item["rank"] = rank
            item["selected"] = rank == 1

    return {
        "status": "SUCCESS",
        "selected_agency": (
            ranked[0]
            if ranked
            else None
        ),
        "ranked_agencies": ranked
    }


def send_notification(
    organization_id,
    bin_id,
    detection_id,
    alert_type,
    severity,
    trigger_condition,
    message,
    recipient_group
):
    alert = Alert(
        alert_uid=f"ALT-{uuid.uuid4().hex[:12].upper()}",
        organization_id=organization_id,
        bin_id=bin_id,
        detection_id=detection_id,
        alert_type=alert_type,
        severity=severity,
        status="OPEN",
        trigger_condition=trigger_condition,
        message=message,
        recipient_group=recipient_group,
        email_delivery_status="PENDING"
    )

    db.session.add(alert)
    db.session.commit()

    return {
        "status": "RECORDED",
        "alert_id": str(alert.alert_id),
        "alert_uid": alert.alert_uid,
        "severity": (
            alert.severity.value
            if hasattr(
                alert.severity,
                "value"
            )
            else str(alert.severity)
        ),
        "recipient_group": recipient_group,
        "message": message
    }