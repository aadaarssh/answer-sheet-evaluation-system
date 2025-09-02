from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "ai_evaluation_system"
    
    # JWT Authentication
    secret_key: str = "your-super-secret-key-change-in-production-123456789"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI APIs
    openai_api_key: str = ""
    gemini_api_key: str = ""
    
    # File Storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10
    
    # Processing
    real_time_threshold: int = 5
    redis_url: str = "redis://localhost:6379"
    
    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_user: str = ""
    email_password: str = ""
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:4200,http://localhost:5173,http://localhost:8080,http://localhost:8081,http://127.0.0.1:3000,http://127.0.0.1:4200,http://127.0.0.1:5173,http://127.0.0.1:8080,http://127.0.0.1:8081"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"

# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)