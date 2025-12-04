"""
JWT authentication middleware for Django Ninja
"""
from ninja.security import HttpBearer
from django.http import HttpRequest
from .jwt_handler import JWTHandler


class JWTAuth(HttpBearer):
    """
    HTTP Bearer authentication for Django Ninja
    Validates JWT tokens and attaches user to request
    """

    def authenticate(self, request: HttpRequest, token: str):
        """
        Authenticate request using JWT token

        Args:
            request: HTTP request object
            token: Bearer token from Authorization header

        Returns:
            User: Authenticated user object or None
        """
        user = JWTHandler.get_user_from_token(token)
        return user
