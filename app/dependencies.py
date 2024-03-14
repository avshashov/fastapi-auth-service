from typing import Annotated
from uuid import NAMESPACE_X500, uuid5

from fastapi import Cookie, Request

from app.errors import NotFoundRefreshTokenException
from app.schemas import UserDeviceInput


def get_user_device(request: Request) -> UserDeviceInput:
    ip_address = request.client.host
    user_agent = request.headers.get('user-agent')
    device_id = str(uuid5(NAMESPACE_X500, user_agent + ip_address))
    return UserDeviceInput(device_id=device_id, ip_address=ip_address, user_agent=user_agent)


def get_token_from_cookie(refresh_token: Annotated[str, Cookie()] = None) -> str:
    if not refresh_token:
        raise NotFoundRefreshTokenException
    return refresh_token
