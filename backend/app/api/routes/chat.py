import json
import re
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from app.core.config import Settings, get_settings
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
)
from app.services.gemini import GeminiService, get_gemini_service
from app.services.visitor_limiter import VisitorSessionTracker, get_visitor_tracker

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a temporary chat message on the landing page (rate-limited preview for visitors)",
)
async def chat_endpoint(
    request: ChatRequest,
    response: Response,
    raw_request: Request,
    x_visitor_session_id: str | None = Header(default=None, alias="X-Visitor-Session-Id"),
    settings: Settings = Depends(get_settings),
    visitor_tracker: VisitorSessionTracker = Depends(get_visitor_tracker),
    gemini_service: GeminiService = Depends(get_gemini_service),
) -> ChatResponse:
    # 1. Enforce No PDF Attachments for visitors
    if re.search(r"\[Referencing (?:uploaded PDF|document):", request.message, re.IGNORECASE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PDF attachments are exclusively available to authenticated students. Please log in to analyze documents.",
        )

    # 2. Derive visitor session identifier
    client_ip = raw_request.client.host if raw_request.client else "unknown_client"
    session_id = x_visitor_session_id.strip() if x_visitor_session_id else f"ip_{client_ip}"

    # 3. Check visitor rate limit
    is_allowed, current_count, remaining = visitor_tracker.check_limit(session_id)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Visitor preview limit reached ({settings.visitor_chat_limit} messages). Please log in with your student credentials to continue unlimited academic chats.",
            headers={
                "X-Visitor-Remaining": "0",
                "X-Visitor-Limit": str(settings.visitor_chat_limit),
            },
        )

    # 4. Generate AI response (never stored in PostgreSQL)
    try:
        gemini_res = await gemini_service.generate_response(request)
        new_count = visitor_tracker.increment(session_id)
        new_remaining = max(0, settings.visitor_chat_limit - new_count)

        response.headers["X-Visitor-Remaining"] = str(new_remaining)
        response.headers["X-Visitor-Limit"] = str(settings.visitor_chat_limit)

        return ChatResponse(
            reply=gemini_res.reply,
            model=gemini_res.model,
            timestamp=gemini_res.timestamp,
            status="success",
            remaining_messages=new_remaining,
            visitor_limit=settings.visitor_chat_limit,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(val_err),
        ) from val_err
    except RuntimeError as r_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(r_err),
        ) from r_err


@router.post(
    "/stream",
    summary="Stream chat response from CampusPilot AI",
)
async def chat_stream_endpoint(
    request: ChatRequest,
    gemini_service: GeminiService = Depends(get_gemini_service),
) -> StreamingResponse:
    if not gemini_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured.",
        )

    async def event_generator():
        try:
            async for chunk in gemini_service.stream_response(request):
                payload = json.dumps({"chunk": chunk, "done": False})
                yield f"data: {payload}\n\n"
            yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
        except Exception as exc:
            err_payload = json.dumps({"error": str(exc), "done": True})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check status of Chat service and API configuration",
)
async def chat_health(
    settings: Settings = Depends(get_settings),
    gemini_service: GeminiService = Depends(get_gemini_service),
) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        gemini_configured=gemini_service.is_configured(),
    )
