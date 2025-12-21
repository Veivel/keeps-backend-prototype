from pydantic import BaseModel
from typing import Optional
from app.models.user import User

class PairingCodeResponse(BaseModel):
    pairing_code: str

class PartnerInfo(BaseModel):
    id: Optional[int]
    email: str
    full_name: Optional[str] = None
    picture: Optional[str] = None
    partner_id: Optional[int]

class PairingResponse(BaseModel):
    message: str
    partner: PartnerInfo
