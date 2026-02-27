from sqlalchemy import Column, Integer, String
from db import Base

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
