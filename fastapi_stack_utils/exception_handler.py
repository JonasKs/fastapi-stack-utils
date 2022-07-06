import logging

from asgi_correlation_id.context import correlation_id
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

log = logging.getLogger('fastapi_stack_utils')


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Forces the HTTPException output to contain a list in the `detail`-key
    """
    headers = getattr(exc, 'headers', {}) or {}
    headers['Correlation-ID'] = correlation_id.get('')
    if 'Access-Control-Expose-Headers' not in headers:
        headers['Access-Control-Expose-Headers'] = 'Correlation-ID'
    if 'Correlation-ID' not in headers.get('Access-Control-Expose-Headers', ''):
        headers['Access-Control-Expose-Headers'] += ',Correlation-ID'
    else:
        headers['Access-Control-Expose-Headers'] = 'Correlation-ID'
    detail: list = exc.detail if isinstance(exc.detail, list) else [exc.detail]  # type: ignore
    return JSONResponse(
        content={'detail': detail},
        status_code=exc.status_code,
        headers=headers,
    )


def generate_json_response(response_body: dict) -> JSONResponse:
    """
    Generate a JSON response with correlation ID attached
    """
    return JSONResponse(
        content=response_body,
        status_code=500,
        headers={'Correlation-ID': correlation_id.get(''), 'Access-Control-Expose-Headers': 'Correlation-ID'},
    )


async def format_and_log_exception_internal(request: Request, exc: Exception) -> JSONResponse:
    """
    Log an error when unhandled exceptions surface an endpoint.
    This exception handler should only be used for internal systems, as it provides the str(exc) in return.
    For customer facing errors, please use `format_and_log_exception_public`
    """
    log.exception('Unhandled exception raised in endpoint')
    response_body = {'detail': [{'description': 'Internal Server Error', 'error': str(exc)}]}
    return generate_json_response(response_body=response_body)


async def format_and_log_exception_public(request: Request, exc: Exception) -> JSONResponse:
    """
    Log an error when unhandled exceptions surface an endpoint.
    This exception handler will hide the actual exception.
    For customer facing errors, please use `format_and_log_exception_public`
    """
    log.exception('Unhandled exception raised in endpoint')
    response_body = {'detail': [{'description': 'Internal Server Error', 'error': 'Internal Server Error'}]}
    return generate_json_response(response_body=response_body)
