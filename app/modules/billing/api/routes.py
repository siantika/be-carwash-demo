from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.shared import RoleChecker
from app.modules.billing.api.dependencies import (
    get_list_transactions_usecase,
    get_process_transaction_usecase,
)
from app.modules.billing.api.schemas import (
    ProcessTransactionRequest,
    TransactionResponse,
)
from app.modules.billing.application.dto.transaction_dto import (
    ProcessTransactionCmd,
)
from app.modules.billing.application.queries.models import (
    TransactionListFilterDto,
)
from app.modules.billing.application.use_cases.transaction_usecase import (
    ListTransactionsUseCase,
    ProcessTransactionUseCase,
)
from app.modules.billing.domain.value_objects.payment import PaymentMethodEnum
from app.modules.billing.domain.value_objects.payment_state import PaymentStatus
from app.modules.identity.domain.entities.account import RoleCode
from app.shared.response import BaseResponse, Metadata

router = APIRouter()

PAYMENT_PROCESSOR_ROLES = [RoleCode.CASHIER]
BILLING_READER_ROLES = [RoleCode.CASHIER, RoleCode.ADMIN, RoleCode.OWNER]


@router.post(
    "",
    response_model=BaseResponse[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def process_transaction(
    payload: ProcessTransactionRequest,
    user=Depends(RoleChecker(PAYMENT_PROCESSOR_ROLES)),
    usecase: ProcessTransactionUseCase = Depends(get_process_transaction_usecase),
):
    transaction = await usecase.execute(
        ProcessTransactionCmd(
            ticket_id=payload.ticket_id,
            cashier_id=int(user.user_id),
            plate_number=payload.plate_number,
            payment_method=payload.payment_method,
            payment_metadata=payload.payment_metadata,
        )
    )
    return BaseResponse(data=transaction)


@router.get("", response_model=BaseResponse[List[TransactionResponse]])
async def list_transactions(
    ticket_id: int | None = Query(default=None, ge=1),
    cashier_id: int | None = Query(default=None, ge=1),
    payment_method: PaymentMethodEnum | None = Query(default=None),
    payment_status: PaymentStatus | None = Query(default=None),
    plate_number: str | None = Query(default=None, min_length=3, max_length=12),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(RoleChecker(BILLING_READER_ROLES)),
    usecase: ListTransactionsUseCase = Depends(get_list_transactions_usecase),
):
    result = await usecase.execute(
        filters=TransactionListFilterDto(
            ticket_id=ticket_id,
            cashier_id=cashier_id,
            payment_method=payment_method,
            payment_status=payment_status,
            plate_number=plate_number,
        ),
        page=page,
        limit=limit,
    )
    return BaseResponse(
        data=result.items,
        metadata=Metadata(page=result.page, limit=result.limit, total=result.total),
    )
