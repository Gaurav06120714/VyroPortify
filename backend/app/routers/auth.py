"""Authentication router — /me endpoint only.

Auth is handled entirely by Clerk (frontend SDK + Clerk-issued JWTs).
The legacy /register and /login endpoints have been removed because:
  1. They called hash_password() / create_access_token() which raise NotImplementedError.
  2. Having dead endpoints that 500 on every call is a liability (pentest surface).
  3. Clerk handles all credential management; we never store plaintext passwords.

The only endpoint we own is GET /me, which resolves the Clerk Bearer token
to our internal User row (auto-creating it on first API call).
"""

import logging

from fastapi import APIRouter

from app.schemas.auth import UserResponse
from app.security import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=200,
    summary="Get the currently authenticated user",
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Missing or invalid Bearer token"},
    },
)
async def me(current_user: CurrentUser) -> UserResponse:
    """Return the currently authenticated user's profile.

    Requires a valid Clerk-issued JWT in the Authorization: Bearer header.
    The token is verified against Clerk's JWKS endpoint (RS256).
    """
    return UserResponse.model_validate(current_user)
