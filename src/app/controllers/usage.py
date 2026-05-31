from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.dependencies.auth import require_principal
from app.schemas.metering import UsageByEndpoint, UsageResponse
from app.services import metering as service

router = APIRouter()


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    principal=Depends(require_principal),
    conn=Depends(get_conn),
):
    """Account usage & billing counters (spec §9.4). Not itself billable."""
    agg = await service.usage(conn, principal.account_id)
    return UsageResponse(
        account_id=principal.account_id,
        env=principal.env,
        total_units=agg["total_units"],
        total_calls=agg["total_calls"],
        by_endpoint=[UsageByEndpoint(**r) for r in agg["by_endpoint"]],
    )
