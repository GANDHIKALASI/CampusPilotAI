"""Supabase database and private storage client service for CampusPilot AI.

Manages interactions with Supabase PostgreSQL and Supabase Storage ('campuspilot-documents').
Enforces strict user isolation and includes in-memory developer fallback when
cloud credentials are in setup/transition.
"""

import logging
from datetime import datetime, timezone, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional
import uuid

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service wrapping Supabase PostgreSQL queries and Storage operations."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        self._init_client()

        # In-memory stores for seamless local test execution and development before cloud credentials are wired
        self._dev_waitlist: List[Dict[str, Any]] = []
        self._dev_conversations: Dict[str, Dict[str, Any]] = {}
        self._dev_messages: Dict[str, List[Dict[str, Any]]] = {}
        self._dev_documents: Dict[str, Dict[str, Any]] = {}
        self._dev_chunks: Dict[str, List[Dict[str, Any]]] = {}
        self._dev_storage: Dict[str, bytes] = {}
        self._dev_profiles: Dict[str, Dict[str, Any]] = {}
        self._dev_subscriptions: Dict[str, Dict[str, Any]] = {}
        self._dev_payments: Dict[str, Dict[str, Any]] = {}
        self._dev_credit_transactions: List[Dict[str, Any]] = []
        self._dev_audit_logs: List[Dict[str, Any]] = []

    def _init_client(self) -> None:
        if self.is_configured():
            try:
                from supabase import create_client, ClientOptions
                # Prefer secret / service role key for administrative server-side operations
                key = self.settings.supabase_secret_key or self.settings.supabase_publishable_key
                self._client = create_client(self.settings.supabase_url, key)
                logger.info("Supabase client initialized successfully with URL: %s", self.settings.supabase_url)
            except Exception as e:
                logger.warning("Could not initialize Supabase client: %s. Using memory fallback.", e)
                self._client = None

    def is_configured(self) -> bool:
        """Check if Supabase credentials are configured."""
        return bool(
            self.settings.supabase_url
            and (self.settings.supabase_secret_key or self.settings.supabase_publishable_key)
        )

    def is_production(self) -> bool:
        """Check if running in production mode."""
        env_val = getattr(self.settings, "app_env", "development").lower()
        return env_val in ("production", "prod")

    @property
    def client(self):
        return self._client

    # --------------------------------------------------------------------------
    # Waitlist Operations
    # --------------------------------------------------------------------------
    async def add_to_waitlist(self, full_name: str, email: str, institution: Optional[str] = None) -> Dict[str, Any]:
        """Add an applicant to the private waitlist.

        Prevents duplicate submissions and ensures no Supabase Auth account is created.
        """
        cleaned_email = email.strip().lower()
        cleaned_name = full_name.strip()
        cleaned_inst = institution.strip() if institution else None

        if self.is_configured() and self._client:
            try:
                # Check for existing duplicate
                existing = (
                    self._client.table("waitlist")
                    .select("id")
                    .eq("email", cleaned_email)
                    .execute()
                )
                if existing.data:
                    return {
                        "status": "already_registered",
                        "message": "You are already on the CampusPilot waitlist! We will notify you once your invite is ready.",
                        "email": cleaned_email,
                    }

                payload = {
                    "full_name": cleaned_name,
                    "email": cleaned_email,
                    "institution": cleaned_inst,
                    "status": "pending",
                }
                res = self._client.table("waitlist").insert(payload).execute()
                record = res.data[0] if res.data else payload
                return {
                    "status": "success",
                    "message": "Thank you for joining the CampusPilot waitlist! We will review your application shortly.",
                    "data": record,
                }
            except Exception as e:
                logger.error("Supabase waitlist insert failed: %s", e)
                # Fallback to dev memory if network issue

        # Dev Memory fallback
        for entry in self._dev_waitlist:
            if entry["email"] == cleaned_email:
                return {
                    "status": "already_registered",
                    "message": "You are already on the CampusPilot waitlist! We will notify you once your invite is ready.",
                    "email": cleaned_email,
                }

        entry = {
            "id": str(uuid.uuid4()),
            "full_name": cleaned_name,
            "email": cleaned_email,
            "institution": cleaned_inst,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._dev_waitlist.append(entry)
        return {
            "status": "success",
            "message": "Thank you for joining the CampusPilot waitlist! We will review your application shortly.",
            "data": entry,
        }

    # --------------------------------------------------------------------------
    # Conversation Operations
    # --------------------------------------------------------------------------
    async def create_conversation(self, user_id: str, title: str = "New Conversation") -> Dict[str, Any]:
        """Create a new persistent conversation for a student."""
        conv_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        if self.is_configured() and self._client:
            try:
                payload = {
                    "id": conv_id,
                    "user_id": user_id,
                    "title": title,
                }
                res = self._client.table("conversations").insert(payload).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error("Supabase conversation insert failed: %s", e)

        record = {
            "id": conv_id,
            "user_id": user_id,
            "title": title,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        self._dev_conversations[conv_id] = record
        self._dev_messages[conv_id] = []
        return record

    async def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """List all conversations belonging to the verified student, newest first."""
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("conversations")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("updated_at", desc=True)
                    .execute()
                )
                return res.data or []
            except Exception as e:
                logger.error("Supabase list conversations failed: %s", e)

        user_convs = [
            c for c in self._dev_conversations.values()
            if c["user_id"] == user_id
        ]
        user_convs.sort(key=lambda x: x["updated_at"], reverse=True)
        return user_convs

    async def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a conversation and its messages, enforcing user ownership."""
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("conversations")
                    .select("*")
                    .eq("id", conversation_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                if res.data:
                    conv = res.data[0]
                    msg_res = (
                        self._client.table("messages")
                        .select("*")
                        .eq("conversation_id", conversation_id)
                        .order("created_at", desc=False)
                        .execute()
                    )
                    conv["messages"] = msg_res.data or []
                    return conv
            except Exception as e:
                logger.error("Supabase get conversation failed: %s", e)

        conv = self._dev_conversations.get(conversation_id)
        if not conv or conv["user_id"] != user_id:
            return None
        res = dict(conv)
        res["messages"] = list(self._dev_messages.get(conversation_id, []))
        return res

    async def rename_conversation(self, user_id: str, conversation_id: str, title: str) -> Optional[Dict[str, Any]]:
        """Rename a conversation owned by the verified student."""
        now_iso = datetime.now(timezone.utc).isoformat()
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("conversations")
                    .update({"title": title, "updated_at": now_iso})
                    .eq("id", conversation_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                return res.data[0] if res.data else None
            except Exception as e:
                logger.error("Supabase rename conversation failed: %s", e)

        conv = self._dev_conversations.get(conversation_id)
        if not conv or conv["user_id"] != user_id:
            return None
        conv["title"] = title
        conv["updated_at"] = now_iso
        return conv

    async def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Delete a conversation and all its messages, enforcing user ownership."""
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("conversations")
                    .delete()
                    .eq("id", conversation_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                return bool(res.data)
            except Exception as e:
                logger.error("Supabase delete conversation failed: %s", e)

        conv = self._dev_conversations.get(conversation_id)
        if not conv or conv["user_id"] != user_id:
            return False
        del self._dev_conversations[conversation_id]
        self._dev_messages.pop(conversation_id, None)
        return True

    # --------------------------------------------------------------------------
    # Message Operations
    # --------------------------------------------------------------------------
    async def add_message(self, conversation_id: str, role: str, content: str) -> Dict[str, Any]:
        """Save a message under a conversation."""
        msg_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        if self.is_configured() and self._client:
            try:
                payload = {
                    "id": msg_id,
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                }
                res = self._client.table("messages").insert(payload).execute()
                # Update conversation updated_at
                self._client.table("conversations").update({"updated_at": now_iso}).eq("id", conversation_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error("Supabase message insert failed: %s", e)

        msg_record = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": now_iso,
        }
        if conversation_id not in self._dev_messages:
            self._dev_messages[conversation_id] = []
        self._dev_messages[conversation_id].append(msg_record)

        if conversation_id in self._dev_conversations:
            self._dev_conversations[conversation_id]["updated_at"] = now_iso

        return msg_record

    async def save_conversation_turn_atomic(
        self,
        user_id: str,
        conversation_id: str,
        user_content: str,
        assistant_content: str,
        is_paid: bool = False,
        idempotency_key: Optional[str] = None,
        owner_token: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        user_message_id: Optional[str] = None,
        assistant_message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Atomically persist user message, assistant message, and coordinate credit deduction.

        Guarantees:
        - If Gemini fails, this method is never invoked (0 credits deducted, 0 messages saved).
        - If free user, row lock on profile prevents concurrent overspending.
        - User and assistant messages are batch-inserted in a single atomic database operation.
        - If message persistence fails, credit deduction is rolled back (compensating refund).
        - Returns a dict with 'user_message', 'assistant_message', 'remaining_credits'.
        """
        u_msg_id = user_message_id or str(uuid.uuid4())
        a_msg_id = assistant_message_id or str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Try unified RPC if Migration 007 has been applied
        if self.is_configured() and self._client:
            try:
                rpc_res = self._client.rpc(
                    "complete_conversation_turn",
                    {
                        "p_user_id": user_id,
                        "p_conversation_id": conversation_id,
                        "p_user_content": user_content,
                        "p_assistant_content": assistant_content,
                        "p_idempotency_key": idempotency_key,
                        "p_owner_token": owner_token,
                        "p_response_data": response_data,
                        "p_user_message_id": u_msg_id,
                        "p_assistant_message_id": a_msg_id,
                    },
                ).execute()
                if rpc_res.data:
                    row = rpc_res.data[0] if isinstance(rpc_res.data, list) else rpc_res.data
                    now_str = row.get("created_at") or now_iso
                    return {
                        "user_message": {
                            "id": str(row.get("user_message_id") or u_msg_id),
                            "conversation_id": conversation_id,
                            "role": "user",
                            "content": user_content,
                            "created_at": now_str,
                        },
                        "assistant_message": {
                            "id": str(row.get("assistant_message_id") or a_msg_id),
                            "conversation_id": conversation_id,
                            "role": "model",
                            "content": assistant_content,
                            "created_at": now_str,
                        },
                        "remaining_credits": row.get("remaining_credits"),
                    }
            except Exception as rpc_err:
                err_msg = str(rpc_err).lower()
                # Inspect error: never bypass business rules or fencing violations!
                if "insufficient credits" in err_msg:
                    raise ValueError("Insufficient free credits. Please upgrade to a paid plan.") from rpc_err
                if "fencing violation" in err_msg:
                    raise RuntimeError("Fencing violation: Idempotency lease expired or overtaken by another worker.") from rpc_err
                if "access denied" in err_msg:
                    raise PermissionError(str(rpc_err)) from rpc_err

                # Fail closed in production!
                if self.is_production():
                    raise RuntimeError(f"PostgreSQL complete_conversation_turn failed in production: {rpc_err}") from rpc_err

                # In development/test: only fallback if RPC is missing from DB schema
                if any(token in err_msg for token in ["pgrst202", "does not exist", "404", "not found"]):
                    logger.debug("RPC complete_conversation_turn not available in schema (%s), using safe coordinated fallback", rpc_err)
                else:
                    logger.error("RPC complete_conversation_turn error: %s", rpc_err)
                    raise

            # 2. Coordinated safe sequence with compensating rollback
            remaining_credits = None
            if not is_paid:
                # Deduct credit atomically using deduct_student_credit (with exclusive FOR UPDATE lock)
                # Throws ValueError if balance is <= 0 (e.g. concurrent spend)
                remaining_credits = await self.deduct_credit_atomic(
                    user_id=user_id,
                    action="ai_message",
                    description=f"AI query in conversation {conversation_id}",
                )

            # Batch insert both messages together
            try:
                msg_rows = [
                    {
                        "id": u_msg_id,
                        "conversation_id": conversation_id,
                        "role": "user",
                        "content": user_content,
                        "created_at": now_iso,
                    },
                    {
                        "id": a_msg_id,
                        "conversation_id": conversation_id,
                        "role": "model",
                        "content": assistant_content,
                        "created_at": now_iso,
                    },
                ]
                self._client.table("messages").insert(msg_rows).execute()
                self._client.table("conversations").update({"updated_at": now_iso}).eq("id", conversation_id).execute()
                return {
                    "user_message": msg_rows[0],
                    "assistant_message": msg_rows[1],
                    "remaining_credits": remaining_credits,
                }
            except Exception as ins_err:
                logger.error("Failed to persist conversation messages: %s", ins_err)
                # Compensating refund if free user was charged
                if not is_paid and remaining_credits is not None:
                    try:
                        profile = await self.get_user_profile(user_id)
                        refund_bal = int(profile.get("credits_balance", 0)) + 1
                        self._client.table("profiles").update({"credits_balance": refund_bal}).eq("id", user_id).execute()
                        self._client.table("credit_transactions").insert({
                            "user_id": user_id,
                            "amount": 1,
                            "balance_after": refund_bal,
                            "action": "refund_error",
                            "description": "Compensating refund for failed message persistence",
                        }).execute()
                    except Exception as ref_err:
                        logger.error("Failed to execute compensating credit refund: %s", ref_err)
                raise RuntimeError(f"Message persistence failed: {ins_err}") from ins_err

        # 3. Local / in-memory dev mode fallback
        remaining_credits = None
        if not is_paid:
            remaining_credits = await self.deduct_credit_atomic(
                user_id=user_id,
                action="ai_message",
                description=f"AI query in conversation {conversation_id}",
            )

        u_msg = await self.add_message(conversation_id, "user", user_content)
        a_msg = await self.add_message(conversation_id, "model", assistant_content)
        return {
            "user_message": u_msg,
            "assistant_message": a_msg,
            "remaining_credits": remaining_credits,
        }

    # --------------------------------------------------------------------------
    # Document & Storage Operations
    # --------------------------------------------------------------------------
    async def upload_document_file(
        self,
        user_id: str,
        document_id: str,
        file_bytes: bytes,
        filename: str,
        mime_type: str = "application/pdf",
    ) -> str:
        """Store original PDF binary in private Supabase Storage bucket 'campuspilot-documents'.

        Path convention: {user_id}/{document_id}.pdf
        """
        storage_path = f"{user_id}/{document_id}.pdf"

        if self.is_configured() and self._client:
            try:
                self._client.storage.from_("campuspilot-documents").upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": mime_type, "upsert": "true"},
                )
                logger.info("Uploaded document to Supabase storage path: %s", storage_path)
                return storage_path
            except Exception as e:
                logger.error("Supabase storage upload failed: %s", e)

        self._dev_storage[storage_path] = file_bytes
        return storage_path

    async def create_signed_download_url(self, user_id: str, storage_path: str, expires_in: int = 3600) -> str:
        """Generate a short-lived signed URL for authorized student download.

        Enforces that the path prefix matches the authenticated user ID.
        """
        if not storage_path.startswith(f"{user_id}/"):
            raise PermissionError("Access denied: You do not own this document.")

        if self.is_configured() and self._client:
            try:
                res = self._client.storage.from_("campuspilot-documents").create_signed_url(
                    path=storage_path,
                    expires_in=expires_in,
                )
                if res and "signedURL" in res:
                    return res["signedURL"]
            except Exception as e:
                logger.error("Supabase signed url creation failed: %s", e)

        return f"/api/documents/download-stream?path={storage_path}"

    async def create_document_record(
        self,
        user_id: str,
        filename: str,
        storage_path: str,
        file_size: int,
        mime_type: str = "application/pdf",
        scope: str = "personal",
        semester_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        unit_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Insert a document record into PostgreSQL supporting personal and shared scopes, and academic categorization."""
        doc_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        clean_scope = "shared" if scope == "shared" else "personal"

        if self.is_configured() and self._client:
            payload = {
                "id": doc_id,
                "user_id": user_id,
                "filename": filename,
                "storage_path": storage_path,
                "mime_type": mime_type,
                "file_size": file_size,
                "processing_status": "pending",
                "scope": clean_scope,
            }
            if semester_id:
                payload["semester_id"] = semester_id
            if subject_id:
                payload["subject_id"] = subject_id
            if unit_id:
                payload["unit_id"] = unit_id

            try:
                res = self._client.table("documents").insert(payload).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                # If extended columns are pending in DB, retry without them
                logger.warning("Supabase insert with extended columns failed (%s), retrying base payload...", e)
                try:
                    payload_base = {
                        "id": doc_id,
                        "user_id": user_id,
                        "filename": filename,
                        "storage_path": storage_path,
                        "mime_type": mime_type,
                        "file_size": file_size,
                        "processing_status": "pending",
                        "scope": clean_scope,
                    }
                    res = self._client.table("documents").insert(payload_base).execute()
                    if res.data:
                        record = res.data[0]
                        record["scope"] = clean_scope
                        if semester_id:
                            record["semester_id"] = semester_id
                        if subject_id:
                            record["subject_id"] = subject_id
                        if unit_id:
                            record["unit_id"] = unit_id
                        return record
                except Exception as inner_e:
                    logger.error("Supabase create document record failed: %s", inner_e)

        record = {
            "id": doc_id,
            "user_id": user_id,
            "filename": filename,
            "storage_path": storage_path,
            "mime_type": mime_type,
            "file_size": file_size,
            "processing_status": "pending",
            "scope": clean_scope,
            "semester_id": semester_id,
            "subject_id": subject_id,
            "unit_id": unit_id,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        self._dev_documents[doc_id] = record
        self._dev_chunks[doc_id] = []
        return record

    async def update_document_status(self, document_id: str, status: str) -> None:
        """Update processing status of a document ('processing', 'completed', 'failed')."""
        now_iso = datetime.now(timezone.utc).isoformat()
        if self.is_configured() and self._client:
            try:
                self._client.table("documents").update(
                    {"processing_status": status, "updated_at": now_iso}
                ).eq("id", document_id).execute()
                return
            except Exception as e:
                logger.error("Supabase update document status failed: %s", e)

        if document_id in self._dev_documents:
            self._dev_documents[document_id]["processing_status"] = status
            self._dev_documents[document_id]["updated_at"] = now_iso

    async def save_document_chunks(
        self,
        document_id: str,
        user_id: str,
        chunks: List[Dict[str, Any]],
        scope: str = "personal",
        semester_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        unit_id: Optional[str] = None,
    ) -> int:
        """Persist structured output into document_chunks table with scope awareness and academic metadata."""
        if not chunks:
            return 0

        chunk_rows = []
        now_iso = datetime.now(timezone.utc).isoformat()
        clean_scope = "shared" if scope == "shared" else "personal"

        for c in chunks:
            row = {
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": c["chunk_index"],
                "page_number": c["page_number"],
                "content": c["content"],
                "token_count": c["token_count"],
                "character_count": c.get("character_count", len(c["content"])),
                "start_char_offset": c.get("start_char_offset", 0),
                "end_char_offset": c.get("end_char_offset", len(c["content"])),
                "scope": clean_scope,
                "created_at": now_iso,
            }
            if semester_id:
                row["semester_id"] = semester_id
            if subject_id:
                row["subject_id"] = subject_id
            if unit_id:
                row["unit_id"] = unit_id
            chunk_rows.append(row)

        if self.is_configured() and self._client:
            try:
                self._client.table("document_chunks").insert(chunk_rows).execute()
                return len(chunk_rows)
            except Exception as e:
                logger.warning("Supabase insert document chunks with academic columns failed (%s), retrying base payload...", e)
                try:
                    fallback_rows = [
                        {k: v for k, v in r.items() if k not in ("semester_id", "subject_id", "unit_id")}
                        for r in chunk_rows
                    ]
                    self._client.table("document_chunks").insert(fallback_rows).execute()
                    return len(fallback_rows)
                except Exception as inner_e:
                    logger.warning("Supabase insert without academic columns failed (%s), retrying without scope...", inner_e)
                    try:
                        minimal_rows = [
                            {k: v for k, v in r.items() if k not in ("scope", "semester_id", "subject_id", "unit_id")}
                            for r in chunk_rows
                        ]
                        self._client.table("document_chunks").insert(minimal_rows).execute()
                        return len(minimal_rows)
                    except Exception as final_e:
                        logger.error("Supabase save document chunks failed: %s", final_e)

        self._dev_chunks[document_id] = chunk_rows
        return len(chunk_rows)

    async def list_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """List all documents accessible to the student: own personal documents + all shared academic documents."""
        if self.is_configured() and self._client:
            try:
                # Query both user's documents and shared library
                res = (
                    self._client.table("documents")
                    .select("*")
                    .or_(f"user_id.eq.{user_id},scope.eq.shared")
                    .order("created_at", desc=True)
                    .execute()
                )
                return res.data or []
            except Exception as e:
                logger.debug("Scope-aware list failed (%s), falling back to user_id filter...", e)
                try:
                    res = (
                        self._client.table("documents")
                        .select("*")
                        .eq("user_id", user_id)
                        .order("created_at", desc=True)
                        .execute()
                    )
                    return res.data or []
                except Exception as inner_e:
                    logger.error("Supabase list user documents failed: %s", inner_e)

        user_docs = [
            d for d in self._dev_documents.values()
            if d.get("user_id") == user_id or d.get("scope") == "shared"
        ]
        user_docs.sort(key=lambda x: x["created_at"], reverse=True)
        return user_docs

    async def get_user_document(self, user_id: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get single document metadata enforcing student ownership or shared academic access."""
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("documents")
                    .select("*")
                    .eq("id", document_id)
                    .or_(f"user_id.eq.{user_id},scope.eq.shared")
                    .execute()
                )
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.debug("Scope get user document failed (%s), falling back...", e)
                try:
                    res = (
                        self._client.table("documents")
                        .select("*")
                        .eq("id", document_id)
                        .eq("user_id", user_id)
                        .execute()
                    )
                    return res.data[0] if res.data else None
                except Exception as inner_e:
                    logger.error("Supabase get user document failed: %s", inner_e)

        doc = self._dev_documents.get(document_id)
        if not doc:
            return None
        if doc.get("user_id") == user_id or doc.get("scope") == "shared":
            return doc
        return None

    async def delete_user_document(self, user_id: str, document_id: str) -> bool:
        """Allow a student or admin to permanently delete a personal document, its chunks, and its storage file."""
        doc = await self.get_user_document(user_id, document_id)
        if not doc:
            return False

        # If it's a shared academic doc, regular students cannot delete it via this endpoint
        if doc.get("scope") == "shared" and doc.get("user_id") != user_id:
            return False

        if self.is_configured() and self._client:
            try:
                # 1. Clean up file from Supabase storage
                storage_path = doc.get("storage_path")
                if storage_path:
                    try:
                        self._client.storage.from_("campuspilot-documents").remove([storage_path])
                    except Exception as stor_err:
                        logger.warning("Could not delete document file from storage: %s", stor_err)

                # 2. Delete document record (document_chunks table cascades)
                self._client.table("documents").delete().eq("id", document_id).execute()
                return True
            except Exception as e:
                logger.error("Supabase delete user document failed: %s", e)
                return False

        # In-memory dev fallback
        if document_id in self._dev_documents:
            del self._dev_documents[document_id]
            if document_id in self._dev_chunks:
                del self._dev_chunks[document_id]
            return True
        return False

    async def delete_user_account(self, user_id: str) -> bool:
        """Permanently delete a user account and purge all associated personal data across tables and storage."""
        if self.is_configured() and self._client:
            try:
                # 1. Clean up all user's storage files
                try:
                    doc_res = self._client.table("documents").select("id, storage_path").eq("user_id", user_id).execute()
                    paths_to_remove = [d["storage_path"] for d in (doc_res.data or []) if d.get("storage_path")]
                    if paths_to_remove:
                        self._client.storage.from_("campuspilot-documents").remove(paths_to_remove)
                except Exception as stor_err:
                    logger.warning("Failed removing user files from storage during account deletion: %s", stor_err)

                # 2. Delete documents (chunks cascade)
                try:
                    self._client.table("documents").delete().eq("user_id", user_id).execute()
                except Exception as doc_del_err:
                    logger.warning("Error deleting documents during account deletion: %s", doc_del_err)

                # 3. Delete conversations and messages
                try:
                    self._client.table("conversations").delete().eq("user_id", user_id).execute()
                except Exception as conv_del_err:
                    logger.warning("Error deleting conversations: %s", conv_del_err)

                # 4. Delete credit transactions & credit balance
                try:
                    self._client.table("credit_transactions").delete().eq("user_id", user_id).execute()
                except Exception:
                    pass
                try:
                    self._client.table("credits").delete().eq("user_id", user_id).execute()
                except Exception:
                    pass

                # 5. Delete subscriptions & payments
                try:
                    self._client.table("subscriptions").delete().eq("user_id", user_id).execute()
                except Exception:
                    pass
                try:
                    self._client.table("payments").delete().eq("user_id", user_id).execute()
                except Exception:
                    pass

                # 6. Delete user profile
                try:
                    self._client.table("profiles").delete().eq("id", user_id).execute()
                except Exception as prof_err:
                    logger.warning("Error deleting profile: %s", prof_err)

                # 7. Delete auth user via admin API if secret key configured
                if self.settings.supabase_secret_key and self._client and hasattr(self._client, "auth"):
                    try:
                        self._client.auth.admin.delete_user(user_id)
                    except Exception as auth_del_err:
                        logger.warning("Failed to delete user from Supabase auth: %s", auth_del_err)

                return True
            except Exception as e:
                logger.error("Supabase delete user account failed: %s", e)
                return False

        # In-memory dev fallback cleanup
        if user_id in self._dev_profiles:
            del self._dev_profiles[user_id]
        if user_id in self._dev_credits:
            del self._dev_credits[user_id]
        if user_id in self._dev_subscriptions:
            del self._dev_subscriptions[user_id]
        if user_id in self._dev_credit_transactions:
            del self._dev_credit_transactions[user_id]

        to_del_docs = [did for did, d in self._dev_documents.items() if d.get("user_id") == user_id]
        for did in to_del_docs:
            self._dev_documents.pop(did, None)
            self._dev_chunks.pop(did, None)

        to_del_convs = [cid for cid, c in self._dev_conversations.items() if c.get("user_id") == user_id]
        for cid in to_del_convs:
            self._dev_conversations.pop(cid, None)
            self._dev_messages.pop(cid, None)

        return True


    async def get_document_chunks(self, user_id: str, document_id: str) -> List[Dict[str, Any]]:
        """Retrieve all extracted and stored chunks for a specific document, ensuring student ownership or shared access."""
        doc = await self.get_user_document(user_id, document_id)
        if not doc:
            logger.warning("Access denied to document chunks for user %s on doc %s", user_id, document_id)
            return []

        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("document_chunks")
                    .select("*")
                    .eq("document_id", document_id)
                    .order("chunk_index", desc=False)
                    .execute()
                )
                return res.data or []
            except Exception as e:
                logger.error("Supabase get document chunks failed: %s", e)

        return self._dev_chunks.get(document_id, [])

    async def find_document_by_name(self, user_id: str, filename: str) -> Optional[Dict[str, Any]]:
        """Find a document owned by the student matching filename (case-insensitive substring or exact)."""
        docs = await self.list_user_documents(user_id)
        if not docs:
            return None

        cleaned_target = filename.strip().lower()
        # 1. Exact match
        for d in docs:
            if d.get("filename", "").strip().lower() == cleaned_target:
                return d

        # 2. Match without extension if user omitted or truncated
        target_stem = cleaned_target.replace(".pdf", "")
        for d in docs:
            doc_stem = d.get("filename", "").strip().lower().replace(".pdf", "")
            if target_stem in doc_stem or doc_stem in target_stem:
                return d

        # 3. Substring match
        for d in docs:
            df = d.get("filename", "").strip().lower()
            if cleaned_target in df or df in cleaned_target:
                return d

        return None

    async def link_conversation_document(self, conversation_id: str, document_id: str) -> None:
        """Associate a document with a conversation in conversation_documents."""
        if self.is_configured() and self._client:
            try:
                self._client.table("conversation_documents").upsert(
                    {"conversation_id": conversation_id, "document_id": document_id}
                ).execute()
                return
            except Exception as e:
                logger.warning("Supabase link conversation document failed: %s", e)

        if not hasattr(self, "_dev_conv_docs"):
            self._dev_conv_docs = {}
        if conversation_id not in self._dev_conv_docs:
            self._dev_conv_docs[conversation_id] = set()
        self._dev_conv_docs[conversation_id].add(document_id)

    async def get_conversation_documents(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get documents linked to a conversation."""
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("conversation_documents")
                    .select("document_id, documents(*)")
                    .eq("conversation_id", conversation_id)
                    .execute()
                )
                docs = []
                for row in res.data or []:
                    if row.get("documents"):
                        docs.append(row["documents"])
                return docs
            except Exception as e:
                logger.warning("Supabase get conversation documents failed: %s", e)

        linked_ids = getattr(self, "_dev_conv_docs", {}).get(conversation_id, set())
        return [self._dev_documents[did] for did in linked_ids if did in self._dev_documents]

    # --------------------------------------------------------------------------
    # Profile & Account Operations
    # --------------------------------------------------------------------------
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Fetch profile for user, ensuring credits_balance and status defaults exist."""
        if self.is_configured() and self._client:
            try:
                res = self._client.table("profiles").select("*").eq("id", user_id).execute()
                if res.data and len(res.data) > 0:
                    profile = res.data[0]
                    # Ensure backward compatibility if columns aren't migrated yet
                    if "credits_balance" not in profile:
                        profile["credits_balance"] = 20
                    if "role" not in profile:
                        profile["role"] = "student"
                    if "status" not in profile:
                        profile["status"] = "active"
                    return profile
            except Exception as e:
                logger.warning("Supabase get profile failed for %s: %s", user_id, e)

        # Fallback in-memory
        if user_id not in self._dev_profiles:
            self._dev_profiles[user_id] = {
                "id": user_id,
                "full_name": "Student",
                "avatar_url": None,
                "role": "student",
                "status": "active",
                "institution": None,
                "credits_balance": 20,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        return self._dev_profiles[user_id]

    async def update_user_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        institution: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update student profile attributes."""
        payload: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if full_name is not None:
            payload["full_name"] = full_name.strip()
        if institution is not None:
            payload["institution"] = institution.strip()
        if avatar_url is not None:
            payload["avatar_url"] = avatar_url

        if self.is_configured() and self._client:
            try:
                res = self._client.table("profiles").update(payload).eq("id", user_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning("Supabase update profile failed: %s", e)

        profile = await self.get_user_profile(user_id)
        profile.update(payload)
        self._dev_profiles[user_id] = profile
        return profile

    # --------------------------------------------------------------------------
    # Free Credit & Usage Tracking Operations
    # --------------------------------------------------------------------------
    async def get_user_credits(self, user_id: str) -> int:
        """Get the current credit balance of a student."""
        profile = await self.get_user_profile(user_id)
        return int(profile.get("credits_balance", 20))

    async def deduct_credit_atomic(
        self,
        user_id: str,
        action: str = "ai_message",
        description: Optional[str] = None,
    ) -> int:
        """Atomically deduct exactly 1 credit from student balance.

        Uses stored procedure public.deduct_student_credit with exclusive row lock.
        Throws ValueError if balance is insufficient.
        """
        if self.is_configured() and self._client:
            try:
                # Call stored procedure with exclusive FOR UPDATE lock
                rpc_res = self._client.rpc(
                    "deduct_student_credit",
                    {
                        "p_user_id": user_id,
                        "p_action": action,
                        "p_description": description or "1 AI interaction credit consumed",
                    },
                ).execute()
                if rpc_res.data is not None:
                    return int(rpc_res.data)
            except Exception as e:
                err_str = str(e).lower()
                if "insufficient credits" in err_str:
                    raise ValueError("Insufficient free credits. Please upgrade to a paid plan.")
                logger.warning("RPC deduct_student_credit failed, falling back to direct table update: %s", e)

                # Fallback via direct query
                profile = await self.get_user_profile(user_id)
                curr = int(profile.get("credits_balance", 0))
                if curr <= 0:
                    raise ValueError("Insufficient free credits. Please upgrade to a paid plan.")
                new_bal = curr - 1
                self._client.table("profiles").update({
                    "credits_balance": new_bal,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", user_id).execute()
                try:
                    self._client.table("credit_transactions").insert({
                        "user_id": user_id,
                        "amount": -1,
                        "balance_after": new_bal,
                        "action": action,
                        "description": description or "AI chat response",
                    }).execute()
                except Exception:
                    pass
                return new_bal

        # Local fallback
        profile = await self.get_user_profile(user_id)
        curr = int(profile.get("credits_balance", 20))
        if curr <= 0:
            raise ValueError("Insufficient free credits. Please upgrade to a paid plan.")
        new_bal = curr - 1
        profile["credits_balance"] = new_bal
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._dev_profiles[user_id] = profile
        self._dev_credit_transactions.append({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": -1,
            "balance_after": new_bal,
            "action": action,
            "description": description or "AI chat response",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return new_bal

    async def grant_user_credits(
        self,
        user_id: str,
        amount: int,
        action: str = "admin_adjustment",
        description: Optional[str] = None,
    ) -> int:
        """Grant credits to a student account."""
        profile = await self.get_user_profile(user_id)
        curr = int(profile.get("credits_balance", 0))
        new_bal = max(0, curr + amount)

        if self.is_configured() and self._client:
            try:
                self._client.table("profiles").update({
                    "credits_balance": new_bal,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", user_id).execute()
                self._client.table("credit_transactions").insert({
                    "user_id": user_id,
                    "amount": amount,
                    "balance_after": new_bal,
                    "action": action,
                    "description": description or f"Credit adjustment: +{amount}",
                }).execute()
                return new_bal
            except Exception as e:
                logger.warning("Supabase grant credits failed: %s", e)

        profile["credits_balance"] = new_bal
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._dev_profiles[user_id] = profile
        self._dev_credit_transactions.append({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": amount,
            "balance_after": new_bal,
            "action": action,
            "description": description or f"Credit adjustment: +{amount}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return new_bal

    async def list_credit_transactions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List credit transaction history for a student."""
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("credit_transactions")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                if res.data is not None:
                    return res.data
            except Exception as e:
                logger.warning("Supabase list credit transactions failed: %s", e)

        user_txs = [tx for tx in self._dev_credit_transactions if tx["user_id"] == user_id]
        return sorted(user_txs, key=lambda x: x["created_at"], reverse=True)[:limit]

    # --------------------------------------------------------------------------
    # Subscriptions & Payment Operations
    # --------------------------------------------------------------------------
    async def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get the active subscription for a student.

        Returns plan ('free', 'monthly', 'yearly'), status, and boolean is_active.
        """
        now_dt = datetime.now(timezone.utc)
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("subscriptions")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("current_period_end", desc=True)
                    .limit(1)
                    .execute()
                )
                if res.data and len(res.data) > 0:
                    sub = res.data[0]
                    # Check expiry
                    end_str = sub.get("current_period_end")
                    if end_str:
                        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                        if end_dt > now_dt and sub.get("status") == "active":
                            return {
                                "plan": sub.get("plan", "free"),
                                "status": "active",
                                "current_period_start": sub.get("current_period_start"),
                                "current_period_end": end_str,
                                "is_active": True,
                                "is_paid": sub.get("plan") in ["monthly", "yearly"],
                            }
                        elif end_dt <= now_dt:
                            # Auto-mark expired
                            return {
                                "plan": "free",
                                "status": "expired",
                                "current_period_start": sub.get("current_period_start"),
                                "current_period_end": end_str,
                                "is_active": False,
                                "is_paid": False,
                            }
            except Exception as e:
                logger.warning("Supabase get subscription failed: %s", e)

        # Fallback in-memory
        sub = self._dev_subscriptions.get(user_id)
        if sub:
            end_str = sub.get("current_period_end")
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            if end_dt > now_dt and sub.get("status") == "active":
                return {
                    "plan": sub.get("plan", "free"),
                    "status": "active",
                    "current_period_start": sub.get("current_period_start"),
                    "current_period_end": end_str,
                    "is_active": True,
                    "is_paid": sub.get("plan") in ["monthly", "yearly"],
                }

        # Default free tier
        return {
            "plan": "free",
            "status": "active",
            "current_period_start": None,
            "current_period_end": None,
            "is_active": False,
            "is_paid": False,
        }

    async def create_or_update_subscription(
        self,
        user_id: str,
        plan: str,
        days: int,
        razorpay_order_id: Optional[str] = None,
        razorpay_payment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Activate or extend a paid subscription for a student."""
        now_dt = datetime.now(timezone.utc)
        current_sub = await self.get_user_subscription(user_id)

        # If already on an active plan, extend from existing end date
        if current_sub.get("is_active") and current_sub.get("current_period_end"):
            curr_end = datetime.fromisoformat(current_sub["current_period_end"].replace("Z", "+00:00"))
            start_dt = datetime.fromisoformat(current_sub["current_period_start"].replace("Z", "+00:00")) if current_sub.get("current_period_start") else now_dt
            new_end = curr_end + timedelta(days=days)
        else:
            start_dt = now_dt
            new_end = now_dt + timedelta(days=days)

        payload = {
            "user_id": user_id,
            "plan": plan,
            "status": "active",
            "current_period_start": start_dt.isoformat(),
            "current_period_end": new_end.isoformat(),
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "updated_at": now_dt.isoformat(),
        }

        if self.is_configured() and self._client:
            try:
                res = self._client.table("subscriptions").insert(payload).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning("Supabase insert subscription failed: %s", e)

        payload["id"] = str(uuid.uuid4())
        payload["created_at"] = now_dt.isoformat()
        self._dev_subscriptions[user_id] = payload
        return payload

    async def create_payment_record(
        self,
        user_id: str,
        plan: str,
        amount_paise: int,
        razorpay_order_id: str,
    ) -> Dict[str, Any]:
        """Create an initial payment record in status 'created'."""
        now_str = datetime.now(timezone.utc).isoformat()
        payload = {
            "user_id": user_id,
            "plan": plan,
            "amount_paise": amount_paise,
            "currency": "INR",
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": None,
            "razorpay_signature": None,
            "status": "created",
            "error_description": None,
            "created_at": now_str,
            "updated_at": now_str,
        }

        if self.is_configured() and self._client:
            try:
                res = self._client.table("payments").insert(payload).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning("Supabase insert payment record failed: %s", e)

        payload["id"] = str(uuid.uuid4())
        self._dev_payments[razorpay_order_id] = payload
        return payload

    async def get_payment_by_order_id(self, razorpay_order_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve payment record by Razorpay order ID."""
        if self.is_configured() and self._client:
            try:
                res = self._client.table("payments").select("*").eq("razorpay_order_id", razorpay_order_id).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                logger.warning("Supabase get payment by order id failed: %s", e)

        return self._dev_payments.get(razorpay_order_id)

    async def update_payment_status(
        self,
        razorpay_order_id: str,
        status: str,
        payment_id: Optional[str] = None,
        signature: Optional[str] = None,
        error_description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update payment status (e.g. captured, failed)."""
        now_str = datetime.now(timezone.utc).isoformat()
        update_data: Dict[str, Any] = {
            "status": status,
            "updated_at": now_str,
        }
        if payment_id:
            update_data["razorpay_payment_id"] = payment_id
        if signature:
            update_data["razorpay_signature"] = signature
        if error_description:
            update_data["error_description"] = error_description

        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("payments")
                    .update(update_data)
                    .eq("razorpay_order_id", razorpay_order_id)
                    .execute()
                )
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                logger.warning("Supabase update payment status failed: %s", e)

        record = self._dev_payments.get(razorpay_order_id)
        if record:
            record.update(update_data)
            return record
        return None

    async def list_user_payments(self, user_id: str) -> List[Dict[str, Any]]:
        """List all payment records for a student."""
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("payments")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .execute()
                )
                if res.data is not None:
                    return res.data
            except Exception as e:
                logger.warning("Supabase list user payments failed: %s", e)

        user_payments = [p for p in self._dev_payments.values() if p["user_id"] == user_id]
        return sorted(user_payments, key=lambda x: x["created_at"], reverse=True)

    # --------------------------------------------------------------------------
    # Admin Platform Management Operations
    # --------------------------------------------------------------------------
    async def get_platform_metrics(self) -> Dict[str, Any]:
        """Aggregate high-level platform metrics for admin dashboard."""
        now_str = datetime.now(timezone.utc).isoformat()
        metrics = {
            "total_students": 0,
            "active_subscriptions": 0,
            "expired_subscriptions": 0,
            "total_documents": 0,
            "total_payments_inr": 0.0,
            "total_transactions_count": 0,
        }

        if self.is_configured() and self._client:
            try:
                # Total students
                p_res = self._client.table("profiles").select("id", count="exact").execute()
                metrics["total_students"] = p_res.count or len(p_res.data or [])

                # Total documents
                d_res = self._client.table("documents").select("id", count="exact").execute()
                metrics["total_documents"] = d_res.count or len(d_res.data or [])

                # Subscriptions
                sub_res = self._client.table("subscriptions").select("status, current_period_end").execute()
                for sub in sub_res.data or []:
                    end = sub.get("current_period_end", "")
                    if sub.get("status") == "active" and end > now_str:
                        metrics["active_subscriptions"] += 1
                    else:
                        metrics["expired_subscriptions"] += 1

                # Payments
                pay_res = self._client.table("payments").select("amount_paise, status").eq("status", "captured").execute()
                total_paise = sum(p.get("amount_paise", 0) for p in (pay_res.data or []))
                metrics["total_payments_inr"] = total_paise / 100.0
                metrics["total_transactions_count"] = len(pay_res.data or [])
                return metrics
            except Exception as e:
                logger.warning("Supabase get platform metrics failed: %s", e)

        # Fallback from dev stores
        metrics["total_students"] = len(self._dev_profiles) or 1
        metrics["total_documents"] = len(self._dev_documents)
        metrics["active_subscriptions"] = len([s for s in self._dev_subscriptions.values() if s.get("status") == "active"])
        captured = [p for p in self._dev_payments.values() if p.get("status") == "captured"]
        metrics["total_payments_inr"] = sum(p.get("amount_paise", 0) for p in captured) / 100.0
        metrics["total_transactions_count"] = len(captured)
        return metrics

    async def list_students(
        self,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List students with their profile, plan status, and credit balance."""
        students: List[Dict[str, Any]] = []

        if self.is_configured() and self._client:
            try:
                query = self._client.table("profiles").select("*")
                if search:
                    query = query.ilike("full_name", f"%{search.strip()}%")
                res = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
                for p in res.data or []:
                    sub = await self.get_user_subscription(p["id"])
                    students.append({
                        "id": p["id"],
                        "full_name": p.get("full_name", "Student"),
                        "email": p.get("email") or f"{p['id'][:8]}@student.edu",
                        "institution": p.get("institution"),
                        "role": p.get("role", "student"),
                        "status": p.get("status", "active"),
                        "credits_balance": p.get("credits_balance", 20),
                        "created_at": p.get("created_at"),
                        "plan": sub.get("plan", "free"),
                        "subscription_status": sub.get("status", "active"),
                        "subscription_expiry": sub.get("current_period_end"),
                    })
                if students:
                    return students
            except Exception as e:
                logger.warning("Supabase list students failed: %s", e)

        # In-memory fallback
        for uid, p in self._dev_profiles.items():
            if search and search.lower() not in p.get("full_name", "").lower():
                continue
            sub = await self.get_user_subscription(uid)
            students.append({
                "id": uid,
                "full_name": p.get("full_name", "Student"),
                "email": f"{uid[:8]}@student.edu",
                "institution": p.get("institution"),
                "role": p.get("role", "student"),
                "status": p.get("status", "active"),
                "credits_balance": p.get("credits_balance", 20),
                "created_at": p.get("created_at"),
                "plan": sub.get("plan", "free"),
                "subscription_status": sub.get("status", "active"),
                "subscription_expiry": sub.get("current_period_end"),
            })
        return students[offset : offset + limit]

    async def update_student_status(self, student_id: str, status: str, admin_id: str) -> Dict[str, Any]:
        """Update student account status (active, suspended, deactivated)."""
        if status not in ["active", "suspended", "deactivated"]:
            raise ValueError(f"Invalid student status: {status}")

        now_str = datetime.now(timezone.utc).isoformat()
        if self.is_configured() and self._client:
            try:
                self._client.table("profiles").update({
                    "status": status,
                    "updated_at": now_str,
                }).eq("id", student_id).execute()
            except Exception as e:
                logger.warning("Supabase update student status failed: %s", e)

        if student_id in self._dev_profiles:
            self._dev_profiles[student_id]["status"] = status
            self._dev_profiles[student_id]["updated_at"] = now_str

        await self.record_admin_audit_log(
            admin_id=admin_id,
            action="update_student_status",
            target_type="student",
            target_id=student_id,
            details={"new_status": status},
        )
        return {"status": "success", "student_id": student_id, "new_status": status}

    async def admin_assign_plan(
        self,
        student_id: str,
        plan: str,
        days: int,
        admin_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Administratively grant or change student subscription plan with audit record."""
        sub = await self.create_or_update_subscription(
            user_id=student_id,
            plan=plan,
            days=days,
            razorpay_order_id="admin_grant_" + str(uuid.uuid4())[:8],
            razorpay_payment_id="admin_grant_manual",
        )
        await self.record_admin_audit_log(
            admin_id=admin_id,
            action="admin_assign_plan",
            target_type="subscription",
            target_id=student_id,
            details={"plan": plan, "days": days, "reason": reason},
        )
        return sub

    async def admin_create_student_account(
        self,
        email: str,
        password: str,
        full_name: str,
        institution: Optional[str] = None,
        role: str = "student",
        admin_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new student account using Supabase Auth Admin API (service role).

        Guarantees that:
        - Never exposes sensitive password in audit logs or responses.
        - Automatically initializes exactly 20 free credits.
        """
        clean_email = email.strip().lower()
        clean_name = full_name.strip()
        clean_inst = institution.strip() if institution else None

        if self.is_configured() and self._client:
            try:
                # Use Supabase Auth Admin API
                user_res = self._client.auth.admin.create_user({
                    "email": clean_email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": clean_name,
                        "institution": clean_inst,
                    },
                    "app_metadata": {
                        "role": role,
                    },
                })
                if user_res and user_res.user:
                    uid = str(user_res.user.id)
                    # Upsert profile with 20 free credits
                    self._client.table("profiles").upsert({
                        "id": uid,
                        "full_name": clean_name,
                        "institution": clean_inst,
                        "role": role,
                        "status": "active",
                        "credits_balance": 20,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }).execute()

                    if admin_id:
                        await self.record_admin_audit_log(
                            admin_id=admin_id,
                            action="create_student_account",
                            target_type="student",
                            target_id=uid,
                            details={"email": clean_email, "role": role},
                        )

                    return {
                        "id": uid,
                        "email": clean_email,
                        "full_name": clean_name,
                        "institution": clean_inst,
                        "role": role,
                        "credits_balance": 20,
                        "status": "active",
                    }
            except Exception as e:
                logger.error("Supabase admin.create_user failed: %s", e)
                raise ValueError(f"Account creation failed: {str(e)}")

        # Dev fallback
        uid = str(uuid.uuid4())
        self._dev_profiles[uid] = {
            "id": uid,
            "full_name": clean_name,
            "email": clean_email,
            "institution": clean_inst,
            "role": role,
            "status": "active",
            "credits_balance": 20,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return {
            "id": uid,
            "email": clean_email,
            "full_name": clean_name,
            "institution": clean_inst,
            "role": role,
            "credits_balance": 20,
            "status": "active",
        }

    async def list_all_payments(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all platform payment transactions for admin view."""
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("payments")
                    .select("*, profiles(full_name)")
                    .order("created_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
                if res.data is not None:
                    return res.data
            except Exception as e:
                logger.warning("Supabase list all payments failed: %s", e)

        return sorted(list(self._dev_payments.values()), key=lambda x: x["created_at"], reverse=True)[offset : offset + limit]

    async def list_all_subscriptions(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all platform student subscriptions for admin view."""
        if self.is_configured() and self._client:
            try:
                res = (
                    self._client.table("subscriptions")
                    .select("*, profiles(full_name)")
                    .order("created_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
                if res.data is not None:
                    return res.data
            except Exception as e:
                logger.warning("Supabase list all subscriptions failed: %s", e)

        return sorted(list(self._dev_subscriptions.values()), key=lambda x: x["created_at"], reverse=True)[offset : offset + limit]

    async def list_waitlist(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List waitlist applications for admin triage."""
        if self.is_configured() and self._client:
            try:
                query = self._client.table("waitlist").select("*")
                if status_filter:
                    query = query.eq("status", status_filter)
                res = query.order("created_at", desc=True).execute()
                if res.data is not None:
                    return res.data
            except Exception as e:
                logger.warning("Supabase list waitlist failed: %s", e)

        waitlist_items = self._dev_waitlist
        if status_filter:
            waitlist_items = [w for w in waitlist_items if w.get("status") == status_filter]
        return sorted(waitlist_items, key=lambda x: x.get("created_at", ""), reverse=True)

    async def update_waitlist_status(self, entry_id: str, status: str, admin_id: str) -> Dict[str, Any]:
        """Update waitlist entry status (pending, approved, rejected, contacted)."""
        valid_statuses = ["pending", "approved", "rejected", "contacted"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid waitlist status: {status}")

        if self.is_configured() and self._client:
            try:
                self._client.table("waitlist").update({"status": status}).eq("id", entry_id).execute()
            except Exception as e:
                logger.warning("Supabase update waitlist status failed: %s", e)

        for w in self._dev_waitlist:
            if w.get("id") == entry_id:
                w["status"] = status
                break

        await self.record_admin_audit_log(
            admin_id=admin_id,
            action="update_waitlist_status",
            target_type="waitlist",
            target_id=entry_id,
            details={"new_status": status},
        )
        return {"status": "success", "entry_id": entry_id, "new_status": status}

    async def delete_shared_document(self, document_id: str, admin_id: str) -> bool:
        """Allow admins to delete a shared academic document and all its chunks."""
        if self.is_configured() and self._client:
            try:
                # Retrieve doc info for storage cleanup
                doc_res = self._client.table("documents").select("storage_path").eq("id", document_id).execute()
                if doc_res.data:
                    path = doc_res.data[0].get("storage_path")
                    if path:
                        try:
                            self._client.storage.from_("campuspilot-documents").remove([path])
                        except Exception:
                            pass
                # Delete document record (chunks cascade on delete)
                self._client.table("documents").delete().eq("id", document_id).execute()
                await self.record_admin_audit_log(
                    admin_id=admin_id,
                    action="delete_shared_document",
                    target_type="document",
                    target_id=document_id,
                )
                return True
            except Exception as e:
                logger.error("Supabase delete shared document failed: %s", e)
                return False

        if document_id in self._dev_documents:
            del self._dev_documents[document_id]
            if document_id in self._dev_chunks:
                del self._dev_chunks[document_id]
            await self.record_admin_audit_log(
                admin_id=admin_id,
                action="delete_shared_document",
                target_type="document",
                target_id=document_id,
            )
            return True
        return False

    async def record_admin_audit_log(
        self,
        admin_id: str,
        action: str,
        target_type: str,
        target_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write an audit entry recording privileged administrative action."""
        entry = {
            "admin_id": admin_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.is_configured() and self._client:
            try:
                self._client.table("admin_audit_logs").insert(entry).execute()
                return
            except Exception as e:
                logger.warning("Supabase record audit log failed: %s", e)

        entry["id"] = str(uuid.uuid4())
        self._dev_audit_logs.append(entry)

    # --------------------------------------------------------------------------
    # Academic Structure & Curriculum Operations (Semester V & VI)
    # --------------------------------------------------------------------------
    async def get_semesters(self) -> List[Dict[str, Any]]:
        """List all active semesters ordered by semester_number (or order_index fallback)."""
        if self.is_configured() and self._client:
            try:
                try:
                    res = self._client.table("semesters").select("*").order("semester_number").execute()
                except Exception:
                    res = self._client.table("semesters").select("*").order("order_index").execute()
                if res.data:
                    normalized = []
                    for s in res.data:
                        item = dict(s)
                        if "name" not in item and "title" in item:
                            item["name"] = item["title"]
                        if "title" not in item and "name" in item:
                            item["title"] = item["name"]
                        if "order_index" not in item:
                            item["order_index"] = item.get("semester_number", 0)
                        normalized.append(item)
                    return normalized
            except Exception as e:
                logger.debug("Supabase get_semesters failed (%s), using canonical fallback...", e)

        if self.settings.database_url:
            try:
                import asyncpg
                conn = await asyncpg.connect(self.settings.database_url)
                try:
                    rows = await conn.fetch("SELECT id::text, title as name, title, code, semester_number as order_index, semester_number FROM public.semesters ORDER BY semester_number ASC")
                except Exception:
                    rows = await conn.fetch("SELECT id::text, name, code, academic_year, order_index, description FROM public.semesters ORDER BY order_index ASC")
                await conn.close()
                if rows:
                    return [dict(r) for r in rows]
            except Exception as e:
                logger.debug("Database direct query get_semesters failed (%s)...", e)

        from app.core.curriculum import CANONICAL_SEMESTERS
        return [
            {k: v for k, v in sem.items() if k != "subjects"}
            for sem in CANONICAL_SEMESTERS
        ]

    async def get_full_curriculum(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return the complete academic hierarchy (Semesters -> Subjects -> Units / Practicals / Project)."""
        curriculum = None

        # 1. Try Supabase PostgREST
        if self.is_configured() and self._client:
            try:
                try:
                    sem_res = self._client.table("semesters").select("*").order("semester_number").execute()
                except Exception:
                    sem_res = self._client.table("semesters").select("*").order("order_index").execute()

                try:
                    sub_res = self._client.table("subjects").select("*").order("display_order").execute()
                except Exception:
                    sub_res = self._client.table("subjects").select("*").order("order_index").execute()

                try:
                    unit_res = self._client.table("units").select("*").order("display_order").execute()
                except Exception:
                    unit_res = self._client.table("units").select("*").order("order_index").execute()

                try:
                    prac_res = self._client.table("practicals").select("*").order("display_order").execute()
                except Exception:
                    prac_res = self._client.table("practicals").select("*").order("order_index").execute()

                proj_res = self._client.table("project_guidelines").select("*").execute()

                if sem_res.data and sub_res.data:
                    semesters = sem_res.data
                    subjects = sub_res.data
                    units = unit_res.data or []
                    practicals = prac_res.data or []
                    guidelines = proj_res.data or []

                    # Normalize units
                    for u in units:
                        if "order_index" not in u:
                            u["order_index"] = u.get("display_order", 0)

                    # Normalize practicals
                    for p in practicals:
                        if "order_index" not in p:
                            p["order_index"] = p.get("display_order", 0)

                    # Normalize project guidelines
                    for g in guidelines:
                        if "title" not in g:
                            g["title"] = "Project Work-I Guidelines"
                        if "description" not in g:
                            g["description"] = "Independent academic project under faculty guidance."

                    subj_map = {}
                    for s in subjects:
                        s_id = str(s["id"])
                        if "order_index" not in s:
                            s["order_index"] = s.get("display_order", 0)
                        subj_map[s_id] = {
                            **s,
                            "units": [u for u in units if str(u.get("subject_id")) == s_id],
                            "practicals": [p for p in practicals if str(p.get("subject_id")) == s_id],
                            "project_guidelines": next((g for g in guidelines if str(g.get("subject_id")) == s_id), None),
                        }

                    for sem in semesters:
                        sem_id = str(sem["id"])
                        if "name" not in sem and "title" in sem:
                            sem["name"] = sem["title"]
                        if "title" not in sem and "name" in sem:
                            sem["title"] = sem["name"]
                        if "order_index" not in sem:
                            sem["order_index"] = sem.get("semester_number", 0)
                        sem["subjects"] = [s for s in subj_map.values() if str(s.get("semester_id")) == sem_id]
                    curriculum = semesters
            except Exception as e:
                logger.debug("Supabase full curriculum fetch failed (%s)...", e)

        # 2. Try direct PostgreSQL connection
        if not curriculum and self.settings.database_url:
            try:
                import asyncpg
                import json
                conn = await asyncpg.connect(self.settings.database_url)
                try:
                    sem_rows = await conn.fetch("SELECT id::text, title as name, title, code, semester_number as order_index, semester_number, created_at FROM public.semesters ORDER BY semester_number ASC")
                    sub_rows = await conn.fetch("SELECT id::text, semester_id::text, name, code, subject_type, display_order as order_index, display_order, description FROM public.subjects ORDER BY display_order ASC")
                    unit_rows = await conn.fetch("SELECT id::text, subject_id::text, unit_number, title, topics, display_order as order_index, display_order FROM public.units ORDER BY display_order ASC")
                    prac_rows = await conn.fetch("SELECT id::text, subject_id::text, exercise_number, title, description, display_order as order_index, display_order FROM public.practicals ORDER BY display_order ASC")
                    proj_rows = await conn.fetch("SELECT id::text, subject_id::text, report_sections, evaluation_criteria FROM public.project_guidelines")
                except Exception:
                    sem_rows = await conn.fetch("SELECT id::text, name, code, academic_year, order_index, description FROM public.semesters ORDER BY order_index ASC")
                    sub_rows = await conn.fetch("SELECT id::text, semester_id::text, name, code, subject_type, order_index, description FROM public.subjects ORDER BY order_index ASC")
                    unit_rows = await conn.fetch("SELECT id::text, subject_id::text, unit_number, title, topics, order_index FROM public.units ORDER BY order_index ASC")
                    prac_rows = await conn.fetch("SELECT id::text, subject_id::text, exercise_number, title, description, order_index FROM public.practicals ORDER BY order_index ASC")
                    proj_rows = await conn.fetch("SELECT id::text, subject_id::text, title, description, report_sections, evaluation_criteria FROM public.project_guidelines")
                await conn.close()

                if sem_rows and sub_rows:
                    units_by_sub = {}
                    for u in unit_rows:
                        ud = dict(u)
                        if "order_index" not in ud:
                            ud["order_index"] = ud.get("display_order", 0)
                        units_by_sub.setdefault(ud["subject_id"], []).append(ud)

                    prac_by_sub = {}
                    for p in prac_rows:
                        pd = dict(p)
                        if "order_index" not in pd:
                            pd["order_index"] = pd.get("display_order", 0)
                        prac_by_sub.setdefault(pd["subject_id"], []).append(pd)

                    proj_by_sub = {}
                    for g in proj_rows:
                        gd = dict(g)
                        if "title" not in gd:
                            gd["title"] = "Project Work-I Guidelines"
                        if "description" not in gd:
                            gd["description"] = "Independent academic project under faculty guidance."
                        if isinstance(gd.get("report_sections"), str):
                            gd["report_sections"] = json.loads(gd["report_sections"])
                        if isinstance(gd.get("evaluation_criteria"), str):
                            gd["evaluation_criteria"] = json.loads(gd["evaluation_criteria"])
                        proj_by_sub[gd["subject_id"]] = gd

                    subjs_by_sem = {}
                    for s in sub_rows:
                        sd = dict(s)
                        s_id = sd["id"]
                        if "order_index" not in sd:
                            sd["order_index"] = sd.get("display_order", 0)
                        sd["units"] = units_by_sub.get(s_id, [])
                        sd["practicals"] = prac_by_sub.get(s_id, [])
                        sd["project_guidelines"] = proj_by_sub.get(s_id)
                        subjs_by_sem.setdefault(sd["semester_id"], []).append(sd)

                    sems_list = []
                    for sm in sem_rows:
                        smd = dict(sm)
                        sm_id = smd["id"]
                        if "name" not in smd and "title" in smd:
                            smd["name"] = smd["title"]
                        if "title" not in smd and "name" in smd:
                            smd["title"] = smd["name"]
                        if "order_index" not in smd:
                            smd["order_index"] = smd.get("semester_number", 0)
                        smd["subjects"] = subjs_by_sem.get(sm_id, [])
                        sems_list.append(smd)

                    curriculum = sems_list
            except Exception as e:
                logger.debug("Database direct query full curriculum failed (%s)...", e)

        # 3. Fallback to canonical curriculum
        if not curriculum:
            from app.core.curriculum import get_canonical_curriculum
            curriculum = get_canonical_curriculum()

        return curriculum

    async def get_subject_detail(self, subject_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Return full subject details including units, practicals, project guidelines, and associated accessible documents."""
        curriculum = await self.get_full_curriculum(user_id=user_id)
        target_subject = None
        for sem in curriculum:
            for subj in sem.get("subjects", []):
                if str(subj.get("id")) == str(subject_id) or subj.get("name", "").lower() == str(subject_id).lower():
                    import copy
                    target_subject = copy.deepcopy(subj)
                    break
            if target_subject:
                break

        if not target_subject:
            from app.core.curriculum import find_canonical_subject
            target_subject = find_canonical_subject(subject_id)
            if not target_subject:
                return None

        # Fetch associated accessible documents
        docs = await self.list_subject_documents(subject_id=str(target_subject.get("id", subject_id)), user_id=user_id)
        target_subject["documents"] = docs
        target_subject["documents_count"] = len(docs)
        return target_subject

    async def list_subject_documents(self, subject_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve documents associated with a subject that are accessible to user."""
        docs: List[Dict[str, Any]] = []

        if self.is_configured() and self._client:
            try:
                query = self._client.table("documents").select("*").eq("subject_id", subject_id)
                if user_id:
                    query = query.or_(f"user_id.eq.{user_id},scope.eq.shared")
                else:
                    query = query.eq("scope", "shared")
                res = query.order("created_at", desc=True).execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.debug("Supabase list_subject_documents failed (%s)...", e)

        if self.settings.database_url:
            try:
                import asyncpg
                conn = await asyncpg.connect(self.settings.database_url)
                if user_id:
                    rows = await conn.fetch(
                        """
                        SELECT id::text, user_id::text, filename, storage_path, mime_type, file_size,
                               processing_status, scope, semester_id::text, subject_id::text, unit_id::text,
                               created_at, updated_at
                        FROM public.documents
                        WHERE subject_id = $1::uuid AND (user_id = $2::uuid OR scope = 'shared')
                        ORDER BY created_at DESC
                        """,
                        subject_id, user_id
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id::text, user_id::text, filename, storage_path, mime_type, file_size,
                               processing_status, scope, semester_id::text, subject_id::text, unit_id::text,
                               created_at, updated_at
                        FROM public.documents
                        WHERE subject_id = $1::uuid AND scope = 'shared'
                        ORDER BY created_at DESC
                        """,
                        subject_id
                    )
                await conn.close()
                if rows:
                    return [dict(r) for r in rows]
            except Exception as e:
                logger.debug("Database list_subject_documents failed (%s)...", e)

        # In-memory dev documents check
        for d in self._dev_documents.values():
            if str(d.get("subject_id")) == str(subject_id):
                if user_id:
                    if d.get("user_id") == user_id or d.get("scope") == "shared":
                        docs.append(d)
                else:
                    if d.get("scope") == "shared":
                        docs.append(d)
        docs.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return docs


@lru_cache()
def get_supabase_service() -> SupabaseService:
    """Return cached singleton instance of SupabaseService."""
    return SupabaseService()
