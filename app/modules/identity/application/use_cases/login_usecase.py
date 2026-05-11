"""
Authentication login use case.

Handles user authentication and token generation.
"""
from datetime import timedelta

from app.modules.identity.application.config.auth_config import AuthConfig
from app.modules.identity.application.dto.login_dto import TokenPairDto
from app.modules.identity.application.services.i_password_hasher import IPasswordHasher
from app.modules.identity.application.services.i_token_service import ITokenService
from app.modules.identity.domain.entities.refresh_token import RefreshToken
from app.modules.identity.domain.repositories.i_account_repo import IAccountRepository
from app.modules.identity.domain.repositories.i_refresh_token_repo import (
    IRefreshTokenRepository,
)
from app.modules.identity.domain.value_objects.username import Username
from app.shared.domain.entities.base import _utcnow
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    EntityNotFound,
    InactiveUserError,
    InvalidPasswordError,
)


class LoginUseCase: 
    """Use case for authenticating a user and issuing an access token."""

    def __init__(
        self,
        account_repo: IAccountRepository,
        refresh_token_repo: IRefreshTokenRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        auth_config: AuthConfig
    ):
        self.account_repo = account_repo
        self.refresh_token_repo = refresh_token_repo
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.auth_config = auth_config 
        
    async def execute(self, username: str, password: str) -> TokenPairDto:

        now = _utcnow()
        account = await self.account_repo.find_by_username(Username(username))

        if account is None:
            raise EntityNotFound("Invalid username")

        if not account.can_login(now):
            if not account.is_active:
                raise InactiveUserError("Account is inactive")
            raise BusinessRuleViolation("Account is temporarily locked")

        if not self.password_hasher.verify(password, account.password_hash):
            account.record_failed_login(now)
            await self.account_repo.save(account)
            raise InvalidPasswordError("Invalid password")

        if account.id is None:
            raise BusinessRuleViolation("Authenticated account must have an id")

        account.record_successful_login(now)
        await self.account_repo.save(account)

        token = self.token_service.create_access_token(
            str(account.id),
            account.username,
            account.role,
            self.auth_config.access_token_expire_hours
        )
        refresh_token = self.token_service.generate_refresh_token()

        await self.refresh_token_repo.save(
            RefreshToken(
                user_id=account.id,
                token_hash=self.token_service.hash_refresh_token(refresh_token),
                expires_at=now + timedelta(days=self.auth_config.refresh_token_expire_days),
            )
        )

        return TokenPairDto(
            access_token=token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )
