# CRM System Implementation TODO Plan

## Project Overview
Multi-tenant CRM system with FastAPI, SQLAlchemy 2.0, PostgreSQL 15+, JWT authentication, in-memory caching, and comprehensive testing.

## Phase 1: Project Setup and Infrastructure
### 1.1 Project Structure Creation
- [ ] Create main project directory structure
  ```
  app/
  ├── api/
  │   ├── v1/
  │   └── dependencies.py
  ├── core/
  │   ├── config.py
  │   ├── database.py
  │   ├── security.py
  │   ├── jwt.py
  │   ├── cache.py
  │   ├── permissions.py
  │   └── exceptions.py
  ├── models/
  ├── repositories/
  ├── services/
  ├── schemas/
  └── main.py
  tests/
  ├── unit/
  ├── integration/
  ├── fixtures/
  └── conftest.py
  migrations/
  ├── alembic.ini
  └── versions/
  scripts/
  docs/
  docker/
  ├── app/
  │   └── Dockerfile
  └── nginx/
      └── nginx.conf
  ```

### 1.2 Docker Setup
- [ ] Create Dockerfile for Python application
  - Multi-stage build for smaller image
  - Python 3.10+ base image
  - Non-root user for security
  - Health check endpoint
- [ ] Create docker-compose.yml with services:
  - app (FastAPI application)
  - postgres (PostgreSQL 15+)
  - redis (optional, for future caching if needed)
  - nginx (reverse proxy, optional)
- [ ] Create docker-compose.override.yml for development
- [ ] Create .dockerignore file
  - Exclude .env, __pycache__, .git, etc.
- [ ] Create docker-compose.test.yml for testing environment
- [ ] Setup environment variables for Docker
  - Database connection strings
  - Service URLs
  - Development vs production configs

### 1.3 Dependencies Setup
- [ ] Create requirements.txt with all necessary packages
  - FastAPI
  - SQLAlchemy 2.0
  - Alembic
  - asyncpg
  - pydantic 2.x
  - python-jose[cryptography]
  - passlib[bcrypt]
  - python-multipart
  - pytest
  - pytest-asyncio
  - mypy
  - black
  - ruff
  - uvicorn[standard]
  - redis (optional, for future use)
  - httpx (for testing)
- [ ] Create requirements-dev.txt for development dependencies

### 1.4 Configuration Management
- [ ] Implement core/config.py with Pydantic BaseSettings
- [ ] Define all environment variables
- [ ] Create .env.example file
- [ ] Setup multiple environment configurations (dev, test, prod)
- [ ] Configure Docker environment variables mapping

### 1.5 Database Configuration
- [ ] Implement core/database.py with SQLAlchemy 2.0 async engine
- [ ] Setup connection pooling (min=5, max=20)
- [ ] Implement database session management
- [ ] Create async context managers for transactions

### 1.6 In-Memory Cache Configuration
- [ ] Implement core/cache.py for in-memory caching
- [ ] Create TTL-based cache with automatic expiration
- [ ] Implement cache decorators for analytics endpoints
- [ ] Define cache key patterns and invalidation strategy

## Phase 2: Database Models and Migrations

### 2.1 SQLAlchemy Models
- [ ] Create models/base.py with base model class
- [ ] Implement models/user.py
  - id (UUID)
  - email (unique)
  - hashed_password
  - name
  - created_at
- [ ] Implement models/organization.py
  - id (UUID)
  - name
  - default_currency (optional, ISO code)
  - created_at
- [ ] Implement models/organization_member.py
  - id (UUID)
  - organization_id (FK)
  - user_id (FK)
  - role (owner, admin, manager, member)
  - created_at
  - Unique constraint on (organization_id, user_id)
- [ ] Implement models/contact.py
  - id (UUID)
  - organization_id (FK)
  - owner_id (FK to user)
  - name
  - email
  - phone
  - created_at
- [ ] Implement models/deal.py
  - id (UUID)
  - organization_id (FK)
  - contact_id (FK)
  - owner_id (FK to user)
  - title
  - amount (decimal)
  - currency (ISO code)
  - status (new, in_progress, won, lost)
  - stage (qualification, proposal, negotiation, closed)
  - created_at
  - updated_at
- [ ] Implement models/task.py
  - id (UUID)
  - deal_id (FK)
  - title
  - description
  - due_date
  - is_done
  - created_at
- [ ] Implement models/activity.py
  - id (UUID)
  - deal_id (FK)
  - author_id (FK to user, nullable)
  - type (comment, status_changed, stage_changed, task_created, system)
  - payload (JSONB)
  - created_at

### 2.2 Database Migrations
- [ ] Setup Alembic configuration
- [ ] Create initial migration with all tables
- [ ] Add all necessary indexes
  - User email index
  - Organization members lookup indexes
  - Contact search indexes (GIN for full-text)
  - Deal status/stage/amount indexes
  - Task due date index
  - Activity timeline indexes
- [ ] Add all foreign key constraints
- [ ] Create migration scripts for execution

## Phase 3: Core Security and Authentication

### 3.1 Security Implementation
- [ ] Implement core/security.py
  - Password hashing with bcrypt (cost=12)
  - Password verification
  - Strong password validation
- [ ] Implement core/jwt.py
  - JWT token creation (access & refresh)
  - Token decoding and validation
  - Token expiration (access: 15min, refresh: 7 days)
  - Token refresh logic

### 3.2 Authentication Service
- [ ] Create services/auth_service.py
  - User registration with organization
  - User login
  - Token refresh
  - Password reset (optional)
- [ ] Implement rate limiting (5 attempts/minute)
- [ ] Add audit logging for auth events

### 3.3 Authentication Endpoints
- [ ] Create api/v1/auth.py router
- [ ] Implement POST /api/v1/auth/register
  - Validate input (email, password min 8 chars)
  - Create user and organization in transaction
  - Return tokens and user info
- [ ] Implement POST /api/v1/auth/login
  - Verify credentials
  - Return tokens and organizations list
- [ ] Implement POST /api/v1/auth/refresh
  - Validate refresh token
  - Issue new token pair

## Phase 4: Authorization and RBAC

### 4.1 Permission System
- [ ] Implement core/permissions.py
  - Role hierarchy definition
  - Permission matrices
  - Resource access rules
- [ ] Create permission decorators
- [ ] Implement role-based filtering

### 4.2 Dependencies
- [ ] Implement api/dependencies.py
  - get_current_user dependency
  - get_current_organization dependency (via X-Organization-Id header)
  - require_role dependency
  - ownership validation
  - X-Organization-Id header validation and extraction

### 4.3 Permission Service
- [ ] Create services/permission_service.py
  - Check user access to organization
  - Validate role hierarchy
  - Apply ownership filters
  - Cross-organization access prevention

## Phase 5: Repository Layer

### 5.1 Base Repository
- [ ] Create repositories/base.py
  - Generic CRUD operations
  - Pagination support
  - Filtering helpers

### 5.2 Specific Repositories
- [ ] Implement repositories/user_repository.py
  - Get by email
  - Create user
  - Update user
- [ ] Implement repositories/organization_repository.py
  - Create organization
  - Get by ID
  - Update settings
- [ ] Implement repositories/organization_member_repository.py
  - Add member
  - Remove member
  - Get user organizations
  - Get organization members
  - Check membership
- [ ] Implement repositories/contact_repository.py
  - CRUD operations
  - Check email uniqueness in org
  - Search functionality
  - Ownership filtering
- [ ] Implement repositories/deal_repository.py
  - CRUD operations
  - Status/stage transitions
  - Filtering and aggregation
  - Count by contact
- [ ] Implement repositories/task_repository.py
  - CRUD operations
  - Get by deal
  - Overdue tasks query
  - Completion tracking
- [ ] Implement repositories/activity_repository.py
  - Create activity
  - Get timeline by deal
  - Pagination support
- [ ] Implement repositories/analytics_repository.py
  - Aggregate by status
  - Calculate averages
  - Funnel analysis
  - Conversion rates

## Phase 6: Pydantic Schemas

### 6.1 Request/Response Schemas
- [ ] Create schemas/base.py with base schemas
- [ ] Implement schemas/auth_schemas.py
  - RegisterRequest
  - LoginRequest
  - TokenResponse
  - RefreshRequest
- [ ] Implement schemas/organization_schemas.py
  - OrganizationResponse
  - OrganizationWithRole
- [ ] Implement schemas/contact_schemas.py
  - ContactCreate
  - ContactUpdate
  - ContactResponse
  - ContactPaginated
- [ ] Implement schemas/deal_schemas.py
  - DealCreate
  - DealUpdate
  - DealResponse
  - DealPaginated
  - DealWithRelations
- [ ] Implement schemas/task_schemas.py
  - TaskCreate
  - TaskUpdate
  - TaskResponse
  - TaskPaginated
- [ ] Implement schemas/activity_schemas.py
  - CommentCreate
  - ActivityResponse
  - TimelineResponse
- [ ] Implement schemas/analytics_schemas.py
  - SummaryResponse
  - FunnelResponse
  - MetricsResponse

## Phase 7: Service Layer

### 7.1 Business Logic Services
- [ ] Implement services/organization_service.py
  - Get user organizations
  - Manage members
  - Update settings
- [ ] Implement services/contact_service.py
  - Create with validation
  - Update with ownership check
  - Delete with deal check
  - Search and filter
- [ ] Implement services/deal_service.py
  - Create with contact validation
  - Status transition validation
  - Stage progression rules
  - Amount validation for won deals
  - Currency handling with org defaults
- [ ] Implement services/task_service.py
  - Create with due date validation
  - Update with ownership check
  - Overdue task handling
  - Completion tracking
- [ ] Implement services/activity_service.py
  - Auto-log system events
  - Create manual comments
  - Build timeline
  - Format activity payloads
- [ ] Implement services/analytics_service.py
  - Calculate deal summary
  - Generate funnel metrics
  - In-memory cache management (TTL-based)
  - Trend analysis

## Phase 8: API Endpoints

**Note**: All endpoints are versioned under `/api/v1/` prefix

### 8.1 Organization Endpoints
- [ ] Create api/v1/organizations.py
- [ ] GET /api/v1/organizations/me
  - Return user's organizations with roles

### 8.2 Contact Endpoints
- [ ] Create api/v1/contacts.py
- [ ] GET /api/v1/contacts (paginated, filtered)
- [ ] POST /api/v1/contacts
- [ ] GET /api/v1/contacts/{id}
- [ ] PUT /api/v1/contacts/{id}
- [ ] DELETE /api/v1/contacts/{id}

### 8.3 Deal Endpoints
- [ ] Create api/v1/deals.py
- [ ] GET /api/v1/deals (paginated, filtered)
- [ ] POST /api/v1/deals
- [ ] GET /api/v1/deals/{id}
- [ ] PATCH /api/v1/deals/{id}
- [ ] DELETE /api/v1/deals/{id}

### 8.4 Task Endpoints
- [ ] Create api/v1/tasks.py
- [ ] GET /api/v1/tasks (paginated, filtered)
- [ ] POST /api/v1/tasks
- [ ] GET /api/v1/tasks/{id}
- [ ] PATCH /api/v1/tasks/{id}
- [ ] DELETE /api/v1/tasks/{id}

### 8.5 Activity Endpoints
- [ ] Create api/v1/activities.py
- [ ] GET /api/v1/deals/{id}/activities
- [ ] POST /api/v1/deals/{id}/activities

### 8.6 Analytics Endpoints
- [ ] Create api/v1/analytics.py
- [ ] GET /api/v1/analytics/deals/summary
- [ ] GET /api/v1/analytics/deals/funnel

## Phase 9: Middleware and Error Handling

### 9.1 Middleware
- [ ] Create api/middleware.py
- [ ] Implement error handling middleware
- [ ] Add CORS middleware
- [ ] Implement request ID middleware
- [ ] Add logging middleware
- [ ] Implement rate limiting middleware

### 9.2 Exception Handling
- [ ] Enhance core/exceptions.py
  - Custom exception classes
  - Error codes
  - User-friendly messages
- [ ] Implement global exception handlers
- [ ] Add validation error formatting
- [ ] Database error handling

## Phase 10: Testing

### 10.1 Test Setup
- [ ] Configure pytest with asyncio
- [ ] Create test database setup
- [ ] Implement test fixtures
- [ ] Create factory classes for test data

### 10.2 Unit Tests
- [ ] Test all service methods
- [ ] Test repository operations
- [ ] Test permission logic
- [ ] Test validation functions
- [ ] Test JWT operations
- [ ] Test password hashing

### 10.3 Integration Tests
- [ ] Test authentication flow
- [ ] Test all API endpoints
- [ ] Test permission scenarios
- [ ] Test transaction rollbacks
- [ ] Test in-memory cache operations
- [ ] Test error responses

### 10.4 End-to-End Tests
- [ ] Full user registration to deal close
- [ ] Multi-organization scenarios
- [ ] Role permission matrix verification
- [ ] Data isolation verification

## Phase 11: Performance and Monitoring

### 11.1 Performance Optimization
- [ ] Add database query optimization
- [ ] Implement N+1 query prevention
- [ ] Add eager loading where needed
- [ ] Optimize search queries
- [ ] Add database connection pooling

### 11.2 Caching Strategy
- [ ] Implement in-memory analytics caching with TTL
- [ ] Add organization settings cache (in-memory)
- [ ] Implement permission cache (in-memory)
- [ ] Add activity count cache with automatic expiration

### 11.3 Monitoring
- [ ] Implement health check endpoints
- [ ] Add performance logging
- [ ] Create basic application logs

## Phase 12: Documentation and Deployment

### 12.1 API Documentation
- [ ] Configure OpenAPI/Swagger
- [ ] Add endpoint descriptions
- [ ] Document request/response schemas
- [ ] Add example requests
- [ ] Create API usage guide

### 12.2 Developer Documentation
- [ ] Create README.md
- [ ] Document setup instructions
- [ ] Add development guidelines
- [ ] Create contribution guide
- [ ] Document deployment process

### 12.3 Deployment Preparation
- [ ] Configure production environment variables
- [ ] Setup CI/CD pipeline
- [ ] Create deployment scripts
- [ ] Add backup procedures
- [ ] Configure monitoring and alerting
- [ ] Setup log aggregation

## Phase 13: Security Hardening

### 13.1 Security Measures
- [ ] Implement SQL injection prevention
- [ ] Add XSS protection
- [ ] Implement CSRF protection
- [ ] Add security headers
- [ ] Implement secrets management
- [ ] Add audit logging

### 13.2 Data Protection
- [ ] Implement basic data retention policies
- [ ] Add data export functionality for users

## Implementation Priority Order

### Critical Path (Must complete in order):
1. Project Setup and Docker (Phase 1) - including Docker setup for unified development environment
2. Database Models (Phase 2)
3. Core Security (Phase 3)
4. Authorization (Phase 4)
5. Repository Layer (Phase 5)
6. Pydantic Schemas (Phase 6)
7. Service Layer (Phase 7)
8. API Endpoints (Phase 8)

### Parallel Work (Can be done alongside):
- Testing (Phase 10) - write tests as you implement
- Documentation (Phase 12) - document as you go
- Error Handling (Phase 9) - implement with endpoints

### Final Phases:
- Performance Optimization (Phase 11)
- Security Hardening (Phase 13)
- Production Deployment Configuration (Phase 12.3)

## Success Criteria

### Functional Requirements:
- ✅ All 11 pipelines fully implemented
- ✅ Multi-tenant data isolation working
- ✅ RBAC with 4 role levels functional
- ✅ All CRUD operations for entities
- ✅ Deal stage/status transitions validated
- ✅ Task management with due dates
- ✅ Activity timeline tracking
- ✅ Analytics with caching

### Non-Functional Requirements:
- ✅ 90% test coverage minimum
- ✅ Response time < 500ms for all endpoints
- ✅ Proper error handling with user-friendly messages
- ✅ Security best practices implemented
- ✅ Database properly indexed
- ✅ Code follows PEP8 and type hints
- ✅ API fully documented

### Technical Debt Prevention:
- ✅ Clean architecture with separation of concerns
- ✅ DRY principle followed
- ✅ SOLID principles applied
- ✅ Comprehensive logging
- ✅ Monitoring and alerting configured
- ✅ Database migrations automated

## Risk Mitigation

### High Risk Areas:
1. **Data Isolation**: Implement organization_id checks at repository layer
2. **Permission Bypass**: Double-check all role validations
3. **Performance**: Add caching early, profile queries
4. **Security**: Use parameterized queries, validate all inputs
5. **Scalability**: Design for horizontal scaling from start

### Contingency Plans:
- If performance issues: Add read replicas
- If cache issues: Implement fallback to database
- If security breach: Have rollback procedures ready
- If data loss: Implement point-in-time recovery

## Notes

### Currency Handling:
- Organization can optionally set default_currency
- If not set, use application-wide default (USD)
- Validate against configured ISO currency list
- Store as 3-letter ISO codes

### Status/Stage Transitions:
- Status: new → in_progress → won/lost (terminal)
- Stage: qualification → proposal → negotiation → closed
- Members/managers can only move stage forward
- Owners/admins can move stage backward
- Auto-set stage to 'closed' when status is won/lost

### Testing Strategy:
- Write tests before or immediately after implementation
- Use TDD for complex business logic
- Mock external dependencies
- Test all permission scenarios
- Verify data isolation in every test

### Best Practices to Maintain:
- Use async/await throughout
- Type hints on all functions
- Docstrings for complex logic
- Consistent error messages
- Audit logging for sensitive operations
- Correlation IDs for request tracking
- Docker-first development approach
- Environment parity (dev/test/prod)

## Completion Tracking

Total Tasks: ~200
Phases: 13
Estimated Timeline: Based on team size and experience
Priority: Follow critical path first
Testing: Continuous throughout development
Documentation: Update as features complete

---
Generated: 2025-11-20
Version: 1.0
Based on: crm-system-pipelines.md