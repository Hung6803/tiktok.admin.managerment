# System Architecture: TikTok Multi-Account Manager

## Updated Architecture Components: Phase 05

### TikTok API Integration Layer (Existing)
- **Core Components**:
  1. `tiktok_config.py`: Configuration management
  2. `tiktok_api_client.py`: API interaction abstraction
  3. `rate_limiter.py`: Request throttling mechanism
  4. OAuth services for token management

### Analytics Layer (New in Phase 05)
- **Location**: `backend/api/analytics/`
- **Key Components**:
  1. `schemas.py`: 17 Pydantic data validation models
  2. `services.py`: Analytics processing with intelligent caching
  3. `router.py`: 9 API endpoints for analytics
  4. Integrated with `publish_history_model.py`

### Analytics Features
- Account performance metrics
- Time series trend analysis
- Post viral score calculation
- Best posting times insights
- Dashboard aggregation
- Account comparative analysis

### API Endpoints
1. `/api/v1/analytics/accounts/{id}/metrics`
2. `/api/v1/analytics/accounts/{id}/timeseries`
3. `/api/v1/analytics/posts/{id}`
4. `/api/v1/analytics/insights/best-times`
5. `/api/v1/analytics/dashboard`
6. `/api/v1/analytics/compare`
7. `/api/v1/analytics/refresh/{id}`
8. `/api/v1/analytics/export` (Stub)

### Performance & Security
- SQL Injection Prevention
- N+1 Query Optimization
- Caching Strategies (1h/30m/6h TTL)
- Authorization Checks
- Secure Data Aggregation

### Unresolved Questions
- Large dataset performance benchmarking
- Long-term analytics data retention
- Predictive analytics implementation
- Real-time analytics streaming potential

## Existing Architectural Elements
- OAuth 2.0 Compliance
- Distributed Task Queue (Celery)
- Horizontal Worker Scaling
- Circuit Breaker Implementation

Updated: 2025-12-06