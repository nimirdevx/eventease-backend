"""
Custom exception handlers for the EventEase API
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventEaseException(Exception):
    """Base exception for EventEase application"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class UserAlreadyExistsError(EventEaseException):
    """Raised when trying to create a user that already exists"""
    def __init__(self, email: str):
        message = f"User with email {email} already exists"
        super().__init__(message, 409)

class UserNotFoundError(EventEaseException):
    """Raised when user is not found"""
    def __init__(self, identifier: str):
        message = f"User {identifier} not found"
        super().__init__(message, 404)

class EventNotFoundError(EventEaseException):
    """Raised when event is not found"""
    def __init__(self, event_id: int):
        message = f"Event with ID {event_id} not found"
        super().__init__(message, 404)

class UnauthorizedError(EventEaseException):
    """Raised when user is not authorized"""
    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message, 403)

class AlreadyRegisteredError(EventEaseException):
    """Raised when user is already registered for an event"""
    def __init__(self, event_id: int):
        message = f"User is already registered for event {event_id}"
        super().__init__(message, 409)

async def eventease_exception_handler(request: Request, exc: EventEaseException):
    """Handle custom EventEase exceptions"""
    logger.error(f"EventEase exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "type": exc.__class__.__name__
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    
    # Extract meaningful error messages
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"]) if error["loc"] else "unknown"
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation failed",
            "details": errors,
            "type": "ValidationError"
        }
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    logger.error(f"Database integrity error: {str(exc)}")
    
    # Common integrity error messages
    if "Duplicate entry" in str(exc) and "email" in str(exc):
        message = "Email address is already registered"
    elif "Duplicate entry" in str(exc):
        message = "Duplicate entry detected"
    elif "foreign key constraint" in str(exc).lower():
        message = "Referenced record does not exist"
    else:
        message = "Database constraint violation"
    
    return JSONResponse(
        status_code=409,
        content={
            "error": True,
            "message": message,
            "type": "IntegrityError"
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions"""
    logger.error(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "type": "HTTPException"
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected error occurred",
            "type": "InternalServerError"
        }
    )
