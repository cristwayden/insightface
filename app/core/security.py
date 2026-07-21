"""
app/core/security.py
Handles API Key authentication via HTTP Header.

Strategy:
  - Header: X-API-Key (configurable via API_KEY_HEADER_NAME in .env)
  - If settings.API_KEY = "" -> Development Mode (skips authentication, logs a warning)
  - If settings.API_KEY has value -> Production Mode (requires valid API key)

Permissions:
  - PUBLIC  : /  (health check) — no API Key required
  - PRIVATE : /api/v1/* — requires valid API Key

Usage in router:
    from app.core.security import verify_api_key
    router = APIRouter(dependencies=[Depends(verify_api_key)])
"""
from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ──────────────────────────────────────────────────────────────
# Header schema — FastAPI automatically reads from request headers
# auto_error=False: don't raise error immediately, allowing manual control
# ──────────────────────────────────────────────────────────────
_api_key_header_scheme = APIKeyHeader(
    name=settings.API_KEY_HEADER_NAME,
    auto_error=False,
    description=(
        f"Secure API Key. Send via header: `{settings.API_KEY_HEADER_NAME}: <your-key>`"
    ),
)


# ──────────────────────────────────────────────────────────────
# Main dependency — used in router/endpoint
# ──────────────────────────────────────────────────────────────
async def verify_api_key(
    api_key: str | None = Security(_api_key_header_scheme),
) -> str | None:
    """
    FastAPI Dependency — authenticates API Key from HTTP Header.

    Returns:
        str | None: Authenticated API key (or None if dev mode).

    Raises:
        HTTPException 401: Key is missing or invalid.
    """
    # ── Development Mode: API_KEY is empty -> skip authentication ──
    if not settings.API_KEY:
        if not hasattr(verify_api_key, "_dev_warned"):
            logger.warning(
                "⚠  [SECURITY] DEVELOPMENT MODE — API Key authentication is DISABLED. "
                "Set API_KEY in .env before deploying to production!"
            )
            verify_api_key._dev_warned = True  # type: ignore[attr-defined]
        return None

    # ── Production Mode: Key is required ──
    if api_key is None:
        logger.warning("[AUTH] Request denied: missing header '%s'.", settings.API_KEY_HEADER_NAME)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_api_key",
                "message": (
                    f"API Key is required. Send it via header: "
                    f"`{settings.API_KEY_HEADER_NAME}: <your-key>`"
                ),
            },
            headers={"WWW-Authenticate": f'APIKey realm="{settings.API_KEY_HEADER_NAME}"'},
        )

    if api_key != settings.API_KEY:
        # Log security warning (do not log the actual key to prevent leakage)
        masked = f"{api_key[:4]}{'*' * max(0, len(api_key) - 4)}" if len(api_key) > 4 else "****"
        logger.warning("[AUTH] Request denied: Invalid API Key (key: %s...).", masked)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid API Key. Please check your key value.",
            },
            headers={"WWW-Authenticate": f'APIKey realm="{settings.API_KEY_HEADER_NAME}"'},
        )

    logger.debug("[AUTH] ✅ Authentication successful.")
    return api_key
