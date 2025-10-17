"""
Configuration settings for the AI Video Assistant API
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List

class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables"""
    
    # API Configuration
    API_TITLE: str = "AI Video Assistant API"
    API_DESCRIPTION: str = "Backend service for AI-powered video chat with file upload and PostgreSQL storage"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:chatpassword@localhost:5432/chatdb"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.0
    
    # File Upload Configuration
    DATA_FOLDER: Path = Path(__file__).parent / "data"
    ALLOWED_FILE_EXTENSIONS: List[str] = ['.mp3', '.mp4']
    MAX_FILE_SIZE_MB: int = 100
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    ALLOW_ALL_ORIGINS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    def initialize_data_folder(self):
        """Create data folder if it doesn't exist"""
        self.DATA_FOLDER.mkdir(exist_ok=True)


# Initialize settings
settings = Settings()
settings.initialize_data_folder()
