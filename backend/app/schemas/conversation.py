"""Pydantic schemas for persistent conversations and messages in CampusPilot AI."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Payload to post a new student message to a conversation."""

    content: str = Field(..., min_length=1, description="Student question or academic prompt")


class MessageItem(BaseModel):
    """Represents a persisted message."""

    id: str
    conversation_id: str
    role: str = Field(..., description="user, model, or system")
    content: str
    created_at: str


class ConversationCreate(BaseModel):
    """Payload to create a new persistent conversation."""

    title: Optional[str] = Field(default="New Academic Conversation", max_length=150)


class ConversationRename(BaseModel):
    """Payload to rename an existing conversation."""

    title: str = Field(..., min_length=1, max_length=150, description="Updated conversation title")


class ConversationSummary(BaseModel):
    """Summary item for sidebar conversation listing."""

    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str


class ConversationDetail(BaseModel):
    """Detailed view of a conversation including its chronological messages."""

    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[MessageItem] = Field(default_factory=list)


class ConversationMessageResponse(BaseModel):
    """Response returned when a student message is sent and processed by Gemini."""

    user_message: MessageItem
    assistant_message: MessageItem
    conversation_id: str
    remaining_credits: Optional[int] = None
    is_paid: bool = False
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Validated source citations")
