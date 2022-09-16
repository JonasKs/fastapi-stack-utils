import pytest
from fastapi_stack_utils.logging_config import generate_base_logging_config
from pydantic import BaseSettings


def test_ok_if_using_base_settings_with_correct_attribute():
    class Settings(BaseSettings):
        ENVIRONMENT: str = 'dev'

    settings = Settings()
    generate_base_logging_config(settings=settings)


def test_fails_if_not_valid_settings():
    class Settings(BaseSettings):
        lol: str = 'dev'

    settings = Settings()
    with pytest.raises(AttributeError):
        generate_base_logging_config(settings=settings)
