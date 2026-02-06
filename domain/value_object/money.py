from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    amount: Decimal

    def __post_init__(self) -> None:
        amt = self.amount if isinstance(self.amount, Decimal) else Decimal(str(self.amount))
        if amt < 0:
            raise ValueError("Amount cannot be negative")
        object.__setattr__(self, "amount", amt)

    # domain ops
    def add(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

    def subtract(self, other: "Money") -> "Money":
        if other.amount > self.amount:
            raise ValueError("Subtraction amount exceeds available balance")
        return Money(self.amount - other.amount)

    def multiply(self, multiplier: Decimal) -> "Money":
        m = multiplier if isinstance(multiplier, Decimal) else Decimal(str(multiplier))
        if m < 0:
            raise ValueError("Multiplier cannot be negative")
        return Money(self.amount * m)

    def min(self, other: "Money") -> "Money":
        return self if self.amount <= other.amount else other

    # operators (agar <=, -, max/min bisa jalan)
    def __lt__(self, other: "Money") -> bool: return self.amount < other.amount
    def __le__(self, other: "Money") -> bool: return self.amount <= other.amount
    def __gt__(self, other: "Money") -> bool: return self.amount > other.amount
    def __ge__(self, other: "Money") -> bool: return self.amount >= other.amount

    def __sub__(self, other: "Money") -> "Money":
        return self.subtract(other)
