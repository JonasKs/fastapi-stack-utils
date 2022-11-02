import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_stack_utils.schemas.http_exceptions import ErrorResponse, ServerError

log = logging.getLogger('fastapi_stack_utils')


def generate_json_response(
    response_body: ErrorResponse, status_code: int, headers: dict[str, str] | None = None
) -> JSONResponse:
    """
    Generate a JSON response with correlation ID attached
    """
    return JSONResponse(content=response_body.dict(), status_code=status_code, headers=headers)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Forces the HTTPException output to be of the correct format. Respects status_code raised.
    """
    # We truly have to handle all scenarios, FastAPI allows detail to be `Any`, even though
    # Starlette only allows Optional[str].....
    # https://github.com/tiangolo/fastapi/blob/c5be1b0550f17d827721a5be1dc4344e73b1993f
    # /docs_src/custom_request_and_route/tutorial002.py#L17-L18
    formatted_errors: list[ServerError]
    detail: Any = exc.detail
    if isinstance(detail, (list, tuple)):
        formatted_errors = [ServerError(description=str(element), error=str(element)) for element in detail]
    else:
        formatted_errors = [ServerError(description=str(detail), error=str(detail))]
    return generate_json_response(
        response_body=ErrorResponse(detail=formatted_errors),
        status_code=exc.status_code,
        headers=getattr(exc, 'headers', None) or {},
    )


async def format_and_log_exception_internal(request: Request, exc: Exception) -> JSONResponse:
    """
    Log an error when unhandled exceptions surface an endpoint.
    This exception handler should only be used for internal systems, as it provides the str(exc) in return.
    For customer facing errors, please use `format_and_log_exception_public`
    """
    log.exception('Unhandled exception raised in endpoint: %s', exc)
    response_body = ErrorResponse(detail=[ServerError(description='Internal Server Error', error=str(exc))])
    return generate_json_response(response_body=response_body, status_code=500)


async def format_and_log_exception_public(request: Request, exc: Exception) -> JSONResponse:
    """
    Log an error when unhandled exceptions surface an endpoint.
    This exception handler will hide the actual exception.
    For customer facing errors, please use `format_and_log_exception_public`
    """
    log.exception('Unhandled exception raised in endpoint: %s', exc)
    response_body = ErrorResponse(
        detail=[ServerError(description='Internal Server Error', error='Internal Server Error')]
    )
    return generate_json_response(response_body=response_body, status_code=500)
