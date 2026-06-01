from pydantic import BaseModel, Field


class ImportRow(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    alias: str | None = None
    landmark: str | None = None
    building_desc: str | None = None
    state: str | None = None
    lga: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class ImportRequest(BaseModel):
    rows: list[ImportRow] = Field(min_length=1, max_length=10000)
    source: str = "import"


class ImportResult(BaseModel):
    inserted: int
    skipped: int
