import json
import re

import pytest
from dirty_equals import IsStr
from fastapi import HTTPException, Request
from fastapi_log_utils.exception_handler import (
    format_and_log_exception_internal,
    format_and_log_exception_public,
    http_exception_handler,
)


@pytest.mark.parametrize(
    'exc',
    [(HTTPException(500, ['It should wrap this in a list'])), (HTTPException(500, 'It should wrap this in a list'))],
)
async def test_http_exception_handler(exc):
    response = await http_exception_handler(request=Request(scope={'type': 'http'}), exc=exc)
    assert json.loads(response.body.decode()) == {'detail': ['It should wrap this in a list']}


async def test_http_exception_handler_headers():
    exc = HTTPException(500, ['It should wrap this in a list'], {'some': 'header'})
    response = await http_exception_handler(request=Request(scope={'type': 'http'}), exc=exc)
    assert exc.headers == {'some': 'header', 'Access-Control-Expose-Headers': 'Correlation-ID', 'Correlation-ID': ''}
    assert dict(response.headers) == {
        'some': 'header',
        'correlation-id': '',
        'access-control-expose-headers': 'Correlation-ID',
        'content-length': IsStr,
        'content-type': 'application/json',
    }


async def test_http_exception_handler_no_headers():
    exc = HTTPException(500, ['It should wrap this in a list'])
    response = await http_exception_handler(request=Request(scope={'type': 'http'}), exc=exc)
    assert exc.headers is None
    assert dict(response.headers) == {
        'access-control-expose-headers': 'Correlation-ID',
        'content-length': IsStr,
        'content-type': 'application/json',
        'correlation-id': '',
    }


async def test_http_exception_handler_header_includes_access_expose():
    exc = HTTPException(
        500, ['It should wrap this in a list'], {'some': 'header', 'Access-Control-Expose-Headers': 'some'}
    )
    response = await http_exception_handler(request=Request(scope={'type': 'http'}), exc=exc)
    assert dict(response.headers) == {
        'access-control-expose-headers': 'some,Correlation-ID',
        'content-length': IsStr,
        'content-type': 'application/json',
        'correlation-id': '',
        'some': 'header',
    }


async def test_unhandled_exception_internal():
    exc = ValueError('Some value error')
    response = await format_and_log_exception_internal(request=Request(scope={'type': 'http'}), exc=exc)
    assert dict(response.headers) == {
        'access-control-expose-headers': 'Correlation-ID',
        'content-length': IsStr,
        'content-type': 'application/json',
        'correlation-id': '',
    }
    assert json.loads(response.body) == {
        'detail': [{'description': 'Internal Server Error', 'error': 'Some value error'}]
    }


async def test_unhandled_exception_public():
    exc = ValueError('Some value error')
    response = await format_and_log_exception_public(request=Request(scope={'type': 'http'}), exc=exc)
    assert dict(response.headers) == {
        'access-control-expose-headers': 'Correlation-ID',
        'content-length': IsStr,
        'content-type': 'application/json',
        'correlation-id': '',
    }
    assert json.loads(response.body) == {
        'detail': [{'description': 'Internal Server Error', 'error': 'Internal Server Error'}]
    }
