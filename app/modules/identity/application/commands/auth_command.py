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
    AccountTemporarilyLockedError,
    EntityNotFound,
    InactiveUserError,
    InvalidPasswordError,
    InvalidTokenError,
    MissingPersistedEntityIdError,
    RevokedRefreshTokenMismatchError,
)


class LoginUseCase:
    def __init__(
        self,
        account_repo: IAccountRepository,
        refresh_token_repo: IRefreshTokenRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        auth_config: AuthConfig,
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
            raise InvalidPasswordError("Invalid credentials")

        if not account.can_login(now):
            if not account.is_active:
                raise InactiveUserError("Account is inactive")
            raise AccountTemporarilyLockedError("Account is temporarily locked")

        if not self.password_hasher.verify(password, account.password_hash):
            account.record_failed_login(now)
            await self.account_repo.save(account)
            raise InvalidPasswordError("Invalid credentials")

        if account.id is None:
            raise MissingPersistedEntityIdError("Authenticated account must have an id")

        account.record_successful_login(now)
        await self.account_repo.save(account)

        token = self.token_service.create_access_token(
            str(account.id),
            account.username,
            account.role,
            self.auth_config.access_token_expire_hours,
        )
        refresh_token = self.token_service.generate_refresh_token()

        await self.refresh_token_repo.save(
            RefreshToken(
                account_id=account.id,
                token_hash=self.token_service.hash_refresh_token(refresh_token),
                expires_at=now + timedelta(days=self.auth_config.refresh_token_expire_days),
            )
        )

        return TokenPairDto(
            access_token=token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )


class RefreshSessionUseCase:
    def __init__(
        self,
        account_repo: IAccountRepository,
        refresh_token_repo: IRefreshTokenRepository,
        token_service: ITokenService,
        auth_config: AuthConfig,
    ):
        self.account_repo = account_repo
        self.refresh_token_repo = refresh_token_repo
        self.token_service = token_service
        self.auth_config = auth_config

    async def execute(self, refresh_token: str) -> TokenPairDto:
        now = _utcnow()
        stored_token = await self.refresh_token_repo.find_active_by_hash(
            self.token_service.hash_refresh_token(refresh_token),
            now,
        )

        if stored_token is None:
            raise InvalidTokenError("Invalid refresh token")

        account = await self.account_repo.find_by_id(stored_token.account_id)
        if account is None:
            raise EntityNotFound("Account not found")

        if not account.is_active:
            raise InactiveUserError("Account is inactive")

        if stored_token.id is None:
            raise MissingPersistedEntityIdError("Stored refresh token must have an id")

        if account.id is None:
            raise MissingPersistedEntityIdError("Refresh token user must have an id")

        revoked_token_id = await self.refresh_token_repo.revoke(stored_token.id, now)
        if revoked_token_id != stored_token.id:
            raise RevokedRefreshTokenMismatchError("Revoked refresh token id mismatch")

        new_refresh_token = self.token_service.generate_refresh_token()
        await self.refresh_token_repo.save(
            RefreshToken(
                account_id=account.id,
                token_hash=self.token_service.hash_refresh_token(new_refresh_token),
                expires_at=now + timedelta(days=self.auth_config.refresh_token_expire_days),
            )
        )

        access_token = self.token_service.create_access_token(
            str(account.id),
            account.username,
            account.role,
            self.auth_config.access_token_expire_hours,
        )

        return TokenPairDto(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
        )


class LogoutUseCase:
    def __init__(
        self,
        refresh_token_repo: IRefreshTokenRepository,
        token_service: ITokenService,
    ):
        self.refresh_token_repo = refresh_token_repo
        self.token_service = token_service

    async def execute(self, refresh_token: str) -> None:
        now = _utcnow()
        stored_token = await self.refresh_token_repo.find_active_by_hash(
            self.token_service.hash_refresh_token(refresh_token),
            now,
        )

        if stored_token is None:
            raise InvalidTokenError("Invalid refresh token")

        if stored_token.id is None:
            raise MissingPersistedEntityIdError("Stored refresh token must have an id")

        revoked_token_id = await self.refresh_token_repo.revoke(stored_token.id, now)
        if revoked_token_id != stored_token.id:
            raise RevokedRefreshTokenMismatchError("Revoked refresh token id mismatch")

