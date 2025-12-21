from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    picture: Optional[str] = None
    
    # Pairing
    pairing_code: Optional[str] = Field(default=None, index=True)
    partner_id: Optional[int] = Field(default=None, foreign_key="user.id")
