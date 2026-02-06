from dataclasses import dataclass


@dataclass(frozen=True)
class OffsetPagination:
    limit: int
    offset: int
