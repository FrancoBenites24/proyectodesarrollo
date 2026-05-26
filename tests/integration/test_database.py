"""Tests de integración para la base de datos."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.database import Base
from src.api.models.driver import Driver
from src.api.models.alert_event import AlertEvent
from src.api.models.driving_session import DrivingSession


# Usar SQLite en memoria para los tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_create_driver(db):
    """Test crear un conductor."""
    driver = Driver(name="Juan Pérez", license_plate="ABC-123")
    db.add(driver)
    db.commit()
    db.refresh(driver)
    assert driver.id is not None
    assert driver.name == "Juan Pérez"
    assert driver.status == "inactive"


def test_list_drivers(db):
    """Test listar conductores."""
    db.add(Driver(name="Ana García"))
    db.add(Driver(name="Luis Torres"))
    db.commit()
    drivers = db.query(Driver).all()
    assert len(drivers) == 2


def test_get_driver_by_id(db):
    """Test obtener conductor por ID."""
    driver = Driver(name="Carlos López")
    db.add(driver)
    db.commit()
    found = db.query(Driver).filter(Driver.id == driver.id).first()
    assert found.name == "Carlos López"


def test_update_driver_status(db):
    """Test actualizar estado del conductor."""
    driver = Driver(name="María Díaz")
    db.add(driver)
    db.commit()
    driver.status = "active"
    db.commit()
    db.refresh(driver)
    assert driver.status == "active"


def test_create_alert_event(db):
    """Test registrar una alerta."""
    driver = Driver(name="Pedro Ruiz")
    db.add(driver)
    db.commit()
    alert = AlertEvent(
        driver_id=driver.id,
        alert_level="HIGH",
        event_type="drowsiness",
        perclos=0.45,
        ear=0.2,
        mor=0.1
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    assert alert.id is not None
    assert alert.alert_level == "HIGH"
