from typing import Literal

from pydantic import BaseModel, Field


class DeliveryReport(BaseModel):
    code: str
    status: Literal["delivered", "failed"]
    reason: str | None = None
    time_to_locate_seconds: int | None = Field(default=None, ge=0)


class DeliveryRecorded(BaseModel):
    id: str
    status: str


class AnalyticsSummary(BaseModel):
    total: int
    delivered: int
    failed: int
    failed_rate: float
    avg_time_to_locate_seconds: float | None = None


class Hotspot(BaseModel):
    lga: str | None = None
    total: int
    failed: int
    failed_rate: float


class HotspotsResponse(BaseModel):
    hotspots: list[Hotspot]
