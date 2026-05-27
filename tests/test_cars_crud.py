import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_add_car(client):
    resp = await client.post("/cars", json={"make": "Toyota", "model": "Camry", "year": 2022})
    assert resp.status_code == 200
    data = resp.json()
    assert data["make"] == "Toyota"
    assert data["is_available"] is True


@pytest.mark.asyncio
async def test_list_cars(client):
    await client.post("/cars", json={"make": "Honda", "model": "Civic", "year": 2021})
    resp = await client.get("/cars")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_car_not_found(client):
    resp = await client.get(f"/cars/{uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rent_car(client):
    car = (await client.post("/cars", json={"make": "Ford", "model": "Focus", "year": 2020})).json()
    resp = await client.post(f"/cars/{car['id']}/rent", json={"renter_name": "Alice"})
    assert resp.status_code == 200
    assert resp.json()["is_available"] is False
    assert resp.json()["rented_by"] == "Alice"


@pytest.mark.asyncio
async def test_rent_unavailable_car(client):
    car = (await client.post("/cars", json={"make": "BMW", "model": "3 Series", "year": 2023})).json()
    await client.post(f"/cars/{car['id']}/rent", json={"renter_name": "Alice"})
    resp = await client.post(f"/cars/{car['id']}/rent", json={"renter_name": "Bob"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_return_car(client):
    car = (await client.post("/cars", json={"make": "Audi", "model": "A4", "year": 2022})).json()
    await client.post(f"/cars/{car['id']}/rent", json={"renter_name": "Alice"})
    resp = await client.post(f"/cars/{car['id']}/return")
    assert resp.status_code == 200
    assert resp.json()["is_available"] is True
    assert resp.json()["rented_by"] is None


@pytest.mark.asyncio
async def test_return_available_car(client):
    car = (await client.post("/cars", json={"make": "Kia", "model": "Stinger", "year": 2021})).json()
    resp = await client.post(f"/cars/{car['id']}/return")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_rental_records(client):
    car = (await client.post("/cars", json={"make": "Mazda", "model": "3", "year": 2022})).json()
    await client.post(f"/cars/{car['id']}/rent", json={"renter_name": "Charlie"})
    resp = await client.get("/cars/rentals")
    assert resp.status_code == 200
    assert any(r["car_id"] == car["id"] for r in resp.json())
