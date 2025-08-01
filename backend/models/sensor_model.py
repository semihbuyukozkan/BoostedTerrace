from pydantic import BaseModel

class SensorData(BaseModel):
    soil_moisture: float
    ph: float
    wind_speed: float
