from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from app.routers import auth, events, admin, interactions
from app.exceptions import (
    EventEaseException,
    eventease_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    http_exception_handler,
    general_exception_handler
)
from fastapi.staticfiles import StaticFiles
import os

# Create FastAPI app with enhanced metadata
app = FastAPI(
    title="EventEase API",
    description="A comprehensive event management system with user authentication, event creation, and ticket generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        # Add your production frontend URL here
        # "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With"
    ],
)

# Register exception handlers
app.add_exception_handler(EventEaseException, eventease_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add handler for 404 errors
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": True,
            "message": "Endpoint not found",
            "type": "NotFoundError"
        }
    )

# Add handler for 405 errors
@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    return JSONResponse(
        status_code=405,
        content={
            "error": True,
            "message": "Method not allowed",
            "type": "MethodNotAllowedError"
        }
    )

@app.get("/", tags=["Health"])
def root():
    """Root endpoint to check API health"""
    return {
        "message": "EventEase API is running 🚀",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2025-08-31T00:00:00Z"
    }

os.makedirs("tickets", exist_ok=True)

# Serve static files from the "tickets" folder
app.mount("/tickets", StaticFiles(directory="tickets"), name="tickets")

# Register routers
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(admin.router)
app.include_router(interactions.router)

