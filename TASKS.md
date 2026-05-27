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

## Phase 2 — Filtering 🔲
- [ ] TDD: filter tests (`tests/test_filtering.py`)
- [ ] Verify `GET /cars?make=&model=&year=&available=` works
- [ ] Update README, TASKS.md, CLAUDE.md

## Phase 3 — Security 🔲
- [ ] TDD: security tests (`tests/test_security.py`)
- [ ] Rate limiting via `slowapi` (5/min on write endpoints)
- [ ] CORS restricted to `ALLOWED_ORIGINS` env var
- [ ] Input length caps — already in Pydantic schemas (max_length=100)
- [ ] autouse fixture to reset rate limiter between tests
- [ ] Update README, TASKS.md, CLAUDE.md

## Phase 4 — Interactive UI 🔲
- [ ] Vanilla HTML/CSS/JS at `/` via `FastAPI.StaticFiles`
- [ ] Full happy path: add car, filter, rent, return
- [ ] Mount static files in `app/main.py`
- [ ] Update README, TASKS.md, CLAUDE.md
