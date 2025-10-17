"""
Database Models and Configuration
Defines SQLAlchemy models for chat sessions, messages, and file uploads with PostgreSQL
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
import logging

from config import settings

logger = logging.getLogger(__name__)
Base = declarative_base()


# Database Models
class ChatSession(Base):
    """
    Chat session model representing a conversation thread
    
    Attributes:
        id: Unique session identifier from frontend
        user_id: User identifier for future authentication
        title: Optional session title
        created_at: Session creation timestamp
        updated_at: Last update timestamp
        is_active: Session active status
        messages: Related chat messages (cascade delete)
    """
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_session_created', 'created_at'),
        Index('idx_session_user', 'user_id'),
    )

class ChatMessage(Base):
    """
    Individual chat message model
    
    Attributes:
        id: Unique message identifier
        session_id: Foreign key to chat_sessions
        message_type: Type of message ('user' or 'ai')
        content: Message text content
        timestamp: Message creation timestamp
        tokens_used: Optional AI cost tracking
        model_name: Optional AI model identifier
        response_time: Optional response time in milliseconds
        session: Related chat session
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    message_type = Column(String(10))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    tokens_used = Column(Integer, nullable=True)
    model_name = Column(String(50), nullable=True)
    response_time = Column(Integer, nullable=True)
    
    session = relationship("ChatSession", back_populates="messages")
    
    __table_args__ = (
        Index('idx_message_session', 'session_id'),
        Index('idx_message_timestamp', 'timestamp'),
        Index('idx_message_type', 'message_type'),
    )

class UploadedFile(Base):
    """
    Uploaded file model storing file metadata
    
    Attributes:
        id: Unique file identifier
        session_id: Foreign key to chat_sessions
        filename: Original filename from upload
        file_path: Full path in data folder
        file_type: MIME type of file
        file_size: Size in bytes
        uploaded_at: Upload timestamp
    """
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_file_session', 'session_id'),
        Index('idx_file_uploaded', 'uploaded_at'),
    )


# Database Configuration
masked_url = settings.DATABASE_URL.replace('://postgres:', '://postgres:***@')
logger.info(f"Connecting to database: {masked_url}")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Database Operations
async def create_tables():
    """
    Create all database tables if they don't exist
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


async def test_connection():
    """
    Test database connection by executing a simple query
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            if test_value == 1:
                logger.info("Database connection successful")
                return True
            else:
                logger.error("Database connection test failed")
                return False
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def get_database():
    """
    FastAPI dependency to get database session
    
    Yields:
        AsyncSession: Database session for the request
        
    Note:
        Automatically handles rollback on error and cleanup
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_database():
    """
    Initialize database by testing connection and creating tables
    
    Returns:
        bool: True if initialization successful
        
    Raises:
        Exception: If connection test or table creation fails
    """
    try:
        if not await test_connection():
            raise Exception("Database connection test failed")
        
        if not await create_tables():
            raise Exception("Table creation failed")
            
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_database():
    """
    Close all database connections
    
    Note:
        Should be called on application shutdown
    """
    await engine.dispose()
    logger.info("Database connections closed")


async def quick_test():
    """
    Quick test function for debugging database connection
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("Testing PostgreSQL connection...")
    
    masked_url = settings.DATABASE_URL.replace('://postgres:', '://postgres:***@')
    print(f"Database URL: {masked_url}")

    if await test_connection():
        print("✅ Connection successful!")

        if await create_tables():
            print("✅ Tables created successfully!")
            return True
        else:
            print("❌ Table creation failed!")
            return False
    else:
        print("❌ Connection failed!")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(quick_test())