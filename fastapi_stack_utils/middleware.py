import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from starlette.datastructures import Headers

if TYPE_CHECKING:  # pragma: no cover
    from typing import Callable

    from starlette.middleware import Middleware
    from starlette.types import ASGIApp, Receive, Scope, Send

log = logging.getLogger('fastapi_stack_utils.middleware')


def patch_fastapi_middlewares(middlewares: list['Middleware']) -> None:
    """
    This function will take a list of Middleware(), and replace(extend) the `build_middleware_stack` function in
    FastAPI.
    This means, when you initialize FastAPI(title=...), the `build_new_middleware_stack`-function below
    will be called, instead of `build_middleware_stack` shipped with FastAPI.

    In Starlette applications there are always two middlewares added:
    * `ServerErrorMiddleware` is added as the very outermost middleware, to handle
      any uncaught errors occurring anywhere in the entire stack. (Errors not handled by ExceptionMiddleware)
    * `ExceptionMiddleware` is added as the very innermost middleware, to deal
    with _handled_ exception cases occurring in the routing or endpoints.

    The normal FastAPI middleware stack looks something like this, when using `add_middleware`:
      FastAPI.middleware_stack
        -> ServerErrorMiddleware
          -> CorrelationIdMiddleware
            -> CorsMiddleware
              -> ExceptionMiddleware

    Since the `ServerErrorMiddleware` overrides any uncaught error response, anything we did with the response in
    previous middlewares are overwritten.

    That's why we want this behaviour instead:
      FastAPI.middleware_stack
        -> CorrelationIdMiddleware
          -> CORSMiddleware
            -> ServerErrorMiddleware
              -> ExceptionMiddleware

    Here, we can see that _after_ ServerErrorMiddleware(and ExceptionMiddleware for handled exceptions)
    has done its work, the request will still go through our CorrelationID and CORS middlewares.
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

        # Try to load request ID from the request headers
        user = Headers(scope=scope).get('remote-user', 'Unknown')
        extra = {
            'user': user,
            'method': scope.get('method', ''),
            'path': scope.get('path', ''),
            'query_string': scope.get('query_string', b'').decode(),
        }
        log.info(
            '%s > [%s] %s %s',
            extra['user'],
            extra['method'],
            extra['path'],
            extra['query_string'],
            extra=extra,
        )
        await self.app(scope, receive, send)
        return
