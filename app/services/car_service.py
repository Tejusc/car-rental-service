import logging
from uuid import UUID
from typing import Optional
from app.repositories.base import CarRepository
from app.models.car import Car, RentalRecord
from app.models.schemas import CarCreate, RentRequest
from app.exceptions import CarNotFoundError, CarNotAvailableError, CarNotRentedError

logger = logging.getLogger(__name__)


class CarService:
    def __init__(self, repo: CarRepository):
        self._repo = repo

    async def list_cars(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        available: Optional[bool] = None,
    ) -> list[Car]:
        cars = await self._repo.get_all()
        if make:
            cars = [c for c in cars if c.make.lower() == make.lower()]
        if model:
            cars = [c for c in cars if c.model.lower() == model.lower()]
        if year:
            cars = [c for c in cars if c.year == year]
        if available is not None:
            cars = [c for c in cars if c.is_available == available]
        logger.info(
            "list_cars",
            extra={"count": len(cars), "filters": {"make": make, "model": model, "year": year, "available": available}},
        )
        return cars

    async def get_car(self, car_id: UUID) -> Car:
        car = await self._repo.get_by_id(car_id)
        if not car:
            logger.warning("get_car not found", extra={"car_id": str(car_id)})
            raise CarNotFoundError(car_id)
        return car

    async def add_car(self, data: CarCreate) -> Car:
        car = Car(make=data.make, model=data.model, year=data.year)
        await self._repo.add(car)
        logger.info("add_car", extra={"car_id": str(car.id), "make": car.make, "model": car.model})
        return car

    async def rent_car(self, car_id: UUID, data: RentRequest) -> Car:
        car = await self._repo.get_by_id(car_id)
        if not car:
            raise CarNotFoundError(car_id)
        if not car.is_available:
            logger.warning("rent_car unavailable", extra={"car_id": str(car_id)})
            raise CarNotAvailableError(car_id)
        car.is_available = False
        car.rented_by = data.renter_name
        await self._repo.update(car)
        record = RentalRecord(car_id=car_id, renter_name=data.renter_name)
        await self._repo.add_rental_record(record)
        logger.info("rent_car", extra={"car_id": str(car_id), "renter": data.renter_name})
        return car

    async def return_car(self, car_id: UUID) -> Car:
        car = await self._repo.get_by_id(car_id)
        if not car:
            raise CarNotFoundError(car_id)
        if car.is_available:
            logger.warning("return_car not rented", extra={"car_id": str(car_id)})
            raise CarNotRentedError(car_id)
        active = await self._repo.get_active_rental_for_car(car_id)
        if active:
            await self._repo.close_rental_record(active)
        car.is_available = True
        car.rented_by = None
        await self._repo.update(car)
        logger.info("return_car", extra={"car_id": str(car_id)})
        return car

    async def list_rental_records(self) -> list[RentalRecord]:
        return await self._repo.get_all_rental_records()
