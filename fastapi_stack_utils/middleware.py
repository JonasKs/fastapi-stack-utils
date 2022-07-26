import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI

if TYPE_CHECKING:  # pragma: no cover
    from typing import Callable

    from starlette.middleware import Middleware
    from starlette.types import ASGIApp, Receive, Scope, Send

log = logging.getLogger('fastapi_stack_utils.middleware')


def patch_fastapi_middlewares(middlewares: list['Middleware']) -> None:
    """
    This function will take a list of Middleware(), and replace the `build_middleware_stack` function in
    FastAPI. This means, when you initialize FastAPI(title=...), the `build_new_middleware_stack`-function below
    will be called, instead of `build_middleware_stack` shipped with FastAPI.
    This behaviour is a bit different from `add_middleware` (where the middleware is added to FastAPI), since
    we are now adding FastAPI to our middlewares. In other words, `app` can now be something like this:
        CorrelationIdMiddleware(app=FastAPI())
    Instead of
        FastAPI(middleware=CorrelationIdMiddleware())

    This approach allow us to define `app = FastAPI()` and still do `app.include_router()` etc. in this file.

    We do this because we want FastAPI to fail, and then still pass on the response through our middlewares.
    With `add_middleware()`, any unhandled exception would not go through middlewares on response, but with this
    approach, the response will always be propagated to these middlewares.
    """
    current_middleware_stack = FastAPI.build_middleware_stack

    def _build_new_middleware_stack(self: FastAPI) -> 'Callable[..., Any]':
        """
        Wrap the FastAPI app with given middlewares, while keeping the previously wrapped ones
        """
        app = current_middleware_stack(self)
        for middleware in middlewares:
            app = middleware.cls(app, **middleware.options)
        return app

    FastAPI.build_middleware_stack = _build_new_middleware_stack  # type: ignore


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
