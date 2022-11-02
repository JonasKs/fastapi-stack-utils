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
            extra = {
                'user': request.headers.get('remote-user', 'Unknown'),
                'method': str(request.method),
                'path': str(request.url.path),
                # str(QueryParam) wrongly translates e.g. %20 into `+` instead of `space`
                'query': request.scope['query_string'].decode() if request.query_params else None,
                'str_body': bytes_body.decode() or None,
            }
            with contextlib.suppress(Exception):
                # override body with JSON if possible
                extra['str_body'] = str(await request.json())

            path_param_body = ' | '.join(filter(None, [extra['path'], extra['query'], extra['str_body']]))
            log.info(
                '%s > [%s] | %s',
                extra['user'],
                extra['method'],
                path_param_body,
                extra=extra,
            )
            response: Response = await original_route_handler(request)
            if request.method not in ['OPTIONS', 'GET', 'HEAD']:
                log.info('Response body: %s', response.body.decode())
                log.info('Response headers: %s', response.headers)
            return response

        return input_body_route_handler
