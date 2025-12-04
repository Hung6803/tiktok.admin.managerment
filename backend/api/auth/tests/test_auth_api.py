"""
Integration tests for authentication API endpoints
"""
import pytest
from django.test import Client
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from apps.accounts.models import User
from api.auth.jwt_handler import JWTHandler


@pytest.fixture
def api_client():
    """Django test client"""
    return Client()


@pytest.fixture
def test_user(db):
    """Create test user"""
    return User.objects.create(
        email='test@example.com',
        username='testuser',
        password=make_password('Test123!@#')
    )


@pytest.fixture
def auth_headers(test_user):
    """Generate auth headers with valid token"""
    handler = JWTHandler()
    tokens = handler.generate_tokens(test_user.id)
    return {'HTTP_AUTHORIZATION': f'Bearer {tokens["access_token"]}'}


@pytest.mark.django_db
class TestRegisterEndpoint:
    """Test user registration endpoint"""

    def setup_method(self):
        """Clear cache before each test"""
        cache.clear()

    def test_register_new_user_success(self, api_client):
        """Test successful user registration"""
        response = api_client.post(
            '/api/v1/auth/register',
            data={
                'email': 'new@example.com',
                'password': 'SecurePass123!',
                'username': 'newuser'
            },
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'Bearer'

        # Verify user created
        user = User.objects.get(email='new@example.com')
        assert user.username == 'newuser'

    def test_register_without_username(self, api_client):
        """Test registration uses email prefix as username"""
        response = api_client.post(
            '/api/v1/auth/register',
            data={
                'email': 'john@example.com',
                'password': 'SecurePass123!'
            },
            content_type='application/json'
        )

        assert response.status_code == 200
        user = User.objects.get(email='john@example.com')
        assert user.username == 'john'

    def test_register_duplicate_email(self, api_client, test_user):
        """Test registration with existing email fails"""
        response = api_client.post(
            '/api/v1/auth/register',
            data={
                'email': test_user.email,
                'password': 'NewPassword123!'
            },
            content_type='application/json'
        )

        assert response.status_code == 400
        assert 'already registered' in response.json()['detail'].lower()

    def test_register_weak_password(self, api_client):
        """Test registration with weak password fails"""
        response = api_client.post(
            '/api/v1/auth/register',
            data={
                'email': 'weak@example.com',
                'password': 'short'
            },
            content_type='application/json'
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.django_db
class TestLoginEndpoint:
    """Test user login endpoint"""

    def setup_method(self):
        """Clear cache before each test"""
        cache.clear()

    def test_login_valid_credentials(self, api_client, test_user):
        """Test login with valid credentials"""
        response = api_client.post(
            '/api/v1/auth/login',
            data={
                'email': test_user.email,
                'password': 'Test123!@#'
            },
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data

    def test_login_invalid_email(self, api_client):
        """Test login with non-existent email"""
        response = api_client.post(
            '/api/v1/auth/login',
            data={
                'email': 'nonexistent@example.com',
                'password': 'anypassword'
            },
            content_type='application/json'
        )

        assert response.status_code == 401
        assert 'invalid' in response.json()['detail'].lower()

    def test_login_wrong_password(self, api_client, test_user):
        """Test login with wrong password"""
        response = api_client.post(
            '/api/v1/auth/login',
            data={
                'email': test_user.email,
                'password': 'WrongPassword123'
            },
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_login_rate_limiting(self, api_client, test_user):
        """Test rate limiting after failed attempts"""
        # Make 5 failed attempts
        for _ in range(5):
            api_client.post(
                '/api/v1/auth/login',
                data={
                    'email': test_user.email,
                    'password': 'WrongPassword'
                },
                content_type='application/json'
            )

        # 6th attempt should be rate limited
        response = api_client.post(
            '/api/v1/auth/login',
            data={
                'email': test_user.email,
                'password': 'WrongPassword'
            },
            content_type='application/json'
        )

        assert response.status_code == 429
        assert 'too many' in response.json()['detail'].lower()


@pytest.mark.django_db
class TestRefreshEndpoint:
    """Test token refresh endpoint"""

    def test_refresh_valid_token(self, api_client, test_user):
        """Test refreshing with valid refresh token"""
        handler = JWTHandler()
        tokens = handler.generate_tokens(test_user.id)

        response = api_client.post(
            '/api/v1/auth/refresh',
            data={'refresh_token': tokens['refresh_token']},
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        # Verify token is valid by decoding
        payload = handler.decode_token(data['access_token'])
        assert payload['user_id'] == str(test_user.id)

    def test_refresh_invalid_token(self, api_client):
        """Test refresh with invalid token"""
        response = api_client.post(
            '/api/v1/auth/refresh',
            data={'refresh_token': 'invalid.token.here'},
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_refresh_with_access_token_fails(self, api_client, test_user):
        """Test refresh with access token instead of refresh token"""
        handler = JWTHandler()
        tokens = handler.generate_tokens(test_user.id)

        response = api_client.post(
            '/api/v1/auth/refresh',
            data={'refresh_token': tokens['access_token']},  # Wrong type
            content_type='application/json'
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestMeEndpoint:
    """Test current user profile endpoint"""

    def test_me_with_valid_token(self, api_client, test_user, auth_headers):
        """Test getting current user with valid token"""
        response = api_client.get(
            '/api/v1/auth/me',
            **auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # UUID is serialized to string in JSON response
        assert data['id'] == str(test_user.id)
        assert data['email'] == test_user.email
        assert data['username'] == test_user.username
        # Datetime is serialized to ISO format string
        assert 'created_at' in data

    def test_me_without_token(self, api_client):
        """Test /me endpoint without token"""
        response = api_client.get('/api/v1/auth/me')

        assert response.status_code == 401

    def test_me_with_invalid_token(self, api_client):
        """Test /me endpoint with invalid token"""
        response = api_client.get(
            '/api/v1/auth/me',
            HTTP_AUTHORIZATION='Bearer invalid.token'
        )

        assert response.status_code == 401
