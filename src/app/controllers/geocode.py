from uuid import uuid4

from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.dependencies.auth import require_principal
from app.schemas.geocode import (
    BatchGeocodeRequest,
    BatchGeocodeResponse,
    GeocodeRequest,
    GeocodeResponse,
    GeocodeResult,
    ReverseRequest,
)
from app.services import geocode as service

router = APIRouter()


def _request_id() -> str:
    return "req_" + uuid4().hex[:16]


@router.post("/geocode", response_model=GeocodeResponse)
async def geocode(
    body: GeocodeRequest,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Forward: free-text/landmark + area -> ranked verified candidates (spec §6.2)."""
    results = await service.forward(conn, body)
    return GeocodeResponse(
        results=[GeocodeResult(**r) for r in results], request_id=_request_id(), units=1
    )


@router.post("/reverse", response_model=GeocodeResponse)
async def reverse(
    body: ReverseRequest,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Reverse: coordinates -> nearest verified address(es) (spec §6.2)."""
    results = await service.reverse(conn, body)
    return GeocodeResponse(
        results=[GeocodeResult(**r) for r in results], request_id=_request_id(), units=1
    )


@router.post("/batch/geocode", response_model=BatchGeocodeResponse, status_code=202)
async def batch_geocode(
    body: BatchGeocodeRequest,
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Bulk back-office geocoding (spec §6.2). MVP runs synchronously."""
    groups = await service.batch(conn, body)
    sub_responses = [
        GeocodeResponse(results=[GeocodeResult(**r) for r in g], request_id=_request_id(), units=1)
        for g in groups
    ]
    return BatchGeocodeResponse(job_id="job_" + uuid4().hex[:16], status="completed", results=sub_responses)
