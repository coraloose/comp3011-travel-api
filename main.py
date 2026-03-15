from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from db import SessionLocal, engine, Base
from models import Place, Trip, TripPlace, Bookmark, Review, Expense
from schemas import (
    PlaceCreate, PlaceUpdate, PlaceOut,
    TripCreate, TripUpdate, TripOut,
    TripPlaceCreate, TripPlaceUpdate, TripPlaceOut,
    BookmarkCreate, BookmarkOut,
    ReviewCreate, ReviewOut,
    ExpenseCreate, ExpenseOut,
    BudgetSummaryOut, BudgetCategoryOut,
    PlaceRankOut, ItineraryGenerateOut
)

app = FastAPI(title="Travel Planner API")

# Prototype-grade schema creation; migrations are a future improvement.
Base.metadata.create_all(bind=engine)


def get_db():
    """Per-request database session lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# Place CRUD
# =========================

@app.post("/places", response_model=PlaceOut, status_code=status.HTTP_201_CREATED)
def create_place(payload: PlaceCreate, db: Session = Depends(get_db)):
    place = Place(**payload.model_dump())
    db.add(place)
    db.commit()
    db.refresh(place)
    return place


@app.get("/places", response_model=list[PlaceOut])
def list_places(
    city: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Place)
    if city:
        q = q.filter(Place.city == city)
    if category:
        q = q.filter(Place.category == category)
    return q.order_by(Place.id.desc()).all()


@app.get("/places/{place_id}", response_model=PlaceOut)
def get_place(place_id: int, db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place


@app.put("/places/{place_id}", response_model=PlaceOut)
def update_place(place_id: int, payload: PlaceUpdate, db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(place, k, v)

    db.commit()
    db.refresh(place)
    return place


@app.delete("/places/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place(place_id: int, db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    # Ensure dependent records are removed to avoid orphan references.
    db.query(TripPlace).filter(TripPlace.place_id == place_id).delete()
    db.query(Bookmark).filter(Bookmark.place_id == place_id).delete()
    db.query(Review).filter(Review.place_id == place_id).delete()

    db.delete(place)
    db.commit()
    return None


# =========================
# Trip CRUD
# =========================

@app.post("/trips", response_model=TripOut, status_code=status.HTTP_201_CREATED)
def create_trip(payload: TripCreate, db: Session = Depends(get_db)):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be on/after start_date")

    trip = Trip(**payload.model_dump())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@app.get("/trips", response_model=list[TripOut])
def list_trips(db: Session = Depends(get_db)):
    return db.query(Trip).order_by(Trip.id.desc()).all()


@app.get("/trips/{trip_id}", response_model=TripOut)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@app.put("/trips/{trip_id}", response_model=TripOut)
def update_trip(trip_id: int, payload: TripUpdate, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    data = payload.model_dump(exclude_unset=True)
    new_start = data.get("start_date", trip.start_date)
    new_end = data.get("end_date", trip.end_date)
    if new_end < new_start:
        raise HTTPException(status_code=400, detail="end_date must be on/after start_date")

    for k, v in data.items():
        setattr(trip, k, v)

    db.commit()
    db.refresh(trip)
    return trip


@app.delete("/trips/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    db.query(TripPlace).filter(TripPlace.trip_id == trip_id).delete()
    db.delete(trip)
    db.commit()
    return None


# =========================
# TripPlace (Itinerary)
# =========================

@app.post("/trips/{trip_id}/places", response_model=TripPlaceOut, status_code=status.HTTP_201_CREATED)
def add_place_to_trip(trip_id: int, payload: TripPlaceCreate, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    place = db.query(Place).filter(Place.id == payload.place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    item = TripPlace(trip_id=trip_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/trips/{trip_id}/places", response_model=list[TripPlaceOut])
def list_trip_places(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return (
        db.query(TripPlace)
        .filter(TripPlace.trip_id == trip_id)
        .order_by(
            TripPlace.day.is_(None),
            TripPlace.day.asc(),
            TripPlace.planned_order.asc(),
            TripPlace.id.asc(),
        )
        .all()
    )


@app.patch("/trips/{trip_id}/places/{trip_place_id}", response_model=TripPlaceOut)
def update_trip_place(trip_id: int, trip_place_id: int, payload: TripPlaceUpdate, db: Session = Depends(get_db)):
    item = (
        db.query(TripPlace)
        .filter(TripPlace.id == trip_place_id, TripPlace.trip_id == trip_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="TripPlace not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)
    return item


@app.delete("/trips/{trip_id}/places/{trip_place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip_place(trip_id: int, trip_place_id: int, db: Session = Depends(get_db)):
    item = (
        db.query(TripPlace)
        .filter(TripPlace.id == trip_place_id, TripPlace.trip_id == trip_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="TripPlace not found")

    db.delete(item)
    db.commit()
    return None


# =========================
# Bookmark
# =========================

@app.post("/places/{place_id}/bookmark", response_model=BookmarkOut, status_code=status.HTTP_201_CREATED)
def create_bookmark(place_id: int, payload: BookmarkCreate, db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    bookmark = Bookmark(place_id=place_id, user_name=payload.user_name)

    try:
        db.add(bookmark)
        db.commit()
        db.refresh(bookmark)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bookmark already exists")

    return bookmark


@app.delete("/places/{place_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(place_id: int, user_name: str, db: Session = Depends(get_db)):
    bookmark = (
        db.query(Bookmark)
        .filter(Bookmark.place_id == place_id, Bookmark.user_name == user_name)
        .first()
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    db.delete(bookmark)
    db.commit()
    return None


# =========================
# Review
# =========================

@app.post("/places/{place_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(place_id: int, payload: ReviewCreate, db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    review = Review(
        place_id=place_id,
        user_name=payload.user_name,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@app.get("/places/{place_id}/reviews", response_model=list[ReviewOut])
def list_reviews(place_id: int, db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    return (
        db.query(Review)
        .filter(Review.place_id == place_id)
        .order_by(Review.id.desc())
        .all()
    )


# =========================
# Expense
# =========================

@app.post("/trips/{trip_id}/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(trip_id: int, payload: ExpenseCreate, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    expense = Expense(trip_id=trip_id, **payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@app.get("/trips/{trip_id}/expenses", response_model=list[ExpenseOut])
def list_expenses(
    trip_id: int,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    q = db.query(Expense).filter(Expense.trip_id == trip_id)

    if category:
        q = q.filter(Expense.category == category)

    if date_from:
        q = q.filter(Expense.date >= date_from)
    if date_to:
        q = q.filter(Expense.date <= date_to)

    return q.order_by(Expense.date.desc(), Expense.id.desc()).all()


# =========================
# Analytics: Budget Summary
# =========================

@app.get("/analytics/trips/{trip_id}/budget-summary", response_model=BudgetSummaryOut)
def budget_summary(trip_id: int, currency: str = "EUR", db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Aggregate by category.
    rows = (
        db.query(
            Expense.category.label("category"),
            func.coalesce(func.sum(Expense.amount), 0.0).label("total"),
        )
        .filter(Expense.trip_id == trip_id, Expense.currency == currency)
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )

    by_category = [BudgetCategoryOut(category=r.category, total=float(r.total)) for r in rows]
    total = sum(x.total for x in by_category)

    return BudgetSummaryOut(trip_id=trip_id, currency=currency, total=float(total), by_category=by_category)


# =========================
# Analytics: City Rankings
# =========================

@app.get("/analytics/cities/{city}/top-bookmarked", response_model=list[PlaceRankOut])
def top_bookmarked(city: str, limit: int = 10, db: Session = Depends(get_db)):
    rows = (
        db.query(
            Place.id.label("place_id"),
            Place.city.label("city"),
            Place.name.label("name"),
            Place.category.label("category"),
            func.count(Bookmark.id).label("bookmark_count"),
        )
        .join(Bookmark, Bookmark.place_id == Place.id)
        .filter(Place.city == city)
        .group_by(Place.id, Place.city, Place.name, Place.category)
        .order_by(func.count(Bookmark.id).desc())
        .limit(limit)
        .all()
    )

    return [
        PlaceRankOut(
            place_id=r.place_id,
            city=r.city,
            name=r.name,
            category=r.category,
            value=float(r.bookmark_count),
            count=None,
        )
        for r in rows
    ]


@app.get("/analytics/cities/{city}/top-rated", response_model=list[PlaceRankOut])
def top_rated(city: str, limit: int = 10, min_reviews: int = 3, db: Session = Depends(get_db)):
    rows = (
        db.query(
            Place.id.label("place_id"),
            Place.city.label("city"),
            Place.name.label("name"),
            Place.category.label("category"),
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .join(Review, Review.place_id == Place.id)
        .filter(Place.city == city)
        .group_by(Place.id, Place.city, Place.name, Place.category)
        .having(func.count(Review.id) >= min_reviews)
        .order_by(func.avg(Review.rating).desc(), func.count(Review.id).desc())
        .limit(limit)
        .all()
    )

    return [
        PlaceRankOut(
            place_id=r.place_id,
            city=r.city,
            name=r.name,
            category=r.category,
            value=float(r.avg_rating),
            count=int(r.review_count),
        )
        for r in rows
    ]


# =========================
# Analytics: Itinerary Generator
# =========================

@app.post("/analytics/trips/{trip_id}/generate-itinerary", response_model=ItineraryGenerateOut)
def generate_itinerary(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Determine trip duration.
    num_days = (trip.end_date - trip.start_date).days + 1
    if num_days <= 0:
        raise HTTPException(status_code=400, detail="Invalid trip date range")

    # Select items without assigned day.
    items = (
        db.query(TripPlace)
        .filter(TripPlace.trip_id == trip_id, TripPlace.day.is_(None))
        .order_by(TripPlace.id.asc())
        .all()
    )

    if not items:
        return ItineraryGenerateOut(trip_id=trip_id, updated_items=0)

    # Simple round-robin assignment across days.
    updated = 0
    for idx, item in enumerate(items):
        day = (idx % num_days) + 1
        item.day = day
        # If planned_order is missing, assign sequential order within that day.
        if item.planned_order is None:
            item.planned_order = 1
        updated += 1

    db.commit()
    return ItineraryGenerateOut(trip_id=trip_id, updated_items=updated)