import re
from dataclasses import dataclass

from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


USERNAME_REGEX = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True)
class Username:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()

        if not normalized:
            raise BusinessRuleViolation("Username must not be empty")

        if len(normalized) < 3:
            raise BusinessRuleViolation("Username must be at least 3 characters")

        if len(normalized) > 30:
            raise BusinessRuleViolation("Username must not exceed 30 characters")

        if not USERNAME_REGEX.match(normalized):
            raise BusinessRuleViolation(
                "Username may only contain lowercase letters, numbers, and underscores"
            )

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
