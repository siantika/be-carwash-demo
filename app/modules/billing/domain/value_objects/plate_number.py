import re
from dataclasses import dataclass

from app.shared.domain.exceptions.exceptions import InvalidValueObject

PLATE_REGEX = re.compile(r"^[A-Z]{1,2}\s?\d{1,4}\s?[A-Z]{0,3}$")


@dataclass(frozen=True)
class PlateNumber:
    value: str

    def __post_init__(self):
        if self.value is None:
            raise InvalidValueObject("Plate number cannot be empty")

        normalized = self.value.strip().upper()
        if not normalized:
            raise InvalidValueObject("Plate number cannot be empty")

        if len(normalized) > 12:
            raise InvalidValueObject("Plate number cannot exceed 12 characters")

        if not PLATE_REGEX.match(normalized):
            raise InvalidValueObject("Invalid plate number format (e.g. DK123LL)")

        object.__setattr__(self, "value", normalized)
