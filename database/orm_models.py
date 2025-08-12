from sqlalchemy import Column, Integer, Float, DateTime, func, String
from .db import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    soil_moisture = Column(Float, nullable=False)
    ph = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)
    source = Column(String(64), nullable=True)      # şimdilik opsiyonel
    ts = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
