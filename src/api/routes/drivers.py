"""Endpoints CRUD para conductores."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.models.driver import Driver
from pydantic import BaseModel

router = APIRouter()


class DriverCreate(BaseModel):
    name: str
    license_plate: str | None = None


class DriverStatusUpdate(BaseModel):
    status: str


@router.post("/", status_code=201)
async def create_driver(body: DriverCreate, db: AsyncSession = Depends(get_db)):
    """Registrar un conductor nuevo."""
    driver = Driver(name=body.name, license_plate=body.license_plate)
    db.add(driver)
    await db.flush()
    return {"id": driver.id, "name": driver.name, "status": driver.status}


@router.get("/")
async def list_drivers(db: AsyncSession = Depends(get_db)):
    """Listar todos los conductores."""
    result = await db.execute(select(Driver))
    drivers = result.scalars().all()
    return drivers


@router.get("/{driver_id}")
async def get_driver(driver_id: int, db: AsyncSession = Depends(get_db)):
    """Obtener un conductor por ID."""
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    return driver


@router.put("/{driver_id}/status")
async def update_driver_status(
    driver_id: int, body: DriverStatusUpdate, db: AsyncSession = Depends(get_db)
):
    """Actualizar estado del conductor."""
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    driver.status = body.status
    return {"id": driver.id, "status": driver.status}
