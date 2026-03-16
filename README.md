
# COMP3011 Coursework 1 — Travel Planner API

A RESTful Web API implemented with **FastAPI** and **SQLAlchemy** for a travel planning use case.  
The system supports:
- **Places** (CRUD)
- **Trips** and **Itinerary items** (TripPlace association)
- **Bookmarks** and **Reviews**
- **Expenses** and **Budget Summary**
- **Analytics**: city rankings (top bookmarked / top rated) and itinerary generation

## Tech Stack
- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy ORM
- SQLite (local database file)

## Setup and Run (Windows / PowerShell)

### 1) Create a virtual environment
```powershell
py -3.12 -m venv .venv
```

2) Activate the virtual environment
```powershell
.venv\Scripts\Activate.ps1
3) Install dependencies
```powershell
pip install fastapi uvicorn
pip install sqlalchemy

4) Start the API server
```powershell
python -m uvicorn main:app --reload

5) Open API documentation (Swagger UI)
Swagger UI: http://127.0.0.1:8000/docs
Health check: http://127.0.0.1:8000/health

Database
Database: SQLite
File: travel.db (created/updated automatically when the server starts)
Tables are created automatically (prototype approach using SQLAlchemy create_all).

Key Endpoints
Health
GET /health
Returns { "status": "ok" } when the server is running.

Places (CRUD)
POST /places
GET /places
GET /places/{place_id}
PUT /places/{place_id}
DELETE /places/{place_id}

Trips (CRUD)
POST /trips
GET /trips
GET /trips/{trip_id}
PUT /trips/{trip_id}
DELETE /trips/{trip_id}

Itinerary (TripPlace)
POST /trips/{trip_id}/places
Add a place to a trip (optionally set day and planned_order).
GET /trips/{trip_id}/places
List itinerary items for a trip.
PATCH /trips/{trip_id}/places/{trip_place_id}
Update an itinerary item (e.g., day, planned_order, note).
DELETE /trips/{trip_id}/places/{trip_place_id}

Bookmarks
POST /places/{place_id}/bookmark
DELETE /places/{place_id}/bookmark?user_name=...
Note: duplicate bookmarks for the same user_name and place_id return 409 Conflict.

Reviews
POST /places/{place_id}/reviews
GET /places/{place_id}/reviews
Note: ratings are validated to be within 1–5.

Expenses
POST /trips/{trip_id}/expenses
GET /trips/{trip_id}/expenses
Optional filters may include category, date_from, date_to.

Analytics
GET /analytics/trips/{trip_id}/budget-summary?currency=EUR
Returns expense totals grouped by category and a grand total.
GET /analytics/cities/{city}/top-bookmarked?limit=10
Returns the most bookmarked places within a city.
GET /analytics/cities/{city}/top-rated?limit=10&min_reviews=3
Returns the highest rated places within a city (with a minimum review count).
POST /analytics/trips/{trip_id}/generate-itinerary
Assigns day values for itinerary items that have day = null using a simple round-robin strategy.

Error Handling (Examples)
404 Not Found: place/trip/itinerary item does not exist
409 Conflict: duplicate bookmark (same user_name + place_id)
422 Validation Error: invalid input (FastAPI/Pydantic validation)
400 Bad Request: invalid trip date range (end_date earlier than start_date)

Notes
This project uses a lightweight user_name field to simulate user interactions without implementing authentication.
