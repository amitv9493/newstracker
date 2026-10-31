from dataclasses import dataclass
from math import ceil
from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    def __init__(
        self,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


Pagination = Annotated[PaginationParams, Depends()]


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


@dataclass
class PageResult:
    items: list
    total: int
    page: int
    page_size: int
    pages: int


def paginate(query, params: PaginationParams) -> PageResult:
    total = query.order_by(None).count()
    items = query.offset(params.offset).limit(params.page_size).all()
    pages = ceil(total / params.page_size) if total else 0
    return PageResult(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=pages,
    )
