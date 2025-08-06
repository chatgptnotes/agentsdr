# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentSDR - An AI-powered Sales Development Representative assistant platform designed to augment sales teams with intelligent automation, lead management, and real-time insights. Built with Flask backend and Supabase database.

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with Supabase credentials (Clerk removed)

# Test database connection
python test_connection.py

# Test local authentication (Clerk removed)
python -c "from auth import auth_manager; print('Auth system ready')"
```

### Running the Application
```bash
# Development server
python main.py  # Runs on port 8000

# Production server
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Testing
```bash
# No formal test suite - use individual test scripts:
python test_connection.py      # Test Supabase connection
python -c "from auth_routes import auth_bp; print('Local auth ready')"  # Test local auth
python test_contact_tables.py   # Test database tables
python test_google_oauth.py     # Test OAuth flow
```

## Architecture and Structure

### Monolithic Flask Application
- Single `main.py` file containing all routes and business logic
- Direct Supabase API calls via requests library (no ORM)
- Local SQLite authentication system (Clerk removed)
- Static frontend files served by Flask (no build process)

### Database Hierarchy
```
Organization (Sales Team)
├── Users (Sales Reps, Managers)
├── Leads (Prospects and potential customers)
├── Opportunities (Active sales pipeline)
├── Activities (Follow-ups, calls, meetings)
├── Proposals (Generated sales proposals)
└── Reports (Performance analytics)
```

### Key API Endpoints
- Auth: `/auth/*` - Login, signup, user management
- Organizations: `/api/organizations/*` - Sales team management
- Leads: `/api/leads/*` - Lead and prospect management
- Opportunities: `/api/opportunities/*` - Sales pipeline management
- Activities: `/api/activities/*` - Follow-up and task management
- Proposals: `/api/proposals/*` - Proposal generation and management
- Briefings: `/api/briefings/*` - Daily briefing and insights
- CRM: `/api/crm/*` - CRM integration endpoints

### Middleware Components
- `auth.py` - Local authentication system
- `sales_middleware.py` - Sales team access controls
- `briefing_engine.py` - Daily briefing generation
- `crm_sync.py` - CRM synchronization handlers

### Environment Variables Required
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=your-secret-key
# CLERK_SECRET_KEY removed - using local auth
```

### Current Implementation Status
- Phase 1: Foundation and Basic Sales Management ✅
- Phase 2: SDR Core Features (In Progress)
- Phase 3: AI Intelligence and Automation (Planned)
- Phase 4: Enterprise Features and Integrations (Planned)
- Using local SQLite authentication for sales teams

### Database Schema
Apply schema using Supabase SQL Editor:
- `supabase_schema.sql` - Main database schema
- `sales_schema.sql` - Sales-specific tables and structures
- `briefing_schema.sql` - Daily briefing and analytics tables
- `crm_integration_schema.sql` - CRM synchronization tables

### Development Notes
- Always test with admin@agentsdr.com (superadmin account)
- Row Level Security (RLS) is enabled - ensure proper auth
- Frontend uses vanilla JavaScript - no framework or bundling
- API returns JSON responses with proper error handling
- Sales middleware controls access to sensitive lead data
- WhatsApp integration requires proper Business API setup