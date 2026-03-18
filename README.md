
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

### 2) Activate the virtual environment
```powershell
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies
```powershell
pip install fastapi uvicorn
pip install sqlalchemy
```

### 4) Start the API server
```powershell
python -m uvicorn main:app --reload
```

### 5) Open API documentation (Swagger UI)
- Swagger UI: http://127.0.0.1:8000/docs  
- Health check: http://127.0.0.1:8000/health

## API Documentation (PDF)
- [COMP3011 API Documentation](API_Documentation.pdf)

## Database
- Database: SQLite
- File: `travel.db` (created/updated automatically when the server starts)
- Tables are created automatically (prototype approach using SQLAlchemy `create_all`).

## Key Endpoints

### Health
- `GET /health` — Returns `{ "status": "ok" }`

### Places (CRUD)
- `POST /places`
- `GET /places`
- `GET /places/{place_id}`
- `PUT /places/{place_id}`
- `DELETE /places/{place_id}`

### Trips (CRUD)
- `POST /trips`
- `GET /trips`
- `GET /trips/{trip_id}`
- `PUT /trips/{trip_id}`
- `DELETE /trips/{trip_id}`

### Itinerary (TripPlace)
- `POST /trips/{trip_id}/places` — Add a place to a trip
- `GET /trips/{trip_id}/places` — List itinerary items
- `PATCH /trips/{trip_id}/places/{trip_place_id}` — Update an itinerary item
- `DELETE /trips/{trip_id}/places/{trip_place_id}`

### Bookmarks
- `POST /places/{place_id}/bookmark`
- `DELETE /places/{place_id}/bookmark?user_name=...` — Duplicate bookmarks return **409**

### Reviews
- `POST /places/{place_id}/reviews`
- `GET /places/{place_id}/reviews` — Ratings validated within **1–5**

### Expenses
- `POST /trips/{trip_id}/expenses`
- `GET /trips/{trip_id}/expenses` — Optional filters: `category`, `date_from`, `date_to`

### Analytics
- `GET /analytics/trips/{trip_id}/budget-summary?currency=EUR`
- `GET /analytics/cities/{city}/top-bookmarked?limit=10`
- `GET /analytics/cities/{city}/top-rated?limit=10&min_reviews=3`
- `POST /analytics/trips/{trip_id}/generate-itinerary`

## Error Handling (Examples)
- 404 Not Found: resource does not exist
- 409 Conflict: duplicate bookmark (same `user_name` + `place_id`)
- 422 Validation Error: invalid input (FastAPI/Pydantic validation)
- 400 Bad Request: invalid trip date range (`end_date` earlier than `start_date`)

## Notes
- This project uses a lightweight `user_name` field to simulate user interactions without implementing authentication.

## Notes
- This project uses a lightweight `user_name` field to simulate user interactions without implementing authentication.


Notes
This project uses a lightweight user_name field to simulate user interactions without implementing authentication.
