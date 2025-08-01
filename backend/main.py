from fastapi import FastAPI
from models.sensor_model import SensorData
from typing import Optional

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Let's boost this terrace!"}

app.state.last_data = None

@app.post("/sensor-data")
async def sensor_data(data: SensorData):
    app.state.last_data = data

    return data

@app.get("/latest-sensor-data", response_model=Optional[SensorData])
async def get_latest_sensor_data():
    return app.state.last_data