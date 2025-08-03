from typing import Literal, Optional

from pydantic import BaseModel, Field


class BaseResponseSchema(BaseModel):
    detail: str


class BaseResponseIdSchema(BaseModel):
    id: int


class PaginationSchema(BaseModel):
    limit: int = Field(10, ge=1, le=50)
    page: int = Field(1, ge=1)

    @property
    def page_offset(self):
        return (self.page - 1) * self.limit


class FiltersSchema(BaseModel):
    query: Optional[str] = Field(None, min_length=2, max_length=100)
    order_by: Literal["desc", "asc"] = Field("asc", alias="orderBy")


class SearchResponseSchema[T](BaseModel):
    detail: list[T]
    pagination: PaginationSchema
    total_found: int


class SearchResponseSchemaWithFilters(SearchResponseSchema):
    filters: FiltersSchema
