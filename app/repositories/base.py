from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from app.models.car import Car, RentalRecord


class CarRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[Car]: ...

    @abstractmethod
    async def get_by_id(self, car_id: UUID) -> Optional[Car]: ...

    @abstractmethod
    async def add(self, car: Car) -> Car: ...

    @abstractmethod
    async def update(self, car: Car) -> Car: ...

    @abstractmethod
    async def add_rental_record(self, record: RentalRecord) -> RentalRecord: ...

    @abstractmethod
    async def get_all_rental_records(self) -> list[RentalRecord]: ...

    @abstractmethod
    async def get_active_rental_for_car(self, car_id: UUID) -> Optional[RentalRecord]: ...

    @abstractmethod
    async def close_rental_record(self, record: RentalRecord) -> RentalRecord: ...
