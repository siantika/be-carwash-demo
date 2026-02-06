from fastapi import APIRouter, Depends, Request

from api.dependencies.auth import get_login_usecase
from api.schema.auth_schema import LoginRequest, LoginResponse
from application.use_cases.auth.login_usecase import LoginUseCase
from core.middleware.limiter import limiter
from infra.repositories.response import BaseResponse

router = APIRouter()
@router.post("/login", response_model=BaseResponse[LoginResponse])
@limiter.limit("10/second")
async def login(request: Request, 
                payload: LoginRequest,
                usecase: LoginUseCase = Depends(get_login_usecase)
             ):

    auth = await usecase.execute(payload.username, payload.password)
    
    return BaseResponse(
        status="success",
        message="login success",
        data = auth
    )
  
   