from typing import List

from fastapi import APIRouter, Depends

from api.dependencies.pagination import get_offset_pagination
from api.dependencies.shared import RoleChecker
from api.dependencies.transaction import (
    get_list_transactions_usecase,
    get_process_transaction_usecase,
)
from api.schema.transaction_schema import (
    ProcessTransactionRequest,
    ProcessTransactionResponse,
)
from application.dto.transaction_dto import ProcessTransactionCmd
from app.modules.identity.domain.entities.user import UserRoleEnum
from infra.repositories.response import BaseResponse
from interfaces.i_usecase import IUseCase

router = APIRouter()

@router.post("/transactions", response_model=BaseResponse[ProcessTransactionResponse])
async def create_transaction(
    payload:ProcessTransactionRequest,
    user= Depends(RoleChecker([UserRoleEnum.CASHIER])),
    usecase:IUseCase = Depends(get_process_transaction_usecase)
):
    cmd = ProcessTransactionCmd(
        ticket_id=payload.ticket_id,
        user_id = user.user_id,
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
    user= Depends(RoleChecker([UserRoleEnum.CASHIER, UserRoleEnum.ADMIN])),
    usecase:IUseCase = Depends(get_list_transactions_usecase)
):
    processed_transaction = await usecase.execute(pagination.limit, 
                                                  pagination.offset)
    
    return BaseResponse(
        status="success",
        message="Transaction is processed and saved successfully",
        data=processed_transaction,
    )
