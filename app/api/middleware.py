"""
FastAPI middleware for error handling, logging, and CORS.
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import AppException


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle application exceptions globally.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle request and catch exceptions.

        Args:
            request: HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        try:
            response = await call_next(request)
            return response

        except AppException as exc:
            # Handle custom application exceptions
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error_code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details
                }
            )

        except Exception as exc:
            # Handle unexpected exceptions
            error_id = str(uuid.uuid4())
            print(f"[ERROR {error_id}] Unexpected error: {str(exc)}")

            if settings.debug:
                # In debug mode, return detailed error
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "message": f"Internal server error: {str(exc)}",
                        "error_id": error_id
                    }
                )
            else:
                # In production, return generic error
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "message": "An internal server error occurred",
                        "error_id": error_id
                    }
                )


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to each request.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add request ID to request state and response headers.

        Args:
            request: HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response with X-Request-ID header
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details.

        Args:
            request: HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        start_time = time.time()

        # Get request ID if available
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request
        print(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        print(
            f"[{request_id}] {response.status_code} "
            f"completed in {duration:.3f}s"
        )

        return response


def setup_cors(app):
    """
    Setup CORS middleware.

    Args:
        app: FastAPI application
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]
    )


def setup_middleware(app):
    """
    Setup all middleware for the application.

    Args:
        app: FastAPI application
    """
    # Add CORS middleware
    setup_cors(app)

    # Add custom middleware (in reverse order of execution)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
