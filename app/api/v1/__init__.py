"""
API v1 package.
"""
from fastapi import APIRouter

from app.api.v1 import auth, organizations, contacts, deals, analytics, tasks, activities

# Create API v1 router
router = APIRouter()

# Include all routers
router.include_router(auth.router)
router.include_router(organizations.router)
router.include_router(contacts.router)
router.include_router(deals.router)
router.include_router(analytics.router)
router.include_router(tasks.router)
router.include_router(activities.router)

__all__ = ["router"]
