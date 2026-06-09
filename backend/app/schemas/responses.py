"""Generic structured response schemas.

Use APIResponse[T] for single-item responses and PaginatedResponse[T] for lists.

Example:
    @router.get("/items/{id}", response_model=APIResponse[ItemSchema])
    async def get_item(id: UUID) -> APIResponse[ItemSchema]:
        item = ...
        return APIResponse(success=True, data=item)
"""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """Standard single-item API response envelope."""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    correlation_id: Optional[str] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response."""

    items: List[T]
    total: int
    page: int
    per_page: int
    has_next: bool

    @classmethod
    def build(
        cls,
        items: List[T],
        total: int,
        page: int,
        per_page: int,
    ) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total,
        )
