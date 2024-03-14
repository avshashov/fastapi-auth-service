"""
Authentication service that implements the logic for working with jwt tokens.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.authentication import AuthenticationError

from app.database.models import RefreshSession, User, UserDevice
from app.database.settings import database
from app.errors import (
    IncorrectCredentialsException,
    SessionExpiredException,
    TokenValidationException,
    ValidateCredentialsException,
)
from app.schemas import TokenWithDeviceCreateInput, UserDeviceInput, UserWithMetaOutput
from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    PRIVATE_KEY,
    PUBLIC_KEY,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)


class AuthService:
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify password against an existing hash.
        """
        return AuthService.pwd_context.verify(password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Calculate hash for password.
        """
        return AuthService.pwd_context.hash(password)

    @staticmethod
    async def authenticate_user(session: AsyncSession, email: str, password: str) -> UserWithMetaOutput:
        """
        Authenticate the user using email and password.
        """
        user = await User.get_user_by_email(session, email)
        if not user:
            raise IncorrectCredentialsException
        if not AuthService.verify_password(password, user.hashed_password):
            raise IncorrectCredentialsException
        return UserWithMetaOutput.model_validate(user)

    @staticmethod
    async def get_current_active_user(token: str, session: AsyncSession) -> UserWithMetaOutput:
        """
        Get current user if active.
        """
        payload = AuthService._verify_and_decode_token(token)
        user = await User.get_user_by_user_id(session, user_id=payload.get('sub'))
        if not user:
            raise ValidateCredentialsException
        if user.disabled:
            raise HTTPException(status_code=400, detail='Inactive user')
        return UserWithMetaOutput.model_validate(user)

    @staticmethod
    async def create_token_pair(
            data: dict, session: AsyncSession, user_device: UserDeviceInput
    ) -> tuple[str, str, datetime]:
        """
        Create an access/refresh token pair.
        """
        access_token, _ = await AuthService._create_token(
            data=data, expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        refresh_token, expires_refresh_time = await AuthService._create_token(
            data=data,
            session=session,
            expires_minutes=REFRESH_TOKEN_EXPIRE_MINUTES,
            is_refresh_token=True,
            user_device=user_device,
        )
        return access_token, refresh_token, expires_refresh_time.replace(tzinfo=timezone.utc)

    @staticmethod
    async def validate_refresh_token(
            refresh_token: str, session: AsyncSession, user_device: UserDeviceInput
    ) -> bool:
        """
        Validate the refresh token.
        """
        payload = AuthService._verify_and_decode_token(token=refresh_token)
        jti = payload.get('jti')
        if not jti:
            raise TokenValidationException

        if datetime.fromtimestamp(int(payload.get('exp')), timezone.utc) <= datetime.now(timezone.utc):
            raise SessionExpiredException

        if payload.get('device_id') != user_device.device_id:
            raise TokenValidationException

        token_entity = await RefreshSession.get_token_by_jti(session, jti)
        if not token_entity:
            raise TokenValidationException

        if token_entity.revoked:
            raise TokenValidationException
        return True

    @staticmethod
    async def validate_access_token_and_get_user(request: Request) -> UserWithMetaOutput:
        """
        Validate the access token and get current user.
        """
        if 'Authorization' not in request.headers:
            raise AuthenticationError('No authorization header')

        auth = request.headers['Authorization']
        scheme, token = auth.split()
        if scheme.lower() != 'bearer':
            raise AuthenticationError('Unauthorized access')

        payload = AuthService._verify_and_decode_token(token=token)
        if payload.get('jti'):
            raise AuthenticationError('Invalid token')

        if datetime.fromtimestamp(int(payload.get('exp')), timezone.utc) <= datetime.now(timezone.utc):
            raise AuthenticationError('Session expired')

        user_id = payload.get('sub')
        user = None
        async for session in database.get_session():
            user = await User.get_user_by_user_id(session, user_id=user_id)
        if not user:
            raise AuthenticationError('Invalid token')

        return UserWithMetaOutput.model_validate(user)

    @staticmethod
    async def _create_token(
            data: dict,
            expires_minutes: int,
            session: AsyncSession = None,
            is_refresh_token: bool = False,
            user_device: UserDeviceInput = None,
    ) -> tuple[str, datetime]:
        to_encode = data.copy()
        expire = datetime.now() + timedelta(minutes=expires_minutes)
        to_encode.update({'exp': expire})

        if is_refresh_token:
            jti = str(uuid.uuid4())
            to_encode.update({'jti': jti})
            to_encode.update({'device_id': user_device.device_id})
            token_data = TokenWithDeviceCreateInput(
                user_id=to_encode['sub'], expires_at=expire, jti=jti, device=user_device
            )
            await RefreshSession.revoke_active_tokens_for_user(
                session, user_id=to_encode['sub'], device_id=user_device.device_id
            )
            await UserDevice.add_user_device_to_db(session, user_device)
            await RefreshSession.add_token_to_db(session, token_data)

        encoded_jwt = jwt.encode(claims=to_encode, key=PRIVATE_KEY, algorithm=ALGORITHM)
        return encoded_jwt, expire

    @staticmethod
    def _verify_and_decode_token(token: str) -> dict[str, str]:
        try:
            payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get('sub')
            if not user_id:
                raise ValidateCredentialsException
        except (ValueError, UnicodeDecodeError, JWTError) as exc:
            raise ValidateCredentialsException
        return payload
