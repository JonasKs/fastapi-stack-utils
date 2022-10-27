from datetime import datetime
from logging import Filter, LogRecord
from time import time_ns
from typing import Protocol

import pytz


def get_time_in_nano_seconds() -> str:
    """
    Return timestamp in nanoseconds
    """
    # Get timestamp as nanoseconds
    nano_timestamp = time_ns()
    # Remove nanoseconds and convert into seconds with UTZ format
    date_time = datetime.fromtimestamp(nano_timestamp // 1000000000, tz=pytz.utc)
    return date_time.strftime(f'%Y-%m-%dT%H:%M:%S.{str(int(nano_timestamp % 1000000000)).zfill(9)}')


class NanoStamp(Filter):
    def filter(self, record: LogRecord) -> bool:
        """
        Filter for logging nanoseconds to Logstash on the `nanostamp` field.
        """
        record.nanostamp = get_time_in_nano_seconds()  # type: ignore[attr-defined]
        return True


class Settings(Protocol):
    ENVIRONMENT: str


def generate_base_logging_config(settings: Settings) -> dict:
    """
    Generate a base logging config
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'correlation_id': {
                '()': 'asgi_correlation_id.CorrelationIdFilter',
                'uuid_length': 8 if settings.ENVIRONMENT == 'dev' else 36,
            },
            'nanostamp': {'()': 'fastapi_stack_utils.logging_config.NanoStamp'},
        },
        'formatters': {
            'console': {
                'format': '%(levelname)-8s  [%(correlation_id)s] %(name)s:%(lineno)d    %(message)s',
            },
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': """
                    asctime: %(asctime)s
                    created: %(created)f
                    file_name: %(filename)s
                    func_Name: %(funcName)s
                    level_name: %(levelname)s
                    level: %(levelname)s
                    level_no: %(levelno)s
                    lineno: %(lineno)d
                    message: %(message)s
                    module: %(module)s
                    msec: %(msecs)d
                    name: %(name)s
                    pathname: %(pathname)s
                    process: %(process)d
                    process_name: %(processName)s
                    relative_created: %(relativeCreated)d
                    thread: %(thread)d
                    thread_name: %(threadName)s
                    exc_info: %(exc_info)s
                    correlation_id: %(correlation_id)s
                    nanostamp: %(nanostamp)s
                """,
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'filters': ['correlation_id', 'nanostamp'],
                'formatter': 'console',
            },
            'json': {
                'class': 'logging.StreamHandler',
                'filters': ['correlation_id', 'nanostamp'],
                'formatter': 'json',
            },
        },
        'loggers': {
            # third-party packages
            'asgi_correlation_id': {'level': 'WARNING'},
            'fastapi_audit_log': {'level': 'INFO'},
            'gunicorn': {'level': 'INFO'},
            'uvicorn': {'level': 'WARNING'},
        },
        'root': {
            'handlers': ['console'] if settings.ENVIRONMENT in ['dev', 'test'] else ['json'],
            'level': 'DEBUG' if settings.ENVIRONMENT in ['dev', 'test'] else 'INFO',
        },
    }
