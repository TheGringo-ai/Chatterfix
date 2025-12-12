"""
Middleware package for ChatterFix CMMS
Contains error tracking, logging, and monitoring middleware
"""

from app.middleware.error_tracking import ErrorTrackingMiddleware

__all__ = ["ErrorTrackingMiddleware"]
