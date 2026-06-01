from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.dependencies.auth import require_admin
from app.schemas.data import CoverageResponse, CoverageRow
from app.services import data as service

router = APIRouter()


@router.get("/data/coverage", response_model=CoverageResponse)
async def coverage(principal=Depends(require_admin), conn=Depends(get_conn)):
    """Anonymised coverage data product — aggregate counts per LGA, admin only."""
    rows = await service.coverage(conn)
    return CoverageResponse(coverage=[CoverageRow(**r) for r in rows])
