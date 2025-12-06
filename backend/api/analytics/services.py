"""
Analytics service for calculating and aggregating metrics
"""
from django.db.models import Sum, Avg, Count, Q, F, Max, Min
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
import logging

from apps.analytics.models import AccountAnalytics
from apps.content.models import PublishHistory, ScheduledPost
from apps.tiktok_accounts.models import TikTokAccount

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics calculations and aggregations"""

    CACHE_TTL = 3600  # 1 hour
    CACHE_PREFIX = "analytics"

    # Whitelist of allowed metrics to prevent SQL injection
    ALLOWED_METRICS = {
        'follower_count',
        'following_count',
        'video_count',
        'total_likes',
        'total_views',
        'total_shares',
        'total_comments',
        'follower_growth',
        'engagement_rate'
    }

    def get_account_metrics(self, account_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive account metrics

        Args:
            account_id: TikTok account ID
            use_cache: Whether to use cached data

        Returns:
            Dictionary with account metrics
        """
        cache_key = f"{self.CACHE_PREFIX}:account:{account_id}"

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for account metrics: {account_id}")
                return cached

        try:
            account = TikTokAccount.objects.select_related('user').get(
                id=account_id,
                is_deleted=False
            )

            # Get latest analytics
            analytics = AccountAnalytics.objects.filter(
                tiktok_account=account
            ).order_by('-date').first()

            if not analytics:
                logger.warning(f"No analytics found for account {account_id}")
                # Return default metrics
                return self._get_default_metrics(account)

            # Calculate growth metrics
            prev_analytics = AccountAnalytics.objects.filter(
                tiktok_account=account,
                date__lt=analytics.date
            ).order_by('-date').first()

            follower_growth = 0
            growth_rate = 0.0

            if prev_analytics:
                follower_growth = analytics.follower_count - prev_analytics.follower_count
                if prev_analytics.follower_count > 0:
                    growth_rate = (follower_growth / prev_analytics.follower_count) * 100

            # Calculate engagement rate
            total_engagement = (
                analytics.total_likes +
                analytics.total_comments +
                analytics.total_shares
            )
            engagement_rate = 0.0
            if analytics.follower_count > 0:
                engagement_rate = (total_engagement / analytics.follower_count) * 100

            # Calculate averages
            avg_views_per_video = 0
            avg_engagement_per_video = 0.0

            if analytics.video_count > 0:
                avg_views_per_video = analytics.total_views // analytics.video_count
                avg_engagement_per_video = total_engagement / analytics.video_count

            metrics = {
                'account_id': str(account.id),
                'username': account.username,
                'total_followers': analytics.follower_count,
                'total_following': analytics.following_count,
                'total_videos': analytics.video_count,
                'total_likes': analytics.total_likes,
                'engagement_rate': round(float(engagement_rate), 2),
                'follower_growth': follower_growth,
                'growth_rate': round(float(growth_rate), 2),
                'avg_views_per_video': avg_views_per_video,
                'avg_engagement_per_video': round(float(avg_engagement_per_video), 2),
                'last_updated': analytics.date if isinstance(analytics.date, datetime) else datetime.combine(analytics.date, datetime.min.time())
            }

            cache.set(cache_key, metrics, self.CACHE_TTL)
            logger.info(f"Calculated metrics for account {account_id}")

            return metrics

        except TikTokAccount.DoesNotExist:
            logger.error(f"Account not found: {account_id}")
            raise ValueError(f"Account {account_id} not found")
        except Exception as e:
            logger.error(f"Failed to get account metrics: {str(e)}")
            raise

    def get_time_series_data(
        self,
        account_id: str,
        metric: str,
        period: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get time series data for specific metric

        Args:
            account_id: TikTok account ID
            metric: Metric name (e.g., 'follower_count', 'total_likes')
            period: Time period ('day', 'week', 'month', etc.)
            start_date: Start date for query
            end_date: End date for query

        Returns:
            Dictionary with time series data

        Raises:
            ValueError: If metric not in whitelist
        """
        # Validate metric against whitelist to prevent SQL injection
        if metric not in self.ALLOWED_METRICS:
            raise ValueError(f"Invalid metric: {metric}. Allowed: {', '.join(self.ALLOWED_METRICS)}")

        cache_key = f"{self.CACHE_PREFIX}:timeseries:{account_id}:{metric}:{period}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        if not end_date:
            end_date = date.today()

        if not start_date:
            if period == 'day':
                start_date = end_date - timedelta(days=1)
            elif period == 'week':
                start_date = end_date - timedelta(weeks=1)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'quarter':
                start_date = end_date - timedelta(days=90)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)

        # Query analytics data
        analytics_data = AccountAnalytics.objects.filter(
            tiktok_account_id=account_id,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        # Prepare data points
        data_points = []
        values = []

        for analytics in analytics_data:
            value = float(getattr(analytics, metric, 0))
            values.append(value)
            data_points.append({
                'timestamp': datetime.combine(analytics.date, datetime.min.time()) if isinstance(analytics.date, date) else analytics.date,
                'value': value,
                'label': None
            })

        # Calculate statistics
        if values:
            total = sum(values)
            average = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)

            # Determine trend
            if len(values) > 1:
                # Simple linear trend
                first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
                second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

                if second_half_avg > first_half_avg * 1.05:  # 5% threshold
                    trend = 'up'
                elif second_half_avg < first_half_avg * 0.95:
                    trend = 'down'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
        else:
            total = average = min_value = max_value = 0.0
            trend = 'stable'

        result = {
            'metric': metric,
            'period': period,
            'data': data_points,
            'total': total,
            'average': round(average, 2),
            'min_value': min_value,
            'max_value': max_value,
            'trend': trend
        }

        cache.set(cache_key, result, 1800)  # 30 minutes TTL
        return result

    def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """
        Get analytics for specific post

        Args:
            post_id: Post ID

        Returns:
            Dictionary with post analytics
        """
        try:
            post = ScheduledPost.objects.get(id=post_id)
            publish_history = PublishHistory.objects.filter(
                post=post,
                status='success'
            )

            # Aggregate metrics across all accounts
            aggregates = publish_history.aggregate(
                total_views=Sum('views'),
                total_likes=Sum('likes'),
                total_comments=Sum('comments'),
                total_shares=Sum('shares')
            )

            total_views = aggregates['total_views'] or 0
            total_likes = aggregates['total_likes'] or 0
            total_comments = aggregates['total_comments'] or 0
            total_shares = aggregates['total_shares'] or 0

            total_engagement = total_likes + total_comments + total_shares
            engagement_rate = 0.0
            if total_views > 0:
                engagement_rate = (total_engagement / total_views) * 100

            # Calculate viral score
            viral_score = self._calculate_viral_score(
                total_views, total_engagement, publish_history.count()
            )

            return {
                'post_id': str(post.id),
                'title': post.title,
                'published_at': post.published_at,
                'views': total_views,
                'likes': total_likes,
                'comments': total_comments,
                'shares': total_shares,
                'saves': 0,  # Not available yet
                'completion_rate': 0.0,  # Not available yet
                'engagement_rate': round(engagement_rate, 2),
                'viral_score': round(viral_score, 2)
            }

        except ScheduledPost.DoesNotExist:
            logger.error(f"Post not found: {post_id}")
            raise ValueError(f"Post {post_id} not found")

    def get_best_posting_times(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze best times to post based on engagement

        Args:
            user_id: User ID

        Returns:
            Dictionary with best posting times
        """
        cache_key = f"{self.CACHE_PREFIX}:besttimes:{user_id}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        # Get successful posts
        posts = PublishHistory.objects.filter(
            post__user_id=user_id,
            status='success',
            published_at__isnull=False
        ).select_related('post')

        if not posts.exists():
            return self._get_default_posting_times()

        # Analyze by hour
        hourly_engagement = {}
        daily_engagement = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday

        for history in posts:
            hour = history.published_at.hour
            day = history.published_at.weekday()
            engagement = (history.likes or 0) + (history.comments or 0) + (history.shares or 0)

            if hour not in hourly_engagement:
                hourly_engagement[hour] = []
            hourly_engagement[hour].append(engagement)
            daily_engagement[day].append(engagement)

        # Calculate averages
        hourly_avg = {
            hour: sum(engagements) / len(engagements)
            for hour, engagements in hourly_engagement.items()
            if engagements
        }

        daily_avg = {
            day: sum(engagements) / len(engagements) if engagements else 0
            for day, engagements in daily_engagement.items()
        }

        # Get top hours
        sorted_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)
        best_hours = [
            {'hour': hour, 'avg_engagement': round(eng, 2)}
            for hour, eng in sorted_hours[:5]
        ]

        # Get top days
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        sorted_days = sorted(daily_avg.items(), key=lambda x: x[1], reverse=True)
        best_days = [
            {'day': day_names[day], 'avg_engagement': round(eng, 2)}
            for day, eng in sorted_days[:3]
        ]

        # Calculate optimal frequency
        if posts.count() >= 2:
            first_post = posts.order_by('published_at').first()
            last_post = posts.order_by('published_at').last()
            days_span = (last_post.published_at - first_post.published_at).days
            if days_span > 0:
                posts_per_week = (posts.count() / days_span) * 7
                optimal_frequency = min(max(int(posts_per_week), 3), 7)
            else:
                optimal_frequency = 5
        else:
            optimal_frequency = 5

        result = {
            'best_hours': best_hours if best_hours else self._get_default_posting_times()['best_hours'],
            'best_days': best_days if best_days else self._get_default_posting_times()['best_days'],
            'optimal_frequency': optimal_frequency,
            'timezone': 'UTC'
        }

        cache.set(cache_key, result, 21600)  # 6 hours TTL
        return result

    def _calculate_viral_score(self, views: int, engagement: int, account_count: int) -> float:
        """
        Calculate viral score based on multiple factors

        Args:
            views: Total views
            engagement: Total engagement
            account_count: Number of accounts

        Returns:
            Viral score (0-100)
        """
        if views == 0:
            return 0.0

        # Normalize metrics
        engagement_rate = (engagement / views) * 100
        views_per_account = views / max(account_count, 1)

        # Weighted score
        score = (
            (engagement_rate * 0.4) +
            (min(views / 10000, 10) * 0.3) +  # Cap at 100k views
            (min(views_per_account / 1000, 10) * 0.3)  # Cap at 10k per account
        )

        return min(score * 10, 100)  # Scale to 0-100

    def _get_default_metrics(self, account: TikTokAccount) -> Dict[str, Any]:
        """Return default metrics when no analytics available"""
        return {
            'account_id': str(account.id),
            'username': account.username,
            'total_followers': 0,
            'total_following': 0,
            'total_videos': 0,
            'total_likes': 0,
            'engagement_rate': 0.0,
            'follower_growth': 0,
            'growth_rate': 0.0,
            'avg_views_per_video': 0,
            'avg_engagement_per_video': 0.0,
            'last_updated': timezone.now()
        }

    def _get_default_posting_times(self) -> Dict[str, Any]:
        """Return default optimal posting times"""
        return {
            'best_hours': [
                {'hour': 6, 'avg_engagement': 0},
                {'hour': 10, 'avg_engagement': 0},
                {'hour': 19, 'avg_engagement': 0},
                {'hour': 20, 'avg_engagement': 0},
                {'hour': 21, 'avg_engagement': 0}
            ],
            'best_days': [
                {'day': 'Tuesday', 'avg_engagement': 0},
                {'day': 'Thursday', 'avg_engagement': 0},
                {'day': 'Friday', 'avg_engagement': 0}
            ],
            'optimal_frequency': 5,
            'timezone': 'UTC'
        }

    def clear_cache(self, account_id: Optional[str] = None):
        """
        Clear analytics cache

        Args:
            account_id: Specific account ID or None for all
        """
        if account_id:
            cache.delete(f"{self.CACHE_PREFIX}:account:{account_id}")
            logger.info(f"Cleared cache for account {account_id}")
        else:
            # Clear all analytics cache (pattern matching requires Redis)
            logger.info("Cache clear requested for all analytics")
