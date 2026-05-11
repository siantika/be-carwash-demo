from fastapi import Depends

from app.api.dependencies.service_type import get_service_type_repo
from app.api.dependencies.shared import get_logger, get_uow
from application.use_cases.ticket.create_ticket_usecase import (
    CreateTicketUseCase,
    GenerateEan13TimeBased,
)
from application.use_cases.ticket.list_tickets_usecase import ListTicketsUseCase
from application.use_cases.ticket.void_ticket_usecase import VoidTicketUseCase
from infra.db import get_db
from infra.repositories.ticket_repo import AsyncPgTicketRepository


def get_barcode_generator():
    return GenerateEan13TimeBased()

def get_ticket_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgTicketRepository(db, logger)

def get_list_tickets_usecase(ticket_repo=Depends(get_ticket_repo)):
    return ListTicketsUseCase(ticket_repo)

def get_create_ticket_usecase(ticket_repo=Depends(get_ticket_repo), 
                              service_type_repo= Depends(get_service_type_repo),
                              barcode_generator = Depends(get_barcode_generator)
                              ):
    return CreateTicketUseCase(ticket_repo, service_type_repo, barcode_generator)

def get_void_ticket_usecase(uow=Depends(get_uow)):
    return VoidTicketUseCase(uow)
