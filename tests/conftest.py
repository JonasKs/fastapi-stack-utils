import asyncio
from logging.config import dictConfig

import pytest
import pytest_asyncio
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi_log_utils.middleware import LoggingMiddleware
from fastapi_log_utils.route import AuditLog
from httpx import AsyncClient
from pydantic import BaseModel
from starlette.middleware import Middleware


@pytest.fixture(autouse=True, scope='session')
def _configure_logging():
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'basic': {
                'class': 'logging.Formatter',
                'datefmt': '%H:%M:%S',
                'format': '%(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'basic',
            },
        },
        'loggers': {
            'fastapi_stack_utils': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }
    dictConfig(LOGGING)


fastapi_app = FastAPI(middleware=[Middleware(LoggingMiddleware)])
router = APIRouter(route_class=AuditLog)


@router.get('/logged')
async def logged():
    return {'message': 'Pure view'}


@router.get('/logged/{param}')
async def logged_path_query(param: str, query_param: str):
    return {'message': f'{param}{query_param}'}


class InputBody(BaseModel):
    a: str
    b: str
    c: list[str | int]


@router.post('/logged/{param}')
async def logged_path_query(param: str, body: InputBody):
    print({'message': f'{param}: {body.dict()}'})
    return {'message': f'{param}: {body.dict()}'}


fastapi_app.include_router(router=router)


@pytest.fixture(scope='session', autouse=True)
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='module')
async def client() -> AsyncClient:
    async with AsyncClient(app=fastapi_app, base_url='http://test') as app_client:
        yield app_client
