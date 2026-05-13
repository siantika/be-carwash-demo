from typing import List

from fastapi import APIRouter, Depends

from app.api.dependencies.pagination import get_offset_pagination
from app.api.dependencies.shared import RoleChecker
from app.api.dependencies.transaction import (
    get_list_transactions_usecase,
    get_process_transaction_usecase,
)
from app.api.schema.transaction_schema import (
    ProcessTransactionRequest,
    ProcessTransactionResponse,
)
from app.modules.billing.application.dto.transaction_dto import ProcessTransactionCmd
from app.modules.identity.domain.entities.account import RoleCode
from app.shared.response import BaseResponse
from app.shared.interfaces.i_usecase import IUseCase

router = APIRouter()

@router.post("/transactions", response_model=BaseResponse[ProcessTransactionResponse])
async def create_transaction(
    payload:ProcessTransactionRequest,
    user= Depends(RoleChecker([RoleCode.CASHIER])),
    usecase:IUseCase = Depends(get_process_transaction_usecase)
):
    cmd = ProcessTransactionCmd(
        ticket_id=payload.ticket_id,
        cashier_id = int(user.user_id),
        plate_number= payload.plate_number,
        payment_method= payload.payment_method,
        payment_metadata= payload.payment_metadata
    )
    processed_transaction = await usecase.execute(cmd)
    
    return BaseResponse(
        status="success",
        message="Transaction is processed and saved successfully",
        data=processed_transaction,
    )

@router.get("/transactions", response_model=BaseResponse[List[ProcessTransactionResponse]])
async def list_transaction(
    pagination = Depends(get_offset_pagination),
    user= Depends(RoleChecker([RoleCode.CASHIER, RoleCode.ADMIN])),
    usecase:IUseCase = Depends(get_list_transactions_usecase)
):
    processed_transaction = await usecase.execute(
        page=(pagination.offset // pagination.limit) + 1,
        limit=pagination.limit,
    )
    
    return BaseResponse(
        status="success",
        message="Transaction is processed and saved successfully",
        data=processed_transaction,
    )
