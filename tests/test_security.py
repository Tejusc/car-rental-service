import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_input_make_length_cap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/cars", json={"make": "A" * 101, "model": "B", "year": 2020})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_input_model_length_cap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/cars", json={"make": "A", "model": "B" * 101, "year": 2020})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_renter_name_length_cap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        car = (await c.post("/cars", json={"make": "Test", "model": "Car", "year": 2020})).json()
        resp = await c.post(f"/cars/{car['id']}/rent", json={"renter_name": "A" * 101})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_rate_limit_on_rent():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        car = (await c.post("/cars", json={"make": "Test", "model": "RateTest", "year": 2020})).json()
        statuses = []
        for _ in range(7):
            r = await c.post(f"/cars/{car['id']}/rent", json={"renter_name": "Tester"})
            statuses.append(r.status_code)
            if r.status_code == 200:
                await c.post(f"/cars/{car['id']}/return")
        assert 429 in statuses


@pytest.mark.asyncio
async def test_cors_header_present():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.options(
            "/cars",
            headers={"Origin": "http://localhost:8000", "Access-Control-Request-Method": "GET"},
        )
        assert "access-control-allow-origin" in resp.headers
