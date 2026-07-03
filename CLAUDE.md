# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**"Beton" / Project Sari** — a brokerage marketplace matching **contractors** with perishable leftover concrete (hardens within hours) to **customers** needing small quantities. Brokerage only: show a price and connect the parties, no in-app payment. UI is **RTL Hebrew**.

- **`SPEC.md`** (root) is the source of truth — full functional/technical spec, 17 sections, all product decisions locked (`SPEC.html` is a readable export). Read it before non-trivial work.
- **`prompts/`** holds a self-contained per-phase build brief (phase-0…phase-6); `prompts/README.md` is the master context. Each phase cuts across DB→server→client and ends with E2E tests.

## Commands

```bash
# Backend (from server/) — FastAPI on port 8001; docs at http://localhost:8001/docs
uvicorn app:app --reload --port 8001

# Client (from client/) — Vite dev server on port 5173
npm install && npm run dev
npm run build          # tsc + vite build — use as the client's type/build check

# Tests (pytest infra is introduced in phase 0; once present, from server/):
pytest                 # all tests
pytest tests/test_matching.py::test_name   # single test
```

**Environment gotchas (verified):**
- The `python` / `py` on PATH are **Microsoft Store stubs**, not real interpreters. You must locate or create a real venv and `pip install -r server/requirements.txt` before running the server.
- **`rtree` is used by the matching engine (`from rtree import index`) but is missing from `server/requirements.txt`** — it needs adding (and depends on `libspatialindex`).
- Node v22 is at `C:\nvm4w\nodejs`. The Google Maps key is in `client/.env` (`VITE_GOOGLE_MAPS_API_KEY`); the environment is behind **NetFree** (SSL interception) which can block Maps loading in the browser.

## Architecture

**Server (`server/`) — strict layered flow, preserve it:**
```
controller/ (FastAPI routers) → service/ (business logic) → repository/ (DB access) → models/ (SQLAlchemy)
                                      dto/ (Pydantic in/out)
```
`app.py` wires all routers. `database.py`/`config.py` hold the SQLAlchemy engine + settings.

**The matching engine is the heart of the system** (`service/matching_engine_service.py` + `service/contractor_matching_controller.py`). Core flow: a customer posts a request → it waits (`status=OPEN`); a **contractor posting an offer triggers the engine**, which filters open requests by **geo (R-tree + Haversine, 10km) → purpose→spec → quantity (90–100% of the offer) → score (`5×waiting_days − 1×travel_minutes`)**. Per SPEC the engine is bidirectional (a new customer request also scans open offers) and matches are recorded in an `OfferMatches` table with in-app `Notifications`; the first customer to accept wins (atomic). Much of this (persisting offers, matches, notifications, accept flow, auth) is **specced but not yet built** — see `SPEC.md` §14 and the phase prompts.

**Database:** local **SQL Server**, DB `beton`, **Windows Authentication**, driver `ODBC Driver 17 for SQL Server`. Schema in `server/db/schema.sql` (9 tables, IDENTITY seed ranges: Customers 100, ConcreteRequests 200, Contractors 300, ContractorConcreteRequests 600, Strength 1100, Reliant 1200, Stone_size 1300, Purpose 1400, Concrete_type 2000).

**Client (`client/src/`):** React 19 + Vite 8 + TS, `react-router-dom`, `axios` (`api/` = types + central client + per-resource modules), `@vis.gl/react-google-maps` (`MapPicker`). RTL Hebrew layout.

## Project-specific conventions & traps

- **Build on the existing code; do not rewrite.** Keep the layered structure.
- **Do not rename existing DB columns** — casing is deliberate and mapped by the ORM (`Reliant`, `Stone_size`, `Purpose`, `Reliant_id`, `Stone_size_id`, `Purpose_id`), and `ContractorConcreteRequests.id_customer` is an FK to `ConcreteRequests.request_id`.
- **`status` is inconsistent** (model `DECIMAL NOT NULL` vs DB nullable vs DTO string); the engine treats `status IS NULL`/non-OPEN as unavailable. Normalize to an enum (OPEN/CLOSED/CANCELLED) per SPEC before relying on it.
- **`POST /contractor-offers/send/` does not persist the offer** (only filters and returns candidates); `POST /contractor-offers/` is commented out. Lookup tables (Purpose, etc.) are **empty**, so the engine finds nothing until seeded.
- **Experimental/junk files** to ignore or clean (per phase 0): `service/{rrrrrrrrrrrrrrr,ttttttttttttttt,test,test163,matching_service,matching_service2,mounday154}.py`, `controller/test.py`, `dto/testDto.py`, `gm2.py`, `GoogleMaps.py`, `main.py` (real entry point is `app.py`).
- After meaningful work, update the auto-memory at `memory/project-sari-state.md` (indexed in `memory/MEMORY.md`).
