from pydantic import BaseModel
from typing import Optional
import uuid


class TokenPayload(BaseModel):
    sub: str
    exp: int
    iat: int
    jti: str
    user_id: uuid.UUID
    role: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenBlacklistRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class AuthResponse(BaseModel):
    message: str
    user: Optional[dict] = None