"""Pydantic schemas for bulk embedding generation, idempotency tracking, and result reporting."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class EmbeddedChunk(BaseModel):
    """Represents an embedded document chunk with its vector, metadata, and content hash."""

    chunk_id: Optional[Union[str, int]] = Field(default=None, description="Original chunk identifier or index")
    chunk_index: int = Field(..., description="Global zero-based sequential index of the chunk")
    page_number: int = Field(default=1, description="1-indexed physical page number of origin")
    document_id: Optional[str] = Field(default=None, description="Source document identifier")
    filename: Optional[str] = Field(default=None, description="Source file name")
    content_hash: str = Field(..., description="Deterministic SHA-256 hash of chunk content and context")
    config_signature: str = Field(..., description="Embedding model, dimension, and task configuration signature")
    vector: List[float] = Field(..., description="Normalized floating point embedding vector")
    token_count: int = Field(default=0, description="Token count of the chunk content")
    character_count: int = Field(default=0, description="Character count of the chunk content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Preserved chunk metadata")


class FailedChunk(BaseModel):
    """Represents a chunk that failed embedding generation."""

    chunk_id: Optional[Union[str, int]] = Field(default=None, description="Original chunk identifier")
    chunk_index: int = Field(..., description="Index of the failed chunk")
    page_number: Optional[int] = Field(default=None, description="Page number of origin")
    error: str = Field(..., description="Specific failure reason or validation error")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    retryable: bool = Field(default=False, description="Whether the error was transient")


class SkippedChunk(BaseModel):
    """Represents a chunk that was skipped (e.g. unchanged content or empty string)."""

    chunk_id: Optional[Union[str, int]] = Field(default=None, description="Original chunk identifier")
    chunk_index: int = Field(..., description="Index of the skipped chunk")
    page_number: Optional[int] = Field(default=None, description="Page number of origin")
    reason: str = Field(..., description="Reason for skipping ('unchanged_content_and_config' or 'empty_content')")
    content_hash: Optional[str] = Field(default=None, description="SHA-256 hash if computed")


class BulkEmbeddingResult(BaseModel):
    """Comprehensive audit and response object for bulk embedding operations."""

    status: str = Field(..., description="'success', 'partial_success', or 'failed'")
    model: str = Field(..., description="Embedding model name used")
    dimension: int = Field(..., description="Embedding vector dimensionality used")
    total_chunks: int = Field(..., description="Total input chunks received")
    successful_count: int = Field(..., description="Number of chunks successfully embedded")
    failed_count: int = Field(..., description="Number of chunks that failed")
    skipped_count: int = Field(..., description="Number of chunks skipped due to idempotency or emptiness")
    api_calls_made: int = Field(..., description="Total API network requests executed")
    total_latency_seconds: float = Field(..., description="Total elapsed processing wall-clock time in seconds")
    average_latency_per_call_ms: float = Field(default=0.0, description="Average API call round-trip latency in ms")
    total_characters_embedded: int = Field(default=0, description="Total characters embedded in API calls")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated API usage cost based on official rates")
    successful_chunks: List[EmbeddedChunk] = Field(default_factory=list, description="List of successfully embedded chunks")
    failed_chunks: List[FailedChunk] = Field(default_factory=list, description="List of failed chunks")
    skipped_chunks: List[SkippedChunk] = Field(default_factory=list, description="List of skipped chunks")
