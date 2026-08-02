"""
HTTP request logging middleware.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


logger = logging.getLogger("healthcare-rag")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming HTTP request and outgoing response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        start_time = time.perf_counter()

        request_id = getattr(
            request.state,
            "request_id",
            "UNKNOWN",
        )

        logger.info(
            "Incoming Request | "
            "request_id=%s method=%s path=%s client_ip=%s",
            request_id,
            request.method,
            request.url.path,
            request.client.host if request.client else "UNKNOWN",
        )

        response = await call_next(request)

        process_time = round(
            time.perf_counter() - start_time,
            4,
        )

        logger.info(
            "Outgoing Response | "
            "request_id=%s status=%s duration=%.4fs",
            request_id,
            response.status_code,
            process_time,
        )

        return response