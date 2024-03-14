from datetime import datetime

from pydantic import BaseModel

from app.schemas.device import UserDeviceInput


class TokenOutput(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenCreateBase(BaseModel):
    user_id: str
    expires_at: datetime
    jti: str


class TokenCreateInput(TokenCreateBase):
    device_id: str


class TokenWithDeviceCreateInput(TokenCreateBase):
    device: UserDeviceInput
