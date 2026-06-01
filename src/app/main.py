from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.controllers import addresses, geocode, usage, verify
from app.core.db import close_pool, open_pool
from app.core.errors import register_error_handlers
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.metering import MeteringMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Pinpoint Addressing API",
    version="0.1.0",
    summary="Verified digital addresses + geocoding & verification for Nigeria (MVP spine).",
    lifespan=lifespan,
)

register_error_handlers(app)

# Middleware order: add inner-first. Metering records billable calls; idempotency
# wraps it outermost so a replayed request short-circuits before auth/metering.
app.add_middleware(MeteringMiddleware)
app.add_middleware(IdempotencyMiddleware)

# Controllers, all under /v1.
app.include_router(addresses.router, prefix="/v1", tags=["addresses"])
app.include_router(geocode.router, prefix="/v1", tags=["geocode"])
app.include_router(verify.router, prefix="/v1", tags=["verify"])
app.include_router(usage.router, prefix="/v1", tags=["usage"])


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}
