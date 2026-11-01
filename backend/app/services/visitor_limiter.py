"""Ephemeral in-memory visitor preview rate-limiter for CampusPilot AI.

Enforces server-side conversation preview limits on the public landing page.
Visitor transcripts and messages are strictly temporary and NEVER persisted in PostgreSQL.
Only ephemeral in-memory turn counts and session timestamps are maintained.
"""

import logging
import time
from typing import Dict, Optional, Tuple
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class VisitorSessionTracker:
    """Tracks ephemeral turn counts per unauthenticated visitor session."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        # session_id -> {"count": int, "created_at": float, "last_active": float}
        self._sessions: Dict[str, Dict[str, float]] = {}
        self._session_ttl_seconds: float = 24 * 3600  # 24 hours TTL

    def _cleanup_stale_sessions(self) -> None:
        """Remove sessions older than TTL to prevent memory bloat."""
        now = time.time()
        stale = [
            sid for sid, data in self._sessions.items()
            if now - data.get("last_active", 0) > self._session_ttl_seconds
        ]
        for sid in stale:
            self._sessions.pop(sid, None)

    def check_limit(self, session_id: str) -> Tuple[bool, int, int]:
        """Check if visitor has remaining previews.

        Returns:
            Tuple[is_allowed: bool, current_count: int, remaining: int]
        """
        self._cleanup_stale_sessions()
        limit = self.settings.visitor_chat_limit
        data = self._sessions.get(session_id)
        if not data:
            return True, 0, limit

        count = int(data.get("count", 0))
        remaining = max(0, limit - count)
        is_allowed = count < limit
        return is_allowed, count, remaining

    def increment(self, session_id: str) -> int:
        """Increment visitor turn count and update timestamp."""
        now = time.time()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "count": 1,
                "created_at": now,
                "last_active": now,
            }
            return 1

        self._sessions[session_id]["count"] += 1
        self._sessions[session_id]["last_active"] = now
        return int(self._sessions[session_id]["count"])

    def get_remaining(self, session_id: str) -> int:
        """Get remaining allowed messages for a visitor session."""
        _, _, remaining = self.check_limit(session_id)
        return remaining


# Global singleton instance
_visitor_tracker: Optional[VisitorSessionTracker] = None


def get_visitor_tracker() -> VisitorSessionTracker:
    global _visitor_tracker
    if _visitor_tracker is None:
        _visitor_tracker = VisitorSessionTracker()
    return _visitor_tracker
