from app.modules.identity.domain.entities.user import User

from app.shared.domain.exceptions.exceptions import EntityAlreadyExists
from application.dto.user_dto import RegisterUserCmd, UserResultDto
from core.security import hash_password
from domain.repositories.i_user_repo import IUserRepository


class RegisterUserUseCase:
    def __init__(self, user_repo:IUserRepository):
        self.user_repo = user_repo

    async def execute(self, cmd: RegisterUserCmd )-> UserResultDto: 
        user = await self.user_repo.get_by_username(cmd.username)
        if user:
            raise EntityAlreadyExists("Username already taken")
        
        hashed_password = hash_password(cmd.plain_password)
        
        user = User(
            username=cmd.username,
            password_hash= hashed_password,
            role = cmd.role            
        )
        created_user =  await self.user_repo.add(user)
        
        return UserResultDto(
            id = created_user.id,
            username= created_user.username,
            role = created_user.role,
            created_at= created_user.created_at,
            updated_at= created_user.updated_at
        )
        

        
     
