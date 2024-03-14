from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import oauth2_scheme
from app.auth.service import AuthService
from app.database.models import User
from app.database.settings import database
from app.errors import UserInactiveException
from app.schemas import UserCreateInput, UserOutput, UserWithHash

router = APIRouter(prefix='/user', tags=['User'])
Session = Annotated[AsyncSession, Depends(database.get_session)]


@router.post('/signup')
async def create_user(user_data: UserCreateInput, session: Session) -> UserOutput:
    password = user_data.password.get_secret_value()
    hashed_password = AuthService.get_password_hash(password)
    user_data = UserWithHash(**user_data.model_dump(), hashed_password=hashed_password)
    user = await User.create_user(session, user_data)
    return UserOutput.model_validate(user)


@router.get('/users/me/')
async def read_users_me(request: Request, token: Annotated[str, Depends(oauth2_scheme)]) -> UserOutput:
    current_user = request.user
    if current_user.disabled:
        raise UserInactiveException
    return current_user
