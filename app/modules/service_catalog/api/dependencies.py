from fastapi import Depends

from app.modules.service_catalog.application.use_cases.service_type_usecase import (
    ActivateServiceTypeUseCase,
    ChangeServiceTypeDataUseCase,
    CreateServiceTypeUseCase,
    DeactivateServiceTypeUseCase,
    DeleteServiceTypeUseCase,
    FindServiceTypeByIdUseCase,
    ListServiceTypesUseCase,
)
from app.modules.service_catalog.infra.repositories.service_type_repo import (
    AsyncPgServiceTypeRepository,
)
from app.shared.middleware.logger import StructlogLogger
from infra.db import get_db
from interfaces.i_logger import ILogger


def get_logger() -> ILogger:
    return StructlogLogger("service_catalog")


def get_service_type_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgServiceTypeRepository(db, logger)


def get_list_service_types_usecase(service_type_repo=Depends(get_service_type_repo)):
    return ListServiceTypesUseCase(service_type_repo)

def get_find_service_type_by_id(service_type_repo=Depends(get_service_type_repo)):
    return FindServiceTypeByIdUseCase(service_type_repo)

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
