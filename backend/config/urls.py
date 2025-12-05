"""
URL configuration for TikTok Manager project.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI

# Initialize Django Ninja API
api = NinjaAPI(
    title="TikTok Manager API",
    version="1.0.0",
    description="Multi-account TikTok management and scheduling API",
    docs_url="/docs"
)

# Register API routers
from apps.tiktok_accounts.api.tiktok_oauth_api import router as tiktok_oauth_router
from api.auth.router import router as auth_router
from api.accounts.router import router as accounts_router

api.add_router("/tiktok/oauth/", tiktok_oauth_router, tags=["TikTok OAuth"])
api.add_router("/auth/", auth_router, tags=["Authentication"])
api.add_router("/accounts/", accounts_router, tags=["TikTok Accounts"])

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/v1/", api.urls),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
