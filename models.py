import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import (
    UUID,
    JSONB,
    ARRAY,
    INET,
    ENUM
)

from database import db


waste_stream_enum = ENUM(
    "DRY",
    "WET",
    "E_WASTE",
    "BATTERY",
    name="waste_stream_enum",
    create_type=True
)

event_status_enum = ENUM(
    "DETECTED",
    "CLASSIFIED",
    "ENRICHED",
    "PERSISTED_BASIC",
    "AGENCY_FILTERED",
    "ROUTE_PRIORITIZED",
    "RECOMMENDATION_STORED",
    "ALERT_DISPATCHED",
    "COMPLETED",
    "LOW_CONFIDENCE_REVIEW",
    "UNSUPPORTED_CLASS",
    "KNOWLEDGE_UNAVAILABLE",
    "NO_SUITABLE_AGENCY",
    "AGENT_FAILED",
    name="event_status_enum",
    create_type=True
)

alert_severity_enum = ENUM(
    "INFO",
    "WARNING",
    "CRITICAL",
    name="alert_severity_enum",
    create_type=True
)

alert_status_enum = ENUM(
    "OPEN",
    "ACKNOWLEDGED",
    "RESOLVED",
    name="alert_status_enum",
    create_type=True
)

agency_verification_enum = ENUM(
    "VERIFIED",
    "PENDING",
    "EXPIRED",
    "UNKNOWN",
    name="agency_verification_enum",
    create_type=True
)

tool_execution_status_enum = ENUM(
    "SUCCESS",
    "FAILED",
    "RETRY",
    "TIMED_OUT",
    name="tool_execution_status_enum",
    create_type=True
)

kb_release_status_enum = ENUM(
    "DRAFT",
    "ACTIVE",
    "SUPERSEDED",
    name="kb_release_status_enum",
    create_type=True
)

notification_delivery_status_enum = ENUM(
    "PENDING",
    "SENT",
    "FAILED",
    name="notification_delivery_status_enum",
    create_type=True
)

bin_operational_status_enum = ENUM(
    "NORMAL",
    "NEAR_CAPACITY",
    "COLLECTION_REQUIRED",
    "MAINTENANCE_REQUIRED",
    "DECOMMISSIONED",
    name="bin_operational_status_enum",
    create_type=True
)


class Organization(db.Model):
    __tablename__ = "organizations"

    organization_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    org_name = db.Column(db.String(255), nullable=False)

    jurisdiction_code = db.Column(
        db.String(64),
        nullable=False,
        unique=True
    )

    contact_email = db.Column(
        db.String(255),
        nullable=False
    )

    address_line = db.Column(db.Text)

    city = db.Column(
        db.String(128),
        nullable=False
    )

    state = db.Column(
        db.String(128),
        nullable=False
    )

    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class Admin(db.Model):
    __tablename__ = "admins"

    admin_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "organizations.organization_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    full_name = db.Column(
        db.String(128),
        nullable=False
    )

    role = db.Column(
        db.String(32),
        nullable=False,
        default="MUNICIPAL_ADMIN"
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('SUPER_ADMIN', 'MUNICIPAL_ADMIN')",
            name="ck_admin_role"
        ),
    )


class SmartBin(db.Model):
    __tablename__ = "smart_bins"

    bin_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "organizations.organization_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    bin_uid = db.Column(
        db.String(64),
        nullable=False,
        unique=True
    )

    household_ref = db.Column(
        db.String(64)
    )

    zone_name = db.Column(
        db.String(128),
        nullable=False
    )

    latitude = db.Column(
        db.Numeric(10, 8),
        nullable=False
    )

    longitude = db.Column(
        db.Numeric(11, 8),
        nullable=False
    )

    operational_status = db.Column(
        bin_operational_status_enum,
        nullable=False,
        default="NORMAL"
    )

    dry_fill_pct = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0.00
    )

    wet_fill_pct = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0.00
    )

    ewaste_fill_pct = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0.00
    )

    battery_fill_pct = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0.00
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "dry_fill_pct BETWEEN 0 AND 100",
            name="ck_dry_fill"
        ),
        CheckConstraint(
            "wet_fill_pct BETWEEN 0 AND 100",
            name="ck_wet_fill"
        ),
        CheckConstraint(
            "ewaste_fill_pct BETWEEN 0 AND 100",
            name="ck_ewaste_fill"
        ),
        CheckConstraint(
            "battery_fill_pct BETWEEN 0 AND 100",
            name="ck_battery_fill"
        ),
        UniqueConstraint(
            "bin_id",
            "organization_id",
            name="uq_smart_bins_org_bin"
        ),
    )


class WasteDetection(db.Model):
    __tablename__ = "waste_detections"

    detection_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    bin_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    presentation_session_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    frame_reference_id = db.Column(
        db.String(128),
        nullable=False
    )

    model_class = db.Column(
        db.String(64),
        nullable=False
    )

    confidence = db.Column(
        db.Numeric(5, 4),
        nullable=False
    )

    waste_stream = db.Column(
        waste_stream_enum,
        nullable=False
    )

    target_compartment = db.Column(
        db.SmallInteger,
        nullable=False
    )

    bounding_box = db.Column(
        JSONB,
        nullable=False
    )

    image_storage_path = db.Column(
        db.String(512),
        nullable=False
    )

    image_mime_type = db.Column(
        db.String(64),
        nullable=False,
        default="image/jpeg"
    )

    image_size_bytes = db.Column(
        db.Integer,
        nullable=False
    )

    image_checksum_sha256 = db.Column(
        db.String(64),
        nullable=False
    )

    model_version = db.Column(
        db.String(64),
        nullable=False,
        default="yolov8n-v1.0"
    )

    status = db.Column(
        event_status_enum,
        nullable=False,
        default="DETECTED"
    )

    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "confidence BETWEEN 0.0000 AND 1.0000",
            name="ck_detection_confidence"
        ),
        CheckConstraint(
            "target_compartment BETWEEN 1 AND 4",
            name="ck_target_compartment"
        ),
        ForeignKeyConstraint(
            ["bin_id", "organization_id"],
            [
                "smart_bins.bin_id",
                "smart_bins.organization_id"
            ],
            ondelete="RESTRICT",
            name="fk_waste_detections_bin_org"
        ),
        UniqueConstraint(
            "detection_id",
            "organization_id",
            name="uq_detections_bin_org"
        ),
    )


class KnowledgeBaseVersion(db.Model):
    __tablename__ = "knowledge_base_versions"

    version_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    release_tag = db.Column(
        db.String(64),
        nullable=False,
        unique=True
    )

    source_reference = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        kb_release_status_enum,
        nullable=False,
        default="DRAFT"
    )

    effective_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    superseded_at = db.Column(
        db.DateTime(timezone=True)
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class KnowledgeBase(db.Model):
    __tablename__ = "knowledge_base"

    kb_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    version_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "knowledge_base_versions.version_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    model_class = db.Column(
        db.String(64),
        nullable=False
    )

    component_group = db.Column(
        db.String(128),
        nullable=False
    )

    material_profile = db.Column(
        JSONB,
        nullable=False
    )

    estimated_metals = db.Column(
        JSONB,
        nullable=False
    )

    recovery_category = db.Column(
        db.String(128),
        nullable=False
    )

    statutory_framework_ref = db.Column(
        db.String(255)
    )

    official_category_mapping = db.Column(
        db.String(128)
    )

    provenance_source = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "model_class",
            name="uq_version_class"
        ),
        UniqueConstraint(
            "kb_id",
            "version_id",
            name="uq_kb_id_version"
        ),
    )


class EWastePrediction(db.Model):
    __tablename__ = "ewaste_predictions"

    prediction_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    detection_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "waste_detections.detection_id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        unique=True
    )

    kb_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    version_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    component_group = db.Column(
        db.String(128),
        nullable=False
    )

    material_profile = db.Column(
        JSONB,
        nullable=False
    )

    estimated_metals = db.Column(
        JSONB,
        nullable=False
    )

    recommended_recovery_category = db.Column(
        db.String(128),
        nullable=False
    )

    provenance_source = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["kb_id", "version_id"],
            [
                "knowledge_base.kb_id",
                "knowledge_base.version_id"
            ],
            ondelete="RESTRICT",
            name="fk_ewaste_predictions_kb_version"
        ),
        ForeignKeyConstraint(
            ["version_id"],
            ["knowledge_base_versions.version_id"],
            ondelete="RESTRICT",
            name="fk_ewaste_predictions_version"
        ),
    )


class Agency(db.Model):
    __tablename__ = "agencies"

    agency_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    facility_name = db.Column(
        db.String(255),
        nullable=False
    )

    registration_no = db.Column(
        db.String(128),
        unique=True
    )

    verification_status = db.Column(
        agency_verification_enum,
        nullable=False,
        default="PENDING"
    )

    verification_source = db.Column(
        db.String(255)
    )

    last_verified_at = db.Column(
        db.DateTime(timezone=True)
    )

    accepted_streams = db.Column(
        ARRAY(waste_stream_enum),
        nullable=False
    )

    capability_tags = db.Column(
        ARRAY(db.Text),
        nullable=False,
        default=list
    )

    latitude = db.Column(
        db.Numeric(10, 8),
        nullable=False
    )

    longitude = db.Column(
        db.Numeric(11, 8),
        nullable=False
    )

    contact_phone = db.Column(
        db.String(32),
        nullable=False
    )

    contact_email = db.Column(
        db.String(255),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class AgencyRecommendation(db.Model):
    __tablename__ = "agency_recommendations"

    recommendation_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    detection_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "waste_detections.detection_id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        unique=True
    )

    selected_agency_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "agencies.agency_id",
            ondelete="RESTRICT"
        )
    )

    candidate_agencies = db.Column(
        JSONB,
        nullable=False
    )

    calculated_distance_km = db.Column(
        db.Numeric(8, 3)
    )

    route_score = db.Column(
        db.Numeric(5, 4)
    )

    decision_summary = db.Column(
        db.Text,
        nullable=False
    )

    decision_evidence = db.Column(
        JSONB,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "route_score BETWEEN 0.0000 AND 1.0000",
            name="ck_route_score"
        ),
    )


class SensorThresholdConfig(db.Model):
    __tablename__ = "sensor_threshold_config"

    config_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    bin_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "smart_bins.bin_id",
            ondelete="CASCADE"
        )
    )

    metric = db.Column(
        db.String(64),
        nullable=False
    )

    severity = db.Column(
        alert_severity_enum,
        nullable=False,
        default="WARNING"
    )

    operator = db.Column(
        db.String(16),
        nullable=False
    )

    threshold_value = db.Column(
        db.Numeric(8, 2)
    )

    unit = db.Column(
        db.String(32),
        nullable=False
    )

    source_reference = db.Column(
        db.String(255),
        nullable=False
    )

    calibration_notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "metric IN ('DHT11_TEMPERATURE', 'MQ135_GAS_INDEX', 'ULTRASONIC_FILL')",
            name="ck_sensor_metric"
        ),
        CheckConstraint(
            "operator IN ('>', '>=', '<', '<=', '=', 'CONFIGURABLE')",
            name="ck_sensor_operator"
        ),
        UniqueConstraint(
            "bin_id",
            "metric",
            "severity",
            name="uq_bin_metric_severity"
        ),
    )


class BinCalibrationLog(db.Model):
    __tablename__ = "bin_calibration_logs"

    calibration_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    bin_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "smart_bins.bin_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    compartment = db.Column(
        db.SmallInteger,
        nullable=False
    )

    empty_distance_cm = db.Column(
        db.Numeric(6, 2)
    )

    full_distance_cm = db.Column(
        db.Numeric(6, 2)
    )

    calibration_status = db.Column(
        db.String(32),
        nullable=False,
        default="REQUIRED"
    )

    calibrated_at = db.Column(
        db.DateTime(timezone=True)
    )

    calibration_notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "compartment BETWEEN 1 AND 4",
            name="ck_calibration_compartment"
        ),
        CheckConstraint(
            "calibration_status IN ('REQUIRED', 'CALIBRATED', 'EXPIRED')",
            name="ck_calibration_status"
        ),
        UniqueConstraint(
            "bin_id",
            "compartment",
            name="uq_bin_compartment"
        ),
    )


class SensorReading(db.Model):
    __tablename__ = "sensor_readings"

    reading_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    bin_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "smart_bins.bin_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    compartment = db.Column(
        waste_stream_enum,
        nullable=False
    )

    recorded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    fill_percentage = db.Column(
        db.Numeric(5, 2)
    )

    temperature_celsius = db.Column(
        db.Numeric(5, 2)
    )

    humidity_percentage = db.Column(
        db.Numeric(5, 2)
    )

    gas_index = db.Column(
        db.Numeric(6, 2)
    )

    raw_sensor_payload = db.Column(
        JSONB
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "fill_percentage BETWEEN 0 AND 100",
            name="ck_sensor_fill"
        ),
        CheckConstraint(
            "humidity_percentage BETWEEN 0 AND 100",
            name="ck_sensor_humidity"
        ),
    )


class Alert(db.Model):
    __tablename__ = "alerts"

    alert_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    alert_uid = db.Column(
        db.String(64),
        nullable=False,
        unique=True
    )

    organization_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    bin_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    detection_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "waste_detections.detection_id",
            ondelete="RESTRICT"
        )
    )

    alert_type = db.Column(
        db.String(64),
        nullable=False
    )

    severity = db.Column(
        alert_severity_enum,
        nullable=False
    )

    status = db.Column(
        alert_status_enum,
        nullable=False,
        default="OPEN"
    )

    trigger_condition = db.Column(
        db.String(128),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    recipient_group = db.Column(
        db.String(128),
        nullable=False
    )

    acknowledged_by = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "admins.admin_id",
            ondelete="SET NULL"
        )
    )

    acknowledged_at = db.Column(
        db.DateTime(timezone=True)
    )

    resolved_by = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "admins.admin_id",
            ondelete="SET NULL"
        )
    )

    resolved_at = db.Column(
        db.DateTime(timezone=True)
    )

    resolution_notes = db.Column(
        db.Text
    )

    email_delivery_status = db.Column(
        notification_delivery_status_enum,
        nullable=False,
        default="PENDING"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["bin_id", "organization_id"],
            [
                "smart_bins.bin_id",
                "smart_bins.organization_id"
            ],
            ondelete="RESTRICT",
            name="fk_alerts_bin_org"
        ),
    )


class AgentToolExecution(db.Model):
    __tablename__ = "agent_tool_executions"

    execution_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    agent_execution_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    detection_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "waste_detections.detection_id",
            ondelete="CASCADE"
        )
    )

    tool_name = db.Column(
        db.String(64),
        nullable=False
    )

    sequence_number = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    input_payload = db.Column(
        JSONB,
        nullable=False
    )

    output_payload = db.Column(
        JSONB
    )

    status = db.Column(
        tool_execution_status_enum,
        nullable=False
    )

    latency_ms = db.Column(
        db.Integer,
        nullable=False
    )

    error_message = db.Column(
        db.Text
    )

    started_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    completed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "tool_name IN ("
            "'classify_waste_type', "
            "'check_environmental_risk', "
            "'get_agency_options', "
            "'calculate_route_priority', "
            "'send_notification'"
            ")",
            name="ck_agent_tool_name"
        ),
    )


class AuditEvent(db.Model):
    __tablename__ = "audit_events"

    audit_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    organization_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "organizations.organization_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    actor_id = db.Column(
        db.String(255),
        nullable=False
    )

    actor_type = db.Column(
        db.String(32),
        nullable=False
    )

    event_type = db.Column(
        db.String(64),
        nullable=False
    )

    entity_type = db.Column(
        db.String(64),
        nullable=False
    )

    entity_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    payload_before = db.Column(
        JSONB
    )

    payload_after = db.Column(
        JSONB,
        nullable=False
    )

    ip_address = db.Column(
        INET
    )

    user_agent = db.Column(
        db.Text
    )

    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "actor_type IN ('AGENT', 'ADMIN', 'SYSTEM')",
            name="ck_audit_actor_type"
        ),
    )


class AuthRefreshSession(db.Model):
    __tablename__ = "auth_refresh_sessions"

    session_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    admin_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "admins.admin_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    jti = db.Column(
        db.String(128),
        nullable=False,
        unique=True
    )

    token_hash = db.Column(
        db.String(255),
        nullable=False
    )

    is_revoked = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    revoked_at = db.Column(
        db.DateTime(timezone=True)
    )


class IdempotencyRecord(db.Model):
    __tablename__ = "idempotency_records"

    idempotency_key = db.Column(
        db.String(255),
        primary_key=True
    )

    organization_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey(
            "organizations.organization_id",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    presentation_session_id = db.Column(
        UUID(as_uuid=True),
        nullable=False
    )

    request_checksum = db.Column(
        db.String(64),
        nullable=False
    )

    response_payload = db.Column(
        JSONB,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )