from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    app_name: str = "Login Permissions System"
    debug: bool = True
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    
    class Config:
        env_file = ".env"

settings = Settings()
