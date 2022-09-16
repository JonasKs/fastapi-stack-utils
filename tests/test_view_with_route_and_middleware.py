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
                "Input body: {'a': 'hehe', 'b': 'hoho', 'c': ['tihi', 123]}",
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
                "Input body: {'bad object': 'lol'}",
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
