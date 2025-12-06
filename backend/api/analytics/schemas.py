"""
Analytics schemas for validation and serialization
"""
from ninja import Schema, Field
from datetime import datetime, date
from typing import Optional, List, Dict
from enum import Enum
from pydantic import field_validator


class TimeRange(str, Enum):
    """Time range enumeration"""
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    year = "year"
    custom = "custom"


class MetricType(str, Enum):
    """Metric type enumeration"""
    views = "total_views"
    likes = "total_likes"
    comments = "total_comments"
    shares = "total_shares"
    followers = "follower_count"
    engagement_rate = "engagement_rate"


class AccountMetricsOut(Schema):
    """Account performance metrics output schema"""
    account_id: str
    username: str
    total_followers: int
    total_following: int
    total_videos: int
    total_likes: int
    engagement_rate: float
    follower_growth: int  # vs previous period
    growth_rate: float  # percentage
    avg_views_per_video: int
    avg_engagement_per_video: float
    last_updated: datetime

    class Config:
        from_attributes = True


class PostAnalyticsOut(Schema):
    """Post analytics output schema"""
    post_id: str
    title: str
    published_at: Optional[datetime]
    views: int
    likes: int
    comments: int
    shares: int
    saves: int = 0
    completion_rate: float = 0.0
    engagement_rate: float
    viral_score: float  # Custom metric

    class Config:
        from_attributes = True


class TimeSeriesDataPoint(Schema):
    """Time series data point schema"""
    timestamp: datetime
    value: float
    label: Optional[str] = None


class TimeSeriesOut(Schema):
    """Time series data output schema"""
    metric: str
    period: TimeRange
    data: List[TimeSeriesDataPoint]
    total: float
    average: float
    min_value: float
    max_value: float
    trend: str  # "up", "down", "stable"


class GrowthMetricsOut(Schema):
    """Growth metrics output schema"""
    period: TimeRange
    start_date: date
    end_date: date
    followers_gained: int
    followers_lost: int
    net_growth: int
    growth_rate: float
    daily_average: float
    best_day: Optional[date]
    worst_day: Optional[date]


class EngagementMetricsOut(Schema):
    """Engagement metrics output schema"""
    total_engagements: int
    likes: int
    comments: int
    shares: int
    saves: int = 0
    engagement_rate: float
    avg_engagement_per_post: float
    most_engaged_post: Optional[Dict] = None
    least_engaged_post: Optional[Dict] = None


class AudienceInsightsOut(Schema):
    """Audience insights output schema"""
    total_reach: int
    unique_viewers: int
    demographics: Dict[str, Dict] = {}  # age, gender, location
    top_countries: List[Dict] = []
    top_cities: List[Dict] = []
    active_hours: List[Dict] = []  # Hour distribution
    device_types: Dict[str, float] = {}  # mobile, desktop percentages


class HashtagPerformanceOut(Schema):
    """Hashtag performance output schema"""
    hashtag: str
    usage_count: int
    total_views: int
    avg_views: float
    total_engagement: int
    avg_engagement: float
    trending_score: float


class BestTimesOut(Schema):
    """Best posting times output schema"""
    best_hours: List[Dict]  # hour, avg_engagement
    best_days: List[Dict]   # day, avg_engagement
    optimal_frequency: int  # posts per week
    timezone: str


class ComparisonOut(Schema):
    """Account comparison output schema"""
    account_1: AccountMetricsOut
    account_2: AccountMetricsOut
    comparison: Dict[str, Dict]  # metric -> {diff, percentage}


class DashboardOut(Schema):
    """Analytics dashboard output schema"""
    summary: AccountMetricsOut
    recent_posts: List[PostAnalyticsOut]
    growth_trend: TimeSeriesOut
    engagement_trend: TimeSeriesOut
    top_posts: List[PostAnalyticsOut]
    upcoming_schedule: List[Dict]


class AnalyticsQueryIn(Schema):
    """Analytics query input schema"""
    account_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    period: TimeRange = TimeRange.month
    metric: Optional[str] = None

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate date is not in future"""
        if v and v > date.today():
            raise ValueError('Date cannot be in the future')
        return v
