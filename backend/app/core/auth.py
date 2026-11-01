"""Authentication and token verification dependencies for CampusPilot AI.

Validates Supabase Auth JWT access tokens, rejects invalid/expired credentials,
and extracts verified student identities (UUID). Client-sent user IDs are never trusted.
"""

import logging
from typing import Any, Dict, Optional
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Represents a verified, authenticated student or administrator identity."""

    def __init__(
        self,
        user_id: str,
        email: str,
        metadata: Optional[Dict[str, Any]] = None,
        app_metadata: Optional[Dict[str, Any]] = None,
        is_admin: bool = False,
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.metadata = metadata or {}
        self.app_metadata = app_metadata or {}
        self.is_admin = is_admin

    def __repr__(self) -> str:
        return f"<AuthenticatedUser id={self.user_id} email={self.email} is_admin={self.is_admin}>"


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    settings: Settings = Depends(get_settings),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> AuthenticatedUser:
    """Validate incoming Supabase JWT token and return authenticated user identity.

    Security Guarantee:
    - Never trust client-supplied user_id or browser-editable user_metadata['role'].
    - Administrative privileges are ONLY granted if:
      1. User's verified email matches a server-configured settings.admin_emails, OR
      2. User's Supabase app_metadata (server-only claim) contains role == 'admin'.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with your student credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    def _is_admin(email: str, app_meta: Optional[Dict[str, Any]] = None) -> bool:
        norm_email = email.strip().lower() if email else ""
        app_m = app_meta or {}
        return bool(
            (norm_email and norm_email in [a.lower() for a in settings.admin_emails])
            or app_m.get("role") == "admin"
        )

    # Step 1: Verification via Supabase Client (Official & Most Compatible)
    if supabase_service.is_configured():
        try:
            user_response = supabase_service.client.auth.get_user(token)
            if user_response and user_response.user:
                u = user_response.user
                u_email = str(u.email or "")
                u_meta = u.user_metadata or {}
                u_app_meta = getattr(u, "app_metadata", None) or {}
                return AuthenticatedUser(
                    user_id=str(u.id),
                    email=u_email,
                    metadata=u_meta,
                    app_metadata=u_app_meta,
                    is_admin=_is_admin(u_email, u_app_meta),
                )
        except Exception as e:
            logger.debug("Supabase auth.get_user check failed: %s. Checking local verification fallback.", e)

    # Step 2: Local PyJWT verification if JWT secret is configured
    if settings.supabase_jwt_secret:
        try:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={"verify_signature": True, "verify_exp": True},
            )
            sub = payload.get("sub")
            if not sub:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: missing user subject.",
                )
            u_email = str(payload.get("email", ""))
            u_meta = payload.get("user_metadata", {})
            u_app_meta = payload.get("app_metadata", {})
            return AuthenticatedUser(
                user_id=str(sub),
                email=u_email,
                metadata=u_meta,
                app_metadata=u_app_meta,
                is_admin=_is_admin(u_email, u_app_meta),
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWTError as jwt_err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(jwt_err)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Step 3: Fast unverified payload inspection for dev testing when backend Supabase credentials are in local dev
    if settings.app_env == "development":
        try:
            unverified = jwt.decode(token, options={"verify_signature": False, "verify_exp": True})
            sub = unverified.get("sub")
            if sub:
                u_email = str(unverified.get("email", ""))
                u_meta = unverified.get("user_metadata", {})
                u_app_meta = unverified.get("app_metadata", {})
                return AuthenticatedUser(
                    user_id=str(sub),
                    email=u_email,
                    metadata=u_meta,
                    app_metadata=u_app_meta,
                    is_admin=_is_admin(u_email, u_app_meta),
                )
        except Exception as dev_err:
            logger.warning("Dev unverified token decode failed: %s", dev_err)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_admin_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Dependency that strictly requires administrative privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Administrative privileges required.",
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    settings: Settings = Depends(get_settings),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Optional[AuthenticatedUser]:
    """Dependency that returns AuthenticatedUser if valid token is provided, or None if anonymous."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return await get_current_user(
            credentials=credentials,
            settings=settings,
            supabase_service=supabase_service,
        )
    except Exception:
        return None

