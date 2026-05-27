# TASKS.md — Car Rental Service

## Phase 1 — Core ✅
- [x] Project bootstrap (git init, requirements.txt, skeleton dirs)
- [x] `.gitignore`
- [x] Domain models: `Car`, `RentalRecord` (`app/models/car.py`)
- [x] Pydantic schemas: `CarCreate`, `RentRequest`, `CarResponse`, `RentalRecordResponse` (`app/models/schemas.py`)
- [x] Typed domain exceptions (`app/exceptions.py`)
- [x] `CarRepository` ABC (`app/repositories/base.py`)
- [x] `InMemoryCarRepository` with per-car `asyncio.Lock` (`app/repositories/in_memory.py`)
- [x] `CarService` with list, get, add, rent, return (`app/services/car_service.py`)
- [x] DI wiring (`app/dependencies.py`)
- [x] Cars router (`app/routers/cars.py`)
- [x] FastAPI app (`app/main.py`)
- [x] TDD: 8 tests passing (`tests/test_cars_crud.py`)
- [x] CLAUDE.md, TASKS.md, README.md, demo.sh

## Phase 2 — Filtering ✅
- [x] TDD: filter tests (`tests/test_filtering.py`) — 7 tests
- [x] Filter `GET /cars?make=&model=&year=&available=` verified
- [x] autouse fixture in `conftest.py` for isolated test state

## Phase 3 — Security ✅
- [x] TDD: security tests (`tests/test_security.py`) — 5 tests
- [x] Rate limiting via `slowapi` (5/min on rent endpoint, per IP)
- [x] CORS restricted to `ALLOWED_ORIGINS` env var
- [x] Input length caps on all string fields (max_length=100)
- [x] `limiter._storage.reset()` in autouse fixture prevents cross-test accumulation
- [x] `app/limiter.py` singleton avoids circular import with `app/main.py`

## Phase 4 — Interactive UI ✅
- [x] Vanilla HTML/CSS/JS at `/` via `FastAPI.StaticFiles` + `FileResponse`
- [x] Full happy path: add car, filter by make/model/year/availability, rent, return
- [x] Toast notifications for success and error states
- [x] XSS-safe rendering via `escHtml()` helper
- [x] 20/20 tests passing
