from app.modules.identity.application.dto.account_dto import (
    AccountListResultDto,
    AccountResultDto,
    RegisterAccountCmd,
)
from app.modules.identity.application.services.i_password_hasher import IPasswordHasher
from app.modules.identity.domain.entities.account import Account, RoleCode
from app.modules.identity.domain.repositories.i_account_repo import IAccountRepository
from app.modules.identity.domain.value_objects.email import Email
from app.modules.identity.domain.value_objects.plain_password import PlainPassword
from app.modules.identity.domain.value_objects.username import Username
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    EntityAlreadyExists,
    EntityNotFound,
)

def _to_account_result(account: Account) -> AccountResultDto:
    return AccountResultDto(
        id=account.id,
        username=account.username.value,
        email=account.email.value,
        role=account.role.value,
        is_active=account.is_active,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def _parse_role(role: RoleCode | str) -> RoleCode:
    if isinstance(role, RoleCode):
        parsed_role = role
    else:
        try:
            parsed_role = RoleCode(role.strip().upper())
        except ValueError as exc:
            raise BusinessRuleViolation("Invalid account role") from exc

    return parsed_role


class RegisterAccountUseCase:
    def __init__(
        self,
        account_repo: IAccountRepository,
        password_hasher: IPasswordHasher,
    ):
        self.account_repo = account_repo
        self.password_hasher = password_hasher

    async def execute(self, cmd: RegisterAccountCmd) -> AccountResultDto:
        username = Username(cmd.username)

        existing_account = await self.account_repo.find_by_username(username)
        if existing_account is not None:
            raise EntityAlreadyExists("Account", username.value)

        password = PlainPassword(cmd.password)
        account = Account(
            username=username,
            email=Email(cmd.email),
            password_hash=self.password_hasher.hash(password.value),
            role=_parse_role(cmd.role),
            is_active=cmd.is_active,
        )

        created_account = await self.account_repo.create(account)
        return _to_account_result(created_account)


class GetAccountUseCase:
    def __init__(self, account_repo: IAccountRepository):
        self.account_repo = account_repo

    async def execute(self, account_id: int) -> AccountResultDto:
        account = await self.account_repo.find_by_id(account_id)
        if account is None:
            raise EntityNotFound("Account", account_id)

        return _to_account_result(account)


class ListAccountsUseCase:
    def __init__(self, account_repo: IAccountRepository):
        self.account_repo = account_repo

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
        accounts, total = await self.account_repo.find_all_filtered(
            role=parsed_role,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

        return AccountListResultDto(
            items=[_to_account_result(account) for account in accounts],
            total=total,
            page=page,
            limit=limit,
        )


class ActivateAccountUseCase:
    def __init__(self, account_repo: IAccountRepository):
        self.account_repo = account_repo

    async def execute(self, account_id: int) -> AccountResultDto:
        account = await self.account_repo.find_by_id(account_id)
        if account is None:
            raise EntityNotFound("Account", account_id)

        account.activate()
        saved_account = await self.account_repo.save(account)
        return _to_account_result(saved_account)


class DeactivateAccountUseCase:
    def __init__(self, account_repo: IAccountRepository):
        self.account_repo = account_repo

    async def execute(self, account_id: int) -> AccountResultDto:
        account = await self.account_repo.find_by_id(account_id)
        if account is None:
            raise EntityNotFound("Account", account_id)

        account.deactivate()
        saved_account = await self.account_repo.save(account)
        return _to_account_result(saved_account)


class DeleteAccountUseCase:
    def __init__(self, account_repo: IAccountRepository):
        self.account_repo = account_repo

    async def execute(self, account_id: int) -> None:
        account = await self.account_repo.find_by_id(account_id)
        if account is None:
            raise EntityNotFound("Account", account_id)

        deleted_account_id = await self.account_repo.delete(account_id)
        if deleted_account_id != account_id:
            raise BusinessRuleViolation("Deleted account id mismatch")
