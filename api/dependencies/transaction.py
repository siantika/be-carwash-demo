from fastapi import Depends

from api.dependencies.shared import get_logger, get_uow
from application.use_cases.transaction.list_transaction_usecase import (
    ListTransactionUseCase,
)
from application.use_cases.transaction.process_transaction_usecase import (
    ProcessTransactionUseCase,
)
from infra.db import get_db
from infra.repositories.transaction_repo import AsyncPgTransactionRepository


def get_transaction_repo(db=Depends(get_db), 
                         logger= Depends(get_logger)) -> AsyncPgTransactionRepository:
    return AsyncPgTransactionRepository(db, logger)
    
def get_process_transaction_usecase(uow=Depends(get_uow)) -> ProcessTransactionUseCase:
    return ProcessTransactionUseCase(uow)

def get_list_transactions_usecase(repo= Depends(get_transaction_repo)) -> ListTransactionUseCase:
    return ListTransactionUseCase(repo)