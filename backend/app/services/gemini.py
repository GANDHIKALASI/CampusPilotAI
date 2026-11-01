import logging
from typing import AsyncIterator, List
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse, Role

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            api_key = self.settings.gemini_api_key
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Please set it in backend/.env"
                )
            self._client = genai.Client(api_key=api_key)
        return self._client

    def is_configured(self) -> bool:
        return bool(self.settings.gemini_api_key and self.settings.gemini_api_key.strip())

    def _build_contents(self, message: str, history: List[ChatMessage]) -> List[types.Content]:
        contents: List[types.Content] = []

        for msg in history:
            role = "user" if msg.role == Role.USER else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)],
                )
            )

        # Append current user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )
        )
        return contents

    async def generate_response(self, request: ChatRequest) -> ChatResponse:
        primary_model = request.model or self.settings.gemini_model
        fallback_candidates = [primary_model]
        for candidate in ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]:
            if candidate not in fallback_candidates:
                fallback_candidates.append(candidate)

        contents = self._build_contents(request.message, request.history)
        config = types.GenerateContentConfig(
            temperature=request.temperature,
            system_instruction=self.settings.system_instruction,
        )

        last_error = None
        for model in fallback_candidates:
            try:
                response = await self.client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                reply_text = response.text or "I apologize, but I could not generate a response."
                return ChatResponse(
                    reply=reply_text,
                    model=model,
                    status="success",
                )
            except APIError as exc:
                last_error = exc
                logger.warning("Gemini model '%s' failed (%s). Trying fallback...", model, exc.message)
                continue
            except Exception as exc:
                logger.exception("Unexpected error communicating with Gemini on model '%s': %s", model, exc)
                last_error = exc
                continue

        raise RuntimeError(f"All Gemini models exhausted. Last error: {last_error}")

    async def stream_response(self, request: ChatRequest) -> AsyncIterator[str]:
        model = request.model or self.settings.gemini_model
        contents = self._build_contents(request.message, request.history)

        config = types.GenerateContentConfig(
            temperature=request.temperature,
            system_instruction=self.settings.system_instruction,
        )

        try:
            stream = await self.client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except APIError as exc:
            logger.error("Gemini streaming API Error: %s", exc)
            yield f"\n[Error: {exc.message}]"
        except Exception as exc:
            logger.exception("Gemini streaming unexpected error: %s", exc)
            yield f"\n[Service Error: {str(exc)}]"


_gemini_service: GeminiService | None = None


def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
