import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def seeded_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/cars", json={"make": "Toyota", "model": "Camry", "year": 2022})
        await c.post("/cars", json={"make": "Toyota", "model": "Corolla", "year": 2021})
        await c.post("/cars", json={"make": "Honda", "model": "Civic", "year": 2021})
        yield c


def items(resp):
    """Helper: extract items list from paginated response."""
    return resp.json()["items"]


@pytest.mark.asyncio
async def test_filter_by_make(seeded_client):
    resp = await seeded_client.get("/cars?make=Toyota")
    assert resp.status_code == 200
    assert all(c["make"] == "Toyota" for c in items(resp))
    assert len(items(resp)) == 2


@pytest.mark.asyncio
async def test_filter_by_model(seeded_client):
    resp = await seeded_client.get("/cars?model=Civic")
    assert resp.status_code == 200
    assert all(c["model"] == "Civic" for c in items(resp))


@pytest.mark.asyncio
async def test_filter_by_year(seeded_client):
    resp = await seeded_client.get("/cars?year=2021")
    assert resp.status_code == 200
    assert all(c["year"] == 2021 for c in items(resp))
    assert len(items(resp)) == 2


@pytest.mark.asyncio
async def test_filter_by_available(seeded_client):
    first_id = items(await seeded_client.get("/cars"))[0]["id"]
    await seeded_client.post(f"/cars/{first_id}/rent", json={"renter_name": "Alice"})
    resp = await seeded_client.get("/cars?available=true")
    assert resp.status_code == 200
    assert all(c["is_available"] for c in items(resp))


@pytest.mark.asyncio
async def test_filter_by_unavailable(seeded_client):
    first_id = items(await seeded_client.get("/cars"))[0]["id"]
    await seeded_client.post(f"/cars/{first_id}/rent", json={"renter_name": "Bob"})
    resp = await seeded_client.get("/cars?available=false")
    assert resp.status_code == 200
    assert all(not c["is_available"] for c in items(resp))


@pytest.mark.asyncio
async def test_filter_combined(seeded_client):
    resp = await seeded_client.get("/cars?make=Toyota&year=2022")
    assert resp.status_code == 200
    assert len(items(resp)) == 1
    assert items(resp)[0]["model"] == "Camry"


@pytest.mark.asyncio
async def test_no_filter_returns_all(seeded_client):
    resp = await seeded_client.get("/cars")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3
