from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging_config import set_correlation_id
from uuid import uuid4


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware для управления correlation ID."""

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        set_correlation_id(correlation_id)
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
