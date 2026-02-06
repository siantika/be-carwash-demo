import re
from dataclasses import dataclass

from domain.exceptions import InvalidValueObject

PLATE_REGEX = re.compile(r"^[A-Z]{1,2}\s?\d{1,4}\s?[A-Z]{0,3}$")

@dataclass(frozen=True)
class PlateNumber:
    value: str

    def __post_init__(self):
        if self.value is None:
            raise InvalidValueObject("Plate number cannot be empty")
        
        if len(self.value) > 10:
            raise InvalidValueObject("Plate number cannot exceed 10 characters")

        if not PLATE_REGEX.match(self.value):
            raise InvalidValueObject(
                "Invalid plate number format (e.g. DK123LL)"
            )
