import pytest

from app.modules.identity.domain.value_objects.plain_password import PlainPassword
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation

VALID_PLAIN_PASSWORD = [
    "AbC123AA",
    "S@pt)4654",
    "abcE55554",
]


INVALID_NO_LOWER_PLAIN_PASSWORD = [
    "ABC456889",
    "ASDASDASDASD88",
]

INVALID_NO_UPPERCASE_PLAIN_PASSWORD = [
    "adsadsada45656",
    "asdbc1234",
]

INVALID_NO_NUMBER_PLAIN_PASSWORD = [
    "Asdasdsadasd",
    "ASdasdsad",
]

INVALID_TOO_SHORT_PLAIN_PASSWORD = [
    "Abc123",
    "A1b",
]


@pytest.mark.parametrize("plain_password", VALID_PLAIN_PASSWORD)
def test_plain_password_should_be_valid(plain_password):
    assert PlainPassword(plain_password)


@pytest.mark.parametrize("plain_password", INVALID_NO_LOWER_PLAIN_PASSWORD)
def test_plain_password_should_raise_no_lower_case(plain_password):
    with pytest.raises(BusinessRuleViolation, match="lowercase"):
        PlainPassword(plain_password)


@pytest.mark.parametrize("plain_password", INVALID_NO_UPPERCASE_PLAIN_PASSWORD)
def test_plain_password_should_raise_no_uppercase(plain_password):
    with pytest.raises(BusinessRuleViolation, match="uppercase"):
        PlainPassword(plain_password)


@pytest.mark.parametrize("plain_password", INVALID_NO_NUMBER_PLAIN_PASSWORD)
def test_plain_password_should_raise_no_number(plain_password):
    with pytest.raises(BusinessRuleViolation, match="number"):
        PlainPassword(plain_password)


@pytest.mark.parametrize("plain_password", INVALID_TOO_SHORT_PLAIN_PASSWORD)
def test_plain_password_should_raise_too_short(plain_password):
    with pytest.raises(BusinessRuleViolation, match="minimum 8"):
        PlainPassword(plain_password)


def test_plain_password_should_raise_empty_password():
    with pytest.raises(BusinessRuleViolation, match="filled"):
        PlainPassword("")
