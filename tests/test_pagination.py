import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def seeded_client():
    """Client pre-loaded with 25 cars."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for i in range(25):
            await c.post("/cars", json={"make": "Toyota", "model": f"Model{i}", "year": 2020 + (i % 5)})
        yield c


@pytest.mark.asyncio
async def test_default_page_size_is_20(seeded_client):
    resp = await seeded_client.get("/cars")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) == 20
    assert data["total"] == 25
    assert data["total_pages"] == 2


@pytest.mark.asyncio
async def test_second_page_has_remaining(seeded_client):
    resp = await seeded_client.get("/cars?page=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_page_size_30(seeded_client):
    resp = await seeded_client.get("/cars?page_size=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page_size"] == 30
    assert len(data["items"]) == 25
    assert data["total_pages"] == 1


@pytest.mark.asyncio
async def test_page_size_50(seeded_client):
    resp = await seeded_client.get("/cars?page_size=50")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page_size"] == 50
    assert len(data["items"]) == 25


@pytest.mark.asyncio
async def test_pagination_with_filter(seeded_client):
    # All 25 are Toyota — filter + paginate
    resp = await seeded_client.get("/cars?make=Toyota&page_size=10&page=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 25
    assert len(data["items"]) == 10
    assert data["page"] == 2
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_out_of_range_page_returns_empty(seeded_client):
    resp = await seeded_client.get("/cars?page=99")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["page"] == 99


@pytest.mark.asyncio
async def test_response_shape(seeded_client):
    resp = await seeded_client.get("/cars")
    data = resp.json()
    assert all(k in data for k in ("items", "total", "page", "page_size", "total_pages"))
