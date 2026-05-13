from fastapi import Depends

from app.modules.billing.application.use_cases.transaction_usecase import (
    ListTransactionsUseCase,
    ProcessTransactionUseCase,
)
from app.modules.billing.infra.repositories.transaction_repo import (
    AsyncPgTransactionRepository,
)
from app.modules.billing.infra.unit_of_work import AsyncPgBillingUnitOfWork
from app.shared.infra.database.db import get_db, get_db_pool
from app.shared.middleware.logger import StructlogLogger
from app.shared.interfaces.i_logger import ILogger


def get_logger() -> ILogger:
    return StructlogLogger("billing")


def get_transaction_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgTransactionRepository(db, logger)


def get_billing_uow(pool=Depends(get_db_pool), logger=Depends(get_logger)):
    return AsyncPgBillingUnitOfWork(pool, logger)


def get_process_transaction_usecase(uow=Depends(get_billing_uow)):
    return ProcessTransactionUseCase(uow)


def get_list_transactions_usecase(repo=Depends(get_transaction_repo)):
    return ListTransactionsUseCase(repo)
