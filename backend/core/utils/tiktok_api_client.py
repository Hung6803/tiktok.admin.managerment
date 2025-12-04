"""
TikTok API HTTP client with retry logic and error handling
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional
import logging
from config.tiktok_config import TikTokConfig

logger = logging.getLogger(__name__)


class TikTokAPIClient:
    """
    HTTP client for TikTok API with automatic retry logic
    Handles authentication, rate limiting, and error responses
    """

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize API client

        Args:
            access_token: OAuth access token (decrypted)
        """
        self.access_token = access_token
        self.config = TikTokConfig()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry strategy

        Returns:
            Configured requests Session
        """
        session = requests.Session()

        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=self.config.MAX_RETRIES,
            backoff_factor=self.config.RETRY_BACKOFF_FACTOR,
            status_forcelist=self.config.RETRY_STATUS_CODES,
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            raise_on_status=False
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with authentication

        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            'Content-Type': 'application/json',
        }

        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'

        return headers

    def get(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute GET request

        Args:
            url: Request URL
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            requests.exceptions.RequestException: On request failure
        """
        try:
            logger.info(f"GET request to: {url}")
            response = self.session.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            logger.info(f"GET request successful: {url}")
            return data

        except requests.exceptions.HTTPError as e:
            # Redact token endpoint responses
            if 'oauth/token' in url or 'oauth/access_token' in url:
                logger.error(f"HTTP error for GET {url}: {e.response.status_code} - [RESPONSE REDACTED - TOKEN ENDPOINT]")
            else:
                logger.error(f"HTTP error for GET {url}: {e.response.status_code} - {e.response.text}")
            raise

        except requests.exceptions.Timeout:
            logger.error(f"Timeout for GET {url}")
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for GET {url}: {str(e)}")
            raise

    def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        files: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute POST request

        Args:
            url: Request URL
            data: Form data
            json: JSON payload
            files: File uploads
            timeout: Custom timeout in seconds

        Returns:
            Response JSON data

        Raises:
            requests.exceptions.RequestException: On request failure
        """
        try:
            logger.info(f"POST request to: {url}")

            headers = self._get_headers()
            # Remove Content-Type for multipart/form-data (auto-set by requests)
            if files:
                headers.pop('Content-Type', None)

            timeout = timeout or self.config.REQUEST_TIMEOUT

            response = self.session.post(
                url,
                headers=headers,
                data=data,
                json=json,
                files=files,
                timeout=timeout
            )

            response.raise_for_status()
            data = response.json()

            logger.info(f"POST request successful: {url}")
            return data

        except requests.exceptions.HTTPError as e:
            # Redact token endpoint responses
            if 'oauth/token' in url or 'oauth/access_token' in url:
                logger.error(f"HTTP error for POST {url}: {e.response.status_code} - [RESPONSE REDACTED - TOKEN ENDPOINT]")
            else:
                logger.error(f"HTTP error for POST {url}: {e.response.status_code} - {e.response.text}")
            raise

        except requests.exceptions.Timeout:
            logger.error(f"Timeout for POST {url}")
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for POST {url}: {str(e)}")
            raise

    def put(self, url: str, data=None, timeout: Optional[int] = None) -> bool:
        """
        Execute PUT request (typically for file uploads)

        Supports both in-memory bytes and file-like objects for streaming.
        When passing a file object, requests will automatically stream it
        without loading the entire file into memory.

        Args:
            url: Upload URL
            data: Binary data (bytes) or file-like object to upload
            timeout: Custom timeout in seconds

        Returns:
            True if upload successful

        Raises:
            requests.exceptions.RequestException: On upload failure
        """
        try:
            logger.info(f"PUT request to: {url}")

            timeout = timeout or self.config.UPLOAD_TIMEOUT

            response = self.session.put(
                url,
                data=data,
                headers={'Content-Type': 'application/octet-stream'},
                timeout=timeout
            )

            response.raise_for_status()
            logger.info(f"PUT request successful: {url}")
            return True

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for PUT {url}: {e.response.status_code}")
            raise

        except requests.exceptions.Timeout:
            logger.error(f"Timeout for PUT {url}")
            raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for PUT {url}: {str(e)}")
            raise

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
