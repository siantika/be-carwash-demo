from multiprocessing import get_logger

from fastapi import Depends

from application.use_cases.service_type.change_service_type_data_usecase import (
    ChangeServiceTypeDataUseCase,
)
from application.use_cases.service_type.create_service_type_usecase import (
    CreateServiceTypeUseCase,
)
from application.use_cases.service_type.list_service_types_usecase import (
    ListServiceTypesUseCase,
)
from application.use_cases.service_type.manage_activation_status_usecase import (
    ActivateStatusServiceTypeUseCase,
    DeactivateStatusServiceTypeUseCase,
)
from infra.db import get_db
from infra.repositories.service_type_repo import AsyncPgServiceTypeRepository


def get_service_type_repo(db=Depends(get_db), logger=Depends(get_logger)):
    return AsyncPgServiceTypeRepository(db, logger)

def get_list_service_types_usecase(service_type_repo=Depends(get_service_type_repo)):
    return ListServiceTypesUseCase(service_type_repo)

def get_create_service_type_usecase(service_type_repo=Depends(get_service_type_repo)):
    return CreateServiceTypeUseCase(service_type_repo)

def get_change_service_type_usercase(service_type_repo=Depends(get_service_type_repo)):
    return ChangeServiceTypeDataUseCase(service_type_repo)

def get_activate_service_type_usercase(service_type_repo=Depends(get_service_type_repo)):
    return ActivateStatusServiceTypeUseCase(service_type_repo)

def get_deactivate_service_type_usercase(service_type_repo=Depends(get_service_type_repo)):
    return DeactivateStatusServiceTypeUseCase(service_type_repo)