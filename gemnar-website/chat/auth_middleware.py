from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from channels.auth import AuthMiddlewareStack
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    """Get user from token key."""
    try:
        token = Token.objects.select_related("user").get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom middleware that adds token authentication to existing session auth.
    This runs after AuthMiddleware has set up session-based authentication.
    """

    async def __call__(self, scope, receive, send):
        # Only process WebSocket connections
        if scope["type"] != "websocket":
            return await super().__call__(scope, receive, send)

        # Check if we already have an authenticated user from session
        current_user = scope.get("user", AnonymousUser())

        is_authenticated = (
            hasattr(current_user, "is_authenticated") and current_user.is_authenticated
        )
        logger.info(
            f"WebSocket auth check - user: {current_user}, "
            f"is_authenticated: {is_authenticated}"
        )

        # If session auth succeeded, use that and don't modify anything
        if current_user and is_authenticated:
            logger.info(f"WebSocket session auth: {current_user.username}")
            return await super().__call__(scope, receive, send)

        # Try token auth from query string (fallback if session auth failed)
        query_string = scope.get("query_string", b"").decode("utf-8")
        token_key = None
        
        # Parse query string for token parameter
        if "token=" in query_string:
            for param in query_string.split("&"):
                if param.startswith("token="):
                    token_key = param.split("=", 1)[1]
                    break
        
        # Also check headers (for backward compatibility)
        if not token_key:
            headers = dict(scope["headers"])
            auth_header = headers.get(b"authorization", b"").decode("utf-8")
            if auth_header.startswith("Token "):
                token_key = auth_header[6:]  # Remove 'Token ' prefix

        if token_key:
            token_preview = token_key[:10]
            logger.info(f"WebSocket token auth attempt: {token_preview}...")

            user = await get_user_from_token(token_key)

            user_is_authenticated = (
                hasattr(user, "is_authenticated") and user.is_authenticated
            )
            if user and user_is_authenticated:
                logger.info(f"WebSocket token auth success: {user.username}")
                scope["user"] = user
            else:
                logger.warning(f"WebSocket token auth failed: {token_preview}")
                # Don't modify scope["user"] - leave as is from session auth
        else:
            logger.warning("WebSocket: No token found in query or headers, using session result")
            # Don't modify scope["user"] - leave it as is from session auth

        return await super().__call__(scope, receive, send)


def HybridAuthMiddlewareStack(inner):
    """
    Middleware stack that provides both session and token authentication.
    Uses Django's built-in AuthMiddlewareStack for session auth,
    then adds token auth support.
    """
    # AuthMiddlewareStack already includes Cookie and Session middleware
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
