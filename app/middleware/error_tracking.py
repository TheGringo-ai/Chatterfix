"""
Error Tracking Middleware for ChatterFix CMMS

This middleware captures and logs all unhandled exceptions in a structured format.
It integrates with external monitoring services (Sentry, Cloud Logging, etc.)
and returns user-friendly error responses.
"""

import logging
import sys
import traceback
from datetime import datetime
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log all application errors with structured logging.

    Features:
    - Captures all unhandled exceptions
    - Structured logging with context (request info, timestamps, etc.)
    - Integration hooks for external monitoring services
    - User-friendly error responses
    - Special handling for import errors
    """

    def __init__(
        self,
        app,
        sentry_dsn: Optional[str] = None,
        environment: str = "development",
    ):
        """
        Initialize error tracking middleware.

        Args:
            app: FastAPI application instance
            sentry_dsn: Optional Sentry DSN for error tracking
            environment: Environment name (development, staging, production)
        """
        super().__init__(app)
        self.environment = environment
        self.sentry_dsn = sentry_dsn

        # Initialize Sentry if DSN is provided
        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.fastapi import FastApiIntegration
                from sentry_sdk.integrations.starlette import StarletteIntegration

                sentry_sdk.init(
                    dsn=sentry_dsn,
                    environment=environment,
                    integrations=[
                        StarletteIntegration(),
                        FastApiIntegration(),
                    ],
                    traces_sample_rate=1.0 if environment == "production" else 0.1,
                )
                logger.info(f"✅ Sentry initialized for {environment}")
            except ImportError:
                logger.warning(
                    "⚠️ Sentry SDK not installed. Install with: pip install sentry-sdk"
                )
            except Exception:
                logger.error("❌ Failed to initialize Sentry")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle any exceptions.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            Response: HTTP response (either from handler or error response)
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the error with structured format
            error_details = self._create_error_details(request, exc)
            self._log_error(error_details)

            # Send to external monitoring if configured
            self._send_to_monitoring(exc, error_details)

            # Return user-friendly error response
            return self._create_error_response(exc, error_details)

    def _create_error_details(self, request: Request, exc: Exception) -> dict:
        """
        Create structured error details for logging and monitoring.

        Args:
            request: The HTTP request that caused the error
            exc: The exception that was raised

        Returns:
            dict: Structured error information
        """
        # Get exception traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        traceback_str = "".join(tb_lines)

        # Check if this is an import error
        is_import_error = self._is_import_error(exc, traceback_str)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "is_import_error": is_import_error,
            "traceback": traceback_str,
            "request": {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "headers": dict(request.headers),
                "client": request.client.host if request.client else None,
            },
        }

    def _is_import_error(self, exc: Exception, traceback_str: str) -> bool:
        """
        Check if the exception is related to import errors.

        Args:
            exc: The exception
            traceback_str: Full traceback string

        Returns:
            bool: True if this is an import-related error
        """
        import_error_indicators = [
            "ImportError",
            "ModuleNotFoundError",
            "cannot import name",
            "No module named",
            "ImportWarning",
        ]

        # Check exception type
        if any(
            indicator in type(exc).__name__ for indicator in import_error_indicators
        ):
            return True

        # Check traceback
        if any(indicator in traceback_str for indicator in import_error_indicators):
            return True

        return False

    def _log_error(self, error_details: dict) -> None:
        """
        Log the error with structured format.

        Args:
            error_details: Structured error information
        """
        # Determine log level based on error type
        is_import_error = error_details.get("is_import_error", False)
        log_level = logging.CRITICAL if is_import_error else logging.ERROR

        # Create structured log message
        log_message = (
            f"{'�� IMPORT ERROR' if is_import_error else '❌ ERROR'}: "
            f"{error_details['error_type']}: {error_details['error_message']}\n"
            f"📍 Path: {error_details['request']['method']} {error_details['request']['path']}\n"
            f"🕐 Time: {error_details['timestamp']}\n"
            f"🌍 Environment: {error_details['environment']}\n"
        )

        # Log with appropriate level
        logger.log(
            log_level,
            log_message,
            extra={
                "error_details": error_details,
                "structured": True,
            },
        )

        # Also log full traceback at debug level
        logger.debug(f"Full traceback:\n{error_details['traceback']}")

    def _send_to_monitoring(self, exc: Exception, error_details: dict) -> None:
        """
        Send error to external monitoring services.

        Args:
            exc: The exception
            error_details: Structured error information
        """
        # If Sentry is configured, it will automatically capture the exception
        # Additional custom monitoring can be added here
        try:
            # Example: Send to custom monitoring endpoint
            # This is a placeholder for custom monitoring integration
            # monitoring_client.send_error(error_details)
            pass
        except Exception:
            logger.warning("⚠️ Failed to send error to monitoring")

    def _create_error_response(
        self, exc: Exception, error_details: dict
    ) -> JSONResponse:
        """
        Create user-friendly error response.

        Args:
            exc: The exception
            error_details: Structured error information

        Returns:
            JSONResponse: HTTP error response
        """
        is_import_error = error_details.get("is_import_error", False)

        # Determine status code and message
        if is_import_error:
            status_code = 503  # Service Unavailable
            user_message = (
                "The service is temporarily unavailable due to a configuration issue. "
                "Please try again later or contact support."
            )
        else:
            status_code = 500  # Internal Server Error
            user_message = (
                "An unexpected error occurred. "
                "Our team has been notified and is working on a fix."
            )

        # Include error details in development mode
        response_data = {
            "error": True,
            "message": user_message,
            "timestamp": error_details["timestamp"],
        }

        # Add debug information in non-production environments
        if self.environment != "production":
            response_data["debug"] = {
                "error_type": error_details["error_type"],
                "error_message": error_details["error_message"],
                "path": error_details["request"]["path"],
            }

        return JSONResponse(
            status_code=status_code,
            content=response_data,
        )
