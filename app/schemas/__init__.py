"""
Pydantic schemas package.
"""
from app.schemas.base import (
    BaseSchema,
    IDModelMixin,
    TimestampMixin,
    UpdateTimestampMixin,
    PaginatedResponse,
    ErrorResponse,
    MessageResponse
)
from app.schemas.auth_schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    OrganizationWithRole,
    LoginResponse,
    RegisterResponse
)
from app.schemas.organization_schemas import (
    OrganizationResponse,
    MemberListResponse,
    UpdateOrganizationRequest,
    AddMemberRequest,
    UpdateMemberRoleRequest
)
from app.schemas.contact_schemas import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactListResponse
)
from app.schemas.deal_schemas import (
    DealCreate,
    DealUpdate,
    DealResponse,
    DealListResponse,
    DealSummary
)
from app.schemas.task_schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse
)
from app.schemas.activity_schemas import (
    CommentCreate,
    ActivityResponse,
    TimelineResponse
)
from app.schemas.analytics_schemas import (
    DealsSummaryResponse,
    FunnelResponse,
    MetricsResponse
)

__all__ = [
    # Base
    "BaseSchema",
    "IDModelMixin",
    "TimestampMixin",
    "UpdateTimestampMixin",
    "PaginatedResponse",
    "ErrorResponse",
    "MessageResponse",
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "UserResponse",
    "OrganizationWithRole",
    "LoginResponse",
    "RegisterResponse",
    # Organization
    "OrganizationResponse",
    "MemberListResponse",
    "UpdateOrganizationRequest",
    "AddMemberRequest",
    "UpdateMemberRoleRequest",
    # Contact
    "ContactCreate",
    "ContactUpdate",
    "ContactResponse",
    "ContactListResponse",
    # Deal
    "DealCreate",
    "DealUpdate",
    "DealResponse",
    "DealListResponse",
    "DealSummary",
    # Task
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    # Activity
    "CommentCreate",
    "ActivityResponse",
    "TimelineResponse",
    # Analytics
    "DealsSummaryResponse",
    "FunnelResponse",
    "MetricsResponse",
]
