from flask import Blueprint, jsonify
from database import db
from models import SmartBin

bins_bp = Blueprint("bins", __name__, url_prefix="/api/v1/bins")


@bins_bp.get("")
def get_bins():
    bins = SmartBin.query.all()

    return jsonify({
        "success": True,
        "data": [
            {
                "bin_id": str(b.bin_id),
                "bin_uid": b.bin_uid,
                "household_ref": b.household_ref,
                "zone_name": b.zone_name,
                "latitude": float(b.latitude) if b.latitude else None,
                "longitude": float(b.longitude) if b.longitude else None,
                "operational_status": b.operational_status if b.operational_status else None,
                "dry_fill_pct": b.dry_fill_pct,
                "wet_fill_pct": b.wet_fill_pct,
                "ewaste_fill_pct": b.ewaste_fill_pct,
                "battery_fill_pct": b.battery_fill_pct
            }
            for b in bins
        ]
    })