from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import SessionLocal, engine, Base
from models import Place, Trip, TripPlace, Bookmark, Review
from schemas import (
    PlaceCreate, PlaceUpdate, PlaceOut,
    TripCreate, TripUpdate, TripOut,
    TripPlaceCreate, TripPlaceUpdate, TripPlaceOut,
    BookmarkCreate, BookmarkOut,
    ReviewCreate, ReviewOut
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