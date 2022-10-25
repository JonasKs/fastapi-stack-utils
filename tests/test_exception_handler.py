import json
import re

import pytest
from dirty_equals import IsStr
from fastapi import HTTPException, Request
from fastapi_stack_utils.exception_handler import (
    format_and_log_exception_internal,
    format_and_log_exception_public,
    http_exception_handler,
)


@pytest.mark.parametrize(
    'exception, expected',
    [
        (
            HTTPException(
                500, [{'description': 'It should wrap this in a list', 'error': 'It should wrap this in a list'}]
            ),
            [{'description': 'It should wrap this in a list', 'error': 'It should wrap this in a list'}],
        ),
        (
            HTTPException(
                500, {'description': 'It should wrap this in a list', 'error': 'It should wrap this in a list'}
            ),
            [{'description': 'It should wrap this in a list', 'error': 'It should wrap this in a list'}],
        ),
        (
            HTTPException(
                422,
                {'loc': ['param', 'subnet_id'], 'msg': 'It should wrap this in a list', 'type': 'value_error.invalid'},
            ),
            [{'loc': ['param', 'subnet_id'], 'msg': 'It should wrap this in a list', 'type': 'value_error.invalid'}],
        ),
        (
            HTTPException(
                422,
                [
                    {
                        'loc': ['param', 'subnet_id'],
                        'msg': 'It should wrap this in a list',
                        'type': 'value_error.invalid',
                    }
                ],
            ),
            [{'loc': ['param', 'subnet_id'], 'msg': 'It should wrap this in a list', 'type': 'value_error.invalid'}],
        ),
    ],
)
async def test_http_exception_handler(exception, expected):
    response = await http_exception_handler(request=Request(scope={'type': 'http'}), exc=exception)
    assert json.loads(response.body.decode()) == {'detail': expected}


class X:
    def __init__(self):
        self.a = 'yolo'

    def __repr__(self):
        return repr(self.a)


@pytest.mark.parametrize(
    'exc, expected',
    [
        (
            HTTPException(500, {'errors': 'hello', 'body': 'world'}),
            {
                'detail': [
                    {
                        'description': "{'errors': 'hello', 'body': 'world'}",
                        'error': "{'errors': 'hello', 'body': 'world'}",
                    }
                ]
            },
        ),
        (HTTPException(500, X()), {'detail': [{'description': "'yolo'", 'error': "'yolo'"}]}),
        (HTTPException(500, [X()]), {'detail': [{'description': "'yolo'", 'error': "'yolo'"}]}),
        (HTTPException(422, [X()]), {'detail': [{'description': "'yolo'", 'error': "'yolo'"}]}),
    ],
)
async def test_exception_handler_random_types(exc, expected):
    response = await http_exception_handler(request=Request(scope={'type': 'http'}), exc=exc)
    assert json.loads(response.body.decode()) == expected


async def test_http_exception_handler_headers():
    exc = HTTPException(
        500,
        {'description': 'It should wrap this in a list', 'error': 'It should wrap this in a list'},
        {'some': 'header'},
    )
    response = await http_exception_handler(request=Request(scope={'type': 'http'}), exc=exc)
    assert exc.headers == {'some': 'header'}
    assert dict(response.headers) == {
        'some': 'header',
        'content-length': IsStr,
        'content-type': 'application/json',
    }


async def test_http_exception_handler_no_headers():
    exc = HTTPException(500, {'description': 'It should wrap this in a list', 'error': 'It should wrap this in a list'})
    response = await http_exception_handler(request=Request(scope={'type': 'http'}), exc=exc)
    assert exc.headers is None
    assert dict(response.headers) == {
        'content-length': IsStr,
        'content-type': 'application/json',
    }


async def test_http_exception_handler_header_includes_access_expose():
    exc = HTTPException(
        500,
        {'description': 'It should wrap this in a list', 'error': 'It should wrap this in a list'},
        {'some': 'header', 'Access-Control-Expose-Headers': 'some'},
    )
    response = await http_exception_handler(request=Request(scope={'type': 'http'}), exc=exc)
    assert dict(response.headers) == {
        'access-control-expose-headers': 'some',
        'content-length': IsStr,
        'content-type': 'application/json',
        'some': 'header',
    }


async def test_unhandled_exception_internal():
    exc = ValueError('Some value error')
    response = await format_and_log_exception_internal(request=Request(scope={'type': 'http'}), exc=exc)
    assert dict(response.headers) == {
        'content-length': IsStr,
        'content-type': 'application/json',
    }
    assert json.loads(response.body) == {
        'detail': [{'description': 'Internal Server Error', 'error': 'Some value error'}]
    }


async def test_unhandled_exception_public():
    exc = ValueError('Some value error')
    response = await format_and_log_exception_public(request=Request(scope={'type': 'http'}), exc=exc)
    assert dict(response.headers) == {
        'content-length': IsStr,
        'content-type': 'application/json',
    }
    assert json.loads(response.body) == {
        'detail': [{'description': 'Internal Server Error', 'error': 'Internal Server Error'}]
    }
