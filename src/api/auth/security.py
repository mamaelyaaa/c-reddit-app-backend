from authx import AuthX, AuthXConfig

from core import settings

config = AuthXConfig(
    JWT_ALGORITHM=settings.jwt.algorithm,
    JWT_SECRET_KEY=settings.jwt.secret_key,
    JWT_ACCESS_TOKEN_EXPIRES=settings.jwt.access_expires,
    JWT_REFRESH_TOKEN_EXPIRES=settings.jwt.refresh_expires,
    JWT_COOKIE_MAX_AGE=settings.jwt.cookie_max_age,
    JWT_COOKIE_HTTP_ONLY=settings.jwt.cookie_http_only,
    JWT_COOKIE_SECURE=settings.jwt.cookie_secure,
    JWT_COOKIE_SAMESITE=settings.jwt.cookie_samesite,
    JWT_SESSION_COOKIE=settings.jwt.cookie_session,
)

security: AuthX = AuthX(config=config)
