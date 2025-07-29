from pydantic import BaseModel, Field


class BaseResponseSchema(BaseModel):
    detail: str


class BaseResponseIdSchema(BaseModel):
    id: int


class PaginationSchema(BaseModel):
    limit: int = Field(10, ge=1, le=50)
    page: int = Field(1, ge=1)


class SearchResponseSchema[T](BaseModel):
    detail: list[T]
    pagination: PaginationSchema
    total_found: int
