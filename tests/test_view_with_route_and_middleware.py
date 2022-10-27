import json
import logging

import pytest
from fastapi_stack_utils.logging_config import get_time_in_nano_seconds

logger = logging.getLogger('fastapi_stack_utils')


@pytest.mark.parametrize(
    'method,path,logs,expected_response',
    (
        [
            'GET',
            'logged',
            ['Jonas > [GET] /logged ', 'HTTP Request: GET http://test/logged "HTTP/1.1 200 OK"'],
            {'message': 'Pure view'},
        ],
        [
            'GET',
            '/logged/hello?query_param=hehe',
            [
                'Jonas > [GET] /logged/hello query_param=hehe',
                'HTTP Request: GET http://test/logged/hello?query_param=hehe "HTTP/1.1 200 OK"',
            ],
            {'message': 'hellohehe'},
        ],
    ),
)
async def test_input_logged_get(method, path, logs, expected_response, client, caplog, freezer):
    response = await client.request(method=method, url=path, headers={'Remote-User': 'Jonas'})
    assert caplog.messages == logs
    assert caplog.records[0].nanostamp == get_time_in_nano_seconds()
    assert response.json() == expected_response


@pytest.mark.parametrize(
    'method,path,input_body,logs,expected_response',
    (
        [
            'POST',
            '/logged/hello?query_param=hehe',
            {'a': 'hehe', 'b': 'hoho', 'c': ['tihi', 123]},
            [
                'Unknown > [POST] /logged/hello query_param=hehe',
                "Unknown sent body: {'a': 'hehe', 'b': 'hoho', 'c': ['tihi', 123]}",
                'Response body: {"message":"hello: {\'a\': \'hehe\', \'b\': \'hoho\', \'c\': ' '[\'tihi\', \'123\']}"}',
                "Response headers: MutableHeaders({'content-length': '69', 'content-type': " "'application/json'})",
                'HTTP Request: POST http://test/logged/hello?query_param=hehe "HTTP/1.1 200 ' 'OK"',
            ],
            {'message': "hello: {'a': 'hehe', 'b': 'hoho', 'c': ['tihi', '123']}"},
        ],
        [
            'POST',
            '/logged/hello?query_param=hehe',
            {'bad object': 'lol'},
            [
                'Unknown > [POST] /logged/hello query_param=hehe',
                "Unknown sent body: {'bad object': 'lol'}",
                'HTTP Request: POST http://test/logged/hello?query_param=hehe "HTTP/1.1 422 ' 'Unprocessable Entity"',
            ],
            {
                'detail': [
                    {'loc': ['body', 'a'], 'msg': 'field required', 'type': 'value_error.missing'},
                    {'loc': ['body', 'b'], 'msg': 'field required', 'type': 'value_error.missing'},
                    {'loc': ['body', 'c'], 'msg': 'field required', 'type': 'value_error.missing'},
                ]
            },
        ],
    ),
)
async def test_input_logged_post(method, path, input_body, logs, expected_response, client, caplog):
    response = await client.request(method, path, data=json.dumps(input_body))
    assert caplog.messages == logs
    assert response.json() == expected_response


async def test_input_logged_post_user(client, caplog):
    await client.request(
        method='POST', url='/logged/hello', data=json.dumps({'hello': 'world'}), headers={'remote-user': 'Jonas'}
    )
    assert caplog.messages == [
        'Jonas > [POST] /logged/hello ',
        "Jonas sent body: {'hello': 'world'}",
        'HTTP Request: POST http://test/logged/hello "HTTP/1.1 422 Unprocessable ' 'Entity"',
    ]


async def test_openapi_unknown_user_not_logged(client, caplog):
    await client.request(method='GET', url='/api/v1/openapi.json')
    assert caplog.messages == ['HTTP Request: GET http://test/api/v1/openapi.json "HTTP/1.1 404 Not Found"']


async def test_openapi_but_with_user_is_logged(client, caplog):
    await client.request(method='GET', url='/api/v1/openapi.json', headers={'remote-user': 'Jonas'})
    assert caplog.messages == [
        'Jonas > [GET] /api/v1/openapi.json ',
        'HTTP Request: GET http://test/api/v1/openapi.json "HTTP/1.1 404 Not Found"',
    ]
