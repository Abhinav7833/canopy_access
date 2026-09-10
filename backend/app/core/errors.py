import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("canopy")


class NotFound(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class LLMNotConfigured(Exception):
    """Raised when an LLM-backed endpoint is called but no LLM credentials are set."""

    def __init__(self, message: str) -> None:
        self.message = message


def _envelope(code: str, message: str, detail: object = None) -> dict:
    return {"error": {"code": code, "message": message, "detail": detail}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    async def _not_found(_: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content=_envelope("not_found", exc.message))

    @app.exception_handler(LLMNotConfigured)
    async def _llm_not_configured(_: Request, exc: LLMNotConfigured) -> JSONResponse:
        return JSONResponse(status_code=503, content=_envelope("llm_not_configured", exc.message))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_envelope(
                "validation_error", "Invalid request.", jsonable_encoder(exc.errors())
            ),
        )

    @app.exception_handler(Exception)
    async def _server_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500, content=_envelope("internal_error", "Internal server error.")
        )
