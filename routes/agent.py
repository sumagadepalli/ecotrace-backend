from flask import Blueprint, jsonify

from agent.orchestrator import run_agent

agent_bp = Blueprint(
    "agent",
    __name__,
    url_prefix="/api/v1/agent"
)


@agent_bp.post("/run/<detection_id>")
def run_agent_endpoint(detection_id):

    result = run_agent(detection_id)

    if result.get("status") == "FAILED":
        return jsonify({
            "success": False,
            "data": result
        }), 500

    return jsonify({
        "success": True,
        "data": result
    })