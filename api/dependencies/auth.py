from fastapi import Depends

from api.dependencies.shared import get_logger
from application.use_cases.auth.login_usecase import LoginUseCase
from infra.db import get_db
from infra.repositories.user_repo import AsyncPgUserRepository


def get_user_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgUserRepository(db, logger)

def get_login_usecase(user_repo=Depends(get_user_repo)):
    return LoginUseCase(user_repo)

