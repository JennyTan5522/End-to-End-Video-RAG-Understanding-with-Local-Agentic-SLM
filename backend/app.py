from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
import logging
import traceback
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database components
from database import get_database, ChatSession, ChatMessage, create_tables, test_connection

# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: str = Field(default="default", description="Session identifier")

class MessageModel(BaseModel):
    id: int
    type: str  # 'user' or 'ai'
    message: str
    timestamp: str

class ChatResponse(BaseModel):
    success: bool
    user_message: MessageModel
    ai_response: MessageModel
    session_id: str

class ChatHistoryResponse(BaseModel):
    success: bool
    messages: List[MessageModel]
    session_id: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str

# Initialize FastAPI app
app = FastAPI(
    title="AI Chat API",
    description="Full-stack AI chat application backend with PostgreSQL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_database)):
    """
    Send a message to AI and get response with PostgreSQL storage
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")
        
        # Validate message
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get or create session
        result = await db.execute(select(ChatSession).where(ChatSession.id == request.session_id))
        session = result.scalar_one_or_none()
        
        if not session:
            session = ChatSession(id=request.session_id)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            logger.info(f"Created new session: {request.session_id}")
        
        # Create and store user message
        user_message = ChatMessage(
            session_id=request.session_id,
            message_type="user",
            content=request.message,
            timestamp=datetime.now()
        )
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)
        
        logger.info(f"Stored user message: {user_message.id}")
        
        # Generate AI response
        try:
            ai_response_text = await generate_ai_response(request.message)
        except Exception as ai_error:
            logger.error(f"AI generation failed: {ai_error}")
            ai_response_text = "Sorry, I'm having trouble processing your request right now."
        
        # Create and store AI message
        ai_message = ChatMessage(
            session_id=request.session_id,
            message_type="ai",
            content=ai_response_text,
            timestamp=datetime.now()
        )
        db.add(ai_message)
        await db.commit()
        await db.refresh(ai_message)
        
        logger.info(f"Stored AI message: {ai_message.id}")
        
        # Convert to response format
        user_msg_dict = {
            "id": user_message.id,
            "type": user_message.message_type,
            "message": user_message.content,
            "timestamp": user_message.timestamp.isoformat()
        }
        
        ai_msg_dict = {
            "id": ai_message.id,
            "type": ai_message.message_type,
            "message": ai_message.content,
            "timestamp": ai_message.timestamp.isoformat()
        }
        
        return ChatResponse(
            success=True,
            user_message=MessageModel(**user_msg_dict),
            ai_response=MessageModel(**ai_msg_dict),
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/chat/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_database)):
    """
    Get chat history from PostgreSQL database
    """
    try:
        # Get messages from database
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp)
        )
        messages = result.scalars().all()
        
        # Convert to response format
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "type": msg.message_type,
                "message": msg.content,
                "timestamp": msg.timestamp.isoformat()
            })
        
        return ChatHistoryResponse(
            success=True,
            messages=[MessageModel(**msg) for msg in message_list],
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Failed to retrieve chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

@app.delete("/api/chat/{session_id}")
async def clear_chat_session(session_id: str, db: AsyncSession = Depends(get_database)):
    """
    Clear chat session from PostgreSQL database
    """
    try:
        # Delete session (will cascade to messages)
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        
        if session:
            await db.delete(session)
            await db.commit()
            return {"success": True, "message": f"Session {session_id} cleared"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to clear session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def list_sessions(db: AsyncSession = Depends(get_database)):
    """
    List all active chat sessions from PostgreSQL
    """
    try:
        result = await db.execute(select(ChatSession).order_by(ChatSession.updated_at.desc()))
        sessions = result.scalars().all()
        
        session_list = []
        for session in sessions:
            # Count messages for this session
            msg_result = await db.execute(
                select(ChatMessage).where(ChatMessage.session_id == session.id)
            )
            messages = msg_result.scalars().all()
            
            session_list.append({
                "session_id": session.id,
                "message_count": len(messages),
                "created_at": session.created_at.isoformat(),
                "last_activity": session.updated_at.isoformat()
            })
        
        return {"success": True, "sessions": session_list}
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_ai_response(user_message: str) -> str:
    """
    Generate AI response using OpenAI
    """
    try:
        logger.info(f"Generating AI response for: {user_message}")
        
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Check if API key exists
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return "Sorry, AI service is not configured properly."
        
        logger.info("Creating ChatOpenAI instance...")
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.0,
            openai_api_key=api_key
        )
        
        logger.info("Invoking LLM...")
        response = llm.invoke(user_message)
        
        # Handle different response types
        if hasattr(response, 'content'):
            return response.content
        elif isinstance(response, str):
            return response
        else:
            logger.warning(f"Unexpected response type: {type(response)}")
            return str(response)
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return "Sorry, required AI libraries are not installed."
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Sorry, I encountered an error: {str(e)}"

# Startup event - create database tables
@app.on_event("startup")
async def startup_event():
    try:
        # Test database connection first
        if not await test_connection():
            raise Exception("Database connection failed")
        
        # Create tables
        await create_tables()
        
        print("🚀 FastAPI AI Chat Server Starting...")
        print("🗄️ PostgreSQL database initialized")
        print("📊 API Documentation available at:")
        print("   • Swagger UI: http://localhost:8000/docs")
        print("   • ReDoc: http://localhost:8000/redoc")
        print("🔗 API Endpoints:")
        print("   • POST /api/chat - Send message to AI")
        print("   • GET /api/chat/{session_id} - Get chat history")
        print("   • DELETE /api/chat/{session_id} - Clear session")
        print("   • GET /api/sessions - List all sessions")
        print("   • GET /api/health - Health check")
        print("💾 Chat conversations will persist in PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        print("❌ Startup failed - check your PostgreSQL connection and .env file")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 FastAPI AI Chat Server Shutting Down...")

if __name__ == '__main__':
    print("Starting FastAPI server...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )