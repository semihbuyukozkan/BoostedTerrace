from fastapi import APIRouter, Request
from typing import Optional
from models.sensor_model import SensorData
from database.db import SessionLocal
from database.orm_models import SensorReading

router = APIRouter()

@router.post("/sensor-data", response_model=SensorData)
def sensor_data(data: SensorData, request: Request):
    request.app.state.last_data = data
    with SessionLocal() as s:
        rec = SensorReading(
            soil_moisture=data.soil_moisture,
            ph=data.ph,
            wind_speed=data.wind_speed,
        )
        s.add(rec)
        s.commit()
        s.refresh(rec)

    return data

@router.get("/latest-sensor-data", response_model=Optional[SensorData])
def get_latest_sensor_data(request: Request):

    if request.app.state.last_data is not None:
        return request.app.state.last_data


    with SessionLocal() as s:
        rec = s.query(SensorReading).order_by(SensorReading.created_at.desc()).first()
        if rec is None:
            return None
        return SensorData(
            soil_moisture=rec.soil_moisture,
            ph=rec.ph,
            wind_speed=rec.wind_speed,
        )
