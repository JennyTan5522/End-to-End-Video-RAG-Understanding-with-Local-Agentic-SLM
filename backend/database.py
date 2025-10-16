from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

Base = declarative_base()

class ChatSession(Base):
    """Chat session model - represents a conversation thread"""
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True)  # session_id from frontend
    user_id = Column(String, nullable=True)  # For future user authentication
    title = Column(String(255), nullable=True)  # Optional session title
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship to messages
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Index for faster queries
    __table_args__ = (
        Index('idx_session_created', 'created_at'),
        Index('idx_session_user', 'user_id'),
    )

class ChatMessage(Base):
    """Individual chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    message_type = Column(String(10))  # 'user' or 'ai'
    content = Column(Text)  # The actual message content
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Optional fields for enhanced functionality
    tokens_used = Column(Integer, nullable=True)  # For AI cost tracking
    model_name = Column(String(50), nullable=True)  # Which AI model was used
    response_time = Column(Integer, nullable=True)  # Response time in ms
    
    # Relationship to session
    session = relationship("ChatSession", back_populates="messages")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_message_session', 'session_id'),
        Index('idx_message_timestamp', 'timestamp'),
        Index('idx_message_type', 'message_type'),
    )

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:chatpassword@localhost:5432/chatdb"
)

print(f"Connecting to database: {DATABASE_URL.replace('://postgres:', '://postgres:***@')}")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Changed to False to reduce log noise
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def create_tables():
    """Create all database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

async def test_connection():
    """Test database connection"""
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
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

# Database utility functions
async def init_database():
    """Initialize database and create tables"""
    try:
        # Test connection first
        if not await test_connection():
            raise Exception("Database connection test failed")
        
        # Create tables
        if not await create_tables():
            raise Exception("Table creation failed")
            
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise

async def close_database():
    """Close database connections"""
    await engine.dispose()
    print("Database connections closed")

# Quick connection test function
async def quick_test():
    """Quick test function for debugging"""
    print("Testing PostgreSQL connection...")
    
    # Print connection info (without password)
    masked_url = DATABASE_URL.replace('://postgres:', '://postgres:***@')
    print(f"Database URL: {masked_url}")

    # Test connection
    if await test_connection():
        print("Connection successful!")

        # Test table creation
        if await create_tables():
            print("Tables created successfully!")
            return True
        else:
            print("Table creation failed!")
            return False
    else:
        print("Connection failed!")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(quick_test())