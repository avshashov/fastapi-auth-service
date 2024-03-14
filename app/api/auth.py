from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthService
from app.constants import TokenType
from app.database.models import RefreshSession
from app.database.settings import database
from app.dependencies import get_token_from_cookie, get_user_device
from app.schemas import TokenOutput, UserDeviceInput

router = APIRouter(prefix='/auth', tags=['Authentication'])
Session = Annotated[AsyncSession, Depends(database.get_session)]
UserDevice = Annotated[UserDeviceInput, Depends(get_user_device)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')


@router.post('/login')
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session,
    user_device: UserDevice,
    response: Response,
) -> TokenOutput:
    user = await AuthService.authenticate_user(session, form_data.username, form_data.password)
    access_token, refresh_token, expires_refresh_time = await AuthService.create_token_pair(
        data={'sub': str(user.user_id)}, session=session, user_device=user_device
    )
    response.set_cookie(
        key=TokenType.REFRESH.value,
        value=refresh_token,
        expires=expires_refresh_time,
        httponly=True,
        path='/auth/refresh',
    )
    return TokenOutput(access_token=access_token, refresh_token=refresh_token, token_type=TokenType.BEARER)


@router.post('/logout')
async def logout(
    request: Request,
    session: Session,
    user_device: UserDevice,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict[str, bool]:
    await RefreshSession.revoke_active_tokens_for_user(
        session=session, user_id=request.scope['user'].user_id, device_id=user_device.device_id
    )
    return {'logout': True}


@router.post('/refresh')
async def update_token_pair(
    session: Session,
    user_device: UserDevice,
    refresh_token: Annotated[str, Depends(get_token_from_cookie)],
    response: Response,
) -> TokenOutput:
    await AuthService.validate_refresh_token(
        refresh_token=refresh_token, session=session, user_device=user_device
    )
    user = await AuthService.get_current_active_user(token=refresh_token, session=session)
    access_token, refresh_token, expires_refresh_time = await AuthService.create_token_pair(
        data={'sub': str(user.user_id)}, session=session, user_device=user_device
    )
    response.set_cookie(
        key=TokenType.REFRESH.value,
        value=refresh_token,
        expires=expires_refresh_time,
        httponly=True,
        path='/auth/refresh',
    )
    return TokenOutput(access_token=access_token, refresh_token=refresh_token, token_type=TokenType.BEARER)
