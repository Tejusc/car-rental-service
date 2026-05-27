# Car Rental Service — Design Spec
**Date:** 2026-05-26  
**Status:** Approved

---

## 1. Overview

A FastAPI-based car rental service. Users (anonymous) can browse available cars, filter them by attributes, rent a car, and return it. Storage is in-memory with a DB-ready repository interface.

---

## 2. Stack & Constraints

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| Storage | In-memory (ABC-backed, DB-ready) |
| Auth | None (anonymous rental — renter name in request body) |
| Testing | pytest + httpx (TDD — tests written before implementation) |
| UI | Vanilla HTML/CSS/JS served via FastAPI StaticFiles at `/` |

---

## 3. Phases

| Phase | Branch | Scope |
|---|---|---|
| 1 | `feat/phase-1-core` | Car model, in-memory repo, CRUD endpoints, rent, return |
| 2 | `feat/phase-2-filtering` | Filter `GET /cars` by make, model, year, availability |
| 3 | `feat/phase-3-security` | Rate limiting, CORS, input length caps |
| 4 | `feat/phase-4-ui` | Vanilla HTML/CSS/JS at `/`, full happy path coverage |

Security before UI. UI is always last.

---

## 4. Architecture Layers

```
HTTP Request
     │
     ▼
┌─────────────┐
│   Routes    │  app/routers/cars.py
│             │  — validates HTTP, calls service, maps domain exceptions → HTTPException
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Services   │  app/services/car_service.py
│             │  — business logic only; raises typed domain exceptions; no FastAPI imports
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Repository  │  app/repositories/base.py  (ABC — CarRepository)
│    ABC      │  app/repositories/in_memory.py  (InMemoryCarRepository)
└─────────────┘
```

**Layer rules:**
- Routes → Services → Repositories. No layer may skip a level.
- Services never import `fastapi` — they raise domain exceptions only.
- Repositories contain no business logic — pure data access.
- `app/dependencies.py` is the **only** place repos and services are instantiated.

---

## 5. Data Models

### Car (domain model)

| Field | Type | Notes |
|---|---|---|
| `id` | `UUID` | Generated on creation |
| `make` | `str` | Max 100 chars |
| `model` | `str` | Max 100 chars |
| `year` | `int` | e.g. 2022 |
| `is_available` | `bool` | `True` on creation; flips on rent/return |
| `rented_by` | `Optional[str]` | Renter name; `None` when available; max 100 chars |
| `created_at` | `datetime` | UTC, set on creation |
| `updated_at` | `datetime` | UTC, updated on every mutation |

### RentalRecord (domain model)

| Field | Type | Notes |
|---|---|---|
| `id` | `UUID` | Generated on creation |
| `car_id` | `UUID` | References Car |
| `renter_name` | `str` | Max 100 chars |
| `rented_at` | `datetime` | UTC |
| `returned_at` | `Optional[datetime]` | `None` until returned; UTC |

### Pydantic Schemas (request/response DTOs)

- `CarCreate` — `make`, `model`, `year`
- `RentRequest` — `renter_name: str`
- `CarResponse` — all Car fields
- `RentalRecordResponse` — all RentalRecord fields

---

## 6. API Surface

| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| `GET` | `/cars` | query params (Phase 2) | `List[CarResponse]` | — |
| `GET` | `/cars/{car_id}` | — | `CarResponse` | 404 |
| `POST` | `/cars` | `CarCreate` | `CarResponse` | 422 |
| `POST` | `/cars/{car_id}/rent` | `RentRequest` | `CarResponse` | 404, 409 |
| `POST` | `/cars/{car_id}/return` | — | `CarResponse` | 404, 409 |
| `GET` | `/cars/rentals` | — | `List[RentalRecordResponse]` | — |

**Phase 2 query params on `GET /cars`:**
- `make: Optional[str]`
- `model: Optional[str]`
- `year: Optional[int]`
- `available: Optional[bool]`

**Error semantics:**
- `404` — car not found
- `409` — car already rented (on rent) or not currently rented (on return)
- `422` — Pydantic validation failure or input length cap exceeded

---

## 7. Dependency Injection Strategy

`app/dependencies.py` — single source of truth, instantiated once at startup:

```python
_car_repo = InMemoryCarRepository()
_car_service = CarService(repo=_car_repo)

def get_car_service() -> CarService:
    return _car_service
```

Routes use `Depends(get_car_service)`. No route file ever calls a constructor.  
To swap to a DB repo: change two lines in `dependencies.py`, nothing else.

---

## 8. Concurrency Strategy

**Risk:** Two simultaneous `POST /cars/{id}/rent` requests both read `is_available=True` and double-book the same car.

**Fix:** One `asyncio.Lock` per car, stored in `InMemoryCarRepository`. Rent and return acquire the car's lock before reading or mutating `is_available`. Read-only operations (`GET`) do not need locking.

No sorted lock acquisition is required — there are no two-car opposing operations in this domain. A single per-car lock is deadlock-free.

---

## 9. Domain Exceptions

Defined in `app/exceptions.py`. Routes catch and convert to HTTP.

| Exception | HTTP Status | Scenario |
|---|---|---|
| `CarNotFoundError` | 404 | Car ID does not exist |
| `CarNotAvailableError` | 409 | Car is already rented |
| `CarNotRentedError` | 409 | Return attempted on an available car |

---

## 10. Security Hardening (Phase 3)

| Control | Detail |
|---|---|
| Rate limiting | Applied per-IP via `slowapi` — configurable limits on write endpoints |
| CORS | Origins restricted to env var `ALLOWED_ORIGINS`; defaults to `localhost` |
| Input length caps | All `str` fields capped at 100 chars via Pydantic `Field(max_length=100)` |

---

## 11. Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| `GET /cars/rentals` returns 422 | Router matches `"rentals"` as `car_id` UUID | Define `/cars/rentals` route **before** `/cars/{car_id}` in the router file |
| Items created via one endpoint invisible to another | Each router created its own repo instance | Always wire through `app/dependencies.py` — never instantiate inside route files |
| Double-booking under concurrent load | Two requests read `is_available=True` before either writes | Acquire per-car `asyncio.Lock` in repo before read-modify-write |

---

## 12. Code Quality Standards (all phases)

- **Logging:** `structlog` or stdlib `logging` with meaningful context in every service method
- **Comments:** Explain *why*, not *what*; only where non-obvious
- **Exceptions:** Typed domain exceptions bubble from services; routes convert to HTTP
- **TDD:** Tests written before implementation each phase
- **Git discipline:** Feature branch → tests pass → PR → wait for approval → merge to main
