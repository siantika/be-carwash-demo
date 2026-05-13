from fastapi import Depends

from app.modules.carwash_operation.application.commands.ticket_command import (
    CreateTicketUseCase,
    GenerateEan13TimeBased,
    VoidTicketUseCase,
)
from app.modules.carwash_operation.application.queries.ticket_query import ListTicketsUseCase
from app.modules.carwash_operation.infra.repositories.idempotency_repo import (
    AsyncPgTicketIdempotencyRepository,
)
from app.modules.carwash_operation.infra.repositories.ticket_repo import (
    AsyncPgTicketRepository,
)
from app.modules.carwash_operation.infra.repositories.query.postgres_ticket_query_repository import (
    PostgresTicketQueryRepository,
)
from app.modules.carwash_operation.infra.unit_of_work import (
    AsyncPgCarwashOperationUnitOfWork,
)
from app.modules.carwash_operation.infra.services.request_hasher import Sha256RequestHasher
from app.modules.service_catalog.api.dependencies import get_service_type_repo
from app.shared.infra.database.db import get_db, get_db_pool
from app.shared.middleware.logger import StructlogLogger
from app.shared.interfaces.i_logger import ILogger


def get_logger() -> ILogger:
    return StructlogLogger("carwash_operation")


def get_ticket_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgTicketRepository(db, logger)


def get_ticket_query(db=Depends(get_db), logger=Depends(get_logger)):
    return PostgresTicketQueryRepository(db, logger)


def get_ticket_idempotency_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgTicketIdempotencyRepository(db, logger)


def get_barcode_generator():
    return GenerateEan13TimeBased()


def get_carwash_operation_uow(pool=Depends(get_db_pool), logger=Depends(get_logger)):
    return AsyncPgCarwashOperationUnitOfWork(pool, logger)


def get_request_hasher():
    return Sha256RequestHasher()


def get_create_ticket_usecase(
    ticket_repo=Depends(get_ticket_repo),
    service_type_repo=Depends(get_service_type_repo),
    barcode_generator=Depends(get_barcode_generator),
    idempotency_repo=Depends(get_ticket_idempotency_repo),
    request_hasher=Depends(get_request_hasher),
):
    return CreateTicketUseCase(
        ticket_repo,
        service_type_repo,
        barcode_generator,
        idempotency_repo,
        request_hasher,
    )


def get_list_tickets_usecase(ticket_query=Depends(get_ticket_query)):
    return ListTicketsUseCase(ticket_query)


def get_void_ticket_usecase(uow=Depends(get_carwash_operation_uow)):
    return VoidTicketUseCase(uow)
