"""
Authentication API router
Handles user registration, login, token refresh, and profile
"""
from ninja import Router
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from django.http import HttpRequest
from apps.accounts.models import User
from .schemas import RegisterIn, LoginIn, RefreshIn, LogoutIn, TokenOut, UserOut, ErrorOut
from .jwt_handler import JWTHandler
from .middleware import JWTAuth

router = Router()
jwt_auth = JWTAuth()


@router.post("/register", response={200: TokenOut, 400: ErrorOut}, tags=["Authentication"])
def register(request: HttpRequest, data: RegisterIn):
    """
    Register a new user

    Returns JWT access and refresh tokens on success
    """
    # Check if email already exists
    if User.objects.filter(email=data.email, is_deleted=False).exists():
        return 400, {"detail": "Email already registered"}

    # Create user
    user = User.objects.create(
        email=data.email,
        username=data.username or data.email.split('@')[0],
        password=make_password(data.password)
    )

    # Generate tokens
    handler = JWTHandler()
    tokens = handler.generate_tokens(user.id)
    return 200, tokens


@router.post("/login", response={200: TokenOut, 401: ErrorOut, 429: ErrorOut}, tags=["Authentication"])
def login(request: HttpRequest, data: LoginIn):
    """
    Login with email and password

    Returns JWT access and refresh tokens on success
    Rate limited to 5 attempts per minute per email
    """
    # Rate limiting check
    cache_key = f"login_attempts:{data.email}"
    attempts = cache.get(cache_key, 0)

    if attempts >= 5:
        return 429, {"detail": "Too many login attempts. Try again in 1 minute"}

    # Authenticate user
    try:
        user = User.objects.get(email=data.email, is_deleted=False)
        if not check_password(data.password, user.password):
            # Increment failed attempts
            cache.set(cache_key, attempts + 1, 60)  # 60 seconds TTL
            raise ValueError("Invalid credentials")
    except (User.DoesNotExist, ValueError):
        return 401, {"detail": "Invalid email or password"}

    # Clear rate limit on successful login
    cache.delete(cache_key)

    # Generate tokens
    handler = JWTHandler()
    tokens = handler.generate_tokens(user.id)
    return 200, tokens


@router.post("/refresh", response={200: TokenOut, 401: ErrorOut}, tags=["Authentication"])
def refresh_token(request: HttpRequest, data: RefreshIn):
    """
    Refresh access token using refresh token

    Returns new access token (refresh token remains unchanged)
    """
    handler = JWTHandler()
    payload = handler.decode_token(data.refresh_token)

    # Validate refresh token
    if not payload:
        return 401, {"detail": "Invalid or expired refresh token"}

    if payload.get('type') != 'refresh':
        return 401, {"detail": "Token is not a refresh token"}

    # Verify user exists
    user_id = payload.get('user_id')
    try:
        User.objects.get(id=user_id, is_deleted=False)
    except User.DoesNotExist:
        return 401, {"detail": "User not found"}

    # Generate new tokens
    new_tokens = handler.generate_tokens(user_id)
    return 200, new_tokens


@router.get("/me", response={200: UserOut, 401: ErrorOut}, auth=jwt_auth, tags=["Authentication"])
def get_current_user(request: HttpRequest):
    """
    Get current authenticated user profile

    Requires Bearer token authentication
    """
    if not request.auth:
        return 401, {"detail": "Authentication required"}

    return 200, request.auth


@router.post("/logout", response={200: dict, 401: ErrorOut}, tags=["Authentication"], auth=jwt_auth)
def logout(request: HttpRequest, data: LogoutIn):
    """
    Logout user and invalidate tokens

    Blacklists the access token and optionally the refresh token
    Requires Bearer token authentication
    """
    if not request.auth:
        return 401, {"detail": "Authentication required"}

    handler = JWTHandler()

    # Get access token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        access_token = auth_header.replace('Bearer ', '')
        handler.blacklist_token(access_token)

    # Blacklist refresh token if provided
    if data.refresh_token:
        handler.blacklist_token(data.refresh_token)

    return 200, {"detail": "Successfully logged out"}
