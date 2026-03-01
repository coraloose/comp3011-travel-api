from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from db import Base


class Place(Base):
    """Entity representing a point of interest."""
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)


class Trip(Base):
    """Entity representing a travel plan with a date interval."""
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)


class TripPlace(Base):
    """Association entity linking Trip and Place with itinerary metadata."""
    __tablename__ = "trip_places"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, index=True)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False, index=True)

    day = Column(Integer, nullable=True)
    planned_order = Column(Integer, nullable=True)
    note = Column(String, nullable=True)


class Bookmark(Base):
    """User-level bookmark of a place (unique per user/place)."""
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False, index=True)
    user_name = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("place_id", "user_name", name="uq_bookmark_place_user"),
    )


class Review(Base):
    """User-level review of a place."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False, index=True)
    user_name = Column(String, nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
