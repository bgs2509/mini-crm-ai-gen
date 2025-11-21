# Detailed API Testing Plan for Mini-CRM

## Goal
Test all API endpoints and populate the database with 10-20 records in each table with various data scenarios.

## Testing Methodology
For each endpoint:
1. **Step 1**: Endpoint name, expected behavior, reference to docs/senior-python-crm-assignment.md
2. **Step 2**: Call the endpoint and verify no errors, check if everything went according to plan
3. **Step 3**: Analyze how the endpoint changed data in the database and whether it matches expectations
4. **Step 4**: If there are errors - fix them

## Database Population Plan

### Users Table (Target: 12 users)
1. owner1@example.com - Owner of Org1 (Acme Inc)
2. owner2@example.com - Owner of Org2 (TechCorp)
3. owner3@example.com - Owner of Org3 (StartupXYZ)
4. admin1@example.com - Admin in Org1
5. admin2@example.com - Admin in Org2
6. manager1@example.com - Manager in Org1
7. manager2@example.com - Manager in Org2
8. manager3@example.com - Manager in Org3
9. member1@example.com - Member in Org1
10. member2@example.com - Member in Org2
11. member3@example.com - Member in Org3
12. member4@example.com - Member in Org1

### Organizations Table (Target: 3 organizations)
1. Acme Inc - Main testing org with most data
2. TechCorp - Secondary org for testing multi-tenancy
3. StartupXYZ - Third org for isolation testing

### OrganizationMember Table (Target: 15 memberships)
- Org1 (Acme Inc): owner1, admin1, manager1, member1, member4, admin2 (cross-org)
- Org2 (TechCorp): owner2, admin2, manager2, member2, manager1 (cross-org)
- Org3 (StartupXYZ): owner3, manager3, member3

### Contacts Table (Target: 20 contacts)
#### Org1 Contacts (12 contacts):
1. John Doe - owned by owner1
2. Jane Smith - owned by owner1
3. Bob Johnson - owned by admin1
4. Alice Williams - owned by manager1
5. Charlie Brown - owned by member1
6. David Lee - owned by member1
7. Emma Wilson - owned by owner1
8. Frank Miller - owned by admin1
9. Grace Davis - owned by manager1
10. Henry Garcia - owned by member4
11. Ivy Martinez - owned by member4
12. Jack Robinson - owned by owner1

#### Org2 Contacts (6 contacts):
13. Kate Anderson - owned by owner2
14. Leo Thomas - owned by admin2
15. Mary Jackson - owned by manager2
16. Nathan White - owned by member2
17. Olivia Harris - owned by owner2
18. Peter Martin - owned by admin2

#### Org3 Contacts (2 contacts):
19. Quinn Thompson - owned by owner3
20. Rachel Moore - owned by manager3

### Deals Table (Target: 22 deals with various statuses and stages)
#### Org1 Deals (15 deals):
1. Deal: Website Redesign - new/qualification - $10,000 USD - Contact: John Doe - Owner: owner1
2. Deal: Mobile App Development - in_progress/proposal - $50,000 USD - Contact: Jane Smith - Owner: owner1
3. Deal: SEO Optimization - in_progress/negotiation - $5,000 EUR - Contact: Bob Johnson - Owner: admin1
4. Deal: Cloud Migration - won/closed - $100,000 USD - Contact: Alice Williams - Owner: manager1
5. Deal: Data Analytics - lost/closed - $25,000 USD - Contact: Charlie Brown - Owner: member1
6. Deal: CRM Implementation - new/qualification - $75,000 EUR - Contact: David Lee - Owner: member1
7. Deal: Security Audit - in_progress/proposal - $15,000 USD - Contact: Emma Wilson - Owner: owner1
8. Deal: API Integration - in_progress/negotiation - $20,000 USD - Contact: Frank Miller - Owner: admin1
9. Deal: Training Program - won/closed - $8,000 EUR - Contact: Grace Davis - Owner: manager1
10. Deal: Consulting Services - new/qualification - $30,000 USD - Contact: Henry Garcia - Owner: member4
11. Deal: Logo Design - in_progress/proposal - $3,000 USD - Contact: Ivy Martinez - Owner: member4
12. Deal: Infrastructure Setup - won/closed - $45,000 EUR - Contact: Jack Robinson - Owner: owner1
13. Deal: Marketing Campaign - in_progress/negotiation - $12,000 USD - Contact: John Doe - Owner: owner1
14. Deal: Software License - new/qualification - $5,500 USD - Contact: Jane Smith - Owner: admin1
15. Deal: Support Contract - lost/closed - $18,000 EUR - Contact: Bob Johnson - Owner: manager1

#### Org2 Deals (5 deals):
16. Deal: ERP System - in_progress/proposal - $200,000 USD - Contact: Kate Anderson - Owner: owner2
17. Deal: Hardware Upgrade - new/qualification - $35,000 EUR - Contact: Leo Thomas - Owner: admin2
18. Deal: Network Setup - won/closed - $28,000 USD - Contact: Mary Jackson - Owner: manager2
19. Deal: Database Optimization - in_progress/negotiation - $15,000 USD - Contact: Nathan White - Owner: member2
20. Deal: Backup Solution - new/qualification - $9,000 EUR - Contact: Olivia Harris - Owner: owner2

#### Org3 Deals (2 deals):
21. Deal: MVP Development - in_progress/proposal - $80,000 USD - Contact: Quinn Thompson - Owner: owner3
22. Deal: Brand Identity - new/qualification - $12,000 USD - Contact: Rachel Moore - Owner: manager3

### Tasks Table (Target: 30 tasks with various statuses)
#### Open Tasks (15 tasks):
- 5 tasks due in the future (not done)
- 5 tasks due today (not done)
- 5 tasks overdue (not done, past due_date)

#### Completed Tasks (15 tasks):
- 5 completed on time
- 5 completed early
- 5 completed late

Tasks will be distributed across all deals with variety of titles:
- Call client
- Send proposal
- Schedule demo
- Follow up email
- Prepare contract
- Review requirements
- Conduct meeting
- Update documentation
- Get approval
- Send invoice
- etc.

### Activity Table (Target: 40+ activities)
#### Types of activities:
1. **comment** - User-created comments via POST /api/v1/deals/{deal_id}/activities (20 activities)
2. **status_changed** - Automatically created when deal status changes (10 activities)
   - Created by business logic in DealService when status is updated
   - Payload contains old and new status values
3. **stage_changed** - Automatically created when deal stage changes (8 activities)
   - Created by business logic in DealService when stage transitions
   - Payload contains old and new stage values
4. **task_created** - Task creation events (optional, if implemented)
5. **system** - System events (2 activities)

**Important**: Activities with types "status_changed" and "stage_changed" are created automatically
by the business logic (not via API calls) and must be verified during testing.

Activities distributed across all deals, especially deals with status/stage changes.

## Testing Sequence

### Phase 1: Authentication & Organizations (Endpoints: 4)
1. POST /api/v1/auth/register - Register 12 users with their initial organizations
2. POST /api/v1/auth/login - Login each user to get tokens
3. POST /api/v1/auth/refresh - Test token refresh for 2-3 users
4. GET /api/v1/organizations/me - Get organizations for each user

### Phase 2: Contacts Management (Endpoints: 5)
5. POST /api/v1/contacts - Create 20 contacts across 3 organizations
6. GET /api/v1/contacts - List contacts with various filters (pagination, search, owner_id)
7. GET /api/v1/contacts/{contact_id} - Get individual contacts
8. PUT /api/v1/contacts/{contact_id} - Update several contacts
9. DELETE /api/v1/contacts/{contact_id} - Try to delete (should fail if has deals)

### Phase 3: Deals Management (Endpoints: 5)
10. POST /api/v1/deals - Create 22 deals with different statuses/stages
11. GET /api/v1/deals - List deals with filters (status, stage, amount, owner_id, sorting)
12. GET /api/v1/deals/{deal_id} - Get individual deals
13. PATCH /api/v1/deals/{deal_id} - Update deals (test status transitions, validations)
    - **IMPORTANT**: Verify automatic Activity creation when status/stage changes
    - Test status change to "won" → verify Activity with type="status_changed" is created
    - Test stage transitions → verify Activity with type="stage_changed" is created
14. DELETE /api/v1/deals/{deal_id} - Delete some deals

### Phase 4: Tasks Management (Endpoints: 8)
15. POST /api/v1/tasks - Create 30 tasks for various deals
16. GET /api/v1/tasks - List tasks with filters (deal_id, only_open, due_before/after)
17. GET /api/v1/tasks/{task_id} - Get individual tasks
18. PATCH /api/v1/tasks/{task_id} - Update tasks (description, due_date)
19. POST /api/v1/tasks/{task_id}/done - Mark tasks as done
20. POST /api/v1/tasks/{task_id}/undone - Unmark tasks
21. GET /api/v1/tasks/overdue/by-deal/{deal_id} - Get overdue tasks (additional endpoint)
22. DELETE /api/v1/tasks/{task_id} - Delete some tasks

### Phase 5: Activities Timeline (Endpoints: 2)
23. POST /api/v1/deals/{deal_id}/activities - Create comment activities (manual)
24. GET /api/v1/deals/{deal_id}/activities - Get activity timeline for deals
    - **Verify automatic activities** created by system:
      - Activities with type="status_changed" from Phase 3 status updates
      - Activities with type="stage_changed" from Phase 3 stage transitions
    - **Verify manual activities** created via POST endpoint:
      - Activities with type="comment" from user interactions

### Phase 6: Analytics (Endpoints: 2)
25. GET /api/v1/analytics/deals/summary - Get deals summary for each org
26. GET /api/v1/analytics/deals/funnel - Get sales funnel for each org

### Phase 7: Permission Testing
**Cross-organization access tests:**
- Test accessing resources from different organization (should fail with 403/404)
- Test member trying to access another org's contacts/deals/tasks

**Role-based permission tests:**
- **Member role:**
  - Can only modify their own contacts, deals, and tasks
  - Cannot modify resources owned by other users
  - Cannot rollback deal stages
- **Manager role:**
  - Can modify all resources within organization
  - Can rollback deal stages
- **Admin/Owner roles:**
  - Have full access to all organization resources
  - Can perform any operation

**Business validation rules tests:**
- Cannot close deal as won with amount <= 0
- Cannot delete contact with active deals
- Cannot create task for other user's deal (if member)
- Cannot set due_date in the past
- Cannot rollback stage (for members)

## Total Endpoints to Test: 26 endpoints (25 required + 1 additional)
## Expected Database Records:
- Users: 12
- Organizations: 3
- OrganizationMembers: 15
- Contacts: 20
- Deals: 22
- Tasks: 30
- Activities: 40+

## Notes:
- Each test will include database verification using SQL queries
- All responses will be validated for correct status codes and data structure
- Error cases will be tested along with success cases
- Performance will be noted (though not a primary concern)
