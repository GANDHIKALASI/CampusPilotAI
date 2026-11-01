from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    USER = "user"
    MODEL = "model"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: Role = Field(default=Role.USER, description="Message sender role: user, model, or system")
    content: str = Field(..., min_length=1, description="Message text content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Current user query")
    history: List[ChatMessage] = Field(default_factory=list, description="Prior conversation messages")
    model: Optional[str] = Field(default=None, description="Optional override for Gemini model")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Generated AI reply text")
    model: str = Field(..., description="Gemini model used")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="success")
    remaining_messages: Optional[int] = Field(default=None, description="Remaining preview messages for unauthenticated visitor")
    visitor_limit: Optional[int] = Field(default=None, description="Total preview limit for visitors")


class StreamChunk(BaseModel):
    chunk: str = Field(..., description="Text segment of the streaming answer")
    done: bool = Field(default=False, description="Flag indicating end of stream")


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str
    gemini_configured: bool
