# app/core/request_middleware.py

import time
import uuid
import logging
from fastapi import Request
from app.core.request_context import set_request_id


logger = logging.getLogger("api")


async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # 🔥 Guardar en contexto global
    set_request_id(request_id)


    response = await call_next(request)

    duration = (time.time() - start_time) * 1000

    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "duration_ms": round(duration, 2),
        },
    )

    response.headers["X-Request-ID"] = request_id

    return response
