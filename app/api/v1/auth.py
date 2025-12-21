from typing import Any

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi_sso.sso.google import GoogleSSO
from jose import jwt
from sqlmodel import select

from app.api import deps
from app.core import config
from app.core.config import settings
from app.models.user import User
from app.schemas.token import Token

router = APIRouter()

# Initialize Google SSO
# Note: In a real app, ensure these are set. Errors if None.
# We handle None case gracefully for scaffold or dev.
try:
    google_sso = GoogleSSO(
        client_id=settings.GOOGLE_CLIENT_ID or "client-id",
        client_secret=settings.GOOGLE_CLIENT_SECRET or "client-secret",
        redirect_uri=f"{'http://localhost:8000/api/v1'}/auth/callback/google", # TODO FIX
        allow_insecure_http=True, # For dev/localhost
    )
except Exception as e:
    print(f"Warning: SSO init failed (likely missing env vars): {e}")
    google_sso = None


@router.get("/login/google", response_class=RedirectResponse)
async def google_login():
    """Generate login URL and redirect"""
    if not google_sso:
         raise HTTPException(status_code=500, detail="Google SSO not configured")
    # This automatically redirects
    # We construct the redirect URI dynamically if needed, or rely on the one passed to init
    # Note: fastapi-sso might need the full URL including domain if not behind a proxy properly
    # For now assuming standard behavior
    return await google_sso.get_login_redirect(redirect_uri=f"http://localhost:8000{settings.API_V1_STR}/auth/callback/google")
    # NOTE: Hardcoded localhost:8000 for dev simplicity. In prod, use request.base_url or configured domain.


@router.get("/callback/google", response_model=Token)
async def google_callback(request: Request, session: deps.SessionDep):
    """Process login response from Google and return JWT"""
    if not google_sso:
         raise HTTPException(status_code=500, detail="Google SSO not configured")

    try:
        user_info = await google_sso.verify_and_process(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SSO Error: {str(e)}")

    if not user_info or not user_info.email:
         raise HTTPException(status_code=400, detail="No email returned from Google")

    # Check if user exists
    user = session.exec(select(User).where(User.email == user_info.email)).first()
    if not user:
        # Create new user
        user = User(
            email=user_info.email,
            full_name=user_info.display_name,
            picture=user_info.picture
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    # Create JWT
    token_data = {"sub": str(user.id)} # Storing ID in subject
    # Add expiry? Yes.
    # We should have a create_access_token utility, but putting it inline for speed as per deps? 
    # Or import from security? Let's just use jwt directly here or add utility in core/security.py.
    # Simplicity: inline or simple utility.
    
    # We'll stick to a simple inline JWT creation here for the scaffold.
    import datetime
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = token_data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "user": user
    }

