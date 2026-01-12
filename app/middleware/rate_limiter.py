"""
Rate limiting configuration module for API protection.

This module provides centralized rate limiting configuration using slowapi
to protect against various types of attacks including:
- LLM resource exhaustion
- Brute force authentication attempts
- Denial of Service (DoS) attacks
"""

import logging
from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logger = logging.getLogger(__name__)

# Rate limit definitions for different endpoint types
RATE_LIMITS = {
    "llm": "10/minute",           # LLM endpoint - expensive computational resources
    "auth": "5/minute",            # Authentication - brute force prevention
    "user_info": "30/minute",      # User info endpoint - data access control
    "health": "120/minute",        # Health checks - monitoring overhead reduction
}

# Initialize slowapi limiter with per-IP tracking
limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom error handler for rate limit exceeded exceptions.
    
    Logs rate limit violations and returns structured error response.
    
    Args:
        request: The FastAPI request object
        exc: The RateLimitExceeded exception
        
    Returns:
        JSONResponse with 429 status code and error details
    """
    from fastapi.responses import JSONResponse
    
    # Log rate limit violation with client info
    client_ip = get_remote_address(request)
    logger.warning(
        f"Rate limit exceeded for IP {client_ip} on endpoint {request.url.path}. "
        f"Limit: {exc.detail}"
    )
    
    # Extract rate limit details for user-friendly message
    limit_str = str(exc.detail)
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. You have exceeded the rate limit of {limit_str}. Please try again later.",
            "limit": limit_str
        }
    )
