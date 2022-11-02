from pydantic import BaseModel, Field


class DefaultError(BaseModel):
    description: str = Field(
        ...,
        title='Informative description of the error',
        description='Equal or more verbose error message',
    )
    error: str = Field(..., title='Object not found', description='Object x does not exist under resource y')


class ServerError(DefaultError):
    ...


class ErrorResponse(BaseModel):
    detail: list[ServerError]
