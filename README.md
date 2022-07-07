# fastapi-stack-utils

A small package to extend the FastAPI stack a bit:

* Log middleware and route handler (which compliments each other)
* Exception handlers with logging
* Consistent responses

### Install and implement

```bash 
poetry add fastapi-stack-utils
```

Add exception handlers and middleware to project `main.py`:

```python
from fastapi_stack_utils.exception_handler import http_exception_handler, format_and_log_exception_internal
from fastapi_stack_utils.middleware import LoggingMiddleware
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, format_and_log_exception_internal)
app.add_middleware(LoggingMiddleware)
```

Add route class to all routes _closest_ to the view (`app/api/api_v1/endpoints/<file.py>`)
```python
from fastapi_stack_utils.route import AuditLog
router = APIRouter(route_class=AuditLog)
```
