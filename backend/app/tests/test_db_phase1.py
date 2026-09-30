import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from app.db.models import Measurement, Component, Lot, ScreeningRun, Base

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session

def test_measurement_unique_checkpoint(db_session):
    lot = Lot(lot_id="LOT-TST")
    db_session.add(lot)
    db_session.commit()

    run = ScreeningRun(run_id="RUN-123", lot_id="LOT-TST")
    db_session.add(run)
    db_session.commit()

    comp = Component(component_id="COMP-1", lot_id="LOT-TST")
    db_session.add(comp)
    db_session.commit()

    m1 = Measurement(run_id="RUN-123", component_id="COMP-1", checkpoint_hour=0, iddq_ua=1.0)
    db_session.add(m1)
    db_session.commit()

    # Attempt to add another 0h measurement
    m2 = Measurement(run_id="RUN-123", component_id="COMP-1", checkpoint_hour=0, iddq_ua=1.5)
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()

    # Valid check: add 24h
    m3 = Measurement(run_id="RUN-123", component_id="COMP-1", checkpoint_hour=24, iddq_ua=1.5)
    db_session.add(m3)
    db_session.commit()
