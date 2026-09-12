from flask import Blueprint, jsonify
from database import db
from models import WasteDetection, Agency, AgencyRecommendation
import networkx as nx
import math

agencies_bp = Blueprint(
    "agencies",
    __name__,
    url_prefix="/api/v1/agencies"
)


def calculate_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0

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

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_capability_matches(detection, agency):
    stream = detection.waste_stream.value

    accepted_streams = [
        item.value if hasattr(item, "value") else str(item)
        for item in (agency.accepted_streams or [])
    ]

    if stream not in accepted_streams:
        return False

    tags = [
        str(tag).lower()
        for tag in (agency.capability_tags or [])
    ]

    if stream == "BATTERY":
        return any(
            keyword in tag
            for tag in tags
            for keyword in ["battery", "lithium"]
        )

    if stream == "E_WASTE":
        if detection.model_class in ["pcb_development", "pcb_consumer"]:
            return any(
                keyword in tag
                for tag in tags
                for keyword in ["pcb", "electronic", "e-waste"]
            )

    return True


@agencies_bp.post("/recommend/<detection_id>")
def recommend_agency(detection_id):

    detection = WasteDetection.query.filter_by(
        detection_id=detection_id
    ).first()

    if not detection:
        return jsonify({
            "success": False,
            "error": {
                "code": "DETECTION_NOT_FOUND",
                "message": "Waste detection not found."
            }
        }), 404

    if detection.waste_stream.value not in ["E_WASTE", "BATTERY"]:
        return jsonify({
            "success": False,
            "error": {
                "code": "UNSUPPORTED_STREAM",
                "message": "Agency recommendation is only required for E-Waste or Battery."
            }
        }), 400

    existing = AgencyRecommendation.query.filter_by(
        detection_id=detection.detection_id
    ).first()

    if existing:
        return jsonify({
            "success": True,
            "data": {
                "recommendation_id": str(existing.recommendation_id),
                "selected_agency_id": (
                    str(existing.selected_agency_id)
                    if existing.selected_agency_id
                    else None
                ),
                "candidate_agencies": existing.candidate_agencies,
                "calculated_distance_km": (
                    float(existing.calculated_distance_km)
                    if existing.calculated_distance_km is not None
                    else None
                ),
                "route_score": (
                    float(existing.route_score)
                    if existing.route_score is not None
                    else None
                ),
                "decision_summary": existing.decision_summary,
                "decision_evidence": existing.decision_evidence
            }
        })

    bin_record = detection.bin

    if not bin_record:
        return jsonify({
            "success": False,
            "error": {
                "code": "BIN_NOT_FOUND",
                "message": "The detection is not linked to a valid bin."
            }
        }), 404

    bin_lat = bin_record.latitude
    bin_lon = bin_record.longitude

    if bin_lat is None or bin_lon is None:
        return jsonify({
            "success": False,
            "error": {
                "code": "BIN_LOCATION_UNAVAILABLE",
                "message": "Bin location is unavailable."
            }
        }), 400

    agencies = Agency.query.filter_by(
        verification_status="VERIFIED",
        is_active=True
    ).all()

    eligible_agencies = []

    for agency in agencies:

        if not get_capability_matches(detection, agency):
            continue

        if agency.latitude is None or agency.longitude is None:
            continue

        distance = calculate_distance_km(
            bin_lat,
            bin_lon,
            agency.latitude,
            agency.longitude
        )

        eligible_agencies.append({
            "agency": agency,
            "distance_km": round(distance, 3)
        })

    if not eligible_agencies:
        return jsonify({
            "success": False,
            "error": {
                "code": "NO_ELIGIBLE_AGENCY",
                "message": "No verified and suitable recycling agency is available."
            }
        }), 404

    graph = nx.Graph()

    source_node = "BIN"

    graph.add_node(
        source_node,
        latitude=float(bin_lat),
        longitude=float(bin_lon)
    )

    for item in eligible_agencies:

        agency = item["agency"]
        agency_id = str(agency.agency_id)

        graph.add_node(
            agency_id,
            latitude=float(agency.latitude),
            longitude=float(agency.longitude)
        )

        graph.add_edge(
            source_node,
            agency_id,
            weight=item["distance_km"]
        )

    distances = nx.single_source_dijkstra_path_length(
        graph,
        source_node,
        weight="weight"
    )

    for item in eligible_agencies:
        agency_id = str(item["agency"].agency_id)
        item["distance_km"] = distances[agency_id]

    eligible_agencies.sort(
        key=lambda x: x["distance_km"]
    )

    nearest_distance = eligible_agencies[0]["distance_km"]

    for item in eligible_agencies:
        distance = item["distance_km"]

        if distance == nearest_distance:
            score = 1.0
        else:
            score = nearest_distance / distance

        item["route_score"] = round(
            min(score, 1.0),
            4
        )

    selected = eligible_agencies[0]

    candidate_data = []

    for rank, item in enumerate(
        eligible_agencies,
        start=1
    ):

        agency = item["agency"]

        candidate_data.append({
            "agency_id": str(agency.agency_id),
            "facility_name": agency.facility_name,
            "verification_status": (
                agency.verification_status.value
                if hasattr(agency.verification_status, "value")
                else str(agency.verification_status)
            ),
            "distance_km": round(
                item["distance_km"],
                3
            ),
            "route_score": item["route_score"],
            "rank": rank,
            "selected": rank == 1
        })

    selected_agency = selected["agency"]

    decision_summary = (
        f"Selected {selected_agency.facility_name} as the "
        f"nearest verified agency suitable for "
        f"{detection.model_class}."
    )

    decision_evidence = {
        "detection_id": str(detection.detection_id),
        "model_class": detection.model_class,
        "waste_stream": detection.waste_stream.value,
        "selection_basis": [
            "verified agency",
            "active agency",
            "accepted waste stream",
            "capability match",
            "NetworkX distance ranking"
        ],
        "candidate_count": len(candidate_data)
    }

    recommendation = AgencyRecommendation(
        detection_id=detection.detection_id,
        selected_agency_id=selected_agency.agency_id,
        candidate_agencies=candidate_data,
        calculated_distance_km=round(
            selected["distance_km"],
            3
        ),
        route_score=selected["route_score"],
        decision_summary=decision_summary,
        decision_evidence=decision_evidence
    )

    db.session.add(recommendation)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "recommendation_id": str(
                recommendation.recommendation_id
            ),
            "selected_agency_id": str(
                selected_agency.agency_id
            ),
            "selected_agency": {
                "facility_name": selected_agency.facility_name,
                "distance_km": round(
                    selected["distance_km"],
                    3
                ),
                "route_score": selected["route_score"]
            },
            "candidate_agencies": candidate_data,
            "decision_summary": decision_summary,
            "decision_evidence": decision_evidence
        }
    })