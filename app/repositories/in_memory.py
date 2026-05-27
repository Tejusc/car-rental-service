import asyncio
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from app.models.car import Car, RentalRecord
from app.repositories.base import CarRepository


class InMemoryCarRepository(CarRepository):
    def __init__(self):
        self._cars: dict[UUID, Car] = {}
        self._rentals: dict[UUID, RentalRecord] = {}
        # Per-car locks prevent double-booking under concurrent requests
        self._locks: dict[UUID, asyncio.Lock] = {}

    def _get_lock(self, car_id: UUID) -> asyncio.Lock:
        if car_id not in self._locks:
            self._locks[car_id] = asyncio.Lock()
        return self._locks[car_id]

    async def get_all(self) -> list[Car]:
        return list(self._cars.values())

    async def get_by_id(self, car_id: UUID) -> Optional[Car]:
        return self._cars.get(car_id)

    async def add(self, car: Car) -> Car:
        self._cars[car.id] = car
        return car

    async def update(self, car: Car) -> Car:
        # Acquire per-car lock to prevent concurrent rent/return race conditions
        async with self._get_lock(car.id):
            car.updated_at = datetime.now(timezone.utc)
            self._cars[car.id] = car
            return car

    async def add_rental_record(self, record: RentalRecord) -> RentalRecord:
        self._rentals[record.id] = record
        return record

    async def get_all_rental_records(self) -> list[RentalRecord]:
        return list(self._rentals.values())

    async def get_active_rental_for_car(self, car_id: UUID) -> Optional[RentalRecord]:
        return next(
            (r for r in self._rentals.values()
             if r.car_id == car_id and r.returned_at is None),
            None,
        )

    async def close_rental_record(self, record: RentalRecord) -> RentalRecord:
        record.returned_at = datetime.now(timezone.utc)
        self._rentals[record.id] = record
        return record
