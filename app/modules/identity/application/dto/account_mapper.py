from app.modules.identity.application.dto.account_dto import AccountResultDto
from app.modules.identity.domain.entities.account import Account


def to_account_result(account: Account) -> AccountResultDto:
    return AccountResultDto(
        id=account.id,
        username=account.username.value,
        email=account.email.value,
        role=account.role.value,
        is_active=account.is_active,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )

