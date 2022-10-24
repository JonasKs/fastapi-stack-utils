from typing import List, Optional

from pydantic import BaseModel, Field


class DefaultError(BaseModel):
    description: Optional[str] = Field(
        default=None,
        title='Informative description of the error',
        description='Equal or more verbose error message',
    )
    error: Optional[str] = Field(
        default=None, title='Object not found', description='Object x does not exist under resource y'
    )


class ValidationError(BaseModel):
    loc: Optional[List[str]] = Field(default=None, title='Location of error', description='param, subnet_id')
    msg: Optional[str] = Field(default=None, title='Reason for error', description='Found 2 ranges for 192.168.0.0/24')
    type: Optional[str] = Field(default=None, title='What type of validation error', description='value_error.invalid')


class ServerError(DefaultError, ValidationError):
    ...


class ErrorResponse(BaseModel):
    detail: list[ServerError]
