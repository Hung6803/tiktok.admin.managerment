# Phase 01: Project Setup & Architecture

**Priority:** High
**Status:** Ready to Start
**Estimated Time:** 2-3 hours

## Context Links

- [Main Plan](./plan.md)
- [Development Rules](../../.claude/workflows/development-rules.md)

## Overview

Initialize the project structure with Django Ninja backend and Next.js frontend following best practices for modular, scalable architecture.

## Key Insights

- Use monorepo structure with separate backend/frontend directories
- Follow kebab-case naming convention for self-documenting file names
- Keep files under 200 lines per development rules
- Use Docker for consistent development environment

## Requirements

### Functional Requirements
- Django 5.x project with Django Ninja API framework
- PostgreSQL database configuration
- Next.js 14+ with App Router
- Environment variable management
- CORS configuration for local development

### Non-Functional Requirements
- Hot reload for both backend and frontend
- Type safety with TypeScript
- Code quality tools (ESLint, Prettier, Black, isort)
- Git ignore for sensitive files

## Architecture

```
tiktok-admin-management/
├── backend/
│   ├── config/              # Django settings
│   ├── apps/
│   │   ├── accounts/        # User management
│   │   ├── tiktok_accounts/ # TikTok account management
│   │   ├── content/         # Content & media
│   │   ├── scheduler/       # Scheduling system
│   │   └── analytics/       # Analytics & reporting
│   ├── core/                # Shared utilities
│   ├── api/                 # Django Ninja routers
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router
│   │   ├── components/     # React components
│   │   ├── lib/            # Utilities
│   │   ├── hooks/          # Custom hooks
│   │   └── types/          # TypeScript types
│   ├── public/
│   ├── package.json
│   └── next.config.js
├── docker-compose.yml
├── .gitignore
├── README.md
└── docs/
    ├── project-overview-pdr.md
    ├── code-standards.md
    └── system-architecture.md
```

## Related Code Files

### Files to Create
- `backend/manage.py`
- `backend/config/settings.py`
- `backend/config/urls.py`
- `backend/requirements.txt`
- `frontend/package.json`
- `frontend/next.config.js`
- `frontend/tsconfig.json`
- `docker-compose.yml`
- `.gitignore`
- `.env.example`
- `README.md`

## Implementation Steps

1. **Initialize Backend Directory Structure**
   ```bash
   mkdir -p backend/{config,apps,core,api}
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install Django and Dependencies**
   ```bash
   pip install django==5.0 django-ninja psycopg2-binary python-decouple django-cors-headers celery redis
   pip freeze > requirements.txt
   ```

3. **Create Django Project**
   ```bash
   django-admin startproject config .
   ```

4. **Configure Django Settings**
   - Split settings into base, development, production
   - Configure PostgreSQL database
   - Setup Django Ninja
   - Configure CORS headers
   - Setup static/media file handling

5. **Initialize Frontend**
   ```bash
   cd ../
   npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir
   cd frontend
   npm install axios @tanstack/react-query zustand date-fns
   ```

6. **Setup Docker Environment**
   - Create `docker-compose.yml` with PostgreSQL, Redis, backend, frontend services
   - Configure environment variables
   - Setup volumes for data persistence

7. **Create Environment Files**
   - `.env.example` with all required variables
   - `.env` (gitignored) for local development

8. **Initialize Git Repository**
   ```bash
   git init
   git add .
   git commit -m "chore: initial project setup"
   ```

9. **Create Documentation**
   - `README.md` with setup instructions
   - `docs/project-overview-pdr.md`
   - `docs/code-standards.md`
   - `docs/system-architecture.md`

## Todo List

- [ ] Create backend directory structure
- [ ] Install Django and dependencies
- [ ] Initialize Django project with custom config
- [ ] Configure Django settings (database, CORS, Ninja)
- [ ] Create Django apps structure
- [ ] Initialize Next.js frontend
- [ ] Install frontend dependencies
- [ ] Configure TypeScript and ESLint
- [ ] Create docker-compose.yml
- [ ] Setup environment files
- [ ] Create .gitignore
- [ ] Write README.md
- [ ] Create initial documentation
- [ ] Test backend server startup
- [ ] Test frontend dev server startup
- [ ] Test database connectivity

## Success Criteria

- ✅ Django server runs on http://localhost:8000
- ✅ Next.js dev server runs on http://localhost:3000
- ✅ PostgreSQL connection successful
- ✅ Redis connection successful
- ✅ Hot reload works for both backend and frontend
- ✅ Environment variables load correctly
- ✅ Docker containers start without errors

## Risk Assessment

**Risk:** Version compatibility issues between Django and Django Ninja
**Mitigation:** Use pinned versions in requirements.txt, test immediately after setup

**Risk:** PostgreSQL connection issues on Windows
**Mitigation:** Use Docker for database, provide clear connection string examples

**Risk:** CORS issues during development
**Mitigation:** Configure django-cors-headers properly from the start

## Security Considerations

- Never commit `.env` files
- Use strong SECRET_KEY for Django
- Setup ALLOWED_HOSTS properly
- Configure secure database passwords
- Use environment variables for all sensitive data

## Next Steps

After Phase 01 completion:
1. Proceed to Phase 02: Database Schema Design
2. Create initial Django models
3. Run first database migrations
