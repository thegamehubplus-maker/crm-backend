import hashlib
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import IdempotencyKey


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware implementing idempotency for POST/PUT/PATCH requests.

    If the request contains an Idempotency-Key header, the middleware will
    ensure that repeated requests with the same key/method/path return the
    same response without executing the handler again.
    """

    async def dispatch(self, request: Request, call_next):
        # Only apply to state-changing methods
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idem_key = request.headers.get("Idempotency-Key")
        if not idem_key:
            return await call_next(request)

        # compute hash of the request body
        body_bytes = await request.body()
        body_hash = hashlib.sha256(body_bytes).hexdigest() if body_bytes else None

        db: Session = SessionLocal()
        try:
            rec = (
                db.query(IdempotencyKey)
                .filter(
                    IdempotencyKey.key == idem_key,
                    IdempotencyKey.method == request.method,
                    IdempotencyKey.path == request.url.path,
                )
                .first()
            )
            if rec and (rec.body_hash == body_hash):
                # return previously saved response
                return JSONResponse(
                    content=rec.response_body or {},
                    status_code=rec.response_status or 200,
                )

            # No existing record: call the downstream handler
            response: Response = await call_next(request)

            # Save the response for future calls (JSON only)
            try:
                content = json.loads(response.body.decode() if response.body else "{}")
            except Exception:
                content = None

            new_rec = IdempotencyKey(
                key=idem_key,
                method=request.method,
                path=request.url.path,
                body_hash=body_hash,
                response_status=response.status_code,
                response_body=content,
            )
            db.add(new_rec)
            db.commit()
            return response
        finally:
            db.close()