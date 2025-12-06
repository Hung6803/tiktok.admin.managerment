"""
Analytics router for API endpoints
"""
from ninja import Router, Query
from typing import Optional
from datetime import datetime, date
from django.core.cache import cache
import logging

from api.auth.middleware import JWTAuth
from apps.tiktok_accounts.models import TikTokAccount
from apps.content.models import ScheduledPost, PublishHistory
from .schemas import (
    AccountMetricsOut, PostAnalyticsOut,
    TimeSeriesOut, BestTimesOut,
    DashboardOut, ComparisonOut
)
from .services import AnalyticsService

logger = logging.getLogger(__name__)
router = Router()
auth = JWTAuth()


@router.get("/accounts/{account_id}/metrics", response=AccountMetricsOut, auth=auth)
def get_account_metrics(request, account_id: str):
    """
    Get account performance metrics

    Returns comprehensive metrics including followers, engagement, and growth.
    """
    # Verify account ownership
    try:
        account = TikTokAccount.objects.get(
            id=account_id,
            user=request.auth,
            is_deleted=False
        )
    except TikTokAccount.DoesNotExist:
        return router.api.create_response(
            request,
            {"detail": "Account not found or access denied"},
            status=404
        )

    service = AnalyticsService()

    try:
        metrics = service.get_account_metrics(account_id)
        return metrics
    except ValueError as e:
        return router.api.create_response(
            request,
            {"detail": "Invalid request"},
            status=400
        )
    except Exception as e:
        logger.error(f"Failed to get account metrics for user {request.auth.id}: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": "Failed to retrieve metrics"},
            status=500
        )


@router.get("/accounts/{account_id}/timeseries", response=TimeSeriesOut, auth=auth)
def get_time_series(
    request,
    account_id: str,
    metric: str = Query(..., description="Metric type (follower_count, total_likes, etc.)"),
    period: str = Query("month", description="Time period (day, week, month, quarter, year)"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Get time series data for specific metric

    Supports multiple metrics and time periods with trend analysis.
    """
    # Verify account ownership
    try:
        account = TikTokAccount.objects.get(
            id=account_id,
            user=request.auth,
            is_deleted=False
        )
    except TikTokAccount.DoesNotExist:
        return router.api.create_response(
            request,
            {"detail": "Account not found or access denied"},
            status=404
        )

    service = AnalyticsService()

    try:
        data = service.get_time_series_data(
            account_id, metric, period, start_date, end_date
        )
        return data
    except ValueError as e:
        return router.api.create_response(
            request,
            {"detail": "Invalid request parameters"},
            status=400
        )
    except Exception as e:
        logger.error(f"Failed to get time series for user {request.auth.id}: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": "Failed to retrieve time series"},
            status=500
        )


@router.get("/posts/{post_id}", response=PostAnalyticsOut, auth=auth)
def get_post_analytics(request, post_id: str):
    """
    Get analytics for specific post

    Returns views, engagement, and viral score.
    """
    service = AnalyticsService()

    try:
        analytics = service.get_post_analytics(post_id)
        return analytics
    except ValueError as e:
        return router.api.create_response(
            request,
            {"detail": str(e)},
            status=404
        )
    except Exception as e:
        logger.error(f"Failed to get post analytics: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": "Failed to retrieve post analytics"},
            status=500
        )


@router.get("/insights/best-times", response=BestTimesOut, auth=auth)
def get_best_posting_times(request):
    """
    Get optimal posting times based on engagement

    Analyzes historical data to recommend best hours, days, and frequency.
    """
    service = AnalyticsService()

    try:
        best_times = service.get_best_posting_times(str(request.auth.id))
        return best_times
    except Exception as e:
        logger.error(f"Failed to get best posting times: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": "Failed to retrieve posting insights"},
            status=500
        )


@router.get("/dashboard", response=DashboardOut, auth=auth)
def get_analytics_dashboard(request, account_id: Optional[str] = None):
    """
    Get comprehensive analytics dashboard

    Returns summary metrics, recent posts, trends, and upcoming schedule.
    """
    service = AnalyticsService()

    try:
        # Get primary account if not specified
        if not account_id:
            account = TikTokAccount.objects.filter(
                user=request.auth,
                is_deleted=False
            ).first()
            if not account:
                return router.api.create_response(
                    request,
                    {"detail": "No TikTok accounts found"},
                    status=404
                )
            account_id = str(account.id)

        # Get summary metrics
        summary = service.get_account_metrics(account_id)

        # Get recent posts with prefetched publish history to avoid N+1
        recent_posts = ScheduledPost.objects.filter(
            accounts__id=account_id,
            status='published'
        ).prefetch_related(
            'publish_history',
            'publish_history__account'
        ).order_by('-published_at')[:5]

        recent_analytics = []
        for post in recent_posts:
            try:
                analytics = service.get_post_analytics(str(post.id))
                recent_analytics.append(analytics)
            except Exception as e:
                logger.warning(f"Failed to get analytics for post {post.id}: {str(e)}")
                continue

        # Get trends
        growth_trend = service.get_time_series_data(
            account_id, 'follower_count', 'month'
        )
        engagement_trend = service.get_time_series_data(
            account_id, 'total_likes', 'month'
        )

        # Get top posts with optimized query
        top_posts_query = PublishHistory.objects.filter(
            post__accounts__id=account_id,
            status='success',
            views__isnull=False
        ).select_related('post', 'account').prefetch_related(
            'post__publish_history'
        ).order_by('-views')[:5]

        top_posts = []
        seen_posts = set()
        for history in top_posts_query:
            # Avoid duplicate posts
            if history.post_id in seen_posts:
                continue
            seen_posts.add(history.post_id)

            try:
                analytics = service.get_post_analytics(str(history.post_id))
                top_posts.append(analytics)
            except Exception as e:
                logger.warning(f"Failed to get analytics for post {history.post_id}: {str(e)}")
                continue

        # Get upcoming schedule
        upcoming = ScheduledPost.objects.filter(
            accounts__id=account_id,
            status='scheduled'
        ).order_by('scheduled_time')[:5]

        upcoming_schedule = [
            {
                'id': str(post.id),
                'title': post.title,
                'scheduled_time': post.scheduled_time
            }
            for post in upcoming
        ]

        return DashboardOut(
            summary=summary,
            recent_posts=recent_analytics,
            growth_trend=growth_trend,
            engagement_trend=engagement_trend,
            top_posts=top_posts,
            upcoming_schedule=upcoming_schedule
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": f"Failed to retrieve dashboard: {str(e)}"},
            status=500
        )


@router.get("/compare", response=ComparisonOut, auth=auth)
def compare_accounts(
    request,
    account_1: str = Query(..., description="First account ID"),
    account_2: str = Query(..., description="Second account ID")
):
    """
    Compare metrics between two accounts

    Returns side-by-side comparison with differences and percentages.
    """
    # Verify both accounts belong to user
    try:
        acc1 = TikTokAccount.objects.get(
            id=account_1,
            user=request.auth,
            is_deleted=False
        )
        acc2 = TikTokAccount.objects.get(
            id=account_2,
            user=request.auth,
            is_deleted=False
        )
    except TikTokAccount.DoesNotExist:
        return router.api.create_response(
            request,
            {"detail": "One or both accounts not found or access denied"},
            status=404
        )

    service = AnalyticsService()

    try:
        metrics_1 = service.get_account_metrics(account_1)
        metrics_2 = service.get_account_metrics(account_2)

        comparison = {}
        for key in metrics_1:
            if isinstance(metrics_1[key], (int, float)) and not isinstance(metrics_1[key], bool):
                val1 = float(metrics_1[key])
                val2 = float(metrics_2[key])
                diff = val2 - val1
                percentage = (diff / val1 * 100) if val1 != 0 else 0
                comparison[key] = {
                    'difference': round(diff, 2),
                    'percentage': round(percentage, 2)
                }

        return ComparisonOut(
            account_1=metrics_1,
            account_2=metrics_2,
            comparison=comparison
        )

    except ValueError as e:
        return router.api.create_response(
            request,
            {"detail": str(e)},
            status=404
        )
    except Exception as e:
        logger.error(f"Failed to compare accounts: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": "Failed to compare accounts"},
            status=500
        )


@router.post("/refresh/{account_id}", auth=auth)
def refresh_analytics(request, account_id: str):
    """
    Force refresh analytics from cache

    Clears cache and fetches fresh data.
    """
    service = AnalyticsService()

    try:
        # Clear cache
        service.clear_cache(account_id)

        # Fetch fresh data
        metrics = service.get_account_metrics(account_id, use_cache=False)

        return {
            "success": True,
            "message": "Analytics refreshed successfully",
            "metrics": metrics
        }

    except ValueError as e:
        return router.api.create_response(
            request,
            {"detail": str(e)},
            status=404
        )
    except Exception as e:
        logger.error(f"Failed to refresh analytics: {str(e)}")
        return router.api.create_response(
            request,
            {"detail": "Failed to refresh analytics"},
            status=500
        )


@router.get("/export", auth=auth)
def export_analytics(
    request,
    format: str = Query("csv", regex="^(csv|json)$"),
    account_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Export analytics data

    Supports CSV and JSON formats.
    """
    # TODO: Implement data export functionality
    return router.api.create_response(
        request,
        {"detail": "Export functionality not yet implemented"},
        status=501
    )
