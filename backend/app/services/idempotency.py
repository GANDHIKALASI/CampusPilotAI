"""
CampusPilot AI — Distributed Request Idempotency Service with Lease Fencing.

Provides persistent, atomic request idempotency for authenticated student conversations:
- Binds Idempotency-Key strictly to (user_id, conversation_id, key).
- Generates cryptographically secure lease ownership tokens (`owner_token`) to prevent
  split-brain execution and expired worker overwrites.
- Provides lease renewal (heartbeat) for long-running AI streaming or complex retrieval.
- Enforces payload hash verification; raises HTTP 409 Conflict if same key has different payload.
- Fencing checks: completing or failing a key requires matching the active `owner_token`.
- Automatic recovery of stale processing records after timeout, transferring lease safely.
- Multi-instance AWS safety:
  * In production (`app_env == "production"`), the service FAILS CLOSED if PostgreSQL
    idempotency is unavailable. It never silently switches to local SQLite in multi-instance production.
  * In development/test, it uses durable SQLite with WAL mode, busy timeouts, and `BEGIN IMMEDIATE` row-locking.
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.core.config import Settings, get_settings
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)


class IdempotencyStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AcquireOutcome(str, Enum):
    ACQUIRED = "acquired"          # Fresh lock acquired; proceed with RAG + LLM execution
    COMPLETED = "completed"        # Previously completed; return cached response data
    IN_PROGRESS = "in_progress"    # Concurrently running on another worker/thread
    CONFLICT = "conflict"          # Reused key with different payload -> HTTP 409
    RECOVERED = "recovered"        # Stale record reclaimed after timeout with new lease token


class LeaseHeartbeat:
    """Manages periodic background lease renewal (heartbeat) for active AI requests."""

    def __init__(
        self,
        service: "IdempotencyService",
        user_id: str,
        conversation_id: str,
        idempotency_key: Optional[str],
        owner_token: Optional[str],
        interval_seconds: float = 15.0,
    ) -> None:
        self.service = service
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.key = idempotency_key
        self.owner_token = owner_token
        self.interval = max(0.01, interval_seconds)
        self._task: Optional[asyncio.Task] = None
        self._lease_lost: bool = False
        self._stopped: bool = False

    @property
    def is_active(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def lease_lost(self) -> bool:
        return self._lease_lost

    async def start(self) -> None:
        if not self.key or not self.owner_token:
            return
        self._stopped = False
        self._task = asyncio.create_task(self._run_loop())

    async def _run_loop(self) -> None:
        while not self._stopped:
            try:
                await asyncio.sleep(self.interval)
                if self._stopped:
                    break
                renewed = await self.service.renew_lease(
                    user_id=self.user_id,
                    conversation_id=self.conversation_id,
                    idempotency_key=self.key,
                    owner_token=self.owner_token,
                )
                if not renewed:
                    logger.warning(
                        "Idempotency lease lost or expired during heartbeat for key %s (token %s)",
                        self.key,
                        self.owner_token,
                    )
                    self._lease_lost = True
                    break
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("Error during idempotency lease heartbeat: %s", exc)

    async def stop(self) -> None:
        self._stopped = True
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        self._task = None


class IdempotencyService:
    """Manages persistent request-level idempotency with lease fencing across workers and restarts."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        supabase_service: Optional[SupabaseService] = None,
        stale_timeout_seconds: int = 60,
        sqlite_db_path: Optional[str] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.supabase_service = supabase_service or get_supabase_service()
        self.stale_timeout_seconds = stale_timeout_seconds

        # Determine SQLite path for persistent local / test / fallback storage
        if sqlite_db_path:
            self.sqlite_path = Path(sqlite_db_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            cache_dir = base_dir / ".cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.sqlite_path = cache_dir / "idempotency.db"

        self._supabase_table_available: Optional[bool] = None
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize persistent SQLite table with WAL mode for local/test concurrency."""
        try:
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(self.sqlite_path), timeout=10.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA busy_timeout=5000;")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS idempotency_keys (
                        user_id TEXT NOT NULL,
                        conversation_id TEXT NOT NULL,
                        key TEXT NOT NULL,
                        request_hash TEXT NOT NULL,
                        status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
                        owner_token TEXT NOT NULL,
                        recovery_count INTEGER NOT NULL DEFAULT 0,
                        response_data TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (user_id, conversation_id, key)
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_idem_lookup ON idempotency_keys (user_id, conversation_id, key);"
                )
        except Exception as exc:
            logger.warning("Failed to initialize SQLite idempotency store: %s", exc)

    @asynccontextmanager
    async def heartbeat_scope(
        self,
        user_id: str,
        conversation_id: str,
        idempotency_key: Optional[str],
        owner_token: Optional[str],
        interval_seconds: Optional[float] = None,
    ):
        """Context manager guaranteeing heartbeat execution and cleanup on every exit path."""
        interval = interval_seconds if interval_seconds is not None else 15.0
        heartbeat = LeaseHeartbeat(
            service=self,
            user_id=user_id,
            conversation_id=conversation_id,
            idempotency_key=idempotency_key,
            owner_token=owner_token,
            interval_seconds=interval,
        )
        await heartbeat.start()
        try:
            yield heartbeat
        finally:
            await heartbeat.stop()

    def create_heartbeat(
        self,
        user_id: str,
        conversation_id: str,
        idempotency_key: Optional[str],
        owner_token: Optional[str],
        interval_seconds: float = 15.0,
    ) -> LeaseHeartbeat:
        """Create a standalone LeaseHeartbeat instance for fine-grained lifecycle management."""
        return LeaseHeartbeat(
            service=self,
            user_id=user_id,
            conversation_id=conversation_id,
            idempotency_key=idempotency_key,
            owner_token=owner_token,
            interval_seconds=interval_seconds,
        )

    def is_production(self) -> bool:
        """Check if running in production mode."""
        env_val = getattr(self.settings, "app_env", "development").lower()
        return env_val in ("production", "prod")

    def compute_request_hash(self, content: str) -> str:
        """Compute deterministic SHA-256 hash of student message content."""
        normalized = content.strip().encode("utf-8")
        return hashlib.sha256(normalized).hexdigest()

    def _check_supabase_available(self) -> bool:
        """Check if hosted Supabase has public.idempotency_keys table migrated."""
        if self._supabase_table_available is not None:
            return self._supabase_table_available

        if not self.supabase_service.is_configured() or not self.supabase_service._client:
            self._supabase_table_available = False
            return False

        try:
            res = self.supabase_service._client.table("idempotency_keys").select("key").limit(1).execute()
            self._supabase_table_available = True
            return True
        except Exception:
            self._supabase_table_available = False
            return False

    async def acquire_key(
        self,
        user_id: str,
        conversation_id: str,
        idempotency_key: str,
        content: str,
        owner_token: Optional[str] = None,
    ) -> Tuple[AcquireOutcome, Optional[Dict[str, Any]], Optional[str]]:
        """
        Attempt to acquire or check an idempotency key atomically with lease token fencing.

        Returns:
            Tuple of (AcquireOutcome, cached_response_data, active_owner_token).
        """
        if not idempotency_key or not idempotency_key.strip():
            # If no key provided, treat as fresh request without idempotency tracking
            return AcquireOutcome.ACQUIRED, None, None

        key = idempotency_key.strip()
        req_hash = self.compute_request_hash(content)
        token = owner_token or str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Primary path: Supabase / PostgreSQL RPC if migrated
        if self._check_supabase_available():
            client = self.supabase_service._client
            # Try PostgreSQL stored procedure with FOR UPDATE lock first (MEDIUM-2 fix)
            try:
                rpc_res = client.rpc(
                    "acquire_idempotency_key",
                    {
                        "p_key": key,
                        "p_user_id": user_id,
                        "p_conversation_id": conversation_id,
                        "p_request_hash": req_hash,
                        "p_owner_token": token,
                        "p_stale_seconds": self.stale_timeout_seconds,
                    },
                ).execute()
                if rpc_res.data:
                    row = rpc_res.data[0] if isinstance(rpc_res.data, list) else rpc_res.data
                    rec_status = row.get("record_status")
                    cached_resp = row.get("cached_response")
                    active_token = row.get("active_owner_token")
                    if rec_status == "acquired":
                        return AcquireOutcome.ACQUIRED, None, active_token or token
                    elif rec_status == "completed":
                        return AcquireOutcome.COMPLETED, cached_resp, active_token
                    elif rec_status == "in_progress":
                        return AcquireOutcome.IN_PROGRESS, None, None
                    elif rec_status == "conflict":
                        return AcquireOutcome.CONFLICT, None, None
                    elif rec_status == "recovered":
                        return AcquireOutcome.RECOVERED, None, active_token or token
            except Exception as rpc_err:
                err_msg = str(rpc_err).lower()
                if self.is_production() and not any(t in err_msg for t in ["pgrst202", "not found", "does not exist"]):
                    raise RuntimeError(f"PostgreSQL acquire_idempotency_key failed in production: {rpc_err}") from rpc_err
                logger.debug("RPC acquire_idempotency_key not used (%s), falling back to table query", rpc_err)

            try:
                res = (
                    client.table("idempotency_keys")
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("conversation_id", conversation_id)
                    .eq("key", key)
                    .execute()
                )
                if res.data:
                    row = res.data[0]
                    if row["request_hash"] != req_hash:
                        return AcquireOutcome.CONFLICT, None, None
                    if row["status"] == IdempotencyStatus.COMPLETED.value:
                        return AcquireOutcome.COMPLETED, row.get("response_data"), row.get("owner_token")
                    if row["status"] == IdempotencyStatus.PROCESSING.value:
                        try:
                            updated_dt = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00"))
                            elapsed = (datetime.now(timezone.utc) - updated_dt).total_seconds()
                            if elapsed > self.stale_timeout_seconds:
                                # Safe recovery with new owner token
                                current_rec = int(row.get("recovery_count", 0)) + 1
                                client.table("idempotency_keys").update({
                                    "owner_token": token,
                                    "recovery_count": current_rec,
                                    "updated_at": now_iso,
                                }).eq("user_id", user_id).eq("conversation_id", conversation_id).eq("key", key).execute()
                                return AcquireOutcome.RECOVERED, None, token
                        except Exception:
                            pass
                        return AcquireOutcome.IN_PROGRESS, None, None
                    if row["status"] == IdempotencyStatus.FAILED.value:
                        # Re-try previously failed turn with fresh lease token
                        client.table("idempotency_keys").update({
                            "status": IdempotencyStatus.PROCESSING.value,
                            "owner_token": token,
                            "updated_at": now_iso,
                        }).eq("user_id", user_id).eq("conversation_id", conversation_id).eq("key", key).execute()
                        return AcquireOutcome.ACQUIRED, None, token

                # Fresh insert with owner token
                client.table("idempotency_keys").insert({
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "key": key,
                    "request_hash": req_hash,
                    "status": IdempotencyStatus.PROCESSING.value,
                    "owner_token": token,
                    "recovery_count": 0,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }).execute()
                return AcquireOutcome.ACQUIRED, None, token
            except Exception as e:
                err_str = str(e).lower()
                if "duplicate" in err_str or "conflict" in err_str or "23505" in err_str:
                    return AcquireOutcome.IN_PROGRESS, None, None
                logger.warning("Supabase idempotency check error (%s)", e)

        # 2. Production AWS safety guard: Fail Closed!
        if self.is_production():
            raise RuntimeError(
                "CRITICAL: PostgreSQL idempotency table 'idempotency_keys' is unavailable in production. "
                "Process-local SQLite fallback is disabled in multi-instance production to prevent state divergence. "
                "Apply migration 007 to Supabase."
            )

        # 3. Development / Test fallback: Persistent SQLite with lease fencing
        return self._acquire_sqlite(user_id, conversation_id, key, req_hash, token, now_iso)

    def _acquire_sqlite(
        self,
        user_id: str,
        conversation_id: str,
        key: str,
        req_hash: str,
        token: str,
        now_iso: str,
    ) -> Tuple[AcquireOutcome, Optional[Dict[str, Any]], Optional[str]]:
        """Atomic SQLite acquire using BEGIN IMMEDIATE transaction with lease fencing."""
        with sqlite3.connect(str(self.sqlite_path), timeout=10.0) as conn:
            conn.execute("PRAGMA busy_timeout=5000;")
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")

            cursor.execute(
                """
                SELECT status, request_hash, response_data, owner_token, recovery_count, updated_at
                FROM idempotency_keys
                WHERE user_id = ? AND conversation_id = ? AND key = ?;
                """,
                (user_id, conversation_id, key),
            )
            row = cursor.fetchone()

            if row is None:
                # Fresh key
                cursor.execute(
                    """
                    INSERT INTO idempotency_keys (
                        user_id, conversation_id, key, request_hash, status, owner_token, recovery_count, response_data, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, NULL, ?, ?);
                    """,
                    (user_id, conversation_id, key, req_hash, IdempotencyStatus.PROCESSING.value, token, now_iso, now_iso),
                )
                conn.commit()
                return AcquireOutcome.ACQUIRED, None, token

            status_str, existing_hash, resp_json_str, active_token, rec_count, updated_str = row

            if existing_hash != req_hash:
                conn.commit()
                return AcquireOutcome.CONFLICT, None, None

            if status_str == IdempotencyStatus.COMPLETED.value:
                conn.commit()
                cached_data = json.loads(resp_json_str) if resp_json_str else {}
                return AcquireOutcome.COMPLETED, cached_data, active_token

            if status_str == IdempotencyStatus.PROCESSING.value:
                try:
                    updated_dt = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                    elapsed = (datetime.now(timezone.utc) - updated_dt).total_seconds()
                    if elapsed > self.stale_timeout_seconds:
                        # Reclaim stale processing record with new owner token
                        cursor.execute(
                            """
                            UPDATE idempotency_keys
                            SET owner_token = ?, recovery_count = ?, updated_at = ?
                            WHERE user_id = ? AND conversation_id = ? AND key = ?;
                            """,
                            (token, (rec_count or 0) + 1, now_iso, user_id, conversation_id, key),
                        )
                        conn.commit()
                        return AcquireOutcome.RECOVERED, None, token
                except Exception:
                    pass

                conn.commit()
                return AcquireOutcome.IN_PROGRESS, None, None

            if status_str == IdempotencyStatus.FAILED.value:
                cursor.execute(
                    """
                    UPDATE idempotency_keys
                    SET status = ?, owner_token = ?, updated_at = ?
                    WHERE user_id = ? AND conversation_id = ? AND key = ?;
                    """,
                    (IdempotencyStatus.PROCESSING.value, token, now_iso, user_id, conversation_id, key),
                )
                conn.commit()
                return AcquireOutcome.ACQUIRED, None, token

            conn.commit()
            return AcquireOutcome.CONFLICT, None, None

    async def renew_lease(
        self,
        user_id: str,
        conversation_id: str,
        idempotency_key: str,
        owner_token: str,
    ) -> bool:
        """
        Renew an active lease (heartbeat) for long-running requests.
        Returns False if the lease was lost or expired.
        """
        if not idempotency_key or not owner_token:
            return False

        key = idempotency_key.strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        if self._check_supabase_available():
            # Try PostgreSQL RPC first (MEDIUM-2 fix)
            try:
                rpc_res = (
                    self.supabase_service._client.rpc(
                        "renew_idempotency_lease",
                        {
                            "p_key": key,
                            "p_user_id": user_id,
                            "p_conversation_id": conversation_id,
                            "p_owner_token": owner_token,
                        },
                    ).execute()
                )
                if rpc_res.data is True:
                    return True
                if self.is_production():
                    return False
            except Exception as rpc_err:
                err_msg = str(rpc_err).lower()
                if self.is_production() and not any(t in err_msg for t in ["pgrst202", "not found", "does not exist"]):
                    return False
                logger.debug("RPC renew_idempotency_lease not used (%s), falling back to table update", rpc_err)

            try:
                res = (
                    self.supabase_service._client.table("idempotency_keys")
                    .update({"updated_at": now_iso})
                    .eq("user_id", user_id)
                    .eq("conversation_id", conversation_id)
                    .eq("key", key)
                    .eq("owner_token", owner_token)
                    .eq("status", IdempotencyStatus.PROCESSING.value)
                    .execute()
                )
                if res.data:
                    return True
            except Exception as e:
                logger.warning("Supabase renew_lease failed (%s)", e)

        if self.is_production():
            return False

        try:
            with sqlite3.connect(str(self.sqlite_path), timeout=5.0) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE idempotency_keys
                    SET updated_at = ?
                    WHERE user_id = ? AND conversation_id = ? AND key = ? AND owner_token = ? AND status = 'processing';
                    """,
                    (now_iso, user_id, conversation_id, key, owner_token),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as exc:
            logger.error("Failed to renew lease in SQLite: %s", exc)
            return False

    async def complete_key(
        self,
        user_id: str,
        conversation_id: str,
        idempotency_key: str,
        response_data: Dict[str, Any],
        owner_token: Optional[str] = None,
    ) -> bool:
        """
        Mark idempotency key as completed with fencing check.
        Returns True if completed successfully, False if worker lost lease ownership.
        """
        if not idempotency_key or not idempotency_key.strip():
            return True

        key = idempotency_key.strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        if self._check_supabase_available():
            try:
                query = (
                    self.supabase_service._client.table("idempotency_keys")
                    .update({
                        "status": IdempotencyStatus.COMPLETED.value,
                        "response_data": response_data,
                        "updated_at": now_iso,
                    })
                    .eq("user_id", user_id)
                    .eq("conversation_id", conversation_id)
                    .eq("key", key)
                    .in_("status", [IdempotencyStatus.PROCESSING.value, IdempotencyStatus.COMPLETED.value])
                )
                if owner_token:
                    query = query.eq("owner_token", owner_token)
                res = query.execute()
                if res.data:
                    return True
            except Exception as e:
                logger.warning("Supabase complete_key failed (%s)", e)

        if self.is_production():
            raise RuntimeError("PostgreSQL idempotency failure in production complete_key.")

        # SQLite update with fencing check
        try:
            resp_str = json.dumps(response_data)
            with sqlite3.connect(str(self.sqlite_path), timeout=10.0) as conn:
                conn.execute("PRAGMA busy_timeout=5000;")
                cursor = conn.cursor()
                if owner_token:
                    cursor.execute(
                        """
                        UPDATE idempotency_keys
                        SET status = ?, response_data = ?, updated_at = ?
                        WHERE user_id = ? AND conversation_id = ? AND key = ? AND owner_token = ? AND status IN ('processing', 'completed');
                        """,
                        (IdempotencyStatus.COMPLETED.value, resp_str, now_iso, user_id, conversation_id, key, owner_token),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE idempotency_keys
                        SET status = ?, response_data = ?, updated_at = ?
                        WHERE user_id = ? AND conversation_id = ? AND key = ? AND status IN ('processing', 'completed');
                        """,
                        (IdempotencyStatus.COMPLETED.value, resp_str, now_iso, user_id, conversation_id, key),
                    )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as sq_err:
            logger.error("Failed to complete idempotency key in SQLite: %s", sq_err)
            return False

    async def fail_key(
        self,
        user_id: str,
        conversation_id: str,
        idempotency_key: str,
        error_message: Optional[str] = None,
        owner_token: Optional[str] = None,
    ) -> bool:
        """
        Mark idempotency key as failed with fencing check.
        Returns True if marked failed, False if lease was lost.
        """
        if not idempotency_key or not idempotency_key.strip():
            return True

        key = idempotency_key.strip()
        now_iso = datetime.now(timezone.utc).isoformat()

        if self._check_supabase_available():
            try:
                query = (
                    self.supabase_service._client.table("idempotency_keys")
                    .update({
                        "status": IdempotencyStatus.FAILED.value,
                        "updated_at": now_iso,
                    })
                    .eq("user_id", user_id)
                    .eq("conversation_id", conversation_id)
                    .eq("key", key)
                    .eq("status", IdempotencyStatus.PROCESSING.value)
                )
                if owner_token:
                    query = query.eq("owner_token", owner_token)
                res = query.execute()
                return bool(res.data)
            except Exception:
                pass

        if self.is_production():
            return False

        try:
            with sqlite3.connect(str(self.sqlite_path), timeout=10.0) as conn:
                conn.execute("PRAGMA busy_timeout=5000;")
                cursor = conn.cursor()
                if owner_token:
                    cursor.execute(
                        """
                        UPDATE idempotency_keys
                        SET status = ?, updated_at = ?
                        WHERE user_id = ? AND conversation_id = ? AND key = ? AND owner_token = ? AND status = 'processing';
                        """,
                        (IdempotencyStatus.FAILED.value, now_iso, user_id, conversation_id, key, owner_token),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE idempotency_keys
                        SET status = ?, updated_at = ?
                        WHERE user_id = ? AND conversation_id = ? AND key = ? AND status = 'processing';
                        """,
                        (IdempotencyStatus.FAILED.value, now_iso, user_id, conversation_id, key),
                    )
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False


_idempotency_service: Optional[IdempotencyService] = None


def get_idempotency_service() -> IdempotencyService:
    global _idempotency_service
    if _idempotency_service is None:
        _idempotency_service = IdempotencyService()
    return _idempotency_service
