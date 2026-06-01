from pydantic import BaseModel, Field


class Capture(BaseModel):
    capture_id: str
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    landmark: str | None = None
    building_desc: str | None = None
    contact: str | None = None
    consent: bool = False
    captured_at: str | None = None


class SyncRequest(BaseModel):
    captures: list[Capture] = Field(min_length=1, max_length=1000)


class SyncItemResult(BaseModel):
    capture_id: str
    code: str
    status: str  # 'created' | 'duplicate'


class SyncResult(BaseModel):
    results: list[SyncItemResult]
