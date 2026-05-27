# CLAUDE.md — Car Rental Service

## Project Snapshot
- **Stack:** Python 3.9+, FastAPI, Pydantic v2, pytest, httpx, slowapi
- **Storage:** In-memory (`InMemoryCarRepository` implements `CarRepository` ABC)
- **Auth:** None — anonymous rental; renter_name passed in request body
- **Run:** `uvicorn app.main:app --reload`
- **Test:** `python3 -m pytest -v`

## Architecture Layer Rules
| Layer | File | Rule |
|---|---|---|
| Routes | `app/routers/cars.py` | Validates HTTP, calls service, catches domain exceptions → HTTPException. Never imports repo directly. |
| Services | `app/services/car_service.py` | Business logic only. Raises domain exceptions. Never imports `fastapi`. |
| Repositories | `app/repositories/` | Pure data access. No business logic. |
| DI wiring | `app/dependencies.py` | **Single source of truth** — only place repos and services are instantiated. |

## Critical File Map
| File | Owns |
|---|---|
| `app/main.py` | FastAPI app factory; mounts router; logging config |
| `app/dependencies.py` | DI wiring — `get_car_service()` used by all routes |
| `app/exceptions.py` | `CarNotFoundError`, `CarNotAvailableError`, `CarNotRentedError` |
| `app/models/car.py` | `Car` + `RentalRecord` domain models |
| `app/models/schemas.py` | Pydantic DTOs: `CarCreate`, `RentRequest`, `CarResponse`, `RentalRecordResponse` |
| `app/repositories/base.py` | `CarRepository` ABC — all method signatures |
| `app/repositories/in_memory.py` | `InMemoryCarRepository` — per-car `asyncio.Lock` for concurrency |
| `app/services/car_service.py` | All business logic: list, get, add, rent, return |
| `app/routers/cars.py` | All HTTP endpoints |
| `static/index.html` | Vanilla UI (Phase 4) |

## Key Patterns
- **DI:** `Depends(get_car_service)` in every route — never instantiate in route files
- **Exception flow:** raise `CarNotFoundError` in service → catch in route → `HTTPException(404)`
- **Concurrency:** `asyncio.Lock` per car in `InMemoryCarRepository._get_lock()` — acquired in `update()`
- **Route order:** `/cars/rentals` defined **before** `/cars/{car_id}` — prevents UUID parse error on "rentals"
- **Filtering:** All filter logic lives in `CarService.list_cars()` — service layer, not route
- **Timestamps:** All models use `utcnow()` from `app/models/car.py` — always UTC

## Gotchas
| Symptom | Cause | Fix |
|---|---|---|
| `GET /cars/rentals` returns 422 | `"rentals"` matched as UUID path param | Define `/cars/rentals` before `/cars/{car_id}` in router |
| Items created via one endpoint invisible elsewhere | Multiple repo instances in different routes | Always wire through `dependencies.py`; never instantiate in route files |
| Double-booking under concurrent load | Two requests read `is_available=True` before either writes | Per-car `asyncio.Lock` in `InMemoryCarRepository.update()` |
| Rate limiter accumulates between tests | Shared state in `slowapi` limiter | Add autouse fixture in `conftest.py` to reset limiter between tests (Phase 3) |

## Phase Status
| Phase | Branch | Status |
|---|---|---|
| 1 — Core CRUD + rent/return | `feat/phase-1-core` | ✅ Complete |
| 2 — Filtering | `feat/phase-2-filtering` | 🔲 Pending |
| 3 — Security hardening | `feat/phase-3-security` | 🔲 Pending |
| 4 — Interactive UI | `feat/phase-4-ui` | 🔲 Pending |
