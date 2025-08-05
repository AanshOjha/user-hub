from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database Configuration
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Security Configuration
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application Configuration
    app_name: str = "Login Permissions System"
    debug: bool = True
    
    # Admin Configuration
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    
    class Config:
        env_file = ".env"

settings = Settings()
