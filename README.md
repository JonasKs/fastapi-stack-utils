# fastapi-stack-utils

A small package to extend the FastAPI stack a bit:

* Log middleware and route handler (which compliments each other)
* Exception handlers with logging
* Consistent responses
* Util to properly inject middlewares into FastAPI, so that unhandled exceptions still pass through middlewares
  * Usable for correlation IDs, CORS, audit logging etc
  * See [docstring here](https://github.com/JonasKs/fastapi-stack-utils/blob/29a03ec70ca8f8662bd1efcb0b948e3913bb845b/fastapi_stack_utils/middleware.py#L16-L44)

### Install and implement

```bash 
poetry add fastapi-stack-utils
```

Add exception handlers and middleware to project `main.py`:

```python
from fastapi_stack_utils.exception_handler import http_exception_handler, format_and_log_exception_internal
from fastapi_stack_utils.middleware import LoggingMiddleware, patch_fastapi_middlewares

patch_fastapi_middlewares(  # this must be done _before_  FastAPI is initialized
    middlewares=[
        Middleware(LoggingMiddleware),
        # Alternatively other middlewares you would like to be run even when 500 server errors occur:
        # Middleware(
        #    CORSMiddleware,
        #    allow_credentials=True,
        #    allow_headers=['*'],
        #    allow_methods=['*'],
        #    allow_origins=['*'],
        # ),
        # Middleware(CorrelationIdMiddleware, header_name='Correlation-ID'),
    ]
)

# If you have Sentry, initialize this here:
# sentry_sdk.init(
#     dsn='...',
#     integrations=[StarletteIntegration(), FastApiIntegration()],
# )

app = FastAPI()  # this must be done _after_ `patch_fastapi_middlewares()` is called 
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, format_and_log_exception_internal)
```

Add route class to all routes _closest_ to the view (`app/api/api_v1/endpoints/<file.py>`)
```python
from fastapi_stack_utils.route import AuditLog
router = APIRouter(route_class=AuditLog)
```
