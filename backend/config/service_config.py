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
    DATABASE_URL: str = "postgresql+asyncpg://postgres:admin@localhost:5432/chatdb"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.0
    
    # Audio Model Configuration
    AUDIO_MODEL_NAME: str = "distil-whisper/distil-small.en"

    # Qwen-VL Model Configuration
    QWEN_VL_MODEL_NAME: str = "yangjie-cv/WeThink-Qwen2.5VL-7B"
    QWEN_VL_USE_4BIT: bool = True

    # bge Embedding Model Configuration
    BGE_EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"

    # File Upload Configuration
    DATA_FOLDER: Path = Path(__file__).parent.parent / "data"
    ALLOWED_FILE_EXTENSIONS: List[str] = ['.mp3', '.mp4']
    MAX_FILE_SIZE_MB: int = 100

    # MCP Server COnfiguration
    AUDIO_MCP_URL:str = "http://127.0.0.1:8002/mcp"
    AUDIO_MCP_PORT: int = 8002
    
    VIDEO_FRAME_MCP_URL: str = "http://127.0.0.1:8003/mcp"
    VIDEO_FRAME_MCP_PORT: int = 8003
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://*.proxy.runpod.net",
        "*"
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
