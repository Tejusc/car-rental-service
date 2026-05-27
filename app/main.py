import logging
from fastapi import FastAPI
from app.routers.cars import router as cars_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Car Rental Service", version="1.0.0")
app.include_router(cars_router)
