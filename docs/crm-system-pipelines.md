# CRM System Pipelines Documentation

## Overview
This document describes all data and process pipelines in the multi-tenant CRM system. Each pipeline is structured according to a standardized 7-point format for consistency and completeness.

## Technology Stack
- **Framework:** FastAPI (async)
- **ORM:** SQLAlchemy 2.0 with Alembic for migrations
- **Database:** PostgreSQL 15+
- **Authentication:** JWT (access/refresh tokens)
- **Cache:** Redis for session management and short-term caching
- **Testing:** pytest with async support
- **Type Checking:** mypy with strict mode

---

## 1. Authentication & Session Pipeline

### 1.1 Pipeline Name
**User Authentication and JWT Session Management Pipeline**

### 1.2 Modules and Dependencies
```
├── app/
│   ├── api/v1/auth.py
│   ├── services/auth_service.py
│   ├── repositories/user_repository.py
│   ├── repositories/organization_repository.py
│   ├── models/user.py
│   ├── models/organization.py
│   └── core/
│       ├── security.py
│       ├── jwt.py
│       └── redis.py
```

### 1.3 Classes and Methods (Call Sequence)
```python
# Registration Flow
# 1. AuthRouter.register() -> POST /api/v1/auth/register
# 2. AuthService.register_user_with_organization()
# 3. async with database.transaction():
# 4.   UserRepository.create_user()
# 5.   PasswordHasher.hash_password()
# 6.   OrganizationRepository.create_organization()
# 7.   OrganizationMemberRepository.add_member(role="owner")
# 8. JWTService.create_token_pair()
# 9. RedisClient.set_refresh_token()
# 10. Return tokens and user info

# Login Flow
# 1. AuthRouter.login() -> POST /api/v1/auth/login
# 2. AuthService.authenticate_user()
# 3. UserRepository.get_by_email()
# 4. PasswordHasher.verify_password()
# 5. OrganizationMemberRepository.get_user_organizations()
# 6. JWTService.create_token_pair()
# 7. RedisClient.set_refresh_token()
# 8. Return tokens and organizations list
```

### 1.4 Database Changes
```sql
-- Users table
INSERT INTO users (id, email, hashed_password, name, created_at)
VALUES (gen_random_uuid(), $1, $2, $3, NOW())
RETURNING *;

-- Organizations table
-- Base assignment tracks id + name; we add optional best-practice default_currency
-- to prefill deals. Allowed ISO codes come from configuration (e.g., USD/EUR/RUB).
INSERT INTO organizations (id, name, default_currency, created_at)
VALUES (gen_random_uuid(), $1, COALESCE($2, 'USD'), NOW())
RETURNING *;

-- Organization Members table
INSERT INTO organization_members (
    id, organization_id, user_id, role, created_at
)
VALUES (gen_random_uuid(), $1, $2, 'owner', NOW())
RETURNING *;

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_org_members_unique ON organization_members(organization_id, user_id);
CREATE INDEX idx_org_members_user ON organization_members(user_id);
```

### 1.5 Endpoint Details
```yaml
POST /api/v1/auth/register:
  request:
    body:
      email: string (email format)
      password: string (min 8 chars)
      name: string
      organization_name: string
      organization_currency: string (optional, must be in configured ISO currency list, e.g., "USD", "EUR")
  response:
    201:
      access_token: string (JWT, expires in 15 min)
      refresh_token: string (JWT, expires in 7 days)
      user:
        id: uuid
        email: string
        name: string
      organization:
        id: uuid
        name: string
        default_currency: string (present when optional org preference is enabled)

POST /api/v1/auth/login:
  request:
    body:
      email: string
      password: string
  response:
    200:
      access_token: string
      refresh_token: string
      organizations: array[{
        id: uuid,
        name: string,
        role: string
      }]

POST /api/v1/auth/refresh:
  request:
    body:
      refresh_token: string
  response:
    200:
      access_token: string
      refresh_token: string
```

### 1.6 Side Effects
- Redis session creation with TTL (access: 15 min, refresh: 7 days)
- Default organization settings initialization
- Audit log entry for authentication events
- Rate limiting counter increment (max 5 attempts per minute)

### 1.7 Metrics and Monitoring
```yaml
Metrics:
  - auth_registration_total (Counter)
  - auth_login_attempts_total (Counter)
  - auth_login_success_rate (Gauge)
  - auth_token_refresh_total (Counter)
  - auth_response_time_ms (Histogram)

Alerts:
  - Failed login attempts > 10/min from single IP
  - Registration rate > 100/hour (possible spam)
  - Token refresh failures > 5% in 5 min
  - Response time p95 > 500ms
```

---

## 2. Organization Management Pipeline

### 2.1 Pipeline Name
**Organization Membership and Context Management Pipeline**

### 2.2 Modules and Dependencies
```
├── app/
│   ├── api/v1/organizations.py
│   ├── services/organization_service.py
│   ├── repositories/organization_repository.py
│   ├── repositories/organization_member_repository.py
│   └── models/organization.py
```

### 2.3 Classes and Methods (Call Sequence)
```python
# Get User Organizations Flow
# 1. OrganizationRouter.get_my_organizations() -> GET /api/v1/organizations/me
# 2. Extract current_user from JWT token
# 3. OrganizationService.get_user_organizations()
# 4. OrganizationMemberRepository.get_organizations_by_user()
# 5. For each membership:
# 6.   OrganizationRepository.get_by_id()
# 7.   Include role information
# 8. Return list of organizations with roles
```

### 2.4 Database Changes
```sql
-- Get user's organizations
SELECT
    o.id,
    o.name,
    o.created_at,
    om.role,
    om.created_at as joined_at
FROM organizations o
JOIN organization_members om ON o.id = om.organization_id
WHERE om.user_id = $1
ORDER BY om.created_at DESC;

-- Index for fast lookups
CREATE INDEX idx_org_members_user_lookup ON organization_members(user_id);
```

### 2.5 Endpoint Details
```yaml
GET /api/v1/organizations/me:
  response:
    200:
      organizations: array[{
        id: uuid,
        name: string,
        role: string (owner, admin, manager, member),
        created_at: datetime,
        joined_at: datetime
      }]
    401: Unauthorized (missing or invalid token)
```

### 2.6 Side Effects
- No side effects (read-only operation)
- May populate cache with organization list

### 2.7 Metrics and Monitoring
```yaml
Metrics:
  - organizations_list_requests_total (Counter)
  - organizations_per_user_avg (Gauge)
  - organizations_list_latency_ms (Histogram)

Alerts:
  - Response time > 200ms
  - Users with no organizations > 0
```

---

## 3. Authorization & RBAC Pipeline

### 3.1 Pipeline Name
**Role-Based Access Control and Permission Validation Pipeline**

### 3.2 Modules and Dependencies
```
├── app/
│   ├── api/dependencies.py
│   ├── services/permission_service.py
│   ├── repositories/organization_member_repository.py
│   ├── models/organization_member.py
│   └── core/
│       ├── permissions.py
│       └── exceptions.py
```

### 3.3 Classes and Methods (Call Sequence)
```python
# Permission Check Flow
# 1. get_current_user() dependency
# 2. JWTService.decode_token()
# 3. get_current_organization() dependency
# 4. Extract X-Organization-Id header
# 5. PermissionService.check_user_access()
# 6. OrganizationMemberRepository.get_member_role()
# 7. Cache role in request state
# 8. require_role() dependency
# 9. PermissionService.validate_role_hierarchy()
# 10. If authorized, proceed to endpoint
# 11. If not, raise HTTPException(403)

# Data Filtering Flow
# 1. PermissionService.apply_ownership_filter()
# 2. Check user role
# 3. If member: add owner_id=current_user filter
# 4. If manager/admin/owner: no filter
# 5. Return filtered query
```

### 3.4 Database Changes
```sql
-- Get user role in organization
SELECT role FROM organization_members
WHERE user_id = $1 AND organization_id = $2;

-- Check organization membership
SELECT COUNT(*) FROM organization_members
WHERE user_id = $1 AND organization_id = $2;

-- Indexes for fast lookups
CREATE INDEX idx_org_members_lookup ON organization_members(user_id, organization_id);
```

### 3.5 Endpoint Details
```yaml
All Protected Endpoints:
  headers:
    Authorization: Bearer <access_token>
    X-Organization-Id: <uuid>

  Role Permissions:
    owner:
      - Full access to all endpoints
      - Can manage organization settings
      - Can delete organization

    admin:
      - Full access to all data endpoints
      - Cannot delete organization
      - Can manage users

    manager:
      - Full access to contacts, deals, tasks
      - Read-only access to organization settings
      - Cannot move deal stages backward

    member:
      - Read access to all data
      - Write access only to own contacts, deals, tasks
      - Cannot access organization settings

  Error Responses:
    401: Missing or invalid token
    403: Insufficient permissions
    404: Organization not found or no access
```

### 3.6 Side Effects
- Request state population with user context
- Permission cache update (TTL: 5 minutes)
- Audit log for sensitive operations
- Rate limiting per user/organization

### 3.7 Metrics and Monitoring
```yaml
Metrics:
  - rbac_permission_checks_total (Counter by role)
  - rbac_permission_denied_total (Counter by endpoint)
  - rbac_check_latency_ms (Histogram)
  - rbac_cache_hit_rate (Gauge)

Alerts:
  - Permission denied rate > 20% for any endpoint
  - Cross-organization access attempts > 0
  - Missing X-Organization-Id header > 10/min
```

---

## 4. Contact Management Pipeline

### 4.1 Pipeline Name
**Contact CRUD and Ownership Management Pipeline**

### 4.2 Modules and Dependencies
```
├── app/
│   ├── api/v1/contacts.py
│   ├── services/contact_service.py
│   ├── repositories/contact_repository.py
│   ├── repositories/deal_repository.py
│   ├── models/contact.py
│   └── schemas/contact_schemas.py
```

### 4.3 Classes and Methods (Call Sequence)
```python
# Create Contact Flow
# 1. ContactRouter.create_contact() -> POST /api/v1/contacts
# 2. Validate request with ContactCreateSchema
# 3. ContactService.create_contact()
# 4. Set owner_id = current_user.id
# 5. Set organization_id from request context
# 6. ContactRepository.check_email_unique_in_org()
# 7. ContactRepository.create()
# 8. Return ContactResponseSchema

# Delete Contact Flow (with validation)
# 1. ContactRouter.delete_contact() -> DELETE /api/v1/contacts/{id}
# 2. ContactService.delete_contact()
# 3. ContactRepository.get_by_id()
# 4. PermissionService.check_ownership()
# 5. DealRepository.count_by_contact_id()
# 6. If deals exist -> raise HTTPException(409)
# 7. ContactRepository.delete()
# 8. Return 204 No Content

# List Contacts Flow
# 1. ContactRouter.list_contacts() -> GET /api/v1/contacts
# 2. ContactService.list_contacts()
# 3. Apply ownership filter if role=member
# 4. Apply search filter if provided
# 5. ContactRepository.paginate()
# 6. Return PaginatedResponse
```

### 4.4 Database Changes
```sql
-- Create contact
INSERT INTO contacts (
    id, organization_id, owner_id, name, email, phone, created_at
) VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NOW())
RETURNING *;

-- Check for existing deals before deletion
SELECT COUNT(*) FROM deals WHERE contact_id = $1;

-- Delete contact (hard delete)
DELETE FROM contacts
WHERE id = $1 AND organization_id = $2;

-- Search contacts
SELECT * FROM contacts
WHERE organization_id = $1
  AND ($2::uuid IS NULL OR owner_id = $2)
  AND ($3::text IS NULL OR
       name ILIKE '%' || $3 || '%' OR
       email ILIKE '%' || $3 || '%')
ORDER BY created_at DESC
LIMIT $4 OFFSET $5;

-- Indexes
CREATE INDEX idx_contacts_org ON contacts(organization_id);
CREATE INDEX idx_contacts_owner ON contacts(owner_id);
CREATE INDEX idx_contacts_search ON contacts USING gin(
    to_tsvector('simple', name || ' ' || COALESCE(email, ''))
);
```

### 4.5 Endpoint Details
```yaml
GET /api/v1/contacts:
  parameters:
    - page: integer (default: 1)
    - page_size: integer (default: 20, max: 100)
    - search: string (searches name, email, phone)
    - owner_id: uuid (admin/manager only)
  response:
    200:
      items: Contact[]
      total: integer
      page: integer
      page_size: integer
      pages: integer

POST /api/v1/contacts:
  request:
    body:
      name: string (required, max 255)
      email: string (email format, optional)
      phone: string (optional, max 50)
  response:
    201: Contact object
    400: Validation error
    409: Email already exists in organization

PUT /api/v1/contacts/{contact_id}:
  request:
    body:
      name: string
      email: string
      phone: string
  response:
    200: Updated Contact
    403: Not owner (for member role)
    404: Contact not found

DELETE /api/v1/contacts/{contact_id}:
  response:
    204: No Content
    403: Not owner (for member role)
    404: Contact not found
    409: Contact has associated deals
```

### 4.6 Side Effects
- Cache invalidation for contact lists
- Search index update (if full-text search enabled)
- Activity logging for audit trail
- Organization contact count update

### 4.7 Metrics and Monitoring
```yaml
Metrics:
  - contacts_created_total (Counter by organization)
  - contacts_deleted_total (Counter)
  - contacts_search_latency_ms (Histogram)
  - contacts_deletion_blocked_total (Counter)

Alerts:
  - Contact creation failures > 5% in 5 min
  - Search latency p95 > 500ms
  - Deletion blocked rate > 10% (many contacts with deals)
```

---

## 5. Deal Sales Pipeline

### 5.1 Pipeline Name
**Deal Management and Sales Funnel Pipeline**

### 5.2 Modules and Dependencies
```
├── app/
│   ├── api/v1/deals.py
│   ├── services/deal_service.py
│   ├── services/activity_service.py
│   ├── repositories/deal_repository.py
│   ├── repositories/activity_repository.py
│   ├── models/deal.py
│   ├── models/activity.py
│   └── schemas/deal_schemas.py
```

### 5.3 Classes and Methods (Call Sequence)
```python
# Status Transition Matrix
# Valid status transitions:
#   new -> in_progress, won, lost
#   in_progress -> won, lost
#   won -> (terminal state, cannot be changed)
#   lost -> (terminal state, cannot be changed)
#
# Stage Transition Matrix
# Valid stage progression (forward only for member/manager):
#   qualification -> proposal -> negotiation -> closed
# Notes:
#   - Stages can be skipped forward (e.g., qualification -> negotiation)
#   - Only owner/admin can move stages backward
#   - When status becomes 'won' or 'lost', stage auto-updates to 'closed'

# Create Deal Flow
# 1. DealRouter.create_deal() -> POST /api/v1/deals
# 2. Validate with DealCreateSchema
# 3. DealService.create_deal()
# 4. ContactRepository.verify_same_organization()
#    - Verify that contact exists and belongs to the same organization
#    - Check: Contact.organization_id == current_organization_id
#    - If not matching -> raise HTTPException(400, "Contact belongs to different organization")
#    - This ensures deals cannot be created with contacts from other organizations
# 5. Validate currency if provided (must exist in configurable ISO code list)
# 6. Set initial status='new', stage='qualification'
# 7. If currency not provided, use Organization.default_currency when available,
#    otherwise fall back to application-wide default (e.g., USD)
# 8. DealRepository.create()
# 9. ActivityService.log_event('deal_created')
# 10. Return DealResponseSchema

# Update Deal Status/Stage Flow
# 1. DealRouter.update_deal() -> PATCH /api/v1/deals/{id}
# 2. DealService.update_deal()
# 3. DealRepository.get_by_id()
# 4. PermissionService.check_deal_ownership()
# 5. If status='won': validate amount > 0
# 6. If stage change: validate_stage_transition()
# 7. If stage backward and role NOT in (owner, admin): raise 403
# 8. DealRepository.update()
# 9. ActivityService.log_event('status_changed' or 'stage_changed')
# 10. Return updated Deal

# List Deals with Filters
# 1. DealRouter.list_deals() -> GET /api/v1/deals
# 2. DealService.list_deals()
# 3. Build filters from query params
# 4. Apply ownership filter if role=member
# 5. DealRepository.paginate_with_aggregates()
# 6. Return PaginatedResponse with totals
```

### 5.4 Database Changes
```sql
-- Create deal
-- default_currency is optional; fallback to config value if org column absent
INSERT INTO deals (
    id, organization_id, contact_id, owner_id, title,
    amount, currency, status, stage, created_at, updated_at
) VALUES (
    gen_random_uuid(), $1, $2, $3, $4,
    $5, COALESCE($6, (SELECT default_currency FROM organizations WHERE id = $1)),
    'new', 'qualification', NOW(), NOW()
) RETURNING *;

-- Update deal with validation
UPDATE deals
SET
    status = $2,
    stage = $3,
    amount = $4,
    updated_at = NOW()
WHERE id = $1 AND organization_id = $5
RETURNING *;

-- Get deals with filters
SELECT
    d.*,
    c.name as contact_name,
    u.name as owner_name
FROM deals d
JOIN contacts c ON d.contact_id = c.id
JOIN users u ON d.owner_id = u.id
WHERE d.organization_id = $1
    AND ($2::uuid IS NULL OR d.owner_id = $2)
    AND ($3::text[] IS NULL OR d.status = ANY($3))
    AND ($4::text IS NULL OR d.stage = $4)
    AND ($5::decimal IS NULL OR d.amount >= $5)
    AND ($6::decimal IS NULL OR d.amount <= $6)
ORDER BY d.created_at DESC
LIMIT $7 OFFSET $8;

-- Indexes
CREATE INDEX idx_deals_org ON deals(organization_id);
CREATE INDEX idx_deals_owner ON deals(owner_id);
CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_deals_stage ON deals(stage);
CREATE INDEX idx_deals_amount ON deals(amount);
```

### 4.5 Endpoint Details
```yaml
GET /api/v1/deals:
  parameters:
    - page: integer
    - page_size: integer
    - status: array[string] (new, in_progress, won, lost)
    - stage: string (qualification, proposal, negotiation, closed)
    - min_amount: decimal
    - max_amount: decimal
    - owner_id: uuid (admin/manager only)
    - order_by: string (created_at, amount, updated_at)
    - order: string (asc, desc)
  response:
    200:
      items: Deal[]
      total: integer
      total_amount: decimal
      page: integer
      page_size: integer

POST /api/v1/deals:
  request:
    body:
      contact_id: uuid (required)
      title: string (required, max 255)
      amount: decimal (required, >= 0; must be > 0 before status='won')
      currency: string (optional, must be in configured ISO currency list, e.g., "USD", "EUR")
      # If not provided, uses organization's default_currency when available
      # Note: status and stage are set automatically
      # status = 'new', stage = 'qualification'
  response:
    201: Deal object with auto-set status='new', stage='qualification', and currency
    400: Invalid amount, invalid currency, or contact belongs to different organization
    404: Contact not found

PATCH /api/v1/deals/{deal_id}:
  request:
    body:
      title: string
      amount: decimal
      status: string
      stage: string
  response:
    200: Updated Deal
    400: Invalid status transition or amount <= 0 for won
    403: Cannot move stage backward (member/manager roles)
    404: Deal not found
```

### 4.6 Side Effects
- Activity timeline entry creation for all status/stage changes
- Analytics cache invalidation
- Sales metrics recalculation
- Automatic stage update when status changes

### 4.7 Metrics and Monitoring
```yaml
Metrics:
  - deals_created_total (Counter by organization)
  - deals_status_transitions_total (Counter by from_to)
  - deals_won_amount_total (Counter by currency)
  - deals_conversion_rate (Gauge by stage)
  - deals_average_lifetime_days (Histogram)

Alerts:
  - Deal creation failures > 5%
  - Won deals with amount=0 attempted
  - Average deal age > 90 days
  - Conversion rate drop > 20% week-over-week
```

---

## 6. Task Management Pipeline

### 6.1 Pipeline Name
**Task Tracking and Due Date Management Pipeline**

### 6.2 Modules and Dependencies
```
├── app/
│   ├── api/v1/tasks.py
│   ├── services/task_service.py
│   ├── repositories/task_repository.py
│   ├── models/task.py
│   └── schemas/task_schemas.py
```

### 6.3 Classes and Methods (Call Sequence)
```python
# Create Task Flow
# 1. TaskRouter.create_task() -> POST /api/v1/tasks
# 2. Validate with TaskCreateSchema
# 3. TaskService.create_task()
# 4. Validate due_date >= today (cannot be in the past)
# 5. DealRepository.get_by_id()
# 6. Verify deal belongs to current organization
# 7. If role=member: verify deal.owner_id == current_user.id
# 8. TaskRepository.create()
# 9. ActivityService.log_event('task_created')
# 10. Return TaskResponseSchema

# Update Task Status Flow
# 1. TaskRouter.update_task() -> PATCH /api/v1/tasks/{id}
# 2. TaskService.update_task()
# 3. TaskRepository.get_by_id()
# 4. Check task ownership via deal
# 5. If updating due_date: validate >= today
# 6. TaskRepository.update()
# 7. If is_done changed: ActivityService.log_event()
# 8. Return updated Task

# List Tasks with Filters
# 1. TaskRouter.list_tasks() -> GET /api/v1/tasks
# 2. TaskService.list_tasks()
# 3. Apply filters (deal_id, only_open, due dates)
# 4. If role=member: filter by deal ownership
# 5. TaskRepository.paginate()
# 6. Return PaginatedResponse
```

### 6.4 Database Changes
```sql
-- Create task
INSERT INTO tasks (
    id, deal_id, title, description, due_date, is_done, created_at
) VALUES (
    gen_random_uuid(), $1, $2, $3, $4, false, NOW()
) RETURNING *;

-- Update task
UPDATE tasks
SET
    title = COALESCE($2, title),
    description = COALESCE($3, description),
    due_date = COALESCE($4, due_date),
    is_done = COALESCE($5, is_done)
WHERE id = $1
RETURNING *;

-- Get tasks with filters
SELECT t.*, d.title as deal_title
FROM tasks t
JOIN deals d ON t.deal_id = d.id
WHERE d.organization_id = $1
    AND ($2::uuid IS NULL OR t.deal_id = $2)
    AND ($3::boolean IS NULL OR (NOT $3 OR NOT t.is_done))
    AND ($4::date IS NULL OR t.due_date <= $4)
    AND ($5::date IS NULL OR t.due_date >= $5)
    AND ($6::uuid IS NULL OR d.owner_id = $6)
ORDER BY t.due_date ASC, t.created_at DESC
LIMIT $7 OFFSET $8;

-- Get overdue tasks
SELECT COUNT(*) as overdue_count
FROM tasks t
JOIN deals d ON t.deal_id = d.id
WHERE d.organization_id = $1
    AND t.is_done = false
    AND t.due_date < CURRENT_DATE;

-- Indexes
CREATE INDEX idx_tasks_deal ON tasks(deal_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date) WHERE is_done = false;
CREATE INDEX idx_tasks_is_done ON tasks(is_done);
```

### 5.5 Endpoint Details
```yaml
GET /api/v1/tasks:
  parameters:
    - deal_id: uuid
    - only_open: boolean (default: false)
    - due_before: date
    - due_after: date
    - page: integer
    - page_size: integer
  response:
    200:
      items: Task[]
      total: integer
      overdue_count: integer
      page: integer
      page_size: integer

POST /api/v1/tasks:
  request:
    body:
      deal_id: uuid (required)
      title: string (required, max 255)
      description: string (optional)
      due_date: date (>= today)
  response:
    201: Task object
    400: Due date in past
    403: Cannot create task for other's deal (member)
    404: Deal not found

PATCH /api/v1/tasks/{task_id}:
  request:
    body:
      title: string
      description: string
      due_date: date
      is_done: boolean
  response:
    200: Updated Task
    400: Due date in past
    403: Not authorized
    404: Task not found
```

### 5.6 Side Effects
- Activity timeline entry for task creation/completion
- Deal metrics update (task completion rate)
- Overdue task count cache update
- Email notification for approaching due dates (optional)

### 5.7 Metrics and Monitoring
```yaml
Metrics:
  - tasks_created_total (Counter)
  - tasks_completed_total (Counter)
  - tasks_overdue_count (Gauge)
  - tasks_completion_rate (Gauge)
  - tasks_average_completion_time_hours (Histogram)

Alerts:
  - Overdue tasks > 50 for organization
  - Task completion rate < 50% weekly
  - Task creation without due_date > 30%
```

---

## 7. Activity Timeline Pipeline

### 7.1 Pipeline Name
**Deal Activity Logging and Timeline Generation Pipeline**

### 7.2 Modules and Dependencies
```
├── app/
│   ├── api/v1/activities.py
│   ├── services/activity_service.py
│   ├── repositories/activity_repository.py
│   ├── models/activity.py
│   └── schemas/activity_schemas.py
```

### 7.3 Classes and Methods (Call Sequence)
```python
# Automatic Activity Creation (System Events)
# 1. Any deal state change triggers
# 2. ActivityService.log_event()
# 3. Build activity payload based on event type
# 4. Set author_id = current_user.id or null for system
# 5. ActivityRepository.create()
# 6. Return activity_id

# Manual Comment Creation
# 1. ActivityRouter.create_comment() -> POST /api/v1/deals/{id}/activities
# 2. Validate with CommentCreateSchema
# 3. ActivityService.create_comment()
# 4. DealRepository.verify_exists()
# 5. Build payload with comment text
# 6. ActivityRepository.create(type='comment')
# 7. Return ActivityResponseSchema

# Timeline Retrieval
# 1. ActivityRouter.get_timeline() -> GET /api/v1/deals/{id}/activities
# 2. ActivityService.get_deal_timeline()
# 3. ActivityRepository.get_by_deal_id()
# 4. Format activities with author names
# 5. Return sorted timeline
```

### 6.4 Database Changes
```sql
-- Create activity entry
INSERT INTO activities (
    id, deal_id, author_id, type, payload, created_at
) VALUES (
    gen_random_uuid(), $1, $2, $3, $4::jsonb, NOW()
) RETURNING *;

-- Get timeline for deal
SELECT
    a.*,
    u.name as author_name
FROM activities a
LEFT JOIN users u ON a.author_id = u.id
WHERE a.deal_id = $1
ORDER BY a.created_at DESC
LIMIT $2 OFFSET $3;

-- Activity types and payloads
-- type: 'comment' -> payload: {"text": "string"}
-- type: 'status_changed' -> payload: {"from": "new", "to": "won"}
-- type: 'stage_changed' -> payload: {"from": "qualification", "to": "proposal"}
-- type: 'task_created' -> payload: {"task_id": "uuid", "title": "string"}
-- type: 'system' -> payload: {"message": "string"}

-- Indexes
CREATE INDEX idx_activities_deal ON activities(deal_id);
CREATE INDEX idx_activities_created ON activities(created_at DESC);
CREATE INDEX idx_activities_type ON activities(type);
```

### 6.5 Endpoint Details
```yaml
GET /api/v1/deals/{deal_id}/activities:
  parameters:
    - page: integer
    - page_size: integer (max: 50)
    - type: string (filter by activity type)
  response:
    200:
      items: Activity[]
      total: integer
      page: integer
      page_size: integer

POST /api/v1/deals/{deal_id}/activities:
  request:
    body:
      type: "comment" (only comment allowed for manual creation)
      payload:
        text: string (required, max 1000 chars)
  response:
    201: Activity object
    400: Invalid type or empty text
    404: Deal not found
```

### 6.6 Side Effects
- Real-time updates via WebSocket (if implemented)
- Activity count cache update
- Search index update for comments
- Audit trail for compliance

### 6.7 Metrics and Monitoring
```yaml
Metrics:
  - activities_created_total (Counter by type)
  - activities_per_deal_avg (Gauge)
  - activities_comment_length_avg (Gauge)
  - activities_retrieval_latency_ms (Histogram)

Alerts:
  - Activity creation failures > 1%
  - Timeline query latency p95 > 200ms
  - Missing author_id for comment type
```

---

## 8. Analytics Generation Pipeline

### 8.1 Pipeline Name
**Deal Analytics and Sales Metrics Pipeline**

### 8.2 Modules and Dependencies
```
├── app/
│   ├── api/v1/analytics.py
│   ├── services/analytics_service.py
│   ├── repositories/analytics_repository.py
│   └── core/cache.py
```

### 8.3 Classes and Methods (Call Sequence)
```python
# Deal Summary Analytics
# 1. AnalyticsRouter.get_summary() -> GET /api/v1/analytics/deals/summary
# 2. Check cache with key='summary:{org_id}'
# 3. If cache miss:
# 4.   AnalyticsService.calculate_summary()
# 5.   AnalyticsRepository.aggregate_by_status()
# 6.   AnalyticsRepository.calculate_averages()
# 7.   AnalyticsRepository.count_recent_deals(days=30)
# 8.   Cache result with TTL=300 seconds
# 9. Return SummaryResponseSchema

# Sales Funnel Analytics
# 1. AnalyticsRouter.get_funnel() -> GET /api/v1/analytics/deals/funnel
# 2. Check cache with key='funnel:{org_id}'
# 3. If cache miss:
# 4.   AnalyticsService.calculate_funnel()
# 5.   AnalyticsRepository.group_by_stage_and_status()
# 6.   Calculate conversion rates between stages
# 7.   Identify bottlenecks
# 8.   Cache result with TTL=300 seconds
# 9. Return FunnelResponseSchema
```

### 8.4 Database Changes
```sql
-- Deal summary aggregation
SELECT
    status,
    COUNT(*) as count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MAX(amount) as max_amount,
    MIN(amount) as min_amount
FROM deals
WHERE organization_id = $1
GROUP BY status;

-- Average for won deals
SELECT AVG(amount) as avg_won_amount
FROM deals
WHERE organization_id = $1 AND status = 'won';

-- Recent deals count (last 30 days)
SELECT COUNT(*) as new_deals_count
FROM deals
WHERE organization_id = $1
  AND created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Sales funnel analysis
SELECT
    stage,
    status,
    COUNT(*) as count,
    SUM(amount) as total_amount
FROM deals
WHERE organization_id = $1
GROUP BY stage, status
ORDER BY
    CASE stage
        WHEN 'qualification' THEN 1
        WHEN 'proposal' THEN 2
        WHEN 'negotiation' THEN 3
        WHEN 'closed' THEN 4
    END;

-- Conversion rates calculation
WITH stage_counts AS (
    SELECT
        stage,
        COUNT(*) as total_count,
        COUNT(*) FILTER (WHERE status NOT IN ('lost')) as active_count
    FROM deals
    WHERE organization_id = $1
    GROUP BY stage
)
SELECT
    stage,
    total_count,
    active_count,
    CASE
        WHEN LAG(active_count) OVER (ORDER BY
            CASE stage
                WHEN 'qualification' THEN 1
                WHEN 'proposal' THEN 2
                WHEN 'negotiation' THEN 3
                WHEN 'closed' THEN 4
            END
        ) > 0
        THEN ROUND(active_count::numeric / LAG(active_count) OVER (ORDER BY
            CASE stage
                WHEN 'qualification' THEN 1
                WHEN 'proposal' THEN 2
                WHEN 'negotiation' THEN 3
                WHEN 'closed' THEN 4
            END
        ) * 100, 2)
        ELSE 100
    END as conversion_rate
FROM stage_counts;
```

### 7.5 Endpoint Details
```yaml
GET /api/v1/analytics/deals/summary:
  response:
    200:
      by_status:
        new:
          count: integer
          total_amount: decimal
        in_progress:
          count: integer
          total_amount: decimal
        won:
          count: integer
          total_amount: decimal
          avg_amount: decimal
        lost:
          count: integer
          total_amount: decimal
      totals:
        deals: integer
        amount: decimal
      trends:
        new_deals_30d: integer

GET /api/v1/analytics/deals/funnel:
  response:
    200:
      stages:
        - stage: string
          total: integer
          active: integer
          amount: decimal
          conversion_rate: float
      bottlenecks:
        - stage: string
          drop_rate: float
```

### 7.6 Side Effects
- Redis cache population (TTL: 5 minutes)
- Metrics export to monitoring system
- Dashboard data refresh trigger

### 7.7 Metrics and Monitoring
```yaml
Metrics:
  - analytics_cache_hit_rate (Gauge)
  - analytics_calculation_duration_ms (Histogram)
  - analytics_requests_total (Counter by endpoint)

Alerts:
  - Cache hit rate < 70%
  - Calculation time > 1000ms
  - Analytics endpoint errors > 1%
```

---

## 9. Database Migration Pipeline

### 9.1 Pipeline Name
**Schema Evolution and Migration Management Pipeline**

### 9.2 Modules and Dependencies
```
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── app/
│   └── core/database.py
└── scripts/
    └── migrate.py
```

### 9.3 Classes and Methods (Call Sequence)
```python
# Migration Creation Flow
# 1. alembic revision --autogenerate -m "message"
# 2. Review generated migration file
# 3. Add indexes and constraints manually
# 4. Test migration locally

# Migration Execution Flow
# 1. alembic upgrade head
# 2. Load database URL from config
# 3. Check current revision
# 4. Execute pending migrations in order
# 5. Update alembic_version table
# 6. Verify schema integrity

# Rollback Flow
# 1. alembic downgrade -1
# 2. Execute down() function
# 3. Update alembic_version
# 4. Verify rollback success
```

### 8.4 Database Changes
```sql
-- Alembic version tracking
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Initial schema migration
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    default_currency VARCHAR(3) NOT NULL DEFAULT 'USD' CHECK (default_currency ~ '^[A-Z]{3}$'),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'manager', 'member')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id),
    owner_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'in_progress', 'won', 'lost')),
    stage VARCHAR(20) NOT NULL DEFAULT 'qualification' CHECK (stage IN ('qualification', 'proposal', 'negotiation', 'closed')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE,
    is_done BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('comment', 'status_changed', 'stage_changed', 'task_created', 'system')),
    payload JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 8.5 Endpoint Details
```yaml
Migration Commands:
  alembic upgrade head: Apply all migrations
  alembic current: Show current revision
  alembic history: Show migration history
  alembic downgrade -1: Rollback last migration
```

### 8.6 Side Effects
- Schema changes in database
- Application restart may be required
- Cache invalidation
- Background jobs may need pause

### 8.7 Metrics and Monitoring
```yaml
Metrics:
  - migration_duration_seconds (Histogram)
  - migration_success_total (Counter)
  - migration_failure_total (Counter)

Alerts:
  - Migration failure
  - Migration taking > 60 seconds
  - Schema drift detected
```

---

## 10. Testing Pipeline

### 10.1 Pipeline Name
**Automated Testing and Quality Assurance Pipeline**

### 10.2 Modules and Dependencies
```
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_services/
│   │   └── test_repositories/
│   ├── integration/
│   │   └── test_api/
│   └── fixtures/
│       └── factories.py
```

### 9.3 Classes and Methods (Call Sequence)
```python
# Unit Test Flow
# 1. pytest tests/unit/
# 2. Load test configuration
# 3. Mock external dependencies
# 4. Execute business logic tests
# 5. Verify expectations
# 6. Generate coverage report

# Integration Test Flow
# 1. pytest tests/integration/
# 2. Create test database
# 3. Apply migrations
# 4. Load fixtures
# 5. Create TestClient
# 6. Execute API tests
# 7. Verify responses and side effects
# 8. Cleanup test database

# Full Test Scenario
# 1. Register user and organization
# 2. Login and get tokens
# 3. Create contacts
# 4. Create deals
# 5. Update deal status
# 6. Create tasks
# 7. Add comments
# 8. Get analytics
# 9. Verify all permissions
```

### 9.4 Database Changes
```sql
-- Test database setup
CREATE DATABASE test_crm_db;

-- Test data fixtures
INSERT INTO users (email, hashed_password, name)
VALUES
    ('owner@test.com', '$2b$12$...', 'Test Owner'),
    ('admin@test.com', '$2b$12$...', 'Test Admin'),
    ('member@test.com', '$2b$12$...', 'Test Member');

-- Cleanup after tests
TRUNCATE TABLE activities, tasks, deals, contacts,
         organization_members, organizations, users CASCADE;
```

### 9.5 Endpoint Details
```yaml
Test Coverage Requirements:
  - Unit tests: 90% coverage minimum
  - Integration tests: All endpoints
  - Permission tests: All role combinations
  - Validation tests: All error cases
  - Performance tests: Response time < 500ms
```

### 9.6 Side Effects
- Test database creation/destruction
- Test cache instances
- Mock email sending
- Temporary file creation

### 9.7 Metrics and Monitoring
```yaml
Metrics:
  - test_execution_time_seconds (Histogram)
  - test_pass_rate (Gauge)
  - code_coverage_percent (Gauge)

Alerts:
  - Test failures in CI/CD
  - Coverage drop > 5%
  - Test execution time > 5 minutes
```

---

## 11. Error Handling Pipeline

### 11.1 Pipeline Name
**Exception Management and Error Recovery Pipeline**

### 11.2 Modules and Dependencies
```
├── app/
│   ├── core/
│   │   ├── exceptions.py
│   │   └── error_handlers.py
│   └── api/
│       └── middleware.py
```

### 11.3 Classes and Methods (Call Sequence)
```python
# Error Handling Flow
# 1. Exception raised in any layer
# 2. Exception middleware catches
# 3. Classify error type:
#    - ValidationError -> 400
#    - UnauthorizedError -> 401
#    - ForbiddenError -> 403
#    - NotFoundError -> 404
#    - ConflictError -> 409
#    - DatabaseError -> 500
# 4. Log error with context
# 5. Format error response
# 6. Return appropriate HTTP status

# Validation Error Flow
# 1. Pydantic validation fails
# 2. RequestValidationError raised
# 3. Extract field errors
# 4. Format user-friendly message
# 5. Return 400 with details

# Database Error Recovery
# 1. SQLAlchemy exception raised
# 2. Check for integrity constraint
# 3. If unique violation -> 409
# 4. If foreign key violation -> 400
# 5. Otherwise -> 500
# 6. Log full stack trace
# 7. Return generic error to client
```

### 11.4 Database Changes
```sql
-- Error logging table (optional)
CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id UUID,
    error_code VARCHAR(50),
    message TEXT,
    stack_trace TEXT,
    user_id UUID,
    organization_id UUID,
    endpoint VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for searching errors
CREATE INDEX idx_error_logs_created ON error_logs(created_at DESC);
CREATE INDEX idx_error_logs_user ON error_logs(user_id);
```

### 10.5 Endpoint Details
```yaml
Error Response Format:
  Base contract (applies to every error response):
    {
      "detail": "Human readable message",
      "code": "STABLE_ERROR_CODE"
    }

  Validation extensions (400 Bad Request):
    - Optional "errors" array surfaces field-level problems.
    - Example:
        {
          "detail": "Validation error",
          "code": "VALIDATION_ERROR",
          "errors": [
            {"field": "amount", "message": "Must be greater than 0"}
          ]
        }

  Authz/Authn errors (401/403):
    - Rely only on the base contract, e.g. {"detail": "Authentication required", "code": "AUTH_REQUIRED"}.

  Not found/conflict (404/409):
    - Also base contract only, mirroring the original assignment expectations.

  Server errors (500):
    - Base contract + optional "correlation_id" for debugging.
    - Example:
        {
          "detail": "Internal server error",
          "code": "INTERNAL_ERROR",
          "correlation_id": "uuid"
        }
```

### 10.6 Side Effects
- Error logging to file/database
- Monitoring alerts for 5xx errors
- Rate limiting counter increment
- Audit log entry for security errors

### 10.7 Metrics and Monitoring
```yaml
Metrics:
  - errors_total (Counter by status_code)
  - error_rate (Gauge by endpoint)
  - validation_errors_total (Counter by field)
  - database_errors_total (Counter)

Alerts:
  - Error rate > 5% for any endpoint
  - 5xx errors > 10/min
  - Database connection errors > 5/min
  - Authentication failures > 50/min
```

---

## Implementation Best Practices

### Security Guidelines
- All endpoints require JWT authentication except /auth/*
- Organization isolation enforced at repository layer
- SQL injection prevention via parameterized queries
- Rate limiting: 100 req/min per user
- Password hashing with bcrypt (cost=12)
- Secrets management via environment variables

### Performance Optimization
- Database connection pooling (min=5, max=20)
- Redis caching for analytics (TTL=5 min)
- Pagination mandatory for list endpoints
- Eager loading for related entities
- Database indexes on all foreign keys and search fields
- Async/await for all I/O operations

### Code Quality Standards
- Type hints for all public functions
- Pydantic models for request/response validation
- Dependency injection for services
- Unit test coverage minimum 90%
- Integration tests for all endpoints
- Docstrings for all classes and complex functions

### Deployment Considerations
- Docker containerization
- Environment-based configuration
- Health check endpoints
- Graceful shutdown handling
- Database migration automation
- Logging with correlation IDs
