from datetime import datetime

from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    alias: str | None = None
    landmark: str | None = None
    building_desc: str | None = None
    access_notes: str | None = None
    contact: str | None = None
    state: str | None = None
    lga: str | None = None
    ward: str | None = None


class ClaimRequest(BaseModel):
    alias: str | None = None


class AddressOut(BaseModel):
    code: str
    olc: str
    alias: str | None = None
    lat: float
    lng: float
    geohash: str
    state: str | None = None
    lga: str | None = None
    ward: str | None = None
    confidence: float
    status: str
    landmark: str | None = None
    building_desc: str | None = None
    access_notes: str | None = None
    contact: str | None = None
    created_at: datetime
