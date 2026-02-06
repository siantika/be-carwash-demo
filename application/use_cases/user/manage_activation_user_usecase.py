from application.dto.user_dto import UserResultDto
from domain.exceptions import EntityNotFound
from domain.repositories.i_user_repo import IUserRepository


class ActivateStatusUserUseCase:
    def __init__(self, user_repo:IUserRepository):
        self.user_repo = user_repo
        
    async def execute(self, user_id: int )-> UserResultDto:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFound(f"User with id: {user_id} not found!")
        
        user.activate()
        
        activated_user = await self.user_repo.save(user)
        return UserResultDto(
            id = activated_user.id,
            username= activated_user.username,
            role = activated_user.role,
            created_at= activated_user.created_at,
            updated_at= activated_user.updated_at
        )


class DeactivateStatusUserUseCase:
    def __init__(self, user_repo:IUserRepository):
        self.user_repo = user_repo
        
    async def execute(self, user_id: int )-> UserResultDto:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFound(f"User with id: {user_id} not found!")
        
        user.deactivate()
        
        deactivated_user = await self.user_repo.save(user)
        return UserResultDto(
            id = deactivated_user.id,
            username= deactivated_user.username,
            role = deactivated_user.role,
            created_at= deactivated_user.created_at,
            updated_at= deactivated_user.updated_at
        )