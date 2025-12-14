from pydantic import BaseModel, EmailStr
from typing import Optional, List

class User(BaseModel):
    """
    Pydantic model for a user, designed to work with Firebase Authentication.
    """
    uid: str
    email: EmailStr
    role: str = "technician"
    full_name: Optional[str] = None
    disabled: bool = False
    permissions: List[str] = []

class TokenData(BaseModel):
    """
    Pydantic model for the data encoded in a JWT.
    """
    uid: str
    email: EmailStr