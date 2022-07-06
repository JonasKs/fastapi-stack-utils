import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from starlette.types import ASGIApp, Receive, Scope, Send

log = logging.getLogger('fastapi_stack_utils.middleware')


@dataclass
class LoggingMiddleware:
    app: 'ASGIApp'

    async def __call__(self, scope: 'Scope', receive: 'Receive', send: 'Send') -> None:
        """
        Attempt to log path, method etc.
        Input body will not be logged - check out route.AuditLog()
        """
        # Only handle http requests
        if scope['type'] != 'http':  # pragma: no cover
            return await self.app(scope, receive, send)
        extra = {
            'method': scope.get('method', ''),
            'path': scope.get('path', ''),
            'query_string': scope.get('query_string', b'').decode(),
        }
        log.info(
            '[%s] %s %s',
            extra['method'],
            extra['path'],
            extra['query_string'],
            extra=extra,
        )
        await self.app(scope, receive, send)
        return
