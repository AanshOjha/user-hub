from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Security Configuration
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    bcrypt_rounds: int = 12
    
    # Application Configuration
    app_name: str = "HR Management System"
    debug: bool = False
    base_url: str = "http://localhost:8000"
    
    # Admin Configuration
    admin_email: str
    admin_password: str
    
    # SAML Configuration (Optional)
    saml_enabled: bool = False
    azure_tenant_id: str = ""
    azure_saml_certificate: str = ""
    
    # Security Settings
    cors_origins: Optional[str] = None
    max_login_attempts: int = 5
    login_lockout_duration: int = 300
    session_timeout: int = 3600
    
    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins:
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()
