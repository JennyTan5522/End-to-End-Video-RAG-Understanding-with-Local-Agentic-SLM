"""Pydantic schemas for video transcript analysis and RAG responses"""
from pydantic import BaseModel, Field
from typing import List

class TranscriptInfo(BaseModel):
    """Schema for video transcript segment analysis with summary and topics"""
    summary: str = Field(..., description="A concise yet informative summary describing what happens or is discussed during the given timeframe, including the timeframe explicitly in the text.")
    topics: List[str] = Field(..., description="A list of key topics, themes, or entities mentioned within the transcript segment.")

class RAGAnswerSchema(BaseModel):
    """Schema for RAG-based question answering responses"""
    response_text: str = Field(..., description="Final concise answer to the user's question, derived only from the provided transcript context.")
