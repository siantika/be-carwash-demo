from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from domain.exceptions import InvalidValueObject


class PaymentMethodEnum(str, Enum):
    CASH = "CASH"
    QRIS = "QRIS"
    CARD = "CARD"


_PAYMENT_SCHEMA: dict[PaymentMethodEnum, Dict[str, Any]] = {
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
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not isinstance(self.method, PaymentMethodEnum):
            raise InvalidValueObject("Payment method must be a 'PaymentMethodEnum'")
        if not isinstance(self.metadata, dict):
            raise InvalidValueObject("Payment metadata must be a dict")

        self.validate_metadata(self.method, self.metadata)
            
        
    def validate_metadata(self, method:PaymentMethodEnum,
                                             metadata: Optional[Dict[str, Any]]) -> bool:
        schema = _PAYMENT_SCHEMA.get(method)
        if schema is None:
            raise InvalidValueObject(f"Unsupported payment method: {method}")

        required: set[str] = schema["required"]
        optional: set[str] = schema["optional"]
        types: dict[str, type] = schema["types"]

        # validate metadata contains all required keys
        missing = required - metadata.keys()
        if missing:
            raise InvalidValueObject(
                f"{self.method.value} requires metadata keys: {sorted(missing)}"
            )

        # Only allowed metadata
        allowed = required | optional
        extra = set(self.metadata.keys()) - allowed
        if extra:
            raise InvalidValueObject(
                f"{self.method.value} has invalid metadata keys: {sorted(extra)}"
            )

        # validate metadata's type
        for k, t in types.items():
            is_key_exist_in_metadata = k in self.metadata
            v = self.metadata.get(k) # it will return 'None' if k is not in metadata
            is_value_not_none = v is not None
            is_wrong_type = is_value_not_none and not isinstance(v, t)

            if is_key_exist_in_metadata and is_wrong_type:
                raise InvalidValueObject(
                    f"{self.method.value} metadata '{k}' must be {t.__name__}"
                )
        