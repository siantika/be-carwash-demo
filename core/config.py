from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS:int = 8
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str 
    DB_PORT: int
    
    PORT:int
    HOST:str
    
    API_VERSION:str
    
    CORS_ORIGINS: list[str] = [
        "*"
    ]
    CORS_ALLOW_METHODS: list[str] = [
        "GET", "POST", "PUT", "PATCH", "OPTIONS"
    ]
    CORS_ALLOW_HEADERS: list[str] = [
        "Authorization",
        "Content-Type",
        "Accept",
    ]

    class Config:
        env_file = ".env"

settings = Settings()  
