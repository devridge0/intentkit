"""
FastAPI middleware module
"""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

class HealthCheckFilter(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if request.url.path == "/health":
            # Disable logging for uvicorn.access
            logging.getLogger("uvicorn.access").disabled = True
            response = await call_next(request)
            # Re-enable logging
            logging.getLogger("uvicorn.access").disabled = False
            return response
        return await call_next(request)
