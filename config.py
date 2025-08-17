from pydantic_settings import BaseSettings
from typing import Optional, List

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
    
    # Security Configuration - All from environment variables
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application Configuration
    app_name: str = "Login Permissions System"
    debug: bool = False  # Changed to False for production safety
    
    # Admin Configuration - From environment variables
    admin_email: str
    admin_password: str
    
    # Additional Security Settings (Optional)
    cors_origins: Optional[str] = None  # Comma-separated list of allowed origins
    max_login_attempts: int = 5
    login_lockout_duration: int = 300  # seconds
    session_timeout: int = 3600  # seconds
    bcrypt_rounds: int = 12
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        if self.cors_origins:
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return ["*"]  # Allow all origins in development (not recommended for production)
    
    class Config:
        env_file = ".env"

settings = Settings()
