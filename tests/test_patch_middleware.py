from uuid import uuid4

from asgi_correlation_id import CorrelationIdMiddleware
from dirty_equals import IsUUID
from fastapi import FastAPI
from fastapi_stack_utils.middleware import LoggingMiddleware, patch_fastapi_middlewares
from httpx import AsyncClient
from starlette.middleware import Middleware

patch_fastapi_middlewares(
    middlewares=[
        Middleware(LoggingMiddleware),
        Middleware(CorrelationIdMiddleware, header_name='Correlation-ID', generator=lambda: str(uuid4())),
    ]
)
fastapi_app = FastAPI()


@fastapi_app.get('/view')
async def view():
    return {'message': 'Pure view'}


async def test_overrides_properly():
    async with AsyncClient(app=fastapi_app, base_url='http://test') as app_client:
        response = await app_client.get('/view')
        assert response.json() == {'message': 'Pure view'}
        assert 'correlation-id' in response.headers
        assert response.headers.get('correlation-id') == IsUUID
