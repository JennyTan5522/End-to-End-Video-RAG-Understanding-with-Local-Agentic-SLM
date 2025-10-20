"""Pydantic schemas for video transcript analysis and RAG responses"""
from pydantic import BaseModel, Field
from typing import List, Literal

class TranscriptInfo(BaseModel):
    """Schema for video transcript segment analysis with summary and topics"""
    summary: str = Field(..., description="A concise yet informative summary describing what happens or is discussed during the given timeframe, including the timeframe explicitly in the text.")
    topics: List[str] = Field(..., description="A list of key topics, themes, or entities mentioned within the transcript segment.")

class RAGAnswerSchema(BaseModel):
    """Schema for RAG-based question answering responses"""
    response_text: str = Field(..., description="Final concise answer to the user's question, derived only from the provided transcript context.")

class AgentSupervisorRouter(BaseModel):
    """
    Schema for routing decisions between workflows.
    
    Attributes:
        next: The next workflow to route to, or __end__ to finish.
    """
    next: Literal["general_question_workflow", "frame_processing_workflow", "audio_processing_workflow", "__end__"] = Field(
        ..., 
        description="The next workflow to route to, or __end__ to finish."
    )

class ExtractVideoFileSchema(BaseModel):
    """
    Schema for extracting audio from a video file.
    
    Attributes:
        video_file: The path to the input video file (e.g., '../data/weekly_meeting.mp4').
    """
    video_file: str = Field(
        ..., 
        description="The path to the input video file (e.g., '../data/weekly_meeting.mp4')."
    )
