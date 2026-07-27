"""Standard error model (RFC7807-like) and exception handling.

Implements the contract's error envelope with exactly these fields:
``type``, ``title``, ``status``, ``detail``, ``instance``, ``code``,
``correlation_id`` and ``errors[]``. Also defines the standard error codes and
the FastAPI exception handlers that render ``application/problem+json``.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.logging import get_correlation_id

logger = logging.getLogger(__name__)

PROBLEM_CONTENT_TYPE = "application/problem+json"


# --- Standard error codes (contract Section 4.3) -------------------------- #
class ErrorCode:
    """Canonical error ``code`` values as defined by the API contract."""

    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    ALERT_NOT_FOUND = "alert_not_found"
    WORK_ORDER_NOT_FOUND = "work_order_not_found"
    DUPLICATE_WORK_ORDER = "duplicate_work_order"
    INVALID_STATE = "invalid_state"
    INVALID_REQUEST = "invalid_request"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    INTERNAL_ERROR = "internal_error"


# Default human-readable titles per code.
_TITLES: dict[str, str] = {
    ErrorCode.UNAUTHORIZED: "Unauthorized",
    ErrorCode.FORBIDDEN: "Forbidden",
    ErrorCode.ALERT_NOT_FOUND: "Alert Not Found",
    ErrorCode.WORK_ORDER_NOT_FOUND: "Work Order Not Found",
    ErrorCode.DUPLICATE_WORK_ORDER: "Duplicate Work Order",
    ErrorCode.INVALID_STATE: "Invalid State",
    ErrorCode.INVALID_REQUEST: "Invalid Request",
    ErrorCode.DEPENDENCY_UNAVAILABLE: "Dependency Unavailable",
    ErrorCode.INTERNAL_ERROR: "Internal Server Error",
}


# PUBLIC_INTERFACE
class ErrorItem(BaseModel):
    """A single field-level error entry within ``errors[]``."""

    field: str | None = Field(
        default=None, description="Name of the offending field, if applicable."
    )
    message: str = Field(..., description="Human-readable error message.")
    rule: str | None = Field(
        default=None, description="Validation rule that was violated."
    )
    expected: str | None = Field(
        default=None, description="Expected value/constraint, if applicable."
    )


# PUBLIC_INTERFACE
class Problem(BaseModel):
    """RFC7807-like problem details envelope returned on every error."""

    type: str = Field(..., description="URI identifying the problem type.")
    title: str = Field(..., description="Short, human-readable summary.")
    status: int = Field(..., description="HTTP status code.")
    detail: str | None = Field(
        default=None, description="Human-readable explanation of this occurrence."
    )
    instance: str | None = Field(
        default=None, description="URI reference identifying this occurrence."
    )
    code: str = Field(..., description="Stable machine-readable error code.")
    correlation_id: str | None = Field(
        default=None, description="Correlation id for tracing this request."
    )
    errors: list[ErrorItem] = Field(
        default_factory=list, description="Field-level error details."
    )


# PUBLIC_INTERFACE
class ProblemException(Exception):
    """Raise to short-circuit a request with an RFC7807 problem response.

    Args:
        status: HTTP status code.
        code: One of :class:`ErrorCode` values.
        detail: Human-readable explanation for this occurrence.
        errors: Optional list of field-level error entries.
        title: Optional override for the problem title.
    """

    def __init__(
        self,
        status: int,
        code: str,
        detail: str | None = None,
        errors: list[ErrorItem] | None = None,
        title: str | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.detail = detail
        self.errors = errors or []
        self.title = title or _TITLES.get(code, "Error")
        super().__init__(detail or code)


def _type_uri(code: str) -> str:
    """Build the problem ``type`` URI for a given error code."""
    return f"{get_settings().problem_base_uri}/{code}"


def _render(problem: Problem) -> JSONResponse:
    """Serialize a :class:`Problem` into a problem+json response."""
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(),
        media_type=PROBLEM_CONTENT_TYPE,
    )


def _build_problem(
    request: Request,
    status: int,
    code: str,
    detail: str | None,
    errors: list[ErrorItem] | None,
    title: str | None = None,
) -> Problem:
    """Assemble a :class:`Problem` from request context and error data."""
    return Problem(
        type=_type_uri(code),
        title=title or _TITLES.get(code, "Error"),
        status=status,
        detail=detail,
        instance=str(request.url.path),
        code=code,
        correlation_id=get_correlation_id() or None,
        errors=errors or [],
    )


async def _problem_exception_handler(
    request: Request, exc: ProblemException
) -> JSONResponse:
    """Handle explicitly raised :class:`ProblemException` instances."""
    problem = _build_problem(
        request, exc.status, exc.code, exc.detail, exc.errors, exc.title
    )
    return _render(problem)


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Map Pydantic/FastAPI validation failures to ``invalid_request`` (422)."""
    errors: list[ErrorItem] = []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", []) if p not in ("body",)]
        field = ".".join(loc) if loc else None
        errors.append(
            ErrorItem(
                field=field,
                message=err.get("msg", "Invalid value"),
                rule=err.get("type"),
            )
        )
    problem = _build_problem(
        request,
        422,
        ErrorCode.INVALID_REQUEST,
        "Request validation failed.",
        errors,
    )
    return _render(problem)


async def _http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Map generic HTTP exceptions (e.g., 404 routing) to the problem model."""
    code = ErrorCode.INTERNAL_ERROR
    if exc.status_code == 404:
        code = ErrorCode.WORK_ORDER_NOT_FOUND
    elif exc.status_code == 401:
        code = ErrorCode.UNAUTHORIZED
    elif exc.status_code == 403:
        code = ErrorCode.FORBIDDEN
    elif exc.status_code == 422:
        code = ErrorCode.INVALID_REQUEST
    problem = _build_problem(
        request, exc.status_code, code, str(exc.detail), None
    )
    return _render(problem)


async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler mapping unexpected errors to ``internal_error``."""
    logger.exception("Unhandled error: %s", exc)
    problem = _build_problem(
        request,
        500,
        ErrorCode.INTERNAL_ERROR,
        "An unexpected error occurred.",
        None,
    )
    return _render(problem)


# PUBLIC_INTERFACE
def register_exception_handlers(app: FastAPI) -> None:
    """Register all problem-model exception handlers on the app.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(ProblemException, _problem_exception_handler)
    app.add_exception_handler(
        RequestValidationError, _validation_exception_handler
    )
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)


# PUBLIC_INTERFACE
def problem_responses(*codes: int) -> dict[int, dict[str, Any]]:
    """Build an OpenAPI ``responses`` map documenting the problem schema.

    Args:
        *codes: HTTP status codes to document as returning a problem body.

    Returns:
        dict: A mapping suitable for a route's ``responses`` argument.
    """
    return {
        code: {
            "model": Problem,
            "description": _TITLES_BY_STATUS.get(code, "Error"),
            "content": {PROBLEM_CONTENT_TYPE: {}},
        }
        for code in codes
    }


_TITLES_BY_STATUS: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Validation Error",
    500: "Internal Server Error",
    503: "Service Unavailable",
}
