from fastapi import Depends

from app.modules.service_catalog.application.commands.service_type_command import (
    ActivateServiceTypeUseCase,
    ChangeServiceTypeDataUseCase,
    CreateServiceTypeUseCase,
    DeactivateServiceTypeUseCase,
    DeleteServiceTypeUseCase,
)
from app.modules.service_catalog.application.queries.service_type_query import (
    FindServiceTypeByIdUseCase,
    FindServiceTypeByNameUseCase,
    ListServiceTypesUseCase,
)
from app.modules.service_catalog.infra.repositories.service_type_repo import (
    AsyncPgServiceTypeRepository,
)
from app.modules.service_catalog.infra.repositories.query.postgres_service_type_query_repository import (
    PostgresServiceTypeQueryRepository,
)
from app.shared.infra.database.db import get_db
from app.shared.middleware.logger import StructlogLogger
from app.shared.interfaces.i_logger import ILogger


def get_logger() -> ILogger:
    return StructlogLogger("service_catalog")


def get_service_type_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgServiceTypeRepository(db, logger)


def get_service_type_query(db=Depends(get_db), logger=Depends(get_logger)):
    return PostgresServiceTypeQueryRepository(db, logger)


def get_list_service_types_usecase(service_type_query=Depends(get_service_type_query)):
    return ListServiceTypesUseCase(service_type_query)


def get_find_service_type_by_id(service_type_repo=Depends(get_service_type_repo)):
    return FindServiceTypeByIdUseCase(service_type_repo)


def get_find_service_type_by_name(service_type_repo=Depends(get_service_type_repo)):
    return FindServiceTypeByNameUseCase(service_type_repo)


def get_create_service_type_usecase(service_type_repo=Depends(get_service_type_repo)):
    return CreateServiceTypeUseCase(service_type_repo)


def get_change_service_type_usecase(service_type_repo=Depends(get_service_type_repo)):
    return ChangeServiceTypeDataUseCase(service_type_repo)


def get_activate_service_type_usecase(service_type_repo=Depends(get_service_type_repo)):
    return ActivateServiceTypeUseCase(service_type_repo)


def get_deactivate_service_type_usecase(service_type_repo=Depends(get_service_type_repo)):
    return DeactivateServiceTypeUseCase(service_type_repo)


def get_delete_service_type_usecase(service_type_repo=Depends(get_service_type_repo)):
    return DeleteServiceTypeUseCase(service_type_repo)
