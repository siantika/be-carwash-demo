from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp: Response = await call_next(request)

        # Fix ZAP: MIME sniffing
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")

        # Fix ZAP: Spectre/site-isolation
        resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        return resp
