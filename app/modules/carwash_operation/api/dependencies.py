from fastapi import Depends

from app.modules.carwash_operation.application.use_cases.ticket_usecase import (
    CreateTicketUseCase,
    GenerateEan13TimeBased,
    ListTicketsUseCase,
    VoidTicketUseCase,
)
from app.modules.carwash_operation.infra.repositories.ticket_repo import (
    AsyncPgTicketRepository,
)
from app.modules.carwash_operation.infra.unit_of_work import (
    AsyncPgCarwashOperationUnitOfWork,
)
from app.modules.service_catalog.api.dependencies import get_service_type_repo
from app.shared.middleware.logger import StructlogLogger
from infra.db import get_db, get_db_pool
from interfaces.i_logger import ILogger


def get_logger() -> ILogger:
    return StructlogLogger("carwash_operation")


def get_ticket_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgTicketRepository(db, logger)


def get_barcode_generator():
    return GenerateEan13TimeBased()


def get_carwash_operation_uow(pool=Depends(get_db_pool), logger=Depends(get_logger)):
    return AsyncPgCarwashOperationUnitOfWork(pool, logger)


def get_create_ticket_usecase(
    ticket_repo=Depends(get_ticket_repo),
    service_type_repo=Depends(get_service_type_repo),
    barcode_generator=Depends(get_barcode_generator),
):
    return CreateTicketUseCase(ticket_repo, service_type_repo, barcode_generator)


def get_list_tickets_usecase(ticket_repo=Depends(get_ticket_repo)):
    return ListTicketsUseCase(ticket_repo)


def get_void_ticket_usecase(uow=Depends(get_carwash_operation_uow)):
    return VoidTicketUseCase(uow)
