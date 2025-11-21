"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, close_db
from app.api.middleware import setup_middleware
from app.api.v1 import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting CRM API...")
    print(f"📊 Environment: {settings.environment}")
    print(f"🔧 Debug mode: {settings.debug}")
    print("🌐 API version: v1")

    yield

    # Shutdown
    print("👋 Shutting down CRM API...")
    await close_db()
    print("✅ Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Multi-Tenant CRM API",
    description="FastAPI-based CRM system with multi-tenancy and RBAC",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan
)

# Setup middleware
setup_middleware(app)

# Include API v1 router
app.include_router(
    api_v1_router,
    prefix=settings.api_v1_prefix
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Check if API is running and database is accessible."
)
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        Status message
    """
    try:
        # Test database connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "environment": settings.environment,
                "version": "1.0.0"
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get(
    "/",
    tags=["Root"],
    summary="API root",
    description="Get API information."
)
async def root():
    """
    API root endpoint.

    Returns:
        Welcome message and API info
    """
    return {
        "message": "Multi-Tenant CRM API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
