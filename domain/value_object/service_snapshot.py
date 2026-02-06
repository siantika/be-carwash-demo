from dataclasses import dataclass

from domain.exceptions import InvalidServiceValue
from domain.value_object.money import Money


@dataclass(frozen=True)
class ServiceSnapshot:
    service_name: str
    service_price: Money
    service_desc: str

    def __post_init__(self):
        if not self.service_name.strip():
            raise InvalidServiceValue("Service name cannot be empty")

        if not self.service_desc.strip():
            raise InvalidServiceValue("Service desc cannot be empty")
