"""
AI Video Assistant FASTAPI - Main Application
Provides endpoints for chat, file upload, and session management with PostgreSQL storage
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import uvicorn
import logging
import traceback
from pathlib import Path

from config.service_config import settings
from web.database import (
    get_database, 
    ChatSession, 
    ChatMessage, 
    UploadedFile, 
    create_tables, 
    test_connection
)

# Add backend folder to py path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 

# Pydantic Models for Request/Response Validation
class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str = Field(..., min_length=1, description="User message")
    session_id: str = Field(default="default", description="Session identifier")

class MessageModel(BaseModel):
    """Model representing a chat message"""
    id: int
    type: str
    message: str
    timestamp: str

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    success: bool
    user_message: MessageModel
    ai_response: MessageModel
    session_id: str

class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    success: bool
    messages: List[MessageModel]
    session_id: str

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: str

class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    filename: str
    file_path: str
    file_size: int
    file_id: int
    message: str
    workflow_id: str = None  # Optional, only for MP4 files


class FileListResponse(BaseModel):
    """Response model for file list"""
    success: bool
    files: List[dict]

class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status"""
    success: bool
    status: str  # 'processing', 'completed', 'failed', 'not_found'
    progress: int  # 0-100
    message: str
    current_step: str

# Initialize FastAPI Application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global dictionary to track workflow progress (in production, use Redis or database)
workflow_status = {}

# Configure CORS Middleware
cors_origins = ["*"] if settings.ALLOW_ALL_ORIGINS else settings.CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API Endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_database)):
    """
    Send a message to AI and receive a response
    
    Args:
        request: ChatRequest containing message and session_id
        db: Database session dependency
        
    Returns:
        ChatResponse with user message, AI response, and session_id
        
    Raises:
        HTTPException: If message is empty or server error occurs
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")
        
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Ensure session exists before storing messages
        await get_or_create_session(db, request.session_id)
        
        user_message = await store_message(
            db, request.session_id, "user", request.message
        )
        logger.info(f"Stored user message: {user_message.id}")
        
        try:
            ai_response_text = await generate_ai_response(request.message)
        except Exception as ai_error:
            logger.error(f"AI generation failed: {ai_error}")
            ai_response_text = "Sorry, I'm having trouble processing your request right now."
        
        ai_message = await store_message(
            db, request.session_id, "ai", ai_response_text
        )
        logger.info(f"Stored AI message: {ai_message.id}")
        
        return ChatResponse(
            success=True,
            user_message=message_to_model(user_message),
            ai_response=message_to_model(ai_message),
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}\n{traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/chat/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_database)):
    """
    Retrieve chat history for a session
    
    Args:
        session_id: Unique session identifier
        db: Database session dependency
        
    Returns:
        ChatHistoryResponse with list of messages
    """
    try:
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp)
        )
        messages = result.scalars().all()
        
        return ChatHistoryResponse(
            success=True,
            messages=[message_to_model(msg) for msg in messages],
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Failed to retrieve chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = "default",
    db: AsyncSession = Depends(get_database)
):
    """
    Upload MP3 or MP4 file to server
    
    Args:
        file: Uploaded file (MP3 or MP4 only)
        session_id: Session identifier
        db: Database session dependency
        
    Returns:
        FileUploadResponse with file metadata
        
    Raises:
        HTTPException: If file type is invalid or upload fails
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only {', '.join(settings.ALLOWED_FILE_EXTENSIONS)} files are allowed."
            )
        
        # Ensure session exists before storing file metadata
        await get_or_create_session(db, session_id)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = settings.DATA_FOLDER / safe_filename
        
        content = await file.read()
        file_size = len(content)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"File saved to: {file_path}")
        
        uploaded_file = UploadedFile(
            session_id=session_id,
            filename=file.filename,
            file_path=str(file_path),
            file_type=file.content_type,
            file_size=file_size,
            uploaded_at=datetime.now()
        )
        db.add(uploaded_file)
        await db.commit()
        await db.refresh(uploaded_file)
        
        logger.info(f"File metadata stored in database: {uploaded_file.id}")
        
        # Trigger agent workflow for MP4 files
        workflow_message = None
        workflow_id = None
        if file_extension == '.mp4':
            try:
                logger.info(f"Triggering agent workflow for MP4 file: {safe_filename}")
                from web.agent.agent_workflow_builder import process_uploaded_video
                
                # Create the relative path for the workflow (data/<filename>)
                relative_file_path = f"data/{safe_filename}"
                
                # Generate workflow ID
                workflow_id = f"workflow_{session_id}_{uploaded_file.id}"
                
                # Initialize workflow status
                workflow_status[workflow_id] = {
                    "status": "processing",
                    "progress": 0,
                    "message": "Initializing workflow...",
                    "current_step": "Starting",
                    "file_name": file.filename
                }
                
                # Trigger workflow in background (non-blocking)
                import asyncio
                asyncio.create_task(
                    process_uploaded_video_with_progress(
                        relative_file_path, 
                        workflow_id, 
                        session_id, 
                        db
                    )
                )
                
                # Create automatic user message for workflow
                workflow_message = f"Please process this video file: {relative_file_path}"
                
                # Store the automatic workflow message
                await store_message(db, session_id, "user", workflow_message)
                await store_message(
                    db, session_id, "ai", 
                    f"🎬 Processing video '{file.filename}'... This may take a few minutes. I'll analyze the audio and frames for you.\n\n⏳ Workflow ID: `{workflow_id}`"
                )
                
                logger.info(f"Agent workflow triggered for: {relative_file_path} (ID: {workflow_id})")
            except Exception as workflow_error:
                logger.error(f"Failed to trigger workflow: {str(workflow_error)}")
                # Don't fail the upload if workflow fails
                workflow_message = f"⚠️ File uploaded but workflow failed to start: {str(workflow_error)}"
        
        response_data = FileUploadResponse(
            success=True,
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_id=uploaded_file.id,
            message=f"File '{file.filename}' uploaded successfully{' and processing started' if file_extension == '.mp4' else ''}",
            workflow_id=workflow_id  # Will be None for MP3 files
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {str(e)}\n{traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.get("/api/workflow/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """
    Get the current status and progress of a workflow
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        WorkflowStatusResponse with current status and progress
    """
    try:
        if workflow_id not in workflow_status:
            return WorkflowStatusResponse(
                success=False,
                status="not_found",
                progress=0,
                message="Workflow not found",
                current_step="Unknown"
            )
        
        status_data = workflow_status[workflow_id]
        return WorkflowStatusResponse(
            success=True,
            status=status_data["status"],
            progress=status_data["progress"],
            message=status_data["message"],
            current_step=status_data["current_step"]
        )
    except Exception as e:
        logger.error(f"Failed to get workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@app.get("/api/files/{session_id}", response_model=FileListResponse)
async def get_uploaded_files(session_id: str, db: AsyncSession = Depends(get_database)):
    """
    Get list of uploaded files for a session
    
    Args:
        session_id: Session identifier
        db: Database session dependency
        
    Returns:
        FileListResponse with list of uploaded files
    """
    try:
        result = await db.execute(
            select(UploadedFile)
            .where(UploadedFile.session_id == session_id)
            .order_by(UploadedFile.uploaded_at.desc())
        )
        files = result.scalars().all()
        
        file_list = [
            {
                "id": file.id,
                "filename": file.filename,
                "file_path": file.file_path,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "uploaded_at": file.uploaded_at.isoformat()
            }
            for file in files
        ]
        
        return FileListResponse(success=True, files=file_list)
    except Exception as e:
        logger.error(f"Failed to retrieve files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve files: {str(e)}")

@app.delete("/api/files/{file_id}")
async def delete_file(file_id: int, db: AsyncSession = Depends(get_database)):
    """
    Delete an uploaded file from both database and disk
    
    Args:
        file_id: File identifier
        db: Database session dependency
        
    Returns:
        Success response with file details
        
    Raises:
        HTTPException: If file not found or deletion fails
    """
    try:
        result = await db.execute(
            select(UploadedFile).where(UploadedFile.id == file_id)
        )
        file_record = result.scalar_one_or_none()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = Path(file_record.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted file from disk: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file from disk: {e}")
        
        await db.delete(file_record)
        await db.commit()
        
        logger.info(f"Deleted file record from database: {file_id}")
        
        return {
            "success": True,
            "message": f"File '{file_record.filename}' deleted successfully",
            "file_id": file_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete file: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@app.delete("/api/chat/{session_id}")
async def clear_chat_session(session_id: str, db: AsyncSession = Depends(get_database)):
    """
    Clear all messages for a chat session
    
    Args:
        session_id: Session identifier
        db: Database session dependency
        
    Returns:
        Success response
    """
    try:
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
    List all active chat sessions
    
    Args:
        db: Database session dependency
        
    Returns:
        List of sessions with metadata
    """
    try:
        result = await db.execute(select(ChatSession).order_by(ChatSession.updated_at.desc()))
        sessions = result.scalars().all()
        
        session_list = []
        for session in sessions:
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


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """API health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )


# Helper Functions
async def process_uploaded_video_with_progress(
    file_path: str, 
    workflow_id: str, 
    session_id: str,
    db: AsyncSession
):
    """
    Wrapper function to process video with progress tracking
    
    Args:
        file_path: Path to the uploaded video file
        workflow_id: Unique workflow identifier
        session_id: Session identifier for storing messages
        db: Database session
    """
    try:
        from web.agent.agent_workflow_builder import process_uploaded_video
        
        # Update progress: Starting
        workflow_status[workflow_id].update({
            "progress": 10,
            "message": "Initializing video processing...",
            "current_step": "Initialization"
        })
        
        # Update progress: Processing
        workflow_status[workflow_id].update({
            "progress": 30,
            "message": "Analyzing video content...",
            "current_step": "Analysis"
        })
        
        # Execute the actual workflow
        result = await process_uploaded_video(file_path)
        
        # Update progress: Completing
        workflow_status[workflow_id].update({
            "progress": 90,
            "message": "Finalizing results...",
            "current_step": "Finalization"
        })
        
        # Check if workflow succeeded
        if result.get("success", False):
            workflow_status[workflow_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Video processing completed successfully!",
                "current_step": "Completed"
            })
            
            # Store completion message
            file_name = workflow_status[workflow_id].get("file_name", "video")
            completion_msg = f"✅ Video processing complete for '{file_name}'! The video has been analyzed and indexed. You can now ask questions about it."
            await store_message(db, session_id, "ai", completion_msg)
            
        else:
            workflow_status[workflow_id].update({
                "status": "failed",
                "progress": 100,
                "message": f"Processing failed: {result.get('error', 'Unknown error')}",
                "current_step": "Failed"
            })
            
            error_msg = f"❌ Video processing failed: {result.get('error', 'Unknown error')}"
            await store_message(db, session_id, "ai", error_msg)
            
        logger.info(f"Workflow {workflow_id} completed with status: {workflow_status[workflow_id]['status']}")
        
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed with error: {str(e)}\n{traceback.format_exc()}")
        
        workflow_status[workflow_id].update({
            "status": "failed",
            "progress": 100,
            "message": f"Processing error: {str(e)}",
            "current_step": "Error"
        })
        
        try:
            error_msg = f"❌ Video processing encountered an error: {str(e)}"
            await store_message(db, session_id, "ai", error_msg)
        except Exception as store_error:
            logger.error(f"Failed to store error message: {str(store_error)}")

async def get_or_create_session(db: AsyncSession, session_id: str) -> ChatSession:
    """
    Get existing session or create new one
    
    Args:
        db: Database session
        session_id: Session identifier
        
    Returns:
        ChatSession instance
    """
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    
    if not session:
        session = ChatSession(id=session_id)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        logger.info(f"Created new session: {session_id}")
    
    return session


async def store_message(
    db: AsyncSession, 
    session_id: str, 
    message_type: str, 
    content: str
) -> ChatMessage:
    """
    Store a chat message in database
    
    Args:
        db: Database session
        session_id: Session identifier
        message_type: Type of message ('user' or 'ai')
        content: Message content
        
    Returns:
        ChatMessage instance
    """
    message = ChatMessage(
        session_id=session_id,
        message_type=message_type,
        content=content,
        timestamp=datetime.now()
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


def message_to_model(message: ChatMessage) -> MessageModel:
    """
    Convert ChatMessage to MessageModel
    
    Args:
        message: ChatMessage database instance
        
    Returns:
        MessageModel for API response
    """
    return MessageModel(
        id=message.id,
        type=message.message_type,
        message=message.content,
        timestamp=message.timestamp.isoformat()
    )


async def generate_ai_response(user_message: str) -> str:
    """
    Generate AI response
    
    Args:
        user_message: User's input message
        
    Returns:
        AI-generated response text
    """
    try:
        logger.info(f"Generating AI response for: {user_message[:50]}...")
        
        # Check if OpenAI is configured TODO: Replace with local model
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
            logger.warning("OPENAI_API_KEY not configured, using mock response")
            return f"✅ Message received: '{user_message[:100]}...' (Mock response - Configure OPENAI_API_KEY in .env for real AI responses)"
        
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        response = llm.invoke(user_message)
        
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
        logger.error(f"Error generating AI response: {str(e)}\n{traceback.format_exc()}")
        return f"Sorry, I encountered an error: {str(e)}"

# Application Lifecycle Events
@app.on_event("startup")
async def startup_event():
    """Initialize database and display startup information"""
    try:
        if not await test_connection():
            raise Exception("Database connection failed")
        
        await create_tables()

        # Load global models
        logger.info("Loading AI models...")
        from src.llm.model_loader import model_manager
        await model_manager.load_models()
        logger.info("🤖 AI models loaded and ready")
        
        logger.info(f"🚀 {settings.API_TITLE} Starting...")
        logger.info(f"🗄️  PostgreSQL database initialized")
        logger.info(f"📊 API Documentation:")
        logger.info(f"   • Swagger UI: http://{settings.API_HOST}:{settings.API_PORT}/docs")
        logger.info(f"   • ReDoc: http://{settings.API_HOST}:{settings.API_PORT}/redoc")
        logger.info(f"🔗 API Endpoints:")
        logger.info(f"   • POST /api/chat - Send message to AI")
        logger.info(f"   • GET /api/chat/{{session_id}} - Get chat history")
        logger.info(f"   • POST /api/upload - Upload MP3/MP4 file")
        logger.info(f"   • GET /api/files/{{session_id}} - List uploaded files")
        logger.info(f"   • DELETE /api/files/{{file_id}} - Delete file")
        logger.info(f"   • DELETE /api/chat/{{session_id}} - Clear session")
        logger.info(f"   • GET /api/sessions - List all sessions")
        logger.info(f"   • GET /api/health - Health check")
        logger.info(f"💾 Data stored in: {settings.DATA_FOLDER}")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        logger.info("❌ Startup failed - check your PostgreSQL connection and .env file")
        raise


async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info(f"🛑 {settings.API_TITLE} Shutting Down...")
    
    # Close all database connections properly
    from web.database import engine
    await engine.dispose()
    logger.info(" Database connections closed")


if __name__ == '__main__':
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        "web.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )