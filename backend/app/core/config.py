import os
from functools import lru_cache
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from app.core.prompts import CAMPUSPILOT_SYSTEM_PROMPT


class Settings(BaseSettings):
    app_name: str = "CampusPilot AI"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # Document upload limits (10 MB default)
    max_upload_size_bytes: int = 10 * 1024 * 1024

    # Chunking configurations
    chunk_target_tokens: int = 500
    chunk_overlap_tokens: int = 75

    # Visitor Preview Rate Limit
    visitor_chat_limit: int = 3

    # Administrative identities for shared academic document library
    admin_emails: Union[List[str], str] = [
        "buggandhi@proton.me",
        "admin@campuspilot.ai",
        "administrator@campuspilot.ai",
    ]

    # Razorpay Payment Gateway
    razorpay_key_id: str = "rzp_test_placeholder"
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # Plan definitions (Amounts strictly in paise)
    plan_monthly_paise: int = 9900   # ₹99
    plan_monthly_days: int = 30
    plan_yearly_paise: int = 99900   # ₹999
    plan_yearly_days: int = 365

    # Credit System Configuration
    initial_free_credits: int = 20
    low_credit_threshold: int = 5

    # Idempotency Configuration
    idempotency_stale_timeout_seconds: int = 60
    idempotency_heartbeat_interval_seconds: float = 15.0

    # Supabase configurations
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""
    supabase_jwt_secret: str = ""
    database_url: Optional[str] = None

    # Gemini API configurations
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-2"
    embedding_dimension: int = 768
    embedding_timeout_seconds: float = 30.0
    embedding_batch_size: int = 25
    embedding_max_retries: int = 3
    embedding_retry_initial_delay: float = 1.0
    embedding_retry_max_delay: float = 10.0
    embedding_retry_backoff_factor: float = 2.0

    # Semantic Search configurations
    search_default_top_k: int = 5
    search_max_top_k: int = 20
    search_default_threshold: float = 0.60

    # CORS origins
    cors_origins: Union[List[str], str] = [
        "https://campuspilotai.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Trusted hosts for production reverse proxy (do not use wildcard in production)
    allowed_hosts: Union[List[str], str] = []

    # CampusPilot System Persona / Context
    system_instruction: str = CAMPUSPILOT_SYSTEM_PROMPT

    @field_validator("cors_origins", "admin_emails", "allowed_hosts", mode="after")
    @classmethod
    def assemble_string_or_list(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    return json.loads(v_str)
                except Exception:
                    pass
            return [item.strip() for item in v_str.split(",") if item.strip()]
        elif isinstance(v, list):
            return v
        return []

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
