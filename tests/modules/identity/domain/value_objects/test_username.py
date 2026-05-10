import pytest

from app.modules.identity.domain.value_objects.username import Username
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


def test_username_normalizes_value() -> None:
    username = Username("  Cashier_01  ")

    assert username.value == "cashier_01"
    assert str(username) == "cashier_01"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "ab",
        "this_username_is_more_than_thirty_chars",
        "john.doe",
        "john-doe",
        "john doe",
    ],
)
def test_username_rejects_invalid_values(value: str) -> None:
    with pytest.raises(BusinessRuleViolation):
        Username(value)
