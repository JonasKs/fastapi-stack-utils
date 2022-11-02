import asyncio
from logging.config import dictConfig

import pytest
import pytest_asyncio
from fastapi import APIRouter, FastAPI
from fastapi_stack_utils.logging_config import generate_base_logging_config
from fastapi_stack_utils.route import AuditLog
from httpx import AsyncClient
from pydantic import BaseModel, BaseSettings


@pytest.fixture(autouse=True, scope='session')
def _configure_logging():
    class Settings(BaseSettings):
        ENVIRONMENT: str = 'dev'

    dictConfig(generate_base_logging_config(settings=Settings()))


fastapi_app = FastAPI()


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
