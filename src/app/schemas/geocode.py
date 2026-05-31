from pydantic import BaseModel, Field


class Area(BaseModel):
    state: str | None = None
    lga: str | None = None


class GeocodeRequest(BaseModel):
    query: str = Field(min_length=1)
    area: Area | None = None
    limit: int = Field(default=3, ge=1, le=25)


class ReverseRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    limit: int = Field(default=3, ge=1, le=25)
    radius_m: int = Field(default=2000, ge=1, le=50000)


class BatchGeocodeRequest(BaseModel):
    queries: list[GeocodeRequest] = Field(min_length=1, max_length=1000)


class GeocodeResult(BaseModel):
    code: str
    olc: str | None = None
    lat: float
    lng: float
    confidence: float
    landmark: str | None = None
    verified: bool


class GeocodeResponse(BaseModel):
    results: list[GeocodeResult]
    request_id: str
    units: int


class BatchGeocodeResponse(BaseModel):
    job_id: str
    status: str
    results: list[GeocodeResponse]
