from datetime import datetime, timedelta, timezone

import pytest
from domain.entities.base import BaseEntity

from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


def aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc)


def test_base_entity_accepts_timezone_aware_timestamps():
    created = aware(datetime(2026, 1, 1, 10, 0, 0))
    updated = aware(datetime(2026, 1, 1, 10, 0, 1))

    e = BaseEntity(created_at=created, updated_at=updated)

    assert e.created_at == created
    assert e.updated_at == updated


def test_created_at_must_be_timezone_aware():
    created = datetime(2026, 1, 1, 10, 0, 0)  # naive
    updated = aware(datetime(2026, 1, 1, 10, 0, 1))

    with pytest.raises(BusinessRuleViolation, match="created_at must be timezone-aware"):
        BaseEntity(created_at=created, updated_at=updated)


def test_updated_at_must_be_timezone_aware():
    created = aware(datetime(2026, 1, 1, 10, 0, 0))
    updated = datetime(2026, 1, 1, 10, 0, 1)  # naive

    with pytest.raises(BusinessRuleViolation, match="updated_at must be timezone-aware"):
        BaseEntity(created_at=created, updated_at=updated)


def test_updated_at_cannot_be_earlier_than_created_at():
    created = aware(datetime(2026, 1, 1, 10, 0, 0))
    updated = created - timedelta(seconds=1)

    with pytest.raises(
        BusinessRuleViolation,
        match="updated_at time cannot be earlier than created_at time",
    ):
        BaseEntity(created_at=created, updated_at=updated)


def test_equal_times_are_allowed():
    t = aware(datetime(2026, 1, 1, 10, 0, 0))
    e = BaseEntity(created_at=t, updated_at=t)
    assert e.updated_at == e.created_at
