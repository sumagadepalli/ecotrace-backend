from app import app
from database import db
from models import (
    Organization,
    SmartBin,
    Agency,
    KnowledgeBaseVersion,
    KnowledgeBase
)


with app.app_context():

    # -----------------------------
    # ORGANIZATION
    # -----------------------------

    org = Organization.query.filter_by(
        jurisdiction_code="PUNE-MUN"
    ).first()

    if not org:
        org = Organization(
            org_name="Pune Municipal Corporation",
            jurisdiction_code="PUNE-MUN",
            contact_email="ecotrace@pmc.gov.in",
            address_line="Shivajinagar",
            city="Pune",
            state="Maharashtra",
            latitude=18.5308,
            longitude=73.8475,
            is_active=True
        )

        db.session.add(org)
        db.session.flush()


    # -----------------------------
    # SMART BINS
    # -----------------------------

    if SmartBin.query.count() == 0:

        bins = [
            SmartBin(
                organization_id=org.organization_id,
                bin_uid="ECO-PUNE-001",
                household_ref="HH-SHIV-001",
                zone_name="Shivajinagar",
                latitude=18.5308,
                longitude=73.8475,
                operational_status="NORMAL",
                dry_fill_pct=35,
                wet_fill_pct=52,
                ewaste_fill_pct=20,
                battery_fill_pct=15
            ),

            SmartBin(
                organization_id=org.organization_id,
                bin_uid="ECO-PUNE-002",
                household_ref="HH-SHIV-002",
                zone_name="Model Colony",
                latitude=18.5314,
                longitude=73.8380,
                operational_status="NEAR_CAPACITY",
                dry_fill_pct=72,
                wet_fill_pct=64,
                ewaste_fill_pct=48,
                battery_fill_pct=30
            ),

            SmartBin(
                organization_id=org.organization_id,
                bin_uid="ECO-PUNE-003",
                household_ref="HH-SHIV-003",
                zone_name="Deccan",
                latitude=18.5174,
                longitude=73.8400,
                operational_status="NORMAL",
                dry_fill_pct=28,
                wet_fill_pct=41,
                ewaste_fill_pct=12,
                battery_fill_pct=18
            )
        ]

        db.session.add_all(bins)


    # -----------------------------
    # RECYCLING AGENCIES
    # -----------------------------

    if Agency.query.count() == 0:

        agencies = [
            Agency(
                facility_name="Eco Recycling Facility Pune",
                registration_no="EW-PUNE-001",
                verification_status="VERIFIED",
                verification_source="Seeded Municipal Directory",
                accepted_streams=["E_WASTE"],
                capability_tags=[
                    "PCB",
                    "Electronic Components",
                    "E-Waste"
                ],
                latitude=18.5642,
                longitude=73.7769,
                contact_phone="+91-9000000001",
                contact_email="agency1@example.com",
                is_active=True
            ),

            Agency(
                facility_name="Battery Recovery Centre Pune",
                registration_no="BW-PUNE-001",
                verification_status="VERIFIED",
                verification_source="Seeded Municipal Directory",
                accepted_streams=["BATTERY"],
                capability_tags=[
                    "Battery",
                    "Lithium Battery",
                    "Battery Recovery"
                ],
                latitude=18.5074,
                longitude=73.8077,
                contact_phone="+91-9000000002",
                contact_email="agency2@example.com",
                is_active=True
            )
        ]

        db.session.add_all(agencies)


    # -----------------------------
    # KNOWLEDGE BASE VERSION
    # -----------------------------

    kb_version = KnowledgeBaseVersion.query.filter_by(
        release_tag="KB-EWASTE-v1.0"
    ).first()

    if not kb_version:

        kb_version = KnowledgeBaseVersion(
            release_tag="KB-EWASTE-v1.0",
            source_reference="EcoTrace Curated Knowledge Base",
            status="ACTIVE"
        )

        db.session.add(kb_version)
        db.session.flush()


        # -----------------------------
        # KNOWLEDGE BASE RECORDS
        # -----------------------------

        records = [

            KnowledgeBase(
                version_id=kb_version.version_id,
                model_class="pcb_development",
                component_group="Development PCB",
                material_profile={
                    "materials": [
                        "FR-4",
                        "Copper",
                        "Solder"
                    ]
                },
                estimated_metals=[
                    "Copper"
                ],
                recovery_category="PCB Recycling",
                statutory_framework_ref="E-Waste Rules",
                official_category_mapping="E-Waste",
                provenance_source="EcoTrace Curated Knowledge Base"
            ),

            KnowledgeBase(
                version_id=kb_version.version_id,
                model_class="pcb_consumer",
                component_group="Consumer PCB",
                material_profile={
                    "materials": [
                        "FR-4",
                        "Copper",
                        "Solder"
                    ]
                },
                estimated_metals=[
                    "Copper"
                ],
                recovery_category="PCB Recycling",
                statutory_framework_ref="E-Waste Rules",
                official_category_mapping="E-Waste",
                provenance_source="EcoTrace Curated Knowledge Base"
            ),

            KnowledgeBase(
                version_id=kb_version.version_id,
                model_class="battery",
                component_group="Battery",
                material_profile={
                    "materials": [
                        "Electrochemical Cell Materials"
                    ]
                },
                estimated_metals=[
                    "Lithium",
                    "Cobalt",
                    "Nickel"
                ],
                recovery_category="Battery Recycling",
                statutory_framework_ref="Battery Waste Management Rules",
                official_category_mapping="Battery",
                provenance_source="EcoTrace Curated Knowledge Base"
            ),

            KnowledgeBase(
                version_id=kb_version.version_id,
                model_class="dry",
                component_group="Dry Waste",
                material_profile={
                    "materials": [
                        "Paper",
                        "Plastic",
                        "Metal"
                    ]
                },
                estimated_metals=[
                    "Aluminium"
                ],
                recovery_category="Dry Waste Recycling",
                statutory_framework_ref=None,
                official_category_mapping="Dry Waste",
                provenance_source="EcoTrace Curated Knowledge Base"
            ),

            KnowledgeBase(
                version_id=kb_version.version_id,
                model_class="wet",
                component_group="Wet Waste",
                material_profile={
                    "materials": [
                        "Organic Matter"
                    ]
                },
                estimated_metals=[],
                recovery_category="Organic Waste Processing",
                statutory_framework_ref=None,
                official_category_mapping="Wet Waste",
                provenance_source="EcoTrace Curated Knowledge Base"
            )
        ]

        db.session.add_all(records)


    # -----------------------------
    # COMMIT
    # -----------------------------

    try:

        db.session.commit()

        print()
        print("======================================")
        print("EcoTrace seed data inserted successfully")
        print("======================================")
        print("Organizations:", Organization.query.count())
        print("Bins:", SmartBin.query.count())
        print("Agencies:", Agency.query.count())
        print("KB versions:", KnowledgeBaseVersion.query.count())
        print("KB records:", KnowledgeBase.query.count())

    except Exception as e:

        db.session.rollback()

        print()
        print("======================================")
        print("SEED FAILED")
        print("======================================")
        print(e)
        raise