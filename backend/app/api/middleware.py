from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.exceptions import AppError, UnauthorizedError
from app.infrastructure.logging import get_logger
from app.infrastructure.security import decode_access_token

logger = get_logger("middleware")


class AuthMiddleware(BaseHTTPMiddleware):
    """Enforce JWT authentication on all ``/api/`` routes except public endpoints.

    Defense-in-depth layer: ensures every non-public API request carries a valid
    JWT before reaching route handlers.  Even if a route handler omits
    ``require_permission()``, this middleware rejects unauthenticated access.

    Public endpoints (no JWT required):
    - ``POST /api/auth/login``
    - ``GET  /api/health``
    - ``/hooks/*`` (uses ``X-Source-Token``, separate auth mechanism)
    - ``/docs``, ``/redoc``, ``/openapi.json`` (OpenAPI UI)
    """

    _PUBLIC_PATHS: frozenset[str] = frozenset(
        {
            "/api/auth/login",
            "/api/health",
        }
    )

    _PUBLIC_PREFIXES: tuple[str, ...] = (
        "/hooks/",
        "/hooks",
        "/docs",
        "/redoc",
        "/openapi.json",
    )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        path = request.url.path.rstrip("/") or "/"

        if self._is_public(path):
            return await call_next(request)

        # Only enforce auth on /api/ routes
        if not path.startswith("/api"):
            return await call_next(request)

        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            logger.warning(
                "auth_missing",
                path=request.url.path,
                method=request.method,
            )
            return self._unauthorized_response("Authentication required")

        token = auth_header[7:]  # len("Bearer ") == 7
        try:
            payload = decode_access_token(token)
        except UnauthorizedError:
            logger.warning(
                "auth_invalid_token",
                path=request.url.path,
                method=request.method,
            )
            return self._unauthorized_response("Invalid or expired token")

        # Store decoded payload on request state for downstream access
        request.state.token_payload = payload

        return await call_next(request)

    def _is_public(self, path: str) -> bool:
        """Check whether *path* is a public endpoint that bypasses JWT auth."""
        if path in self._PUBLIC_PATHS:
            return True
        return any(path.startswith(prefix) for prefix in self._PUBLIC_PREFIXES)

    @staticmethod
    def _unauthorized_response(message: str) -> JSONResponse:
        """Build a 401 JSON response matching the standard error envelope."""
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": message,
                    "details": {},
                },
            },
        )


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches AppError subclasses and generic exceptions, returning a standard
    JSON error response per the contract format.

    AppError subtypes are mapped directly.  Unhandled exceptions become a 500
    with code ``INTERNAL_ERROR`` and no stack trace in the response body.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            return await call_next(request)
        except AppError as exc:
            logger.warning(
                "app_error",
                code=exc.code,
                message=exc.message,
                status_code=exc.status_code,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                    },
                },
            )
        except Exception as exc:
            logger.error(
                "unhandled_exception",
                exc_type=type(exc).__name__,
                path=request.url.path,
                error=str(exc),
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {},
                    },
                },
            )


def add_cors_middleware(app: FastAPI) -> None:
    """Add CORS middleware with origins driven by configuration."""
    from app.config import get_settings

    settings = get_settings()
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID", "X-Source-Token"],
    )
