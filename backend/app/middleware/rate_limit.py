"""
Application-Level Rate Limiting Middleware
Implements per-user and per-endpoint rate limiting using Redis
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based rate limiting middleware for API endpoints.
    Provides fine-grained rate limiting per user, per endpoint, and per IP.
    """

    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None

        # Rate limit configurations (requests per time window)
        self.rate_limits = {
            "default": {"requests": 60, "window": 60},  # 60 req/min
            "auth": {"requests": 5, "window": 60},  # 5 req/min for auth
            "upload": {"requests": 10, "window": 60},  # 10 req/min for uploads
            "export": {"requests": 5, "window": 300},  # 5 req/5min for exports
            "api_call": {"requests": 100, "window": 60},  # 100 req/min for authenticated API
        }

    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Rate limit Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {e}")
            raise

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request."""
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Initialize Redis if not already done
        if self.redis_client is None:
            await self.initialize()

        # Determine rate limit tier
        tier = self._get_rate_limit_tier(request)
        config = self.rate_limits.get(tier, self.rate_limits["default"])

        # Get identifier (user ID or IP address)
        identifier = self._get_identifier(request)

        # Check rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(
            identifier=identifier,
            tier=tier,
            max_requests=config["requests"],
            window_seconds=config["window"]
        )

        if not allowed:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for {identifier} on {request.url.path}"
            )

            # Return rate limit error
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Try again in {reset_time} seconds.",
                    "retry_after": reset_time
                },
                headers={
                    "X-RateLimit-Limit": str(config["requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + reset_time)),
                    "Retry-After": str(reset_time)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + reset_time))

        return response

    def _get_rate_limit_tier(self, request: Request) -> str:
        """Determine rate limit tier based on request path."""
        path = str(request.url.path)

        if "/auth/" in path:
            return "auth"
        elif "/upload" in path or "/files/" in path:
            return "upload"
        elif "/export" in path:
            return "export"
        elif "/api/" in path:
            return "api_call"
        else:
            return "default"

    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting (user ID or IP)."""
        # Prefer user ID if authenticated
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        if request.client:
            return f"ip:{request.client.host}"

        # Default identifier
        return "anonymous"

    async def _check_rate_limit(
        self,
        identifier: str,
        tier: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit using sliding window.

        Returns:
            Tuple of (allowed, remaining_requests, reset_time_seconds)
        """
        try:
            # Redis key for this rate limit
            key = f"ratelimit:{tier}:{identifier}"

            # Current timestamp
            now = int(time.time())

            # Remove old entries outside the window
            await self.redis_client.zremrangebyscore(
                key,
                0,
                now - window_seconds
            )

            # Count requests in current window
            current_count = await self.redis_client.zcard(key)

            if current_count >= max_requests:
                # Rate limit exceeded
                # Get oldest entry to calculate reset time
                oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1]) + window_seconds - now
                else:
                    reset_time = window_seconds

                return False, 0, reset_time

            # Add current request to window
            await self.redis_client.zadd(key, {str(now): now})

            # Set expiration on key
            await self.redis_client.expire(key, window_seconds)

            # Calculate remaining requests
            remaining = max_requests - (current_count + 1)

            # Calculate reset time (end of current window)
            oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_time = int(oldest[0][1]) + window_seconds - now
            else:
                reset_time = window_seconds

            return True, remaining, reset_time

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open: allow request if Redis is unavailable
            return True, max_requests, window_seconds

    async def reset_rate_limit(self, identifier: str, tier: str = None):
        """Reset rate limit for a specific identifier."""
        try:
            if tier:
                key = f"ratelimit:{tier}:{identifier}"
                await self.redis_client.delete(key)
            else:
                # Reset all tiers for this identifier
                pattern = f"ratelimit:*:{identifier}"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)

            logger.info(f"Rate limit reset for {identifier}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False

    async def get_rate_limit_stats(self, identifier: str) -> dict:
        """Get rate limit statistics for an identifier."""
        try:
            stats = {}
            for tier in self.rate_limits.keys():
                key = f"ratelimit:{tier}:{identifier}"
                count = await self.redis_client.zcard(key)
                config = self.rate_limits[tier]

                stats[tier] = {
                    "current_requests": count,
                    "max_requests": config["requests"],
                    "window_seconds": config["window"],
                    "remaining": max(0, config["requests"] - count)
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get rate limit stats: {e}")
            return {}


# Global instance
rate_limiter = RateLimitMiddleware(None)


async def initialize_rate_limiter():
    """Initialize rate limiter on application startup."""
    if settings.RATE_LIMIT_ENABLED:
        await rate_limiter.initialize()


async def shutdown_rate_limiter():
    """Shutdown rate limiter on application shutdown."""
    if settings.RATE_LIMIT_ENABLED:
        await rate_limiter.close()
