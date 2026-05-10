import re
from dataclasses import dataclass

from app.shared.domain.exceptions.exceptions import BusinessRuleViolation

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

@dataclass(frozen=True)
class Email:
    value: str 
    
    def __post_init__(self):
        normalized = self.value.strip().lower() 
        
        if not normalized:
            raise BusinessRuleViolation("Email must not be empty")
        
        if len(normalized) > 255:
            raise BusinessRuleViolation("Email is too long")
        
        if not EMAIL_REGEX.match(normalized):
            raise BusinessRuleViolation("Invalid email format")
        
        object.__setattr__(self, "value", normalized)
        
    def __str__(self):
        return self.value
