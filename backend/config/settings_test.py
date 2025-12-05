"""
Test settings - override Redis cache with dummy cache for tests
"""
from .settings import *

# Override cache to use dummy backend for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Use a test-specific secret key
SECRET_KEY = 'test-secret-key-for-pytest-do-not-use-in-production'
