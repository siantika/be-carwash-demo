"""
Authentication login use case.

Handles user authentication and token generation.
"""
from application.dto.login_dto import LoginResultDto
from core.consts import Consts
from core.security import create_access_token, verify_password
from domain.exceptions import (
    EntityNotFound,
    InactiveUserError,
    InvalidPasswordError,
)
from domain.repositories.i_user_repo import IUserRepository


class LoginUseCase: 
    """Use case for authenticating a user and issuing an access token."""

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, username: str, password: str) -> LoginResultDto:

        user = await self.user_repo.get_by_username(username)

        if user is None:
            raise EntityNotFound("Invalid username")

        if not verify_password(password, user.password_hash):
            raise InvalidPasswordError("Invalid password")

        if not user.is_active:
            raise InactiveUserError("User is inactive")

        token = create_access_token(
            str(user.id),
            user.username,
            user.role,
        )

        return LoginResultDto(
            access_token=token,
            token_type= Consts.TOKEN_TYPE,
            user=user
        )
