"""Lightweight academic title generation service for CampusPilot AI.

Generates concise, meaningful 2-5 word titles (e.g., 'DBMS Normalization',
'Operating System Deadlocks', 'Python Data Structures') from the first student message.
Includes robust heuristics with minimal latency and a zero-failure fallback.
"""

import logging
import re
from typing import Optional
from google.genai import types

from app.core.config import Settings, get_settings
from app.services.gemini import GeminiService, get_gemini_service

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "up", "about", "into", "through", "after", "is", "am",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "can", "could", "should", "would", "will", "shall", "may", "might",
    "must", "please", "help", "me", "what", "how", "why", "when", "where", "who",
    "which", "explain", "summarize", "tell", "give", "create", "write", "generate",
    "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her",
    "their", "our", "me", "us", "him", "them", "this", "that", "these", "those"
}


class TitleService:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        gemini_service: Optional[GeminiService] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.gemini_service = gemini_service or get_gemini_service()

    def generate_heuristic_title(self, prompt: str) -> str:
        """Fast fallback heuristic extracting 2-4 primary academic keywords."""
        # Clean tags and special brackets like [Referencing uploaded PDF: ...]
        clean_text = re.sub(r"\[.*?\]", "", prompt)
        clean_text = re.sub(r"[^\w\s-]", " ", clean_text)
        words = [w.strip() for w in clean_text.split() if w.strip()]

        meaningful = [w for w in words if w.lower() not in STOP_WORDS and len(w) > 2]
        if not meaningful:
            meaningful = words[:4]

        selected = meaningful[:4]
        if not selected:
            return "Academic Discussion"

        title = " ".join(s.capitalize() for s in selected)
        return title[:40].strip()

    async def generate_title(self, first_user_message: str) -> str:
        """Generate a concise 2-4 word academic title.

        Tries a fast low-overhead LLM call, falling back immediately to heuristic.
        """
        # Clean any document reference brackets
        clean_msg = re.sub(r"\[Referencing (?:uploaded PDF|document):\s*([^\]]+)\]", r"\1", first_user_message).strip()

        if not self.gemini_service.is_configured():
            return self.generate_heuristic_title(clean_msg)

        try:
            prompt = (
                f"Generate a concise 2 to 4 word academic topic title for this student query.\n"
                f"Examples:\n"
                f"- 'Can you explain deadlocks and how OS handles them?' -> Operating System Deadlocks\n"
                f"- 'Help me understand 3NF and BCNF normalization' -> DBMS Normalization\n"
                f"- 'What are graphs and DFS BFS traversal in Python?' -> Python Graph Traversal\n"
                f"Student Query: {clean_msg}\n"
                f"Title (2 to 4 words ONLY, no quotes, no period):"
            )

            client = self.gemini_service.client
            config = types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=16,
            )
            response = await client.aio.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config=config,
            )

            raw_title = response.text.strip().strip('"\'') if response and response.text else ""
            # Strip trailing punctuation
            raw_title = re.sub(r"[.\n\r]+", "", raw_title).strip()
            word_count = len(raw_title.split())

            if raw_title and 1 <= word_count <= 6:
                return raw_title

        except Exception as exc:
            logger.debug("LLM title generation skipped (%s), using heuristic.", exc)

        return self.generate_heuristic_title(clean_msg)


_title_service: Optional[TitleService] = None


def get_title_service() -> TitleService:
    global _title_service
    if _title_service is None:
        _title_service = TitleService()
    return _title_service
