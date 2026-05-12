from app.modules.service_catalog.api.dependencies import (
    get_activate_service_type_usecase,
    get_change_service_type_usecase,
    get_create_service_type_usecase,
    get_deactivate_service_type_usecase,
    get_list_service_types_usecase,
    get_service_type_repo,
)

# Backward-compatible aliases for legacy endpoint imports with the original typo.
get_change_service_type_usercase = get_change_service_type_usecase
get_activate_service_type_usercase = get_activate_service_type_usecase
get_deactivate_service_type_usercase = get_deactivate_service_type_usecase

__all__ = [
    "get_activate_service_type_usecase",
    "get_activate_service_type_usercase",
    "get_change_service_type_usecase",
    "get_change_service_type_usercase",
    "get_create_service_type_usecase",
    "get_deactivate_service_type_usecase",
    "get_deactivate_service_type_usercase",
    "get_list_service_types_usecase",
    "get_service_type_repo",
]
