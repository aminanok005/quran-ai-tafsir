"""
Middleware for QURAN AI API service

Contains rate limiting, caching, and other middleware components.
"""

import time
import hashlib
from functools import wraps
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import redis
from redis.exceptions import RedisError
import json

from .config import settings

class RateLimitMiddleware:
    """Rate limiting middleware for API endpoints."""

    def __init__(self, limit: int = 100, window: int = 60):
        self.limit = limit
        self.window = window
        self.redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    async def __call__(self, request: Request, call_next):
        """Apply rate limiting to the request."""
        client_ip = request.client.host
        cache_key = f"rate_limit:{client_ip}:{request.url.path}"

        try:
            # Get current request count
            current_count = self.redis.get(cache_key)
            current_count = int(current_count) if current_count else 0

            if current_count >= self.limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {self.limit} requests per {self.window} seconds",
                        "retry_after": self.window,
                        "timestamp": str(time.time())
                    }
                )

            # Increment counter
            self.redis.setex(
                cache_key,
                self.window,
                current_count + 1
            )

            response = await call_next(request)
            return response

        except RedisError as e:
            # If Redis fails, proceed without rate limiting
            print(f"Redis error: {e}")
            response = await call_next(request)
            return response
        except Exception as e:
            print(f"Rate limiting error: {e}")
            response = await call_next(request)
            return response

class CacheMiddleware:
    """Caching middleware for API endpoints."""

    def __init__(self, cache_key: str, ttl: int = 3600):
        self.cache_key = cache_key
        self.ttl = ttl
        self.redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    async def __call__(self, request: Request, call_next):
        """Apply caching to the request."""
        # Generate cache key based on request
        cache_key = self._generate_cache_key(request)

        try:
            # Try to get cached response
            cached_response = self.redis.get(cache_key)
            if cached_response:
                # Return cached response
                response_data = json.loads(cached_response)
                status_code = response_data.get("status_code", 200)
                headers = response_data.get("headers", {})
                body = response_data.get("body", {})

                response = JSONResponse(content=body, status_code=status_code)
                for key, value in headers.items():
                    response.headers[key] = value

                # Add cache hit header
                response.headers["X-Cache-Status"] = "HIT"
                return response

            # Execute request
            response = await call_next(request)

            # Cache successful responses
            if response.status_code < 400 and response.status_code != 404:
                response_data = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.body
                }

                self.redis.setex(cache_key, self.ttl, json.dumps(response_data))

                # Add cache miss header
                response.headers["X-Cache-Status"] = "MISS"

            return response

        except RedisError as e:
            # If Redis fails, proceed without caching
            print(f"Redis cache error: {e}")
            response = await call_next(request)
            return response
        except Exception as e:
            print(f"Cache middleware error: {e}")
            response = await call_next(request)
            return response

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request."""
        # Include method, path, and query parameters
        path = request.url.path
        query_params = dict(request.url.query_params)

        # Sort query params for consistent key
        sorted_params = sorted(query_params.items()) if query_params else []

        # Create cache key
        key_data = {
            "method": request.method,
            "path": path,
            "params": sorted_params
        }

        # Use hash for key
        key_string = json.dumps(key_data, sort_keys=True)
        return f"{self.cache_key}:{hashlib.md5(key_string.encode()).hexdigest()}"
class SecurityMiddleware:
    """Security middleware for API endpoints."""

    async def __call__(self, request: Request, call_next):
        """Apply security checks to the request."""
        # Check for suspicious patterns in request
        if self._is_suspicious_request(request):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Security violation",
                    "message": "Request blocked for security reasons"
                }
            )

        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    def _is_suspicious_request(self, request: Request) -> bool:
        """Check if request appears suspicious."""
        # Check for common attack patterns
        suspicious_patterns = [
            "<script",
            "javascript:",
            "onload=",
            "onerror=",
            "eval(",
            "sql",
            "union select",
            "drop table",
            "insert into",
            "update set",
            "delete from"
        ]

        request_text = request.url.query + str(request.headers)

        for pattern in suspicious_patterns:
            if pattern.lower() in request_text.lower():
                return True

        return False
class ValidationMiddleware:
    """Request/Response validation middleware."""

    async def __call__(self, request: Request, call_next):
        """Validate request and response."""
        # Validate request
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" not in content_type:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid content type",
                        "message": "Content-Type must be application/json"
                    }
                )

            try:
                # Try to parse JSON to validate
                await request.json()
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid JSON",
                        "message": "Request body must be valid JSON"
                    }
                )

        response = await call_next(request)
        return response