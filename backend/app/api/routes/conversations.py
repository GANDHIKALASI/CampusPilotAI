"""Persistent conversation and chat history API routes for CampusPilot AI.

Enforces authenticated student ownership on all conversation and message queries.
Derives user identity securely from Supabase access tokens.
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import get_settings
from app.schemas.chat import ChatMessage, ChatRequest, Role
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationMessageResponse,
    ConversationRename,
    ConversationSummary,
    MessageCreate,
    MessageItem,
)
from app.services.gemini import GeminiService, get_gemini_service
from app.services.idempotency import AcquireOutcome, IdempotencyService, get_idempotency_service
from app.services.rag import RAGRetrievalError, RAGService, get_rag_service
from app.services.supabase import SupabaseService, get_supabase_service
from app.services.title_service import TitleService, get_title_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "",
    response_model=ConversationSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new persistent conversation for the authenticated student",
)
async def create_conversation(
    payload: ConversationCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> ConversationSummary:
    conv = await supabase_service.create_conversation(
        user_id=user.user_id,
        title=payload.title or "New Academic Conversation",
    )
    return ConversationSummary(**conv)


@router.get(
    "",
    response_model=List[ConversationSummary],
    summary="List all conversations owned by the authenticated student",
)
async def list_conversations(
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> List[ConversationSummary]:
    convs = await supabase_service.list_conversations(user_id=user.user_id)
    return [ConversationSummary(**c) for c in convs]


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    summary="Retrieve a conversation and its chronological message history",
)
async def get_conversation(
    conversation_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> ConversationDetail:
    conv = await supabase_service.get_conversation(user_id=user.user_id, conversation_id=conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )
    return ConversationDetail(**conv)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationSummary,
    summary="Rename a conversation owned by the authenticated student",
)
async def rename_conversation(
    conversation_id: str,
    payload: ConversationRename,
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> ConversationSummary:
    updated = await supabase_service.rename_conversation(
        user_id=user.user_id,
        conversation_id=conversation_id,
        title=payload.title,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )
    return ConversationSummary(**updated)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation and all its associated messages",
)
async def delete_conversation(
    conversation_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> None:
    deleted = await supabase_service.delete_conversation(
        user_id=user.user_id,
        conversation_id=conversation_id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )


@router.post(
    "/{conversation_id}/messages",
    response_model=ConversationMessageResponse,
    summary="Send a message in an existing conversation, persist it, and generate AI response",
)
async def send_conversation_message(
    conversation_id: str,
    payload: MessageCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    gemini_service: GeminiService = Depends(get_gemini_service),
    rag_service: RAGService = Depends(get_rag_service),
    title_service: TitleService = Depends(get_title_service),
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
) -> ConversationMessageResponse:
    from fastapi.params import Depends as DependsType, Header as HeaderType
    if isinstance(idempotency_key, HeaderType):
        idempotency_key = None
    if isinstance(idempotency_service, DependsType) or idempotency_service is None:
        idempotency_service = get_idempotency_service()
    if isinstance(title_service, DependsType) or title_service is None:
        title_service = get_title_service()

    # Step 1: Verify conversation ownership
    conv = await supabase_service.get_conversation(user_id=user.user_id, conversation_id=conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )

    # Step 1b: Verify student plan and free AI credit balance
    sub = await supabase_service.get_user_subscription(user.user_id)
    is_paid = sub.get("is_paid", False)
    credits_balance = 0

    if not is_paid:
        credits_balance = await supabase_service.get_user_credits(user.user_id)
        if credits_balance <= 0:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Free trial credits exhausted (0 credits remaining). Please upgrade to a monthly or yearly plan to continue using CampusPilot AI.",
            )

    # Step 1c: Request-level Idempotency Check (Persistent across workers/restarts)
    owner_token: Optional[str] = None
    if idempotency_key:
        outcome, cached_resp, owner_token = await idempotency_service.acquire_key(
            user_id=user.user_id,
            conversation_id=conversation_id,
            idempotency_key=idempotency_key,
            content=payload.content,
        )
        if outcome == AcquireOutcome.CONFLICT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency-Key was already used with a different request payload.",
            )
        if outcome == AcquireOutcome.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A request with this Idempotency-Key is currently being processed. Please wait.",
            )
        if outcome == AcquireOutcome.COMPLETED and cached_resp:
            logger.info("Idempotent hit for key %s in conv %s; returning cached response.", idempotency_key, conversation_id)
            return ConversationMessageResponse(**cached_resp)
    else:
        # Fallback check for rapid duplicate/retry request in conversation history if header was omitted
        existing_msgs = conv.get("messages", [])
        if len(existing_msgs) >= 2:
            last_user = existing_msgs[-2] if existing_msgs[-2].get("role") == "user" else None
            last_asst = existing_msgs[-1] if existing_msgs[-1].get("role") == "model" else None
            if last_user and last_asst and last_user.get("content", "").strip() == payload.content.strip():
                try:
                    asst_time_str = last_asst.get("created_at", "").replace("Z", "+00:00")
                    msg_time = datetime.fromisoformat(asst_time_str)
                    if (datetime.now(timezone.utc) - msg_time).total_seconds() < 15:
                        logger.info("Duplicate/retry detected for conv %s; returning cached turn without re-charging.", conversation_id)
                        u_dict = dict(last_user)
                        u_dict.setdefault("conversation_id", conversation_id)
                        a_dict = dict(last_asst)
                        a_dict.setdefault("conversation_id", conversation_id)
                        return ConversationMessageResponse(
                            user_message=MessageItem(**u_dict),
                            assistant_message=MessageItem(**a_dict),
                            conversation_id=conversation_id,
                            remaining_credits=credits_balance if not is_paid else None,
                            is_paid=is_paid,
                            citations=[],
                        )
                except Exception as t_err:
                    logger.debug("Retry timestamp parse error: %s", t_err)

    # Wrap request execution in heartbeat_scope to periodically renew lease every ~15s
    # and guarantee cleanup on every exit path (success, failure, cancellation)
    hb_interval = getattr(get_settings(), "idempotency_heartbeat_interval_seconds", 15.0)
    async with idempotency_service.heartbeat_scope(
        user_id=user.user_id,
        conversation_id=conversation_id,
        idempotency_key=idempotency_key,
        owner_token=owner_token,
        interval_seconds=hb_interval,
    ) as heartbeat:
        # Step 2: Resolve document reference and derive clean search query
        target_doc = None
        ref_match = re.search(r"\[Referencing (?:uploaded PDF|document):\s*([^\]]+)\]", payload.content, re.IGNORECASE)
        if ref_match:
            ref_filename = ref_match.group(1).strip()
            target_doc = await supabase_service.find_document_by_name(user.user_id, ref_filename)

        if not target_doc:
            conv_docs = await supabase_service.get_conversation_documents(conversation_id)
            if conv_docs:
                target_doc = conv_docs[0]

        clean_student_query = payload.content
        if ref_match:
            clean_student_query = payload.content.replace(ref_match.group(0), "").strip()

        if not clean_student_query or len(clean_student_query) < 2:
            clean_student_query = (
                f"Key concepts, modules, and exam summary for {target_doc['filename']}"
                if target_doc
                else payload.content
            )

        # Step 3: Retrieve context via RAGService (enforces student isolation & scope)
        doc_id_filter = target_doc["id"] if target_doc else None
        try:
            rag_context = await rag_service.retrieve_context(
                user_id=user.user_id,
                query=clean_student_query,
                document_id=doc_id_filter,
                raise_on_error=True,
            )
        except PermissionError as perm_err:
            if idempotency_key:
                await idempotency_service.fail_key(
                    user.user_id, conversation_id, idempotency_key, str(perm_err), owner_token=owner_token
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {perm_err}",
            )
        except RAGRetrievalError as rag_err:
            logger.error("RAG retrieval failed in conversation %s: %s", conversation_id, rag_err)
            if idempotency_key:
                await idempotency_service.fail_key(
                    user.user_id, conversation_id, idempotency_key, str(rag_err), owner_token=owner_token
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document retrieval service is temporarily unavailable. Please try again.",
            )

        # Step 4: Build conversation history and prepare Gemini request
        historical_messages: List[ChatMessage] = []
        for m in conv.get("messages", []):
            role_enum = Role.USER if m["role"] == "user" else Role.MODEL
            historical_messages.append(ChatMessage(role=role_enum, content=m["content"]))

        chat_req = rag_service.prepare_chat_request(
            raw_query=clean_student_query,
            history=historical_messages,
            rag_context=rag_context,
        )

        # Step 5: Invoke Gemini AI model
        try:
            gemini_res = await gemini_service.generate_response(chat_req)
            if hasattr(gemini_res, "reply"):
                assistant_reply = gemini_res.reply
            elif isinstance(gemini_res, str):
                assistant_reply = gemini_res
            else:
                assistant_reply = getattr(gemini_res, "reply", str(gemini_res))
        except Exception as exc:
            logger.error("Gemini response error in conversation %s: %s", conversation_id, exc)
            if idempotency_key:
                await idempotency_service.fail_key(
                    user.user_id, conversation_id, idempotency_key, str(exc), owner_token=owner_token
                )
            # CRITICAL CREDIT SAFETY: 0 credits deducted on failure, 0 messages saved!
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI service temporarily unavailable. No credits were deducted: {str(exc)}",
            )

        # Step 6: Extract authentic citations using backend source metadata
        valid_citations = rag_service.extract_citations(
            reply_text=assistant_reply,
            source_lookup=rag_context.source_lookup,
        )
        formatted_citations = rag_service.format_citation_metadata(valid_citations)

        # Step 6b: Pre-persistence Lease Ownership Check
        # If the heartbeat failed or another worker recovered the key, abort immediately!
        if heartbeat.lease_lost:
            logger.error(
                "Worker lost lease ownership during query execution for key %s (heartbeat failed). Aborting persistence to prevent double-charging.",
                idempotency_key,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request processing exceeded lease duration and was overtaken by another worker. Please retry.",
            )

        # Step 7: Pre-generate message IDs and prepare response data for atomic single-transaction completion
        u_msg_id = str(uuid.uuid4())
        a_msg_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        response_preview = {
            "user_message": {
                "id": u_msg_id,
                "conversation_id": conversation_id,
                "role": "user",
                "content": payload.content,
                "created_at": now_iso,
            },
            "assistant_message": {
                "id": a_msg_id,
                "conversation_id": conversation_id,
                "role": "model",
                "content": assistant_reply,
                "created_at": now_iso,
            },
            "conversation_id": conversation_id,
            "remaining_credits": None,
            "is_paid": is_paid,
            "citations": formatted_citations,
        }

        # Step 8: Atomically coordinate credit deduction, message persistence, and idempotency completion
        # Guarantees:
        # 1) If Gemini fails, messages are never saved and credits are never deducted.
        # 2) If credit deduction fails (e.g. concurrent overspend), messages are rolled back and HTTP 402 is raised.
        # 3) Both user message and model response are committed together in a single ACID transaction.
        try:
            turn_result = await supabase_service.save_conversation_turn_atomic(
                user_id=user.user_id,
                conversation_id=conversation_id,
                user_content=payload.content,
                assistant_content=assistant_reply,
                is_paid=is_paid,
                idempotency_key=idempotency_key,
                owner_token=owner_token,
                response_data=response_preview,
                user_message_id=u_msg_id,
                assistant_message_id=a_msg_id,
            )
        except ValueError as val_err:
            logger.warning("Atomic credit deduction rejected: %s", val_err)
            if idempotency_key:
                await idempotency_service.fail_key(
                    user.user_id, conversation_id, idempotency_key, str(val_err), owner_token=owner_token
                )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Free trial credits exhausted (0 credits remaining). Please upgrade to a monthly or yearly plan to continue using CampusPilot AI.",
            )
        except RuntimeError as r_err:
            err_str = str(r_err).lower()
            if "fencing violation" in err_str:
                logger.error("Fencing violation detected during atomic turn completion for key %s", idempotency_key)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Fencing violation: Idempotency lease expired or was overtaken by another worker.",
                )
            logger.error("Failed to persist conversation turn: %s", r_err)
            if idempotency_key:
                await idempotency_service.fail_key(
                    user.user_id, conversation_id, idempotency_key, str(r_err), owner_token=owner_token
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist conversation response safely. No credits were lost.",
            )
        except Exception as pers_err:
            logger.error("Failed to persist conversation turn: %s", pers_err)
            if idempotency_key:
                await idempotency_service.fail_key(
                    user.user_id, conversation_id, idempotency_key, str(pers_err), owner_token=owner_token
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist conversation response safely. No credits were lost.",
            )

        # Step 9: Build the final response object and sync final remaining_credits to cache
        response = ConversationMessageResponse(
            user_message=MessageItem(**turn_result["user_message"]),
            assistant_message=MessageItem(**turn_result["assistant_message"]),
            conversation_id=conversation_id,
            remaining_credits=turn_result.get("remaining_credits"),
            is_paid=is_paid,
            citations=formatted_citations,
        )

        if idempotency_key:
            await idempotency_service.complete_key(
                user_id=user.user_id,
                conversation_id=conversation_id,
                idempotency_key=idempotency_key,
                response_data=response.model_dump(),
                owner_token=owner_token,
            )

        # Step 10: Link document to conversation if relevant chunks or target doc were used
        if target_doc:
            await supabase_service.link_conversation_document(conversation_id, target_doc["id"])
        elif rag_context.citations:
            top_doc_id = rag_context.citations[0].document_id
            await supabase_service.link_conversation_document(conversation_id, top_doc_id)

        # Step 11: Auto-title conversation if default title on first turn
        if conv.get("title") in ["New Academic Conversation", "New Conversation"] and len(conv.get("messages", [])) == 0:
            if target_doc:
                title_text = f"Study: {target_doc['filename'].replace('.pdf', '')[:30]}"
            elif rag_context.citations:
                title_text = f"Study: {rag_context.citations[0].filename.replace('.pdf', '')[:30]}"
            else:
                title_text = await title_service.generate_title(payload.content)
            await supabase_service.rename_conversation(user.user_id, conversation_id, title_text)

        return response
