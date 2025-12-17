"""
TikTok API configuration
Centralizes all TikTok API settings and constants
"""
from decouple import config


class TikTokConfig:
    """TikTok API configuration and constants"""

    # OAuth credentials
    CLIENT_KEY = config('TIKTOK_CLIENT_KEY', default='')
    CLIENT_SECRET = config('TIKTOK_CLIENT_SECRET', default='')
    REDIRECT_URI = config('TIKTOK_REDIRECT_URI', default='http://localhost:8000/api/v1/tiktok/oauth/callback')

    # API Mode: 'sandbox' uses Creator Inbox API (no review needed)
    #           'production' uses Direct Post API (requires app review)
    API_MODE = config('TIKTOK_API_MODE', default='sandbox')

    @classmethod
    def use_inbox_api(cls) -> bool:
        """
        Check if Creator Inbox API should be used (sandbox mode)

        - Sandbox: Uses post/publish/inbox/video/init/ (no app review required)
        - Production: Uses post/publish/video/init/ (requires video.publish scope + review)
        """
        return cls.API_MODE.lower() == 'sandbox'

    # API endpoints
    OAUTH_AUTHORIZE_URL = 'https://www.tiktok.com/v2/auth/authorize/'
    OAUTH_TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/'
    API_BASE_URL = 'https://open.tiktokapis.com/v2/'

    # API scopes (must match TikTok Developer Portal configuration)
    SCOPES = [
        'user.info.basic',       # Basic user information (open_id, avatar, display_name)
        'user.info.profile',     # Profile info (web_link, bio, is_verified)
        'user.info.stats',       # Stats (likes, followers, following, video count)
        'video.upload',          # Video upload permission (as draft)
        'video.publish',         # Direct video posting (required for direct post)
        'video.list',            # List user videos
    ]

    # TikTok Privacy Levels (API compatibility mapping)
    PRIVACY_LEVELS = {
        'public': 'PUBLIC_TO_EVERYONE',
        'friends': 'MUTUAL_FOLLOW_FRIENDS',
        'private': 'SELF_ONLY',
    }

    # Rate limiting (based on TikTok API research)
    RATE_LIMIT_PER_MINUTE = 6  # Per user access token
    RATE_LIMIT_UPLOADS_PER_DAY = 15  # Video uploads per 24 hours
    RATE_LIMIT_REQUESTS_PER_MINUTE_PER_ENDPOINT = 600

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 1s, 2s, 4s
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

    # Timeout settings
    REQUEST_TIMEOUT = 30  # seconds for normal requests
    UPLOAD_TIMEOUT = 300  # seconds for video uploads (5 minutes)

    # Video specifications (from research)
    MAX_VIDEO_SIZE_MB = 500  # Maximum for web uploads
    RECOMMENDED_VIDEO_FORMAT = 'MP4'
    RECOMMENDED_VIDEO_CODEC = 'H.264'
    RECOMMENDED_RESOLUTION = (1080, 1920)  # 9:16 aspect ratio
    MAX_CAPTION_LENGTH = 2200

    # Slideshow specifications
    SLIDESHOW_IMAGE_DURATION_MS = 4000  # 4 seconds per image
    SLIDESHOW_MIN_IMAGES = 2  # Minimum images required
    SLIDESHOW_MAX_IMAGES = 10  # Maximum images allowed
    SLIDESHOW_OUTPUT_FORMAT = 'mp4'  # Output video format
    SLIDESHOW_OUTPUT_CODEC = 'libx264'  # H.264 codec
    SLIDESHOW_OUTPUT_FPS = 30  # Output frame rate
    SLIDESHOW_MAX_DURATION_SEC = 60  # Max 60 seconds total

    @classmethod
    def get_scope_string(cls) -> str:
        """Get comma-separated scope string for OAuth"""
        # Allow override via environment variable for testing
        override_scopes = config('TIKTOK_SCOPES', default='')
        if override_scopes:
            return override_scopes
        return ','.join(cls.SCOPES)

    @classmethod
    def is_configured(cls) -> bool:
        """Check if TikTok API credentials are configured"""
        return bool(cls.CLIENT_KEY and cls.CLIENT_SECRET)

    @classmethod
    def get_api_privacy_level(cls, privacy: str) -> str:
        """Map internal privacy to TikTok API privacy level"""
        return cls.PRIVACY_LEVELS.get(privacy, 'PUBLIC_TO_EVERYONE')
