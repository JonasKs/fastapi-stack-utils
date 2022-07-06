import contextlib
import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute

log = logging.getLogger('fastapi_stack_utils.route')


class AuditLog(APIRoute):
    def get_route_handler(self) -> Callable:
        """
        Overrides `get_route_handler`
        """
        original_route_handler = super().get_route_handler()

        async def input_body_route_handler(request: Request) -> Response:
            """
            Replacement of route_handler that will attempt to log input body
            """
            bytes_body = await request.body()
            str_body: str = ''
            if isinstance(bytes_body, bytes):
                str_body = bytes_body.decode()
            extra = {
                'method': request.method,
                'path': request.url.path,
                'query': request.query_params,
                'body': str_body,
            }
            with contextlib.suppress(Exception):
                # override body with JSON if possible
                extra['body'] = await request.json()
            if extra['body']:
                log.info('Input body: %s', extra['body'], extra=extra)
            response: Response = await original_route_handler(request)
            if 'method' not in ['OPTIONS', 'GET', 'HEAD']:
                log.info('Response body: %s', response.body.decode())
                log.info('Response headers: %s', response.headers)
            return response

        return input_body_route_handler
