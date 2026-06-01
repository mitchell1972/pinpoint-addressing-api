"""Idempotency for POST requests.

If a POST carries an `Idempotency-Key` header, the first successful response is
stored and any later request with the same key (and same credential) replays
that stored response instead of running the handler again — so a double-submit
can't create two addresses. Scope is the hashed API credential, so keys are
isolated per caller.

Sits outermost, so a replay short-circuits before auth/metering (a replay must
not re-bill or re-count). Note: a repeat with the same key but a *different*
body still replays the first response (the key declares "same logical request");
strict body-mismatch rejection is a future hardening, and concurrent first-time
duplicates are deduped only at the storage layer (ON CONFLICT), not locked.
"""

import hashlib

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.db import open_pool
from app.repositories import idempotency as repo

_REPLAYABLE_STATUSES = {200, 201, 202}


def _scope(request) -> str:
    auth = request.headers.get("Authorization", "")
    return hashlib.sha256(auth.encode()).hexdigest() if auth else "anon"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        key = request.headers.get("Idempotency-Key")
        if request.method != "POST" or not key:
            return await call_next(request)

        scope = _scope(request)
        pool = await open_pool()

        async with pool.connection() as conn:
            stored = await repo.get(conn, scope, key)
        if stored is not None:
            return Response(
                content=stored["response_body"],
                status_code=stored["response_status"],
                headers={
                    "Idempotent-Replay": "true",
                    "content-type": stored["response_media_type"],
                },
            )

        response = await call_next(request)
        if response.status_code not in _REPLAYABLE_STATUSES:
            return response

        body = b"".join([section async for section in response.body_iterator])
        media_type = response.headers.get("content-type", "application/json")
        try:
            async with pool.connection() as conn:
                await repo.put(
                    conn,
                    scope,
                    key,
                    request.method,
                    request.url.path,
                    response.status_code,
                    body.decode(),
                    media_type,
                )
        except Exception:
            pass  # storing must never break the response

        # Rebuild the consumed response; drop content-length so it's recomputed.
        headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
        return Response(content=body, status_code=response.status_code, headers=headers)
