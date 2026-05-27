import pytest
from app.main import app
from app.repositories.in_memory import InMemoryCarRepository
from app.services.car_service import CarService
from app.dependencies import get_car_service


@pytest.fixture(autouse=True)
def reset_dependencies():
    """Give every test a clean, isolated repo and service instance."""
    fresh_repo = InMemoryCarRepository()
    fresh_service = CarService(repo=fresh_repo)
    app.dependency_overrides[get_car_service] = lambda: fresh_service
    yield
    app.dependency_overrides.clear()
