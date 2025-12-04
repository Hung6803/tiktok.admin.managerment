# TikTok Multi-Account Manager

Multi-account TikTok management platform for scheduling and publishing content across multiple TikTok accounts.

## Features

- 🔐 Multi-account TikTok authentication via OAuth 2.0
- 📅 Schedule posts with timezone support
- 🎥 Video upload and publishing
- 📊 Analytics and performance tracking
- ⏰ Automated publishing queue with retry logic
- 🔄 Real-time sync with TikTok accounts

## Tech Stack

### Backend
- **Python 3.12**
- **Django 5.0** - Web framework
- **Django Ninja** - FastAPI-style REST API
- **PostgreSQL** - Database
- **Celery** - Task queue for scheduling
- **Redis** - Message broker

### Frontend
- **Next.js 14+** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Shadcn/ui** - Component library
- **TanStack Query** - Data fetching
- **Zustand** - State management

## Project Structure

```
tiktok-admin-management/
├── backend/              # Django backend
│   ├── apps/            # Django apps
│   ├── config/          # Settings & configuration
│   ├── api/             # API endpoints
│   └── core/            # Shared utilities
├── frontend/            # Next.js frontend
│   ├── app/             # App Router pages
│   ├── components/      # React components
│   ├── lib/             # Utilities
│   └── hooks/           # Custom hooks
├── docs/                # Documentation
├── plans/               # Implementation plans
└── docker-compose.yml   # Docker setup
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 14+
- Redis 7+
- TikTok Developer Account

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd tiktok-admin-management
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python manage.py migrate
python manage.py runserver
```

3. **Frontend Setup**
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your API URL
npm run dev
```

4. **Start Celery Workers**
```bash
cd backend
celery -A core worker -l info
celery -A core beat -l info
```

### Docker Setup

```bash
docker-compose up -d
```

## Configuration

### Environment Variables

**Backend (.env)**
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/tiktok_manager
REDIS_URL=redis://localhost:6379/0
TIKTOK_CLIENT_KEY=your-client-key
TIKTOK_CLIENT_SECRET=your-client-secret
TIKTOK_REDIRECT_URI=http://localhost:8000/api/tiktok/callback
```

**Frontend (.env.local)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Implementation Plan

See [Implementation Plan](./plans/251204-1525-tiktok-multi-account-manager/plan.md) for detailed phases:

1. **Phase 01**: Project Setup & Architecture
2. **Phase 02**: Database Schema Design
3. **Phase 03**: TikTok API Integration
4. **Phase 04**: Backend API Development
5. **Phase 05**: Scheduling System
6. **Phase 06**: Frontend Development
7. **Phase 07**: Testing & QA
8. **Phase 08**: Deployment & DevOps

## API Documentation

API documentation is auto-generated and available at:
- Development: http://localhost:8000/api/v1/docs
- Production: https://yourdomain.com/api/v1/docs

## Testing

### Backend Tests
```bash
cd backend
pytest --cov
```

### Frontend Tests
```bash
cd frontend
npm test
```

### E2E Tests
```bash
npx playwright test
```

## Deployment

See [Phase 08: Deployment](./plans/251204-1525-tiktok-multi-account-manager/phase-08-deployment.md) for detailed deployment instructions.

Quick deploy with Docker:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Follow the development rules in `.claude/workflows/development-rules.md`
2. Keep files under 200 lines
3. Use kebab-case for file names
4. Write comprehensive tests
5. Document all changes

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.
