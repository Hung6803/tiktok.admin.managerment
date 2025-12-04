# Development Startup Guide

## Prerequisites
- Python 3.12+ installed
- Node.js 20+ installed
- Docker Desktop installed (for PostgreSQL)

## First Time Setup

### 1. Start PostgreSQL
```bash
# Start Docker PostgreSQL
docker-compose up -d

# Verify it's running
docker ps
```

### 2. Setup Backend
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp ..\.env.example .env

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### 3. Setup Frontend
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
```

## Daily Development

### Start Services (Run each in separate terminal)

**Terminal 1 - Database**
```bash
docker-compose up
```

**Terminal 2 - Backend**
```bash
cd backend
venv\Scripts\activate
python manage.py runserver
```

**Terminal 3 - Frontend**
```bash
cd frontend
npm run dev
```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Django Admin**: http://localhost:8000/admin
- **PostgreSQL**: localhost:5432

## Common Issues

### PostgreSQL not starting
```bash
# Check if port 5432 is already in use
netstat -ano | findstr :5432

# If yes, stop existing PostgreSQL service or change port in docker-compose.yml
```

### Virtual environment activation issues
```bash
# PowerShell execution policy error
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then retry
venv\Scripts\activate
```

### Port already in use
```bash
# Backend (8000)
netstat -ano | findstr :8000

# Frontend (3000)
netstat -ano | findstr :3000

# Kill process if needed (replace PID)
taskkill /PID <PID> /F
```

## Stop Services

```bash
# Backend/Frontend: Ctrl+C in terminal

# PostgreSQL
docker-compose down
```

## Reset Database

```bash
# Stop and remove database
docker-compose down -v

# Start fresh
docker-compose up -d

# Run migrations again
cd backend
python manage.py migrate
python manage.py createsuperuser
```

## Next: Phase 02 - Database Models

See: `plans/251204-1525-tiktok-multi-account-manager/phase-02-database-schema.md`
