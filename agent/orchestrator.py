import time
import uuid
from datetime import datetime, timezone

from database import db
from models import (
    WasteDetection,
    AgentToolExecution,
    AuditEvent
)

from agent.tools import (
    classify_waste_type,
    check_environmental_risk,
    get_agency_options,
    calculate_route_priority,
    send_notification
)


def record_tool_execution(
    agent_execution_id,
    detection_id,
    tool_name,
    sequence_number,
    input_payload,
    output_payload,
    status,
    latency_ms,
    error_message=None
):
    execution = AgentToolExecution(
        agent_execution_id=agent_execution_id,
        detection_id=detection_id,
        tool_name=tool_name,
        sequence_number=sequence_number,
        input_payload=input_payload,
        output_payload=output_payload,
        status=status,
        latency_ms=latency_ms,
        error_message=error_message,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )

    db.session.add(execution)
    db.session.commit()

    return execution


def run_agent(detection_id):
    detection = WasteDetection.query.filter_by(
        detection_id=detection_id
    ).first()

    if not detection:
        return {
            "status": "FAILED",
            "reason": "Detection not found."
        }

    agent_execution_id = uuid.uuid4()

    sequence = 1
    evidence = []
    decisions = []

    def execute_tool(
        tool_name,
        tool_function,
        input_payload,
        *args,
        **kwargs
    ):
        nonlocal sequence

        started = time.perf_counter()

        try:
            output = tool_function(
                *args,
                **kwargs
            )

            latency = int(
                (time.perf_counter() - started)
                * 1000
            )

            record_tool_execution(
                agent_execution_id,
                detection.detection_id,
                tool_name,
                sequence,
                input_payload,
                output,
                "SUCCESS",
                latency
            )

            evidence.append({
                "tool": tool_name,
                "output": output
            })

            sequence += 1

            return output

        except Exception as error:
            latency = int(
                (time.perf_counter() - started)
                * 1000
            )

            record_tool_execution(
                agent_execution_id,
                detection.detection_id,
                tool_name,
                sequence,
                input_payload,
                None,
                "FAILED",
                latency,
                str(error)
            )

            raise

    try:

        # TOOL 1
        classification = execute_tool(
            "classify_waste_type",
            classify_waste_type,
            {
                "model_class": detection.model_class,
                "confidence": float(
                    detection.confidence
                ),
                "compartment": (
                    detection.target_compartment
                ),
                "model_version": (
                    detection.model_version
                )
            },
            detection.model_class,
            float(detection.confidence),
            detection.target_compartment,
            detection.model_version
        )

        if classification["status"] == "UNSUPPORTED":
            detection.status = "UNSUPPORTED_CLASS"
            db.session.commit()

            return {
                "status": "FAILED",
                "action": "REVIEW",
                "reason": "Unsupported waste class.",
                "evidence": evidence,
                "agent_execution_id": str(
                    agent_execution_id
                )
            }

        if classification["status"] == "LOW_CONFIDENCE_REVIEW":
            detection.status = "LOW_CONFIDENCE_REVIEW"
            db.session.commit()

            return {
                "status": "REVIEW_REQUIRED",
                "action": "REVIEW",
                "reason": "Detection confidence is below policy threshold.",
                "evidence": evidence,
                "agent_execution_id": str(
                    agent_execution_id
                )
            }

        waste_stream = classification[
            "waste_stream"
        ]

        # DRY / WET END HERE
        if waste_stream in [
            "DRY",
            "WET"
        ]:
            final_action = (
                f"Route to {waste_stream} compartment."
            )

            decisions.append(final_action)

            audit = AuditEvent(
                organization_id=detection.organization_id,
                actor_id="EcoTrace-Agent-v1",
                actor_type="AGENT",
                event_type="AGENT_DECISION",
                entity_type="WASTE_DETECTION",
                entity_id=detection.detection_id,
                payload_after={
                    "agent_execution_id": str(
                        agent_execution_id
                    ),
                    "action": final_action,
                    "evidence": evidence
                }
            )

            db.session.add(audit)
            db.session.commit()

            return {
                "status": "SUCCESS",
                "action": final_action,
                "reason": "Standard waste pathway identified.",
                "evidence": evidence,
                "agent_execution_id": str(
                    agent_execution_id
                )
            }

        # TOOL 2
        risk = execute_tool(
            "check_environmental_risk",
            check_environmental_risk,
            {
                "bin_id": str(
                    detection.bin_id
                ),
                "compartment": waste_stream
            },
            str(detection.bin_id),
            waste_stream
        )

        if risk["status"] in [
            "WARNING",
            "CRITICAL"
        ]:
            decisions.append(
                f"Environmental risk: {risk['status']}"
            )

        # TOOL 3
        agencies = execute_tool(
            "get_agency_options",
            get_agency_options,
            {
                "detection_id": str(
                    detection.detection_id
                ),
                "waste_stream": waste_stream,
                "category": classification["category"]
            },
            str(detection.detection_id),
            waste_stream,
            classification["category"]
        )

        if not agencies["candidates"]:

            detection.status = "NO_AGENCY_FOUND"
            db.session.commit()

            if risk["status"] in [
                "WARNING",
                "CRITICAL"
            ]:
                execute_tool(
                    "send_notification",
                    send_notification,
                    {
                        "organization_id": str(
                            detection.organization_id
                        ),
                        "bin_id": str(
                            detection.bin_id
                        ),
                        "detection_id": str(
                            detection.detection_id
                        ),
                        "alert_type": "NO_AGENCY_FOUND",
                        "severity": risk["status"],
                        "trigger_condition": "No eligible agency",
                        "message": "No verified suitable recycling agency found.",
                        "recipient_group": "Municipal Operations Team"
                    },
                    detection.organization_id,
                    detection.bin_id,
                    detection.detection_id,
                    "NO_AGENCY_FOUND",
                    risk["status"],
                    "No eligible agency",
                    "No verified suitable recycling agency found.",
                    "Municipal Operations Team"
                )

            return {
                "status": "REVIEW_REQUIRED",
                "action": "NO_SUITABLE_AGENCY",
                "reason": "No verified suitable agency found.",
                "evidence": evidence,
                "agent_execution_id": str(
                    agent_execution_id
                )
            }

        # TOOL 4
        routing = execute_tool(
            "calculate_route_priority",
            calculate_route_priority,
            {
                "bin_id": str(
                    detection.bin_id
                ),
                "candidate_count": len(
                    agencies["candidates"]
                )
            },
            str(detection.bin_id),
            agencies["candidates"]
        )

        selected = routing.get(
            "selected_agency"
        )

        if not selected:
            return {
                "status": "REVIEW_REQUIRED",
                "action": "NO_ROUTE",
                "reason": "No route could be calculated.",
                "evidence": evidence,
                "agent_execution_id": str(
                    agent_execution_id
                )
            }

        final_action = (
            f"Recommend {selected['facility_name']} "
            f"for downstream processing."
        )

        decisions.append(final_action)

        # TOOL 5 only when an alert is needed
        if risk["status"] in [
            "WARNING",
            "CRITICAL"
        ]:

            notification = execute_tool(
                "send_notification",
                send_notification,
                {
                    "organization_id": str(
                        detection.organization_id
                    ),
                    "bin_id": str(
                        detection.bin_id
                    ),
                    "detection_id": str(
                        detection.detection_id
                    ),
                    "alert_type": "ENVIRONMENTAL_RISK",
                    "severity": risk["status"],
                    "trigger_condition": risk["reason"],
                    "message": (
                        f"{risk['status']}: "
                        f"{risk['reason']}"
                    ),
                    "recipient_group": (
                        "Municipal Operations Team"
                    )
                },
                detection.organization_id,
                detection.bin_id,
                detection.detection_id,
                "ENVIRONMENTAL_RISK",
                risk["status"],
                risk["reason"],
                f"{risk['status']}: {risk['reason']}",
                "Municipal Operations Team"
            )

            decisions.append(
                "Municipal notification recorded."
            )

        detection.status = "PROCESSED"
        db.session.commit()

        audit = AuditEvent(
            organization_id=detection.organization_id,
            actor_id="EcoTrace-Agent-v1",
            actor_type="AGENT",
            event_type="AGENT_DECISION",
            entity_type="WASTE_DETECTION",
            entity_id=detection.detection_id,
            payload_after={
                "agent_execution_id": str(
                    agent_execution_id
                ),
                "action": final_action,
                "decisions": decisions,
                "selected_agency": selected,
                "risk": risk,
                "evidence": evidence
            }
        )

        db.session.add(audit)
        db.session.commit()

        return {
            "status": "SUCCESS",
            "action": final_action,
            "reason": (
                "Waste classified, environmental "
                "risk evaluated and suitable agency ranked."
            ),
            "selected_agency": selected,
            "risk": risk,
            "evidence": evidence,
            "agent_execution_id": str(
                agent_execution_id
            )
        }

    except Exception as error:

        db.session.rollback()

        return {
            "status": "FAILED",
            "action": "RETRY",
            "reason": str(error),
            "evidence": evidence,
            "agent_execution_id": str(
                agent_execution_id
            )
        }