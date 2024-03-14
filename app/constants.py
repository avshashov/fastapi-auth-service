from enum import Enum


class TokenType(str, Enum):
    ACCESS = 'access_token'
    REFRESH = 'refresh_token'
    BEARER = 'bearer'


class UserRole(str, Enum):
    ADMIN = 'admin'
    USER = 'user'


PathsWithoutAuthHeaders = (
    '/auth/login',
    '/auth/refresh',
    '/user/signup',
    '/docs',
    '/openapi.json',
)
