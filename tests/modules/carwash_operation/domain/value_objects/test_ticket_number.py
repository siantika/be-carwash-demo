import pytest

from app.shared.domain.exceptions.exceptions import InvalidTicketNumber
from app.modules.carwash_operation.domain.value_objects.ticket_number import (
    TicketNumber,
)

VALID_EAN13_TICKET_NUMBER = ["5901234123457", "4006381333931", "8999999032111"]


INVALID_EAN13_TICKET_NUMBER = ["123", "456", "789", 123, 8999999032111]


@pytest.mark.parametrize("number", VALID_EAN13_TICKET_NUMBER)
def test_ticket_number_should_valid_ean13(number):
    assert TicketNumber(number)


@pytest.mark.parametrize("number", INVALID_EAN13_TICKET_NUMBER)
def test_ticket_number_should_raise_invalid_ean13(number):
    with pytest.raises(InvalidTicketNumber):
        TicketNumber(number)
