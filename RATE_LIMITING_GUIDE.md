# Rate Limiting Implementation Guide

## Overview

This guide provides complete documentation for the rate limiting implementation in the SecureInfo Concierge application. Rate limiting protects the API from abuse and ensures service availability for legitimate users.

## Table of Contents

1. [Why Rate Limiting](#why-rate-limiting)
2. [Implementation Details](#implementation-details)
3. [Rate Limits Configuration](#rate-limits-configuration)
4. [Security Benefits](#security-benefits)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Why Rate Limiting

Rate limiting is a critical security control that protects against:

- **LLM Resource Exhaustion**: LLM endpoints are computationally expensive and can be exploited with minimal effort
- **Brute Force Attacks**: Unlimited authentication attempts enable password guessing
- **Denial of Service (DoS)**: Single IP can overwhelm service with excessive requests
- **Data Scraping**: Prevents automated extraction of user data
- **Cost Control**: Limits expensive API usage

## Implementation Details

### Architecture

The rate limiting implementation uses the `slowapi` package, which provides:

- Per-IP rate limiting
- Configurable rate limits per endpoint
- Automatic rate limit enforcement
- Custom error handling

### Components

#### 1. Rate Limiter Module (`app/middleware/rate_limiter.py`)

Centralized configuration for all rate limits:

```python
RATE_LIMITS = {
    "llm": "10/minute",           # LLM endpoint
    "auth": "5/minute",            # Authentication
    "user_info": "30/minute",      # User info
    "health": "120/minute",        # Health checks
}
```

The module also provides:
- `limiter`: The slowapi Limiter instance
- `rate_limit_exceeded_handler`: Custom error handler for rate limit violations

#### 2. Main Application (`app/main.py`)

Integration with FastAPI:

```python
from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

#### 3. Protected Endpoints

Rate limits are applied using decorators:

```python
@router.post("/secure-query")
@limiter.limit("10/minute")
async def secure_query(request: Request, ...):
    # Endpoint logic
```

## Rate Limits Configuration

### Current Limits

| Endpoint | Limit | Protection Against |
|----------|-------|-------------------|
| `/api/secure-query` | 10/minute | LLM resource exhaustion, expensive computational abuse |
| `/api/token` | 5/minute | Brute force password attacks, credential stuffing |
| `/api/users/me` | 30/minute | Excessive user data requests |
| `/health`, `/ready` | 120/minute | Monitoring system overhead |

### Customizing Limits

To adjust rate limits, edit `app/middleware/rate_limiter.py`:

```python
RATE_LIMITS = {
    "llm": "20/minute",      # Increase LLM limit
    "auth": "10/minute",      # Increase auth limit
}
```

Then update the corresponding endpoint decorators.

### Rate Limit Format

Rate limits follow the format: `<count>/<period>`

Examples:
- `10/minute` - 10 requests per minute
- `100/hour` - 100 requests per hour
- `1000/day` - 1000 requests per day
- `5/second` - 5 requests per second

## Security Benefits

### 🛡️ Critical Protection: LLM Resource Exhaustion

**Problem**: LLMs require expensive computational resources (GPU time, memory) and can be exploited with simple automated requests.

**Solution**: Strict 10 requests/minute limit on `/api/secure-query`

**Impact**: 
- Prevents attackers from exhausting computational budget
- Ensures fair resource allocation among users
- Protects against financial loss from excessive API usage

### 🔒 Brute Force Prevention

**Problem**: Unlimited login attempts enable automated password guessing attacks.

**Solution**: 5 requests/minute limit on `/api/token`

**Impact**:
- Drastically reduces effectiveness of brute force attacks
- Typical brute force requires thousands of attempts
- With rate limit: 5 attempts/min = 300 attempts/hour vs unlimited
- Makes password cracking practically infeasible

### 🚦 DoS Mitigation

**Problem**: Single IP can overwhelm service with requests, making it unavailable for legitimate users.

**Solution**: Per-IP rate limiting on all endpoints

**Impact**:
- Maintains service availability during attack attempts
- Isolates impact to attacking IPs only
- Legitimate users from other IPs remain unaffected

### 📊 Data Protection

**Problem**: Automated tools can scrape user data through repeated API calls.

**Solution**: 30 requests/minute limit on `/api/users/me`

**Impact**:
- Prevents bulk data extraction
- Limits exposure of sensitive information
- Maintains user privacy

## Testing

### Running the Test Suite

The comprehensive test suite validates all rate limiting functionality:

```bash
# Ensure server is running in another terminal
python -m uvicorn app.main:app --reload

# Run tests
python test_rate_limiting.py
```

### Manual Testing

Test individual endpoints:

```bash
# Test LLM endpoint (should fail after 10 requests)
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/secure-query \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"test $i\"}"
  echo ""
done

# Test auth endpoint (should fail after 5 requests)
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test&password=wrong"
  echo ""
done
```

### Expected Error Response

When rate limited, endpoints return HTTP 429 with:

```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Please try again later.",
  "limit": "10 per 1 minute"
}
```

## Troubleshooting

### Rate Limit Too Strict

**Symptom**: Legitimate users being rate limited

**Solution**: 
1. Review rate limits in `app/middleware/rate_limiter.py`
2. Increase limits for affected endpoints
3. Consider implementing user-based rate limiting for authenticated users

### Rate Limiting Not Working

**Symptom**: Able to exceed rate limits without errors

**Check**:
1. Verify slowapi is properly initialized in `app/main.py`
2. Ensure `request: Request` parameter is present in endpoint signatures
3. Check that `@limiter.limit()` decorator is applied
4. Verify exception handler is registered

### Different Users Sharing Rate Limit

**Symptom**: Multiple users from same IP affected by same rate limit

**Explanation**: Rate limiting is per-IP by default (using `get_remote_address`)

**Solution**: For authenticated endpoints, consider switching to user-based rate limiting:

```python
from slowapi.util import get_remote_address

def get_user_id(request: Request):
    # Extract user ID from JWT token
    return get_current_user(request).username

limiter = Limiter(key_func=get_user_id)
```

## Best Practices

### 1. Set Appropriate Limits

- **Expensive Operations**: Lower limits (e.g., LLM: 10/min)
- **Authentication**: Very low limits (e.g., 5/min)
- **Read Operations**: Moderate limits (e.g., 30/min)
- **Health Checks**: High limits (e.g., 120/min)

### 2. Monitor Rate Limit Violations

Check logs for rate limit violations:

```bash
grep "Rate limit exceeded" /var/log/app.log
```

This helps identify:
- Legitimate users hitting limits (may need adjustment)
- Automated attack attempts
- Unusual traffic patterns

### 3. Document Rate Limits

Include rate limits in API documentation so users know the constraints.

### 4. Provide Clear Error Messages

The current implementation provides:
- HTTP 429 status code
- Clear error message
- Specific rate limit information

### 5. Consider Tiered Rate Limits

For production systems, consider:
- Higher limits for authenticated users
- Premium tiers with higher limits
- Temporary rate limit increases for specific use cases

### 6. Test Rate Limits Regularly

- Run automated tests before deployments
- Monitor rate limit effectiveness in production
- Adjust based on actual usage patterns

## Advanced Configuration

### Redis Backend (Production)

For production deployments with multiple application instances, use Redis:

```python
from slowapi.util import get_remote_address
from slowapi import Limiter

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

### Custom Key Functions

Rate limit by user instead of IP:

```python
def get_user_identifier(request: Request):
    # For authenticated requests
    if hasattr(request.state, "user"):
        return request.state.user.username
    # Fallback to IP for unauthenticated
    return get_remote_address(request)

limiter = Limiter(key_func=get_user_identifier)
```

### Dynamic Rate Limits

Adjust limits based on user tier:

```python
@router.post("/api/secure-query")
async def secure_query(request: Request):
    user = get_current_user(request)
    limit = "100/minute" if user.is_premium else "10/minute"
    
    limiter.limit(limit)(secure_query)
    # Endpoint logic
```

## Conclusion

Rate limiting is a critical security control that protects against multiple attack vectors while ensuring service availability. This implementation provides comprehensive protection with minimal performance impact and is fully backwards compatible with existing functionality.

For questions or issues, consult the troubleshooting section or review the test suite for examples.
