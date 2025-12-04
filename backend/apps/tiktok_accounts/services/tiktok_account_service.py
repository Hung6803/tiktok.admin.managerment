"""
TikTok account management service
Handles account info retrieval and management operations
"""
from typing import Dict, Any
import logging

from config.tiktok_config import TikTokConfig
from core.utils.tiktok_api_client import TikTokAPIClient

logger = logging.getLogger(__name__)


class TikTokAccountService:
    """
    TikTok account operations service
    Manages account information and video list retrieval
    """

    def __init__(self, access_token: str):
        """
        Initialize service with access token

        Args:
            access_token: Decrypted OAuth access token
        """
        self.config = TikTokConfig()
        self.client = TikTokAPIClient(access_token)

    def get_user_info(self) -> Dict[str, Any]:
        """
        Fetch TikTok user information

        Returns:
            Dictionary with user data:
            - open_id: TikTok user ID
            - union_id: Cross-app user ID
            - avatar_url: Profile picture URL
            - display_name: User display name
            - username: TikTok username

        Raises:
            requests.exceptions.RequestException: On API error
        """
        logger.info("Fetching user info from TikTok API")

        url = f"{self.config.API_BASE_URL}user/info/"
        params = {
            'fields': 'open_id,union_id,avatar_url,display_name,username'
        }

        try:
            response = self.client.get(url, params=params)
            user_data = response.get('data', {}).get('user', {})

            logger.info(f"Successfully fetched user info for: {user_data.get('username', 'unknown')}")

            return user_data

        except Exception as e:
            logger.error(f"Failed to fetch user info: {str(e)}")
            raise

    def get_user_videos(self, cursor: int = 0, max_count: int = 20) -> Dict[str, Any]:
        """
        Fetch user's video list

        Args:
            cursor: Pagination cursor
            max_count: Maximum videos to return (default 20)

        Returns:
            Dictionary with:
            - videos: List of video objects
            - cursor: Next page cursor
            - has_more: Whether more videos exist

        Raises:
            requests.exceptions.RequestException: On API error
        """
        logger.info(f"Fetching user videos (cursor={cursor}, max={max_count})")

        url = f"{self.config.API_BASE_URL}video/list/"
        params = {
            'fields': 'id,title,video_description,create_time,cover_image_url,share_url',
            'cursor': cursor,
            'max_count': min(max_count, 20),  # API limit
        }

        try:
            response = self.client.get(url, params=params)
            data = response.get('data', {})

            logger.info(f"Successfully fetched {len(data.get('videos', []))} videos")

            return data

        except Exception as e:
            logger.error(f"Failed to fetch user videos: {str(e)}")
            raise

    def close(self):
        """Close the API client"""
        self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
