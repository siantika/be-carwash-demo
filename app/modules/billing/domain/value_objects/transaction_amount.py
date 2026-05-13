from dataclasses import dataclass

from app.shared.domain.value_objects.money import Money


@dataclass(frozen=True)
class TransactionAmount:
    subtotal: Money

    @property
    def total(self) -> Money:
        return self.subtotal
