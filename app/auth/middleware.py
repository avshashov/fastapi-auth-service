from fastapi import Request
from starlette.authentication import AuthCredentials, AuthenticationBackend

from app.auth.service import AuthService
from app.constants import PathsWithoutAuthHeaders
from app.schemas import UserWithMetaOutput


class AuthBackend(AuthenticationBackend):
    """
    This is a custom auth backend class that will allow you to authenticate
    your request and return auth and user as a tuple
    """

    async def authenticate(self, request: Request) -> tuple[AuthCredentials, UserWithMetaOutput] | None:
        # запросы '/auth/login', '/user/signup' должны работать без токена
        if request.url.path in PathsWithoutAuthHeaders:
            return
        user = await AuthService.validate_access_token_and_get_user(request)
        return AuthCredentials(['authenticated']), user
