# Multi-Tenant CRM System Generation Prompt

## Instructions for AI Agent

I have microservices framework in: .ai-framework/

INSTRUCTIONS FOR AI:
1. First, read .ai-framework/AGENTS.md to understand the framework
2. Then, validate my prompt using .ai-framework/docs/guides/prompt-validation-guide.md
3. Ask me for any missing information before generating code
4. Only after validation passes, generate code following framework rules

---

## MY PROJECT:

### What I'm building:
Multi-tenant CRM system for B2B sales management with organization-based isolation

### Problem it solves:
Enables multiple companies to manage their sales pipelines, contacts, deals, and tasks in a single platform with proper data isolation and role-based access control

### Key features:
- Multi-tenant architecture with Organizations
- User management with roles (owner/admin/manager/member)
- Contact management with ownership
- Deal pipeline with stages and statuses
- Tasks linked to deals with due dates
- Activity timeline for deals (comments, status changes)
- Analytics dashboard (deal summary, sales funnel)
- JWT authentication with refresh tokens
- Versioned API (/api/v1/)

### How complex should it be:
Production-ready

### Additional services needed:
- PostgreSQL Data API for all database operations
- Analytics Worker for background report generation
- Redis for caching and session storage
- RabbitMQ for event-driven communication

### Technical requirements:
- Python 3.12+, FastAPI, SQLAlchemy 2.0+, Alembic
- PostgreSQL 16+ with JSONB for activity payloads
- JWT with access/refresh token rotation
- Full type hints with mypy strict mode
- Comprehensive test coverage (>80%)
- Structured logging with correlation IDs
- Prometheus metrics and health checks

### Business rules:
1. Users work in one organization context at a time (via X-Organization-Id header)
2. Role-based permissions:
   - owner/admin: full access within organization
   - manager: manage all entities except org settings
   - member: view all, edit only own contacts/deals/tasks
3. Deal validation:
   - Cannot close as 'won' if amount <= 0
   - Cannot delete contact with existing deals
   - Cannot set task due_date in the past
   - Stage transitions tracked in activity timeline
4. Automatic activity logging for status/stage changes
5. Cross-organization access returns 403/404 consistently

### Data model entities:
- Organization (id, name, created_at)
- User (id, email, hashed_password, name, created_at)
- OrganizationMember (id, organization_id, user_id, role, created_at)
- Contact (id, organization_id, owner_id, name, email, phone, created_at)
- Deal (id, organization_id, contact_id, owner_id, title, amount, currency, status, stage, created_at, updated_at)
- Task (id, deal_id, title, description, due_date, is_done, created_at)
- Activity (id, deal_id, author_id, type, payload[JSONB], created_at)

### API endpoints needed:
- Auth: /api/v1/auth/register, /api/v1/auth/login, /api/v1/auth/refresh
- Organizations: /api/v1/organizations/me, /api/v1/organizations/{id}/members
- Contacts: CRUD with pagination, search, owner filtering
- Deals: CRUD with status/stage filtering, amount ranges, sorting
- Tasks: CRUD with deal filtering, due date ranges
- Activities: GET/POST for deal timeline
- Analytics: /api/v1/analytics/deals/summary, /api/v1/analytics/deals/funnel

### Service naming:
- crm_core_api (Business API, port 8000)
- crm_data_postgres_api (Data API, port 8001)
- crm_analytics_worker (Background worker)

### Maturity level: Level 4 (Production)
- Docker Compose with all infrastructure
- GitHub Actions CI/CD
- Prometheus + Grafana monitoring
- ELK stack for logging
- Comprehensive documentation
- Load testing scenarios

---

## Notes for Implementation

This prompt follows the framework's Improved Hybrid Approach architecture:
1. Business services (crm_core_api) never access database directly
2. All data operations go through dedicated Data API (crm_data_postgres_api)
3. Background processing handled by separate worker (crm_analytics_worker)
4. Each service runs in its own container with separate event loop
5. Communication via HTTP between business and data layers
6. RabbitMQ for async event-driven communication

The prompt is structured according to the framework's validation guide requirements, providing:
- Clear project description
- Specific problem being solved
- Detailed feature list
- Explicit complexity level (Production-ready)
- Complete technical requirements
- Comprehensive business rules
- Full data model specification
- API endpoint definitions
- Service naming following {context}_{domain}_{type} pattern