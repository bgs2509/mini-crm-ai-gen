"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.jwt import get_user_id_from_token, verify_token_type
from app.core.exceptions import InvalidTokenError
from app.models.organization_member import MemberRole
from app.schemas.auth_schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    OrganizationWithRole
)
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register new user with organization. User becomes organization owner."
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user and create organization.

    - **email**: Valid email address
    - **password**: Min 8 chars with uppercase, lowercase, and digit
    - **name**: User full name
    - **organization_name**: Name for new organization
    """
    service = AuthService(db)

    user, organization, tokens = await service.register_user(
        email=data.email,
        password=data.password,
        name=data.name,
        organization_name=data.organization_name
    )

    return RegisterResponse(
        user=UserResponse.model_validate(user),
        organization=OrganizationWithRole(
            id=organization.id,
            name=organization.name,
            role=MemberRole.OWNER,
            created_at=organization.created_at
        ),
        tokens=TokenResponse(**tokens)
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login user",
    description="Authenticate user and return tokens with organizations list."
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and get access tokens.

    - **email**: User email
    - **password**: User password

    Returns user info, organizations list, and JWT tokens.
    """
    service = AuthService(db)

    user, organizations, tokens = await service.login_user(
        email=data.email,
        password=data.password
    )

    return LoginResponse(
        user=UserResponse.model_validate(user),
        organizations=[
            OrganizationWithRole(
                id=member.organization.id,
                name=member.organization.name,
                role=member.role,
                created_at=member.organization.created_at
            )
            for member in organizations
        ],
        tokens=TokenResponse(**tokens)
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Get new access and refresh tokens using refresh token."
)
async def refresh_tokens(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access and refresh tokens.

    - **refresh_token**: Valid refresh token

    Returns new token pair.
    """
    # Verify token is refresh token
    if not verify_token_type(data.refresh_token, "refresh"):
        raise InvalidTokenError("Invalid token type")

    # Get user ID from token
    user_id = get_user_id_from_token(data.refresh_token)

    # Generate new tokens
    service = AuthService(db)
    tokens = await service.refresh_tokens(user_id)

    return TokenResponse(**tokens)
