from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.dependencies.auth import require_principal
from app.schemas.analytics import (
    AnalyticsSummary,
    DeliveryRecorded,
    DeliveryReport,
    Hotspot,
    HotspotsResponse,
)
from app.services import analytics as service

router = APIRouter()


@router.post("/deliveries", response_model=DeliveryRecorded, status_code=201)
async def record_delivery(
    body: DeliveryReport,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Record a delivery outcome against an address (spec §6.5)."""
    result = await service.record(
        conn, body.code, principal.account_id, body.status, body.reason, body.time_to_locate_seconds
    )
    return DeliveryRecorded(**result)


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def analytics_summary(principal=Depends(require_principal), conn=Depends(get_conn)):
    """Failed-drop rate + average time-to-locate for the caller's account."""
    return AnalyticsSummary(**await service.summary(conn, principal.account_id))


@router.get("/analytics/hotspots", response_model=HotspotsResponse)
async def analytics_hotspots(principal=Depends(require_principal), conn=Depends(get_conn)):
    """Failure hotspots grouped by LGA."""
    rows = await service.hotspots(conn, principal.account_id)
    return HotspotsResponse(hotspots=[Hotspot(**h) for h in rows])
