from typing import Annotated, List

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.dependencies.shared import RoleChecker
from app.modules.carwash_operation.api.dependencies import (
    get_create_ticket_usecase,
    get_list_tickets_usecase,
    get_void_ticket_usecase,
)
from app.modules.carwash_operation.api.schemas import (
    CreateTicketRequest,
    TicketResponse,
    TicketVoidRequest,
    TicketVoidResponse,
)
from app.modules.carwash_operation.application.dto.ticket_dto import (
    CreateTicketCmd,
    TicketListFilterDto,
)
from app.modules.carwash_operation.application.dto.ticket_void_dto import (
    CreateTicketVoidCmd,
)
from app.modules.carwash_operation.application.use_cases.ticket_usecase import (
    CreateTicketUseCase,
    ListTicketsUseCase,
    VoidTicketUseCase,
)
from app.modules.carwash_operation.domain.entities.ticket import TicketStatusEnum
from app.modules.identity.domain.entities.account import RoleCode
from app.shared.response import BaseResponse, Metadata

router = APIRouter()

CARWASH_OPERATION_ROLES = [RoleCode.ADMIN, RoleCode.OWNER, RoleCode.CASHIER]


@router.post("", response_model=BaseResponse[TicketResponse], status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: CreateTicketRequest,
    user=Depends(RoleChecker(CARWASH_OPERATION_ROLES)),
    usecase: CreateTicketUseCase = Depends(get_create_ticket_usecase),
):
    ticket = await usecase.execute(CreateTicketCmd(service_type_id=payload.service_type_id))
    return BaseResponse(data=ticket)


@router.get("", response_model=BaseResponse[List[TicketResponse]])
async def list_tickets(
    ticket_status: TicketStatusEnum | None = Query(default=None, alias="status"),
    service_type_id: int | None = Query(default=None, ge=1),
    ticket_number: str | None = Query(default=None, min_length=1, max_length=32),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(RoleChecker(CARWASH_OPERATION_ROLES)),
    usecase: ListTicketsUseCase = Depends(get_list_tickets_usecase),
):
    result = await usecase.execute(
        filters=TicketListFilterDto(
            status=ticket_status,
            service_type_id=service_type_id,
            ticket_number=ticket_number,
        ),
        page=page,
        limit=limit,
    )
    return BaseResponse(
        data=result.items,
        metadata=Metadata(page=result.page, limit=result.limit, total=result.total),
    )


@router.patch("/{ticket_id}/void", response_model=BaseResponse[TicketVoidResponse])
async def void_ticket(
    ticket_id: Annotated[int, Path(ge=1)],
    payload: TicketVoidRequest,
    user=Depends(RoleChecker(CARWASH_OPERATION_ROLES)),
    usecase: VoidTicketUseCase = Depends(get_void_ticket_usecase),
):
    voided_ticket = await usecase.execute(
        CreateTicketVoidCmd(
            ticket_id=ticket_id,
            account_id=int(user.user_id),
            reason=payload.reason,
        )
    )
    return BaseResponse(data=voided_ticket)
