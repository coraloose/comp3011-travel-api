from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import SessionLocal, engine, Base
from models import Place
from schemas import PlaceCreate, PlaceUpdate, PlaceOut

app = FastAPI(title="Travel Planner API")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/places", response_model=PlaceOut, status_code=status.HTTP_201_CREATED)
def create_place(payload: PlaceCreate, db: Session = Depends(get_db)):
    place = Place(**payload.model_dump())
    db.add(place)
    db.commit()
    db.refresh(place)
    return place

@app.get("/places", response_model=list[PlaceOut])
def list_places(city: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
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
    db.delete(place)
    db.commit()
    return None
