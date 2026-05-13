from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.shared.domain.exceptions.exceptions import InvalidValueObject


class PaymentMethodEnum(str, Enum):
    CASH = "CASH"
    QRIS = "QRIS"
    CARD = "CARD"


_PAYMENT_SCHEMA: dict[PaymentMethodEnum, dict[str, Any]] = {
    PaymentMethodEnum.CASH: {
        "required": set(),
        "optional": set(),
        "types": {},
    },
    PaymentMethodEnum.QRIS: {
        "required": {"rrn"},
        "optional": {"provider"},
        "types": {"rrn": str, "provider": str},
    },
    PaymentMethodEnum.CARD: {
        "required": {"auth_code"},
        "optional": {"last4"},
        "types": {"auth_code": str, "last4": str},
    },
}


@dataclass(frozen=True)
class Payment:
    method: PaymentMethodEnum
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.method, str):
            object.__setattr__(self, "method", PaymentMethodEnum(self.method.strip().upper()))

        if not isinstance(self.method, PaymentMethodEnum):
            raise InvalidValueObject("Payment method must be a PaymentMethodEnum")

        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

        if not isinstance(self.metadata, dict):
            raise InvalidValueObject("Payment metadata must be a dict")

        self._validate_metadata()

    def _validate_metadata(self) -> None:
        schema = _PAYMENT_SCHEMA.get(self.method)
        if schema is None:
            raise InvalidValueObject(f"Unsupported payment method: {self.method}")

        required: set[str] = schema["required"]
        optional: set[str] = schema["optional"]
        allowed = required | optional
        metadata_keys = set(self.metadata.keys())

        missing = required - metadata_keys
        if missing:
            raise InvalidValueObject(
                f"{self.method.value} requires metadata keys: {sorted(missing)}"
            )

        extra = metadata_keys - allowed
        if extra:
            raise InvalidValueObject(
                f"{self.method.value} has invalid metadata keys: {sorted(extra)}"
            )

        for key, expected_type in schema["types"].items():
            value = self.metadata.get(key)
            if value is not None and not isinstance(value, expected_type):
                raise InvalidValueObject(
                    f"{self.method.value} metadata '{key}' must be {expected_type.__name__}"
                )
