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

## Scheduling System Architecture (Phase 05)
### Celery Task Scheduling Components
- **Broker**: Redis
- **Beat Schedule**:
  1. `check_scheduled_posts`: Runs every 60 seconds
  2. `sync_all_accounts`: Daily at 2 AM
- **Task Modules**:
  1. `publish_post_task.py`: Core publishing logic
  2. `check_scheduled_posts_task.py`: Post scheduling validation
  3. `sync_accounts_task.py`: Daily account synchronization

### Scheduling Key Features
- Multi-account support
- Exponential backoff retry logic
- Race condition prevention
- Comprehensive error logging
- Transaction safety with atomic blocks

## Frontend Architecture (Phase 06)
### Technology Stack
- **Framework**: Next.js 14.2.0 (App Router)
- **Language**: TypeScript 5.3.0
- **Styling**: Tailwind CSS 3.4.0
- **UI Components**: Shadcn/ui
- **State Management**: TanStack Query 5.20.0
- **Form Handling**: React Hook Form 7.68.0

### Key Frontend Components
1. **Authentication Module**
   - JWT management
   - OAuth integration
   - Token auto-refresh mechanism

2. **Dashboard Architecture**
   - Protected route handling
   - Sidebar navigation
   - Responsive design system

3. **Account Management**
   - Dynamic listing
   - TikTok account synchronization
   - Account deletion workflows

4. **Media & Scheduling**
   - File upload components
   - Calendar-based scheduling
   - Progress tracking

5. **Analytics Visualization**
   - Time series charts
   - Performance metric displays
   - Responsive data grids

### Security Considerations
- Client-side token encryption
- CSRF protection
- OAuth validation layers
- Secure storage mechanisms

### Performance Optimization
- Code splitting
- Lazy loading
- Minimal bundle sizes (<200KB/page)
- Server-side rendering strategies

## Existing Architectural Elements
- OAuth 2.0 Compliance
- Distributed Task Queue (Celery)
- Horizontal Worker Scaling
- Circuit Breaker Implementation
- Comprehensive Frontend Architecture

Updated: 2025-12-06