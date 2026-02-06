from fastapi import Depends

from api.dependencies.shared import get_logger
from application.use_cases.user.list_users import ListUsersUseCase
from application.use_cases.user.manage_activation_user_usecase import (
    ActivateStatusUserUseCase,
    DeactivateStatusUserUseCase,
)
from application.use_cases.user.register_user_usecase import RegisterUserUseCase
from infra.db import get_db
from infra.repositories.user_repo import AsyncPgUserRepository


def get_user_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgUserRepository(db, logger)

def get_list_users_usecase(user_repo=Depends(get_user_repo)):
    return ListUsersUseCase(user_repo)

def get_register_user_usecase(user_repo=Depends(get_user_repo)):
    return RegisterUserUseCase(user_repo)

def get_activate_user_usecase(user_repo=Depends(get_user_repo)):
    return ActivateStatusUserUseCase(user_repo)

def get_deactivate_user_usecase(user_repo=Depends(get_user_repo)):
    return DeactivateStatusUserUseCase(user_repo)