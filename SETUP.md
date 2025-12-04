# Setup Guide

## Phase 01 Complete ✅

Project structure initialized with Django Ninja backend and Next.js frontend.

**Development Setup:** Run backend and frontend locally, PostgreSQL in Docker.

## Project Structure

```
tiktok-admin-management/
├── backend/
│   ├── config/              # Django settings
│   ├── apps/
│   │   ├── accounts/        # User management
│   │   ├── tiktok_accounts/ # TikTok account management
│   │   ├── content/         # Content & media
│   │   ├── scheduler/       # Scheduling system
│   │   └── analytics/       # Analytics
│   ├── core/                # Shared utilities
│   ├── api/                 # API routers
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js pages
│   │   ├── components/     # React components
│   │   ├── lib/            # Utilities
│   │   ├── hooks/          # Custom hooks
│   │   └── types/          # TypeScript types
│   └── package.json
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Quick Start

### 1. Start PostgreSQL Database

```bash
# Copy environment file
cp .env.example .env
# Edit .env if you want custom credentials

# Start PostgreSQL in Docker
docker-compose up -d

# Verify it's running
docker-compose ps
```

PostgreSQL will be available at: `localhost:5432`

### 2. Setup Backend (Django)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
venv\Scripts\activate
# Windows CMD:
venv\Scripts\activate.bat
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (or use root .env)
# Make sure DB_HOST=localhost (not 'db' like in Docker)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Backend available at: **http://localhost:8000**
API Docs: **http://localhost:8000/api/v1/docs**

### 3. Setup Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Run development server
npm run dev
```

Frontend available at: **http://localhost:3000**

### 4. (Optional) Run Celery for Scheduling

**What is Celery?**
- **Celery Worker**: Executes background tasks (like publishing videos)
- **Celery Beat**: Scheduler that triggers tasks at specific times

You'll need these in Phase 05 (Scheduling System). For now, skip this.

```bash
# Terminal 1 - Celery Worker (does the work)
cd backend
celery -A core worker -l info

# Terminal 2 - Celery Beat (scheduler)
cd backend
celery -A core beat -l info
```

## Docker Commands

### PostgreSQL Database

```bash
# Start database
docker-compose up -d

# Stop database
docker-compose down

# View logs
docker-compose logs -f

# Remove database (WARNING: deletes all data)
docker-compose down -v
```

## Next Steps

### Phase 02: Database Schema
- Create User model
- Create TikTokAccount model
- Create ScheduledPost model
- Create supporting models
- Run migrations

### Before You Start
1. Set up PostgreSQL database
2. Get TikTok Developer credentials (https://developers.tiktok.com/)
3. Configure Redis for Celery

## Useful Commands

### Backend
```bash
# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Django shell
python manage.py shell

# Run tests
pytest
```

### Frontend
```bash
# Development
npm run dev

# Build
npm run build

# Run tests
npm test
```

### Docker
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild
docker-compose up --build -d
```

## Troubleshooting

### PostgreSQL Connection Issues
- Ensure PostgreSQL is running
- Check credentials in .env file
- Verify DB_HOST setting (localhost or db for Docker)

### Frontend Can't Connect to Backend
- Ensure backend is running
- Check NEXT_PUBLIC_API_URL in frontend/.env.local
- Verify CORS settings in backend/config/settings.py

### Celery Not Starting
- Ensure Redis is running
- Check REDIS_URL in .env
- Verify Celery configuration in settings.py

## Development Tips

1. **Hot Reload**: Both backend and frontend support hot reload
2. **API Documentation**: Auto-generated at /api/v1/docs
3. **Admin Panel**: Available at /admin after creating superuser
4. **Code Quality**: Run `black .` and `isort .` for code formatting

## Next Phase

Ready to proceed to Phase 02: Database Schema Design

See: `plans/251204-1525-tiktok-multi-account-manager/phase-02-database-schema.md`
