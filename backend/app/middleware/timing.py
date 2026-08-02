"""
Request timing middleware.

Measures request execution time and adds it
to the response header.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Adds processing time to the response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start_time

        response.headers["X-Process-Time"] = (
            f"{process_time:.4f}s"
        )

        return response