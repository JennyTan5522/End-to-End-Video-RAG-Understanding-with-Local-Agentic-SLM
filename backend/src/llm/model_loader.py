"""
Model Manager
Loads and manages AI models across the application
"""
import logging
from typing import Optional, Tuple
from config.service_config import settings
from src.llm.embedding_model import load_embedding_model
from src.llm.chat_model import load_qwen_vl_model, build_hf_chat_model
from src.vector_database.qdrant_client import get_qdrant_client

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Singleton class to manage global AI models.
    Loads models once at startup and provides access throughout the application.
    """
    
    def __init__(self):
        """Initialize ModelManager with default values"""
        # Model instances
        self.dense_embedding_model: Optional[any] = None
        self.dense_embedding_tokenizer: Optional[any] = None
        self.qwen_processor: Optional[any] = None
        self.qwen_chat_model: Optional[any] = None
        self.chat_model: Optional[any] = None
        self.qdrant_client: Optional[any] = None
        
        # Loading state flag
        self._models_loaded: bool = False
        
        logger.info("ModelManager initialized")
    
    async def load_models(self):
        """
        Load all required models at application startup.
        This is called once during FastAPI startup event.
        """
        if self._models_loaded:
            logger.info("Models already loaded, skipping...")
            return
        
        logger.info("=" * 80)
        logger.info("LOADING GLOBAL MODELS")
        logger.info("=" * 80)
        
        try:
            # Load embedding model
            logger.info(f"Loading dense embedding model: {settings.BGE_EMBEDDING_MODEL_NAME}")
            self.dense_embedding_model, self.dense_embedding_tokenizer = load_embedding_model(
                settings.BGE_EMBEDDING_MODEL_NAME
            )
            logger.info("Dense embedding model loaded")
            
            # Load Qwen VL model
            logger.info(f"Loading Qwen VL model: {settings.QWEN_VL_MODEL_NAME}")
            self.qwen_vision_processor, self.qwen_vision_chat_model = load_qwen_vl_model(
                settings.QWEN_VL_MODEL_NAME, 
                settings.QWEN_VL_USE_4BIT
            )
            logger.info("Qwen VL model loaded")
            
            # Load chat model
            logger.info("Loading HuggingFace chat model")
            self.qwen_chat_model = build_hf_chat_model(deterministic=True)
            logger.info("Chat model loaded")
            
            # Initialize Qdrant client
            logger.info("Initializing Qdrant vector database client")
            self.qdrant_client = get_qdrant_client()
            logger.info("Qdrant client initialized")
            
            self._models_loaded = True
            logger.info("=" * 80)
            logger.info("ALL MODELS LOADED SUCCESSFULLY")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Failed to load models: {str(e)}", exc_info=True)
            raise RuntimeError(f"Model loading failed: {str(e)}")
    
    def get_embedding_model(self) -> Tuple:
        """Get the loaded embedding model and tokenizer"""
        if not self._models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        return self.dense_embedding_model, self.dense_embedding_tokenizer
    
    def get_qwen_vision_model(self) -> Tuple:
        """Get the loaded Qwen VL model and processor"""
        if not self._models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        return self.qwen_vision_processor, self.qwen_vision_chat_model
    
    def get_qdrant_client(self):
        """Get the Qdrant client"""
        if not self._models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        return self.qdrant_client
    
    def get_qwen_chat_model(self):
        """Get the chat model"""
        if not self._models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        return self.qwen_chat_model
    
    @property
    def is_loaded(self) -> bool:
        """Check if models are loaded"""
        return self._models_loaded

model_manager = ModelManager()
