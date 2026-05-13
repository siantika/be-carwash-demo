from app.modules.identity.application.dto.account_dto import (
    AccountListResultDto,
    AccountResultDto,
)
from app.modules.identity.application.dto.account_mapper import to_account_result
from app.modules.identity.application.queries.models import AccountListFilterDto
from app.modules.identity.domain.entities.account import RoleCode
from app.modules.identity.domain.repositories.i_account_repo import IAccountRepository
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation, EntityNotFound


def _parse_role(role: RoleCode | str) -> RoleCode:
    if isinstance(role, RoleCode):
        parsed_role = role
    else:
        try:
            parsed_role = RoleCode(role.strip().upper())
        except ValueError as exc:
            raise BusinessRuleViolation("Invalid account role") from exc

    return parsed_role


class GetAccountUseCase:
    def __init__(self, account_repo: IAccountRepository):
        self.account_repo = account_repo

    async def execute(self, account_id: int) -> AccountResultDto:
        account = await self.account_repo.find_by_id(account_id)
        if account is None:
            raise EntityNotFound("Account", account_id)

        return to_account_result(account)


class ListAccountsUseCase:
    def __init__(self, account_query):
        self.account_query = account_query

    async def execute(
        self,
        role: RoleCode | str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> AccountListResultDto:
        if page < 1:
            raise BusinessRuleViolation("Page must be greater than or equal to 1")

        if limit < 1:
            raise BusinessRuleViolation("Limit must be greater than or equal to 1")

        parsed_role = _parse_role(role) if role is not None else None
        offset = (page - 1) * limit
        accounts, total = await self.account_query.list(
            filters=AccountListFilterDto(
                role=parsed_role,
                is_active=is_active,
            ),
            limit=limit,
            offset=offset,
        )

        return AccountListResultDto(
            items=[to_account_result(account) for account in accounts],
            total=total,
            page=page,
            limit=limit,
        )

