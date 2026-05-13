from fastapi import Depends

from app.modules.billing.application.commands.transaction_command import (
    ProcessTransactionUseCase,
)
from app.modules.billing.infra.services.request_hasher import Sha256RequestHasher
from app.modules.billing.application.queries.transaction_query import ListTransactionsUseCase
from app.modules.billing.infra.repositories.transaction_repo import (
    AsyncPgTransactionRepository,
)
from app.modules.billing.infra.repositories.query.postgres_payment_transaction_query_repository import (
    PostgresPaymentTransactionQueryRepository,
)
from app.modules.billing.infra.unit_of_work import AsyncPgBillingUnitOfWork
from app.shared.infra.database.db import get_db, get_db_pool
from app.shared.middleware.logger import StructlogLogger
from app.shared.interfaces.i_logger import ILogger


def get_logger() -> ILogger:
    return StructlogLogger("billing")


def get_transaction_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgTransactionRepository(db, logger)


def get_transaction_query(db=Depends(get_db), logger=Depends(get_logger)):
    return PostgresPaymentTransactionQueryRepository(db, logger)


def get_billing_uow(pool=Depends(get_db_pool), logger=Depends(get_logger)):
    return AsyncPgBillingUnitOfWork(pool, logger)


def get_request_hasher():
    return Sha256RequestHasher()


def get_process_transaction_usecase(
    uow=Depends(get_billing_uow),
    request_hasher=Depends(get_request_hasher),
):
    return ProcessTransactionUseCase(uow, request_hasher)


def get_list_transactions_usecase(query=Depends(get_transaction_query)):
    return ListTransactionsUseCase(query)
