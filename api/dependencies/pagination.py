from fastapi import Query

from api.schema.pagination_schema import OffsetPagination


def get_offset_pagination(
    limit: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> OffsetPagination:
    return OffsetPagination(limit=limit, offset=offset)
