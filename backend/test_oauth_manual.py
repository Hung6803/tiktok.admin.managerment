"""
Manual test script for TikTok OAuth endpoints
Run this to test the OAuth flow without actual TikTok integration
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tiktok_accounts.services import TikTokOAuthService


def test_authorization_url():
    """Test generating TikTok authorization URL"""
    print("\n=== Test 1: Generate Authorization URL ===")

    try:
        oauth_service = TikTokOAuthService()
        auth_data = oauth_service.get_authorization_url()

        print(f"✅ Authorization URL generated successfully!")
        print(f"URL: {auth_data['url']}")
        print(f"State: {auth_data['state']}")

        # Verify URL structure
        assert 'https://www.tiktok.com/v2/auth/authorize' in auth_data['url']
        assert 'client_key=' in auth_data['url']
        assert 'state=' in auth_data['url']
        assert 'scope=' in auth_data['url']

        print("✅ URL structure is valid")
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_state_validation():
    """Test state validation (CSRF protection)"""
    print("\n=== Test 2: State Validation ===")

    try:
        oauth_service = TikTokOAuthService()

        # Test valid state
        state = "test_state_123"
        assert oauth_service.validate_state(state, state) is True
        print("✅ Valid state accepted")

        # Test invalid state
        assert oauth_service.validate_state("different_state", state) is False
        print("✅ Invalid state rejected")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_environment_config():
    """Test that environment variables are configured"""
    print("\n=== Test 3: Environment Configuration ===")

    from django.conf import settings

    # Check TIKTOK_CLIENT_KEY
    client_key = getattr(settings, 'TIKTOK_CLIENT_KEY', None)
    if client_key and client_key != 'your_client_key_here':
        print(f"✅ TIKTOK_CLIENT_KEY is configured")
    else:
        print(f"⚠️  TIKTOK_CLIENT_KEY is not configured or using default value")
        print(f"   Current value: {client_key}")

    # Check TIKTOK_CLIENT_SECRET
    client_secret = getattr(settings, 'TIKTOK_CLIENT_SECRET', None)
    if client_secret and client_secret != 'your_client_secret_here':
        print(f"✅ TIKTOK_CLIENT_SECRET is configured")
    else:
        print(f"⚠️  TIKTOK_CLIENT_SECRET is not configured or using default value")

    # Check TIKTOK_REDIRECT_URI
    redirect_uri = getattr(settings, 'TIKTOK_REDIRECT_URI', None)
    if redirect_uri:
        print(f"✅ TIKTOK_REDIRECT_URI: {redirect_uri}")
    else:
        print(f"⚠️  TIKTOK_REDIRECT_URI is not configured")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("TikTok OAuth Manual Testing")
    print("=" * 60)

    results = {
        "Environment Config": test_environment_config(),
        "Authorization URL": test_authorization_url(),
        "State Validation": test_state_validation(),
    }

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed! Your OAuth setup is ready.")
        print("\nNext steps:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Access Swagger UI: http://127.0.0.1:8080/api/v1/docs")
        print("3. Create a user account and login")
        print("4. Test /api/v1/tiktok/oauth/authorize endpoint")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")


if __name__ == '__main__':
    main()
