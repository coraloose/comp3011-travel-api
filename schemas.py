from pydantic import BaseModel, Field

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

