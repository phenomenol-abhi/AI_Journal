import asyncio
from urllib.parse import parse_qs

from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        token = parse_qs(scope.get("query_string", b"").decode()).get("token", [None])[0]
        scope["user"] = AnonymousUser()
        if token:
            try:
                validated = JWTAuthentication().get_validated_token(token)
                scope["user"] = await asyncio.to_thread(
                    JWTAuthentication().get_user, validated
                )
            except Exception:
                pass
        return await super().__call__(scope, receive, send)
