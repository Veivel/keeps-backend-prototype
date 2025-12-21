from typing import Generator, Annotated, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import config
from app.core.config import settings
from app.core.db import engine
from app.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token" # We might not use this standard flow with Google, but kept for reference
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: str = Depends(reusable_oauth2)) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        # In this simple implementation we just store email in sub
        # Adjust based on your JWT structure
        token_data = payload.get("sub")
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data) # token_data assumed to be ID? No, usually sub is string.
    # If sub is email, we search. If sub is ID (int), we get.
    # Let's assume we store ID in sub for simplicity or email.
    
    # Actually, let's search by email if sub is email, or ID if sub is ID.
    # Let's decide: sub will be user ID (str).
    
    if not user:
        # Fallback if we stored email? 
        # For now let's assume valid ID.
        # But wait, session.get(User, id) expects primary key.
        # If token_data is string "1", it might work or need int().
        try:
             user = session.get(User, int(token_data))
        except:
             user = None
             
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
