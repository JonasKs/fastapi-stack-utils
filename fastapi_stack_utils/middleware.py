import logging
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI

if TYPE_CHECKING:  # pragma: no cover
    from typing import Callable

    from starlette.middleware import Middleware

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
