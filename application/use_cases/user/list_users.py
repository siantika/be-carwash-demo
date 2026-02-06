from typing import List

from application.dto.user_dto import UserResultDto
from domain.repositories.i_user_repo import IUserRepository


class ListUsersUseCase:
    def __init__(self, user_repo:IUserRepository):
        self.user_repo = user_repo

    async def execute(self, limit:int, offset:int )-> List[UserResultDto]: 
        
        list_users = await self.user_repo.list(limit, offset)
        
        return [
            UserResultDto(
                id = user.id,
                username= user.username,
                role = user.role,
                created_at= user.created_at,
                updated_at= user.updated_at
            ) 
            for user in list_users
        ]
            

        
     