from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.dependencies.auth import require_admin
from app.schemas.imports import ImportRequest, ImportResult
from app.services import importer as service

router = APIRouter()


@router.post("/import", response_model=ImportResult, status_code=201)
async def import_addresses(
    body: ImportRequest,
    principal=Depends(require_admin),
    conn=Depends(get_conn),
):
    """Bulk-import addresses into the graph with provenance (spec §9.8). Admin only."""
    rows = [r.model_dump() for r in body.rows]
    return ImportResult(**await service.import_rows(conn, rows, body.source))
