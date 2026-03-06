"""Authentication routes using OAuth 2.0 (Google and GitHub)."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import uuid4

from authlib.integrations.starlette_client import OAuth
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from app.core.config import get_settings
from app.core.deps import get_current_user, require_admin
from app.db.connection import get_database
from app.models.user import UserInDB, UserResponse, UserRole, UserStatus, OAuthProvider

# Setup router
router = APIRouter()

# Authlib OAuth registry — clients are registered lazily on first use
oauth = OAuth()
_oauth_initialized = False


def _init_oauth():
    """Register Google and GitHub OAuth clients using current settings."""
    global _oauth_initialized
    if _oauth_initialized:
        return
    settings = get_settings()

    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    oauth.register(
        name="github",
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "read:user user:email"},
    )

    _oauth_initialized = True


# Token utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    settings = get_settings()
    to_encode = data.copy()

    to_encode.update(
        {
            "jti": str(uuid4()),
            "iat": datetime.now(timezone.utc),
            "iss": "media-manager-api",
        }
    )

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    from jose import jwt
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def _upsert_user(
    db,
    provider: str,
    provider_id: str,
    email: str,
    display_name: str,
    avatar_url: Optional[str],
) -> UserInDB:
    """Find or create a user. Applies ADMIN_EMAILS bootstrap logic on first login."""
    settings = get_settings()
    now = datetime.now(timezone.utc)

    existing = await db.users.find_one({"provider": provider, "provider_id": provider_id})
    if existing:
        await db.users.update_one(
            {"_id": existing["_id"]},
            {"$set": {"last_login": now, "display_name": display_name, "avatar_url": avatar_url}},
        )
        existing.update({"last_login": now, "display_name": display_name, "avatar_url": avatar_url})
        return UserInDB(**existing)

    role = UserRole.admin if email in settings.ADMIN_EMAILS else UserRole.read_only
    user_status = UserStatus.approved if email in settings.ADMIN_EMAILS else UserStatus.pending

    new_user = UserInDB(
        email=email,
        display_name=display_name,
        avatar_url=avatar_url,
        provider=OAuthProvider(provider),
        provider_id=provider_id,
        role=role,
        status=user_status,
        created_at=now,
        last_login=now,
    )
    doc = new_user.model_dump(exclude_none=True)
    await db.users.insert_one(doc)
    return new_user


# ─── Google OAuth ────────────────────────────────────────────────────────────

@router.get("/google/login")
async def google_login(request: Request):
    """Redirect to Google OAuth consent screen."""
    _init_oauth()
    settings = get_settings()
    redirect_uri = f"{settings.BACKEND_URL}/api/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db=Depends(get_database)):
    """Handle Google OAuth callback, create/update user, issue JWT, redirect to frontend."""
    _init_oauth()
    settings = get_settings()

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=oauth_failed")

    userinfo = token.get("userinfo")
    if not userinfo:
        try:
            userinfo = await oauth.google.userinfo(token=token)
        except Exception:
            return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=oauth_failed")

    email = userinfo.get("email")
    if not email:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=no_email")

    user = await _upsert_user(
        db,
        provider="google",
        provider_id=userinfo["sub"],
        email=email,
        display_name=userinfo.get("name") or email,
        avatar_url=userinfo.get("picture"),
    )

    jwt_token = create_access_token(
        {"sub": user.email, "role": user.role.value, "status": user.status.value}
    )
    return RedirectResponse(f"{settings.FRONTEND_URL}/login/callback?token={jwt_token}")


# ─── GitHub OAuth ─────────────────────────────────────────────────────────────

@router.get("/github/login")
async def github_login(request: Request):
    """Redirect to GitHub OAuth consent screen."""
    _init_oauth()
    settings = get_settings()
    redirect_uri = f"{settings.BACKEND_URL}/api/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request, db=Depends(get_database)):
    """Handle GitHub OAuth callback, create/update user, issue JWT, redirect to frontend."""
    _init_oauth()
    settings = get_settings()

    try:
        token = await oauth.github.authorize_access_token(request)
    except Exception:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=oauth_failed")

    # Fetch GitHub user profile
    try:
        resp = await oauth.github.get("user", token=token)
        profile = resp.json()
    except Exception:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=oauth_failed")

    # GitHub may hide the primary email — fetch emails list if needed
    email = profile.get("email")
    if not email:
        try:
            emails_resp = await oauth.github.get("user/emails", token=token)
            emails = emails_resp.json()
            primary = next(
                (e["email"] for e in emails if e.get("primary") and e.get("verified")),
                None,
            )
            email = primary
        except Exception:
            pass

    if not email:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=no_email")

    user = await _upsert_user(
        db,
        provider="github",
        provider_id=str(profile["id"]),
        email=email,
        display_name=profile.get("name") or profile.get("login") or email,
        avatar_url=profile.get("avatar_url"),
    )

    jwt_token = create_access_token(
        {"sub": user.email, "role": user.role.value, "status": user.status.value}
    )
    return RedirectResponse(f"{settings.FRONTEND_URL}/login/callback?token={jwt_token}")


# ─── User endpoints ───────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_user),
):
    """Get current authenticated user's information."""
    return UserResponse(
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        status=current_user.status,
    )


@router.post("/logout")
async def logout(current_user: UserInDB = Depends(get_current_user)):
    """Logout endpoint — tokens are stateless; this signals the client to clear state."""
    return {"message": f"User {current_user.email} logged out successfully"}


# ─── Admin endpoints ──────────────────────────────────────────────────────────

@router.get("/users/pending", response_model=List[UserResponse])
async def list_pending_users(
    admin: UserInDB = Depends(require_admin),
    db=Depends(get_database),
):
    """List all users awaiting approval. Admin only."""
    cursor = db.users.find({"status": UserStatus.pending.value})
    docs = await cursor.to_list(length=1000)
    return [
        UserResponse(
            email=d["email"],
            display_name=d["display_name"],
            avatar_url=d.get("avatar_url"),
            role=UserRole(d["role"]),
            status=UserStatus(d["status"]),
        )
        for d in docs
    ]


@router.post("/users/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: str,
    admin: UserInDB = Depends(require_admin),
    db=Depends(get_database),
):
    """Set user status to approved. Admin only."""
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await db.users.find_one_and_update(
        {"_id": oid},
        {"$set": {"status": UserStatus.approved.value}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        email=result["email"],
        display_name=result["display_name"],
        avatar_url=result.get("avatar_url"),
        role=UserRole(result["role"]),
        status=UserStatus(result["status"]),
    )


@router.post("/users/{user_id}/reject", status_code=204)
async def reject_user(
    user_id: str,
    admin: UserInDB = Depends(require_admin),
    db=Depends(get_database),
):
    """Delete a pending user. Admin only."""
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await db.users.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
