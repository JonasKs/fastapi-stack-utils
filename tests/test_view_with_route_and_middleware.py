import json
import logging

import pytest

logger = logging.getLogger('fastapi_stack_utils')


@pytest.mark.parametrize(
    'method,path,logs,expected_response',
    (
        [
            'GET',
            'logged',
            [
                '[GET] /logged ',
                'Response body: {"message":"Pure view"}',
                "Response headers: MutableHeaders({'content-length': '23', 'content-type': " "'application/json'})",
            ],
            {'message': 'Pure view'},
        ],
        [
            'GET',
            '/logged/hello?query_param=hehe',
            [
                '[GET] /logged/hello query_param=hehe',
                'Response body: {"message":"hellohehe"}',
                "Response headers: MutableHeaders({'content-length': '23', 'content-type': " "'application/json'})",
            ],
            {'message': 'hellohehe'},
        ],
    ),
)
async def test_input_logged_get(method, path, logs, expected_response, client, caplog):
    response = await client.request(method, path)
    assert caplog.messages == logs
    assert response.json() == expected_response


@pytest.mark.parametrize(
    'method,path,input_body,logs,expected_response',
    (
        [
            'POST',
            '/logged/hello?query_param=hehe',
            {'a': 'hehe', 'b': 'hoho', 'c': ['tihi', 123]},
            [
                '[POST] /logged/hello query_param=hehe',
                "Input body: {'a': 'hehe', 'b': 'hoho', 'c': ['tihi', 123]}",
                'Response body: {"message":"hello: {\'a\': \'hehe\', \'b\': \'hoho\', \'c\': ' '[\'tihi\', \'123\']}"}',
                "Response headers: MutableHeaders({'content-length': '69', 'content-type': " "'application/json'})",
            ],
            {'message': "hello: {'a': 'hehe', 'b': 'hoho', 'c': ['tihi', '123']}"},
        ],
        [
            'POST',
            '/logged/hello?query_param=hehe',
            {'bad object': 'lol'},
            [
                '[POST] /logged/hello query_param=hehe',
                "Input body: {'bad object': 'lol'}",
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
