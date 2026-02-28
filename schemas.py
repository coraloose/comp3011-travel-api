from datetime import date
from pydantic import BaseModel, Field


# Place

class PlaceCreate(BaseModel):
    city: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)


class PlaceUpdate(BaseModel):
    city: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1)


class PlaceOut(BaseModel):
    id: int
    city: str
    name: str
    category: str

    class Config:
        from_attributes = True


# Trip 

class TripCreate(BaseModel):
    name: str = Field(min_length=1)
    start_date: date
    end_date: date


class TripUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    start_date: date | None = None
    end_date: date | None = None


class TripOut(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date

    class Config:
        from_attributes = True


# TripPlace (Itinerary items)

class TripPlaceCreate(BaseModel):
    place_id: int
    day: int | None = Field(default=None, ge=1)
    planned_order: int | None = Field(default=None, ge=1)
    note: str | None = None


class TripPlaceUpdate(BaseModel):
    day: int | None = Field(default=None, ge=1)
    planned_order: int | None = Field(default=None, ge=1)
    note: str | None = None


class TripPlaceOut(BaseModel):
    id: int
    trip_id: int
    place_id: int
    day: int | None
    planned_order: int | None
    note: str | None

    class Config:
        from_attributes = True
