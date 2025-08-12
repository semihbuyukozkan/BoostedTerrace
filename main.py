from fastapi import FastAPI
from routes import sensor, health
from database.db import Base, engine  # EKLENDİ

app = FastAPI()
app.state.last_data = None

# EKLENDİ: Uygulama açılırken tabloları oluştur
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(sensor.router, prefix="/api/v1", tags=["Sensor"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])

@app.get("/")
async def root():
    return {"message": "Let's boost this terrace!"}
