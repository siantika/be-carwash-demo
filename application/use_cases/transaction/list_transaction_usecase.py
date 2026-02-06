from typing import List

from application.dto.transaction_dto import TransactionResultDto
from domain.repositories.i_transaction_repo import ITransactionRepository


class ListTransactionUseCase:
    def __init__(self, transaction_repo:ITransactionRepository):
        self.transaction_repo = transaction_repo

    async def execute(self, limit:int, offset:int) -> List[TransactionResultDto]:
        list_transactions = await self.transaction_repo.list(limit, offset)
        return list_transactions
