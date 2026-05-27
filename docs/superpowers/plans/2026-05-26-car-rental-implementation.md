# Car Rental Service — Implementation Plan

**Goal:** Build a FastAPI car rental service with in-memory storage, TDD, layered architecture, security hardening, and a vanilla HTML/JS UI.

**Architecture:** Routes → Services → Repositories (ABC). `app/dependencies.py` is the single wiring point. Domain exceptions bubble from services; routes convert them to HTTP responses.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, httpx, slowapi (rate limiting)

---

## File Map

```
car-rental/
├── app/
│   ├── main.py                          # FastAPI app factory, mounts router + static files
│   ├── dependencies.py                  # Single DI wiring point
│   ├── exceptions.py                    # Typed domain exceptions
│   ├── models/
│   │   ├── car.py                       # Car + RentalRecord domain models
│   │   └── schemas.py                   # Pydantic request/response DTOs
│   ├── repositories/
│   │   ├── base.py                      # CarRepository ABC
│   │   └── in_memory.py                 # InMemoryCarRepository
│   ├── services/
│   │   └── car_service.py               # Business logic, raises domain exceptions
│   └── routers/
│       └── cars.py                      # HTTP endpoints, catches domain exceptions
├── static/
│   └── index.html                       # Vanilla HTML/CSS/JS UI (Phase 4)
├── tests/
│   ├── conftest.py                      # Shared fixtures
│   ├── test_cars_crud.py                # Phase 1 tests
│   ├── test_filtering.py                # Phase 2 tests
│   ├── test_security.py                 # Phase 3 tests
│   └── test_ui.py                       # Phase 4 smoke test
├── CLAUDE.md
├── TASKS.md
├── README.md
├── demo.sh
└── requirements.txt
```

---

## Phase 1 — Core (branch: `feat/phase-1-core`)

### Task 1: Project bootstrap

- [ ] Create repo directory and init git
```bash
cd "/Users/tejuschandrashekar/Desktop/Car rental system"
git init
git checkout -b main
```

- [ ] Create `requirements.txt`
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.1
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.6
slowapi==0.1.9
```

- [ ] Install dependencies
```bash
pip install -r requirements.txt
```

- [ ] Create skeleton directories
```bash
mkdir -p app/models app/repositories app/services app/routers static tests
touch app/__init__.py app/models/__init__.py app/repositories/__init__.py
touch app/services/__init__.py app/routers/__init__.py tests/__init__.py
```

- [ ] Commit
```bash
git add .
git commit -m "chore: project bootstrap"
```

---

### Task 2: Domain models

- [ ] Create `app/exceptions.py`
```python
class CarNotFoundError(Exception):
    def __init__(self, car_id):
        self.car_id = car_id

class CarNotAvailableError(Exception):
    def __init__(self, car_id):
        self.car_id = car_id

class CarNotRentedError(Exception):
    def __init__(self, car_id):
        self.car_id = car_id
```

- [ ] Create `app/models/car.py`
```python
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Car(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    make: str
    model: str
    year: int
    is_available: bool = True
    rented_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

class RentalRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    car_id: UUID
    renter_name: str
    rented_at: datetime = Field(default_factory=utcnow)
    returned_at: Optional[datetime] = None
```

- [ ] Create `app/models/schemas.py`
```python
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CarCreate(BaseModel):
    make: str = Field(max_length=100)
    model: str = Field(max_length=100)
    year: int

class RentRequest(BaseModel):
    renter_name: str = Field(max_length=100)

class CarResponse(BaseModel):
    id: UUID
    make: str
    model: str
    year: int
    is_available: bool
    rented_by: Optional[str]
    created_at: datetime
    updated_at: datetime

class RentalRecordResponse(BaseModel):
    id: UUID
    car_id: UUID
    renter_name: str
    rented_at: datetime
    returned_at: Optional[datetime]
```

- [ ] Commit
```bash
git add app/exceptions.py app/models/
git commit -m "feat: domain models and exceptions"
```

---

### Task 3: Repository ABC

- [ ] Create `app/repositories/base.py`
```python
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
```

- [ ] Create `app/repositories/in_memory.py`
```python
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
            None
        )

    async def close_rental_record(self, record: RentalRecord) -> RentalRecord:
        record.returned_at = datetime.now(timezone.utc)
        self._rentals[record.id] = record
        return record
```

- [ ] Commit
```bash
git add app/repositories/
git commit -m "feat: repository ABC and in-memory implementation"
```

---

### Task 4: Car service (TDD)

- [ ] Write failing tests first — `tests/test_cars_crud.py`
```python
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
```

- [ ] Run tests — expect all to fail (app not built yet)
```bash
pytest tests/test_cars_crud.py -v
```
Expected: ImportError or collection errors.

- [ ] Create `app/services/car_service.py`
```python
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

    async def list_cars(self, make: Optional[str] = None, model: Optional[str] = None,
                        year: Optional[int] = None, available: Optional[bool] = None) -> list[Car]:
        cars = await self._repo.get_all()
        if make:
            cars = [c for c in cars if c.make.lower() == make.lower()]
        if model:
            cars = [c for c in cars if c.model.lower() == model.lower()]
        if year:
            cars = [c for c in cars if c.year == year]
        if available is not None:
            cars = [c for c in cars if c.is_available == available]
        logger.info("list_cars", extra={"count": len(cars), "filters": {"make": make, "model": model, "year": year, "available": available}})
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
```

- [ ] Create `app/dependencies.py`
```python
from app.repositories.in_memory import InMemoryCarRepository
from app.services.car_service import CarService

_car_repo = InMemoryCarRepository()
_car_service = CarService(repo=_car_repo)

def get_car_service() -> CarService:
    return _car_service
```

- [ ] Create `app/routers/cars.py`
```python
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import CarCreate, RentRequest, CarResponse, RentalRecordResponse
from app.services.car_service import CarService
from app.dependencies import get_car_service
from app.exceptions import CarNotFoundError, CarNotAvailableError, CarNotRentedError

router = APIRouter(prefix="/cars", tags=["cars"])

# /cars/rentals MUST be defined before /cars/{car_id} to avoid UUID parse conflict
@router.get("/rentals", response_model=list[RentalRecordResponse])
async def list_rentals(service: CarService = Depends(get_car_service)):
    return await service.list_rental_records()

@router.get("", response_model=list[CarResponse])
async def list_cars(
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    available: Optional[bool] = None,
    service: CarService = Depends(get_car_service),
):
    return await service.list_cars(make=make, model=model, year=year, available=available)

@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car_id: UUID, service: CarService = Depends(get_car_service)):
    try:
        return await service.get_car(car_id)
    except CarNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")

@router.post("", response_model=CarResponse)
async def add_car(data: CarCreate, service: CarService = Depends(get_car_service)):
    return await service.add_car(data)

@router.post("/{car_id}/rent", response_model=CarResponse)
async def rent_car(car_id: UUID, data: RentRequest, service: CarService = Depends(get_car_service)):
    try:
        return await service.rent_car(car_id, data)
    except CarNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    except CarNotAvailableError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Car is already rented")

@router.post("/{car_id}/return", response_model=CarResponse)
async def return_car(car_id: UUID, service: CarService = Depends(get_car_service)):
    try:
        return await service.return_car(car_id)
    except CarNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    except CarNotRentedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Car is not currently rented")
```

- [ ] Create `app/main.py`
```python
import logging
from fastapi import FastAPI
from app.routers.cars import router as cars_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Car Rental Service", version="1.0.0")
app.include_router(cars_router)
```

- [ ] Create `tests/conftest.py`
```python
import pytest

pytest_plugins = ["pytest_asyncio"]
```

- [ ] Create `pytest.ini`
```ini
[pytest]
asyncio_mode = auto
```

- [ ] Run tests — expect all to pass
```bash
pytest tests/test_cars_crud.py -v
```
Expected: All PASS.

- [ ] Commit
```bash
git add app/ tests/ pytest.ini
git commit -m "feat: phase 1 — core car CRUD, rent, return with TDD"
```

---

### Task 5: Bootstrap files (CLAUDE.md, TASKS.md, README.md, demo.sh)

- [ ] Create `CLAUDE.md` (memory bank)
```markdown
# CLAUDE.md — Car Rental Service

## Project Snapshot
- Stack: Python 3.11+, FastAPI, Pydantic v2, pytest, httpx, slowapi
- Storage: In-memory (InMemoryCarRepository implements CarRepository ABC)
- Auth: None (anonymous — renter_name in request body)
- Run: uvicorn app.main:app --reload

## Architecture Layer Rules
- Routes → Services → Repositories. No layer may skip a level.
- Services never import fastapi. They raise domain exceptions only.
- Repositories contain no business logic — pure data access.
- app/dependencies.py is the ONLY place repos/services are instantiated.

## Critical File Map
| File | Owns |
|---|---|
| app/main.py | App factory, mounts router |
| app/dependencies.py | DI wiring — single source of truth |
| app/exceptions.py | Typed domain exceptions |
| app/models/car.py | Car + RentalRecord domain models |
| app/models/schemas.py | Pydantic request/response DTOs |
| app/repositories/base.py | CarRepository ABC |
| app/repositories/in_memory.py | In-memory implementation |
| app/services/car_service.py | Business logic |
| app/routers/cars.py | HTTP endpoints |

## Key Patterns
- DI: Depends(get_car_service) in every route — never instantiate in route files
- Exceptions: raise CarNotFoundError in service → catch in route → HTTPException
- Concurrency: per-car asyncio.Lock in InMemoryCarRepository.update()
- Route order: /cars/rentals before /cars/{car_id} to avoid UUID parse conflict

## Gotchas
| Symptom | Cause | Fix |
|---|---|---|
| GET /cars/rentals returns 422 | "rentals" matched as UUID | Define /cars/rentals before /cars/{car_id} |
| Items invisible across routes | Multiple repo instances | Wire through dependencies.py only |
| Double-booking under load | No lock on availability check | Per-car asyncio.Lock in update() |
```

- [ ] Create `TASKS.md`
```markdown
# TASKS.md

## Phase 1 — Core ✅
- [x] Project bootstrap
- [x] Domain models (Car, RentalRecord, schemas)
- [x] Repository ABC + in-memory implementation
- [x] CarService (list, get, add, rent, return)
- [x] Cars router
- [x] Tests passing

## Phase 2 — Filtering 🔲
- [ ] Filter GET /cars by make, model, year, available

## Phase 3 — Security 🔲
- [ ] Rate limiting (slowapi)
- [ ] CORS (configured origins)
- [ ] Input length caps (already on schemas)

## Phase 4 — UI 🔲
- [ ] Vanilla HTML/CSS/JS at /
```

- [ ] Create `README.md` (initial)
```markdown
# Car Rental Service

A FastAPI-based car rental service. Browse, filter, rent, and return cars.

## Table of Contents
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [How to Run](#how-to-run)
- [API Reference](#api-reference)
- [Architecture](#architecture)
- [Phases](#phases)

## Tech Stack
Python 3.11+ · FastAPI · Pydantic v2 · pytest · httpx · slowapi

## Project Structure
```
app/
  main.py         # App factory
  dependencies.py # DI wiring
  exceptions.py   # Domain exceptions
  models/         # Domain models + schemas
  repositories/   # ABC + in-memory impl
  services/       # Business logic
  routers/        # HTTP endpoints
tests/
static/           # UI (Phase 4)
```

## Getting Started
```bash
pip install -r requirements.txt
```

## How to Run
```bash
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs
```

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | /cars | List all cars (filterable) |
| GET | /cars/{id} | Get a car |
| POST | /cars | Add a car |
| POST | /cars/{id}/rent | Rent a car |
| POST | /cars/{id}/return | Return a car |
| GET | /cars/rentals | List all rental records |

## Architecture
```
Routes → Services → Repositories (ABC)
app/dependencies.py — single DI wiring point
```

## Phases
| Phase | Status | Scope |
|---|---|---|
| 1 | ✅ | Core CRUD, rent, return |
| 2 | 🔲 | Filtering |
| 3 | 🔲 | Security hardening |
| 4 | 🔲 | Interactive UI |
```

- [ ] Create `demo.sh`
```bash
#!/usr/bin/env bash
set -e
BASE="http://localhost:8000"

echo "=== Add cars ==="
CAR1=$(curl -s -X POST "$BASE/cars" -H "Content-Type: application/json" \
  -d '{"make":"Toyota","model":"Camry","year":2022}')
CAR2=$(curl -s -X POST "$BASE/cars" -H "Content-Type: application/json" \
  -d '{"make":"Honda","model":"Civic","year":2021}')
echo "$CAR1" | python3 -m json.tool
echo "$CAR2" | python3 -m json.tool

ID1=$(echo "$CAR1" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "=== List cars ==="
curl -s "$BASE/cars" | python3 -m json.tool

echo "=== Rent car ==="
curl -s -X POST "$BASE/cars/$ID1/rent" -H "Content-Type: application/json" \
  -d '{"renter_name":"Alice"}' | python3 -m json.tool

echo "=== Try double-rent (expect 409) ==="
curl -s -X POST "$BASE/cars/$ID1/rent" -H "Content-Type: application/json" \
  -d '{"renter_name":"Bob"}' | python3 -m json.tool

echo "=== Return car ==="
curl -s -X POST "$BASE/cars/$ID1/return" | python3 -m json.tool

echo "=== Rental records ==="
curl -s "$BASE/cars/rentals" | python3 -m json.tool
```

- [ ] Make demo.sh executable
```bash
chmod +x demo.sh
```

- [ ] Commit
```bash
git add CLAUDE.md TASKS.md README.md demo.sh
git commit -m "chore: add CLAUDE.md, TASKS.md, README, demo.sh"
```

---

### Task 6: Push Phase 1 PR

- [ ] Push branch and open PR
```bash
git checkout -b feat/phase-1-core
git push -u origin feat/phase-1-core
gh pr create --title "feat: phase 1 — core car rental service" --body "$(cat <<'EOF'
## Summary
- Car domain model (make, model, year, is_available, rented_by) with RentalRecord history
- In-memory repository implementing CarRepository ABC (DB-ready interface)
- CarService with list, get, add, rent, return — typed domain exceptions throughout
- FastAPI router with full CRUD + rent/return + rental history endpoints
- TDD: all tests passing
- Bootstrap files: CLAUDE.md, TASKS.md, README.md, demo.sh

## Test plan
- [ ] `pytest tests/test_cars_crud.py -v` — all pass
- [ ] `uvicorn app.main:app --reload` starts cleanly
- [ ] `bash demo.sh` runs full happy path
EOF
)"
```

- [ ] Wait for PR approval before proceeding to Phase 2.

---

## Phase 2 — Filtering (branch: `feat/phase-2-filtering`)

### Task 7: Filtering tests and implementation

- [ ] Write failing tests — `tests/test_filtering.py`
```python
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

@pytest.mark.asyncio
async def test_filter_by_make(seeded_client):
    resp = await seeded_client.get("/cars?make=Toyota")
    assert resp.status_code == 200
    assert all(c["make"] == "Toyota" for c in resp.json())
    assert len(resp.json()) == 2

@pytest.mark.asyncio
async def test_filter_by_model(seeded_client):
    resp = await seeded_client.get("/cars?model=Civic")
    assert resp.status_code == 200
    assert all(c["model"] == "Civic" for c in resp.json())

@pytest.mark.asyncio
async def test_filter_by_year(seeded_client):
    resp = await seeded_client.get("/cars?year=2021")
    assert resp.status_code == 200
    assert all(c["year"] == 2021 for c in resp.json())
    assert len(resp.json()) == 2

@pytest.mark.asyncio
async def test_filter_by_available(seeded_client):
    cars = (await seeded_client.get("/cars")).json()
    await seeded_client.post(f"/cars/{cars[0]['id']}/rent", json={"renter_name": "Alice"})
    resp = await seeded_client.get("/cars?available=true")
    assert all(c["is_available"] for c in resp.json())

@pytest.mark.asyncio
async def test_filter_combined(seeded_client):
    resp = await seeded_client.get("/cars?make=Toyota&year=2022")
    assert len(resp.json()) == 1
    assert resp.json()[0]["model"] == "Camry"
```

- [ ] Run tests — expect fail
```bash
pytest tests/test_filtering.py -v
```

- [ ] Filtering logic is already in `CarService.list_cars()` from Phase 1. Run tests again:
```bash
pytest tests/test_filtering.py -v
```
Expected: All PASS (filtering was implemented in the service in Phase 1).

- [ ] Update `TASKS.md` — mark Phase 2 done, update `README.md` to note filtering query params, update `CLAUDE.md` if any new patterns.

- [ ] Commit
```bash
git add tests/test_filtering.py TASKS.md README.md
git commit -m "feat: phase 2 — filtering tests verified"
```

- [ ] Push and open PR
```bash
git checkout -b feat/phase-2-filtering
git push -u origin feat/phase-2-filtering
gh pr create --title "feat: phase 2 — car filtering by make, model, year, availability" --body "$(cat <<'EOF'
## Summary
- Verified filtering on GET /cars via query params: make, model, year, available
- Combined filters work (AND logic)
- TDD: all filter tests passing

## Test plan
- [ ] `pytest tests/test_filtering.py -v` — all pass
- [ ] `curl "http://localhost:8000/cars?make=Toyota&available=true"` returns filtered results
EOF
)"
```

- [ ] Wait for PR approval before Phase 3.

---

## Phase 3 — Security (branch: `feat/phase-3-security`)

### Task 8: Rate limiting and CORS

- [ ] Write failing tests — `tests/test_security.py`
```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_rate_limit_on_rent():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        car = (await c.post("/cars", json={"make": "Test", "model": "Car", "year": 2020})).json()
        responses = []
        for _ in range(6):
            resp = await c.post(f"/cars/{car['id']}/rent", json={"renter_name": "Tester"})
            responses.append(resp.status_code)
            # Return between attempts so we're testing rate limit not 409
            await c.post(f"/cars/{car['id']}/return")
        assert 429 in responses

@pytest.mark.asyncio
async def test_input_length_cap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/cars", json={"make": "A" * 101, "model": "B", "year": 2020})
        assert resp.status_code == 422

@pytest.mark.asyncio
async def test_renter_name_length_cap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        car = (await c.post("/cars", json={"make": "Test", "model": "Car", "year": 2020})).json()
        resp = await c.post(f"/cars/{car['id']}/rent", json={"renter_name": "A" * 101})
        assert resp.status_code == 422
```

- [ ] Run tests — expect fail
```bash
pytest tests/test_security.py -v
```

- [ ] Update `app/main.py` to add rate limiting and CORS
```python
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers.cars import router as cars_router

logging.basicConfig(level=logging.INFO)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Car Rental Service", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cars_router)
```

- [ ] Update `app/routers/cars.py` — add rate limit decorator to write endpoints
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

# Add to rent endpoint:
@router.post("/{car_id}/rent", response_model=CarResponse)
@limiter.limit("5/minute")
async def rent_car(request: Request, car_id: UUID, data: RentRequest, service: CarService = Depends(get_car_service)):
    try:
        return await service.rent_car(car_id, data)
    except CarNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    except CarNotAvailableError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Car is already rented")

# Add to return endpoint:
@router.post("/{car_id}/return", response_model=CarResponse)
@limiter.limit("5/minute")
async def return_car(request: Request, car_id: UUID, service: CarService = Depends(get_car_service)):
    try:
        return await service.return_car(car_id)
    except CarNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    except CarNotRentedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Car is not currently rented")
```

- [ ] Run tests
```bash
pytest tests/test_security.py -v
```
Expected: All PASS.

- [ ] Run all tests to check for regressions
```bash
pytest -v
```

- [ ] Update TASKS.md, CLAUDE.md, README.md with security details.

- [ ] Commit and open PR
```bash
git add app/ tests/test_security.py TASKS.md CLAUDE.md README.md
git commit -m "feat: phase 3 — rate limiting, CORS, input length caps"
git checkout -b feat/phase-3-security
git push -u origin feat/phase-3-security
gh pr create --title "feat: phase 3 — security hardening" --body "$(cat <<'EOF'
## Summary
- Rate limiting on POST /cars/{id}/rent and POST /cars/{id}/return (5/min per IP via slowapi)
- CORS restricted to ALLOWED_ORIGINS env var (defaults to localhost)
- Input length caps: all string fields max 100 chars via Pydantic Field(max_length=100)
- TDD: all security tests passing, no regressions

## Test plan
- [ ] `pytest tests/test_security.py -v` — all pass
- [ ] `pytest -v` — full suite passes
EOF
)"
```

- [ ] Wait for PR approval before Phase 4.

---

## Phase 4 — Interactive UI (branch: `feat/phase-4-ui`)

### Task 9: Vanilla HTML/CSS/JS UI

- [ ] Create `static/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Car Rental Service</title>
  <style>
    body { font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }
    h1 { color: #2c3e50; }
    h2 { color: #34495e; border-bottom: 1px solid #ddd; padding-bottom: 8px; }
    .card { background: white; border-radius: 8px; padding: 16px; margin: 12px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
    .car-info { flex: 1; }
    .badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }
    .available { background: #d5f5e3; color: #1e8449; }
    .rented { background: #fde8e8; color: #c0392b; }
    button { padding: 8px 14px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; margin-left: 6px; }
    .btn-rent { background: #2980b9; color: white; }
    .btn-return { background: #27ae60; color: white; }
    .btn-rent:disabled, .btn-return:disabled { opacity: 0.4; cursor: not-allowed; }
    form { background: white; padding: 16px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); display: flex; gap: 8px; flex-wrap: wrap; }
    input { padding: 8px; border: 1px solid #ccc; border-radius: 6px; font-size: 0.9em; }
    .btn-add { background: #8e44ad; color: white; }
    #filters { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    #filters input { padding: 6px; border: 1px solid #ccc; border-radius: 6px; }
    #msg { color: #e74c3c; margin: 8px 0; min-height: 20px; }
  </style>
</head>
<body>
  <h1>Car Rental Service</h1>

  <h2>Add a Car</h2>
  <form id="addForm">
    <input id="make" placeholder="Make" maxlength="100" required>
    <input id="model" placeholder="Model" maxlength="100" required>
    <input id="year" type="number" placeholder="Year" required>
    <button type="submit" class="btn-add">Add Car</button>
  </form>

  <h2>Available Cars</h2>
  <div id="filters">
    <input id="fMake" placeholder="Filter: Make">
    <input id="fModel" placeholder="Filter: Model">
    <input id="fYear" type="number" placeholder="Filter: Year">
    <select id="fAvail">
      <option value="">All</option>
      <option value="true">Available</option>
      <option value="false">Rented</option>
    </select>
    <button onclick="loadCars()" style="background:#7f8c8d;color:white;">Filter</button>
  </div>
  <div id="msg"></div>
  <div id="carList"></div>

  <script>
    const BASE = "";

    async function loadCars() {
      const params = new URLSearchParams();
      const make = document.getElementById("fMake").value.trim();
      const model = document.getElementById("fModel").value.trim();
      const year = document.getElementById("fYear").value.trim();
      const avail = document.getElementById("fAvail").value;
      if (make) params.set("make", make);
      if (model) params.set("model", model);
      if (year) params.set("year", year);
      if (avail !== "") params.set("available", avail);

      const resp = await fetch(`${BASE}/cars?${params}`);
      const cars = await resp.json();
      const list = document.getElementById("carList");
      list.innerHTML = cars.length === 0 ? "<p>No cars found.</p>" : "";
      cars.forEach(car => {
        const div = document.createElement("div");
        div.className = "card";
        div.innerHTML = `
          <div class="car-info">
            <strong>${car.make} ${car.model} (${car.year})</strong>
            <span class="badge ${car.is_available ? 'available' : 'rented'}">
              ${car.is_available ? "Available" : "Rented by " + car.rented_by}
            </span>
          </div>
          <div>
            <button class="btn-rent" ${car.is_available ? "" : "disabled"}
              onclick="rentCar('${car.id}')">Rent</button>
            <button class="btn-return" ${!car.is_available ? "" : "disabled"}
              onclick="returnCar('${car.id}')">Return</button>
          </div>`;
        list.appendChild(div);
      });
    }

    async function rentCar(id) {
      const name = prompt("Enter your name to rent:");
      if (!name || !name.trim()) return;
      const resp = await fetch(`${BASE}/cars/${id}/rent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ renter_name: name.trim() })
      });
      const data = await resp.json();
      document.getElementById("msg").textContent = resp.ok
        ? `Rented to ${data.rented_by}` : data.detail;
      loadCars();
    }

    async function returnCar(id) {
      const resp = await fetch(`${BASE}/cars/${id}/return`, { method: "POST" });
      const data = await resp.json();
      document.getElementById("msg").textContent = resp.ok ? "Car returned." : data.detail;
      loadCars();
    }

    document.getElementById("addForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const resp = await fetch(`${BASE}/cars`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          make: document.getElementById("make").value,
          model: document.getElementById("model").value,
          year: parseInt(document.getElementById("year").value)
        })
      });
      const data = await resp.json();
      document.getElementById("msg").textContent = resp.ok ? `Added: ${data.make} ${data.model}` : data.detail;
      document.getElementById("addForm").reset();
      loadCars();
    });

    loadCars();
  </script>
</body>
</html>
```

- [ ] Mount static files in `app/main.py`
```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Add after app.include_router(cars_router):
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def ui():
    return FileResponse(os.path.join(static_dir, "index.html"))
```

- [ ] Run the server and verify UI works
```bash
uvicorn app.main:app --reload
# Open http://localhost:8000
```

- [ ] Run full test suite
```bash
pytest -v
```

- [ ] Update TASKS.md (all phases done), README.md (add Interactive UI section and Clean Run Process), CLAUDE.md.

- [ ] Commit and open PR
```bash
git add static/ app/main.py TASKS.md CLAUDE.md README.md
git commit -m "feat: phase 4 — interactive UI served at /"
git checkout -b feat/phase-4-ui
git push -u origin feat/phase-4-ui
gh pr create --title "feat: phase 4 — interactive UI" --body "$(cat <<'EOF'
## Summary
- Vanilla HTML/CSS/JS UI served at / via FastAPI StaticFiles + FileResponse
- Full happy path: add car, filter by make/model/year/availability, rent (with name prompt), return
- No framework, no build step, no npm — opens directly in browser
- All existing tests still passing

## Test plan
- [ ] `pytest -v` — full suite passes
- [ ] Open http://localhost:8000 — UI loads
- [ ] Add a car, rent it, return it — all work
- [ ] Filter by make/availability — results update
EOF
)"
```

- [ ] Wait for PR approval — then merge to main.
