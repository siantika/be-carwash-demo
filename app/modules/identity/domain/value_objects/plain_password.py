import re
from dataclasses import dataclass

from app.shared.domain.exceptions.exceptions import BusinessRuleViolation

PASSWORD_HAS_LOWERCASE = re.compile(r"[a-z]")
PASSWORD_HAS_UPPERCASE = re.compile(r"[A-Z]")
PASSWORD_HAS_NUMBER = re.compile(r"\d")

@dataclass(frozen=True)
class PlainPassword:
    value: str 
    
    def __post_init__(self):
        if not self.value:
            raise BusinessRuleViolation("Password must be filled")
        
        if len(self.value) < 8:
            raise BusinessRuleViolation("Passwords length minimum 8 characters")
        
        if not PASSWORD_HAS_LOWERCASE.search(self.value):
            raise BusinessRuleViolation("Password must contain lowercase letter")

        if not PASSWORD_HAS_UPPERCASE.search(self.value):
            raise BusinessRuleViolation("Password must contain uppercase letter")

        if not PASSWORD_HAS_NUMBER.search(self.value):
            raise BusinessRuleViolation("Password must contain number")
        
    
    def __str__(self) -> str:
        return self.value 
