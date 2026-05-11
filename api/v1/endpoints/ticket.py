from typing import List

from fastapi import APIRouter, Depends

from api.dependencies.pagination import get_offset_pagination
from api.dependencies.shared import RoleChecker
from api.dependencies.ticket import (
    get_create_ticket_usecase,
    get_list_tickets_usecase,
    get_void_ticket_usecase,
)
from api.schema.ticket_schema import CreateTicketRequest, TicketResponse
from api.schema.ticket_void_schema import TicketVoidRequest, TicketVoidResponse
from application.dto.ticket_dto import CreateTicketCmd
from application.dto.ticket_void_dto import CreateTicketVoidCmd
from application.use_cases.ticket.create_ticket_usecase import CreateTicketUseCase
from application.use_cases.ticket.void_ticket_usecase import VoidTicketUseCase
from app.modules.identity.domain.entities.account import RoleCode
from infra.repositories.response import BaseResponse
from interfaces.i_usecase import IUseCase

router = APIRouter()


@router.post("/tickets", response_model=BaseResponse[TicketResponse])
async def create_ticket(
    payload:CreateTicketRequest,
    usecase: CreateTicketUseCase=Depends(get_create_ticket_usecase)
):
    cmd = CreateTicketCmd(
        service_type_id = payload.service_type_id
    )
    created_ticket = await usecase.execute(cmd)
    
    return BaseResponse(
        status="success",
        message=f"Ticket with number: {created_ticket.ticket_number} created successfully!",
        data=created_ticket,
    )
    

@router.get("/tickets", response_model=BaseResponse[List[TicketResponse]])
async def list_tickets(
    pagination = Depends(get_offset_pagination),
    usecase: IUseCase = Depends(get_list_tickets_usecase)
):
    list_tickets = await usecase.execute(pagination.limit, pagination.offset)
    return BaseResponse(
        status="success",
        message="List tickets retrieved successfully",
        data=list_tickets,
    )
    
    
@router.patch(
    "/tickets/{ticket_id}/void",
    response_model=BaseResponse[TicketVoidResponse],
)
async def void_ticket(
    ticket_id: int,
    payload:TicketVoidRequest,
     user = Depends(RoleChecker([
        RoleCode.ADMIN, 
        RoleCode.CASHIER,
        ])),
    usecase: VoidTicketUseCase = Depends(get_void_ticket_usecase)
):
    cmd = CreateTicketVoidCmd(
        ticket_id= ticket_id,
        user_id = user.user_id,
        reason = payload.reason
    )
    voided_ticket = await usecase.execute(cmd)

    return BaseResponse(
        status="success",
        message=f"Ticket with id {ticket_id} successfully updated to VOID",
        data=voided_ticket,
    )



# @router.get("/void-tickets", response_model=BaseResponse[List[VoidTicketDto]])
# async def get_void_tickets(
#     q: Optional[str] = Query(default=None, 
#                              description="Search by ticket number or username"),
#     db = Depends(get_db),
# ):
#     ticket_repo = TicketVoidRepository(db)
#     service = ListAllVoidTickets(ticket_repo)
    
#     list_void_tickets = await service.execute(q)

#     return BaseResponse(
#         status="success",
#         message="List all of void ticket successfully fetched",
#         data=list_void_tickets,
#     )

   
