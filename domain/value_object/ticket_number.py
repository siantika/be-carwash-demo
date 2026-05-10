from dataclasses import dataclass

from app.shared.domain.exceptions.exceptions import InvalidTicketNumber


@dataclass(frozen=True)
class TicketNumber:
    value: str

    def __post_init__(self):
        if not self.value:
            raise InvalidTicketNumber("Ticket number must not be empty")
        
        if self.value and not isinstance(self.value, str):
            raise InvalidTicketNumber(f"Ticket number should be string. Got: {type(self.value)}")

        if not self._is_valid_ean13(self.value):
            raise InvalidTicketNumber("Ticket number must be a valid EAN-13")

    @staticmethod
    def _is_valid_ean13(code: str) -> bool:
        if not code.isdigit() or len(code) != 13:
            return False

        digits = [int(d) for d in code]
        checksum = digits.pop()

        total = sum(
            d * 3 if i % 2 else d
            for i, d in enumerate(digits)
        )

        return (10 - (total % 10)) % 10 == checksum
