# Car Rental Service

A FastAPI-based car rental service. Browse available cars, filter by attributes, rent a car, and return it.

---

## Table of Contents
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [How to Run](#how-to-run)
- [Interactive UI](#interactive-ui)
- [Clean Run Process](#clean-run-process)
- [API Reference](#api-reference)
- [Architecture](#architecture)
- [Phases](#phases)
- [Troubleshooting](#troubleshooting)
- [Environment Variables](#environment-variables)

---

## Tech Stack
| | |
|---|---|
| Language | Python 3.9+ |
| Framework | FastAPI |
| Validation | Pydantic v2 |
| Testing | pytest + httpx |
| Rate Limiting | slowapi (Phase 3) |

---

## Project Structure
```
app/
  main.py           # FastAPI app factory
  dependencies.py   # DI wiring — single source of truth
  exceptions.py     # Typed domain exceptions
  models/
    car.py          # Car + RentalRecord domain models
    schemas.py      # Pydantic request/response DTOs
  repositories/
    base.py         # CarRepository ABC
    in_memory.py    # InMemoryCarRepository
  services/
    car_service.py  # Business logic
  routers/
    cars.py         # HTTP endpoints
static/
  index.html        # Vanilla UI (Phase 4)
tests/
  test_cars_crud.py
  test_filtering.py
  test_security.py
```

---

## Getting Started
```bash
pip3 install -r requirements.txt
```

---

## How to Run
```bash
uvicorn app.main:app --reload
```
API docs available at: `http://localhost:8000/docs`

---

## Interactive UI
_(Phase 4 — coming soon)_  
Served at `http://localhost:8000/` — vanilla HTML/CSS/JS, no framework, no build step.

---

## Clean Run Process
```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Run tests
python3 -m pytest -v

# 3. Start server
uvicorn app.main:app --reload

# 4. Run demo
bash demo.sh
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/cars` | List all cars. Filter by `?make=&model=&year=&available=` |
| `GET` | `/cars/{id}` | Get a single car by ID |
| `POST` | `/cars` | Add a new car `{"make":"Toyota","model":"Camry","year":2022}` |
| `POST` | `/cars/{id}/rent` | Rent a car `{"renter_name":"Alice"}` |
| `POST` | `/cars/{id}/return` | Return a rented car |
| `GET` | `/cars/rentals` | List all rental records |

**Error codes:**
- `404` — Car not found
- `409` — Car already rented / not currently rented
- `422` — Validation error (invalid input or length cap exceeded)
- `429` — Rate limit exceeded (Phase 3)

---

## Architecture

```
HTTP Request
     │
     ▼
┌─────────────┐
│   Routes    │  app/routers/cars.py
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Services   │  app/services/car_service.py
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Repository  │  app/repositories/base.py (ABC)
│    ABC      │       ↑ implemented by
└─────────────┘  app/repositories/in_memory.py
```

`app/dependencies.py` is the single DI wiring point — never instantiate repos or services in route files.

---

## Phases
| Phase | Branch | Status | Scope |
|---|---|---|---|
| 1 | `feat/phase-1-core` | ✅ | Core CRUD, rent, return |
| 2 | `feat/phase-2-filtering` | 🔲 | Filter by make, model, year, availability |
| 3 | `feat/phase-3-security` | 🔲 | Rate limiting, CORS, input caps |
| 4 | `feat/phase-4-ui` | 🔲 | Interactive UI at `/` |

---

## Troubleshooting
| Problem | Fix |
|---|---|
| `GET /cars/rentals` returns 422 | This route must be defined before `/cars/{car_id}` in the router |
| Items created via POST not visible on GET | Check `dependencies.py` — all routes must share the same repo instance |
| Double-booking under load | Per-car `asyncio.Lock` in `InMemoryCarRepository` handles this |

---

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:8000` | Comma-separated CORS allowed origins (Phase 3) |
