from pydantic import BaseModel, Field


class LocationRecordCreate(BaseModel):
    species: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_name: str
    date: str | None = None
