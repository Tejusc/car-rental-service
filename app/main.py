import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from app.models.schemas import CarCreate

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed the in-memory store with sample cars on startup."""
    from app.dependencies import get_car_service

    service = get_car_service()
    seed_cars = [
        CarCreate(make="Toyota",    model="Camry",    year=2022),
        CarCreate(make="Toyota",    model="Corolla",  year=2021),
        CarCreate(make="Honda",     model="Civic",    year=2023),
        CarCreate(make="Honda",     model="Accord",   year=2022),
        CarCreate(make="Ford",      model="Mustang",  year=2023),
        CarCreate(make="Ford",      model="Focus",    year=2020),
        CarCreate(make="BMW",       model="3 Series", year=2022),
        CarCreate(make="Audi",      model="A4",       year=2021),
        CarCreate(make="Tesla",     model="Model 3",  year=2023),
        CarCreate(make="Chevrolet", model="Malibu",   year=2021),
    ]
    for car_data in seed_cars:
        await service.add_car(car_data)
    yield  # application runs here


app = FastAPI(title="Car Rental Service", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers.cars import router as cars_router  # noqa: E402 — imported after app to avoid circular ref
app.include_router(cars_router)

STATIC_DIR = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def ui():
    return FileResponse(STATIC_DIR / "index.html")
