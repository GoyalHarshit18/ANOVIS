"""Database seed script with synthetic demo data."""
import logging
from app.db.database import SessionLocal, engine, Base
from app.db.models import Lot, Component, Measurement, ScreeningResult
from app.services.screening_service import screen_component

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

import random
import uuid

def generate_demo_components(n=20):
    components = []
    for i in range(n):
        # Generate some random variations
        is_fail = random.random() < 0.15  # 15% fail rate
        
        comp = {
            "component_id": f"DEMO-{uuid.uuid4().hex[:6].upper()}",
            "lot_id": "LOT-DEMO-999",
            "device_type": "XYZ-IC",
            "station": f"ST-{random.randint(1, 5):02d}",
            "temperature": "125°C",
            "voltage": "3.3V",
            "Iddq_uA_0h": round(random.uniform(10.0, 13.0), 2),
            "Leakage_nA_0h": round(random.uniform(500.0, 550.0), 2),
            "PropDelay_ns_0h": round(random.uniform(3.2, 3.4), 2),
        }
        
        if is_fail:
            comp["Iddq_uA_24h"] = round(comp["Iddq_uA_0h"] + random.uniform(2.0, 5.0), 2)
            comp["Leakage_nA_24h"] = round(comp["Leakage_nA_0h"] + random.uniform(50.0, 150.0), 2)
            comp["PropDelay_ns_24h"] = round(comp["PropDelay_ns_0h"] + random.uniform(0.1, 0.3), 2)
        else:
            comp["Iddq_uA_24h"] = round(comp["Iddq_uA_0h"] + random.uniform(-0.1, 0.2), 2)
            comp["Leakage_nA_24h"] = round(comp["Leakage_nA_0h"] + random.uniform(-2.0, 5.0), 2)
            comp["PropDelay_ns_24h"] = round(comp["PropDelay_ns_0h"] + random.uniform(-0.02, 0.05), 2)
            
        components.append(comp)
    return components

def seed_db():
    logger.info("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        logger.info("Seeding synthetic data...")
        lot = db.query(Lot).filter(Lot.lot_id == "LOT-DEMO-999").first()
        if not lot:
            lot = Lot(lot_id="LOT-DEMO-999")
            db.add(lot)
            db.commit()

        demo_components = generate_demo_components(20)
        for c_data in demo_components:
            cid = c_data["component_id"]
            if db.query(Component).filter(Component.component_id == cid).first():
                logger.info(f"Skipping {cid}, already exists.")
                continue

            comp = Component(
                component_id=cid,
                device_type=c_data["device_type"],
                lot_id="LOT-DEMO-999",
                station_id=c_data["station"],
            )
            db.add(comp)
            db.commit()

            meas = Measurement(
                component_id=cid,
                hour="24h",
                temperature=c_data["temperature"],
                voltage=c_data["voltage"],
                iddq_ua=c_data["Iddq_uA_24h"],
                leakage_na=c_data["Leakage_nA_24h"],
                prop_delay_ns=c_data["PropDelay_ns_24h"],
            )
            db.add(meas)

            try:
                result = screen_component(c_data)
                sr = ScreeningResult(
                    component_id=cid,
                    ldi=result.get("ldi"),
                    a_score=result.get("a_score"),
                    s_score=result.get("s_score"),
                    prediction_risk=result.get("prediction_risk"),
                    uncertainty_risk=result.get("uncertainty_risk"),
                    predicted_168h=result.get("predicted_168h"),
                    decision=result.get("decision"),
                    stage=result.get("screening_stage"),
                    integrity_flag=result.get("test_integrity_flag", False),
                    basis=result.get("basis"),
                    evidence=result.get("evidence"),
                    test_integrity=result.get("test_integrity"),
                    history=result.get("history"),
                    b_models=result.get("b_models"),
                    shap=result.get("shap"),
                    model_version=result.get("model_version"),
                    explanation=result.get("explanation"),
                )
                db.add(sr)
            except Exception as e:
                logger.error(f"Failed to screen {cid}: {e}")

            db.commit()
            
        logger.info("Database seeding completed.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
