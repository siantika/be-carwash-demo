from __future__ import annotations

from dataclasses import dataclass

from domain.value_object.money import Money


@dataclass(frozen=True)
class TransactionAmount:
    subtotal: Money
    
    """ 
        You can implement discount or tax here. 
        For demo, it just use subtotal (without disc and tax calculation) as total amount
    """
    
    @property
    def total(self) -> Money:
        return self.subtotal