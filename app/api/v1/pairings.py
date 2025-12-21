import secrets
import string
from typing import Any

from fastapi import APIRouter, HTTPException, Body
from fastapi.encoders import jsonable_encoder
from sqlmodel import select

from app.api import deps
from app.models.user import User
from app.schemas.pairing import PairingCodeResponse, PairingResponse
from app.schemas.msg import Msg

router = APIRouter()


def generate_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@router.post("/code", response_model=PairingCodeResponse)
def generate_pairing_code(
    session: deps.SessionDep,
    current_user: deps.CurrentUser,
) -> Any:
    """
    Generate a pairing code for the current user.
    """
    if current_user.partner_id:
        raise HTTPException(status_code=400, detail="User is already paired")

    code = generate_code()
    # Ensure uniqueness (simple check)
    while session.exec(select(User).where(User.pairing_code == code)).first():
        code = generate_code()

    current_user.pairing_code = code
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return {"pairing_code": current_user.pairing_code}


@router.post("/pair", response_model=PairingResponse)
def pair_users(
    session: deps.SessionDep,
    current_user: deps.CurrentUser,
    code: str = Body(..., embed=True),
) -> Any:
    """
    Pair with another user using their code.
    """
    if current_user.partner_id:
         raise HTTPException(status_code=400, detail="You are already paired")

    # Find target user
    target_user = session.exec(select(User).where(User.pairing_code == code)).first()
    if not target_user:
         raise HTTPException(status_code=404, detail="Invalid pairing code")
         
    if target_user.id == current_user.id:
         raise HTTPException(status_code=400, detail="Cannot pair with yourself")
         
    if target_user.partner_id:
         raise HTTPException(status_code=400, detail="Target user is already paired")

    # Execute pairing
    current_user.partner_id = target_user.id
    target_user.partner_id = current_user.id
    
    # clear codes
    current_user.pairing_code = None
    target_user.pairing_code = None
    
    session.add(current_user)
    session.add(target_user)
    session.commit()
    
    return {
        "message": "Paired successfully", 
        "partner": {
            "id": target_user.id,
            "email": target_user.email,
            "full_name": target_user.full_name,
            "picture": target_user.picture,
            "partner_id": target_user.partner_id
        }
    }


@router.post("/unpair", response_model=Msg)
def unpair_users(
    session: deps.SessionDep,
    current_user: deps.CurrentUser,
) -> Any:
    """
    Unpair from current partner.
    """
    if not current_user.partner_id:
         raise HTTPException(status_code=400, detail="Not paired")

    partner = session.get(User, current_user.partner_id)
    if partner:
        partner.partner_id = None
        session.add(partner)
    
    current_user.partner_id = None
    session.add(current_user)
    session.commit()
    
    return {"message": "Unpaired successfully"}
