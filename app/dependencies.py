from app.repositories.in_memory import InMemoryCarRepository
from app.services.car_service import CarService

_car_repo = InMemoryCarRepository()
_car_service = CarService(repo=_car_repo)


def get_car_service() -> CarService:
    return _car_service
