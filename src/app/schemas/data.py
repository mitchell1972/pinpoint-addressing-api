from pydantic import BaseModel


class CoverageRow(BaseModel):
    lga: str | None = None
    total: int
    verified: int
    avg_confidence: float | None = None


class CoverageResponse(BaseModel):
    coverage: list[CoverageRow]
