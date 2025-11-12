"""
Token blacklist management for JWT revocation.
Implements Redis-based token blacklisting for secure logout and forced user logout.
"""

from datetime import datetime, timedelta
from typing import Optional
import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class TokenBlacklist:
    """
    Manages JWT token blacklisting using Redis.
    Tokens are blacklisted when users logout or when admins force logout.
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.prefix = "token:blacklist:"

    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Token blacklist Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for token blacklist: {e}")
            raise

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()

    async def blacklist_token(
        self,
        token: str,
        expires_in_seconds: int,
        reason: str = "user_logout"
    ) -> bool:
        """
        Add a token to the blacklist.

        Args:
            token: The JWT token to blacklist
            expires_in_seconds: How long to keep in blacklist (match token expiry)
            reason: Reason for blacklisting (user_logout, admin_revoke, security_breach)

        Returns:
            bool: True if successful
        """
        try:
            key = f"{self.prefix}{token}"
            value = f"{reason}:{datetime.utcnow().isoformat()}"

            await self.redis_client.setex(
                key,
                expires_in_seconds,
                value
            )

            logger.info(f"Token blacklisted: reason={reason}, expires_in={expires_in_seconds}s")
            return True

        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    async def is_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            token: The JWT token to check

        Returns:
            bool: True if token is blacklisted
        """
        try:
            key = f"{self.prefix}{token}"
            result = await self.redis_client.exists(key)
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            # Fail secure: if Redis is down, deny access
            return True

    async def get_blacklist_reason(self, token: str) -> Optional[str]:
        """
        Get the reason why a token was blacklisted.

        Args:
            token: The JWT token

        Returns:
            Optional[str]: Reason and timestamp, or None if not blacklisted
        """
        try:
            key = f"{self.prefix}{token}"
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Failed to get blacklist reason: {e}")
            return None

    async def blacklist_all_user_tokens(
        self,
        user_id: int,
        reason: str = "admin_revoke"
    ) -> int:
        """
        Blacklist all tokens for a specific user.
        Useful for forced logout or security incidents.

        Args:
            user_id: The user ID
            reason: Reason for blacklisting all tokens

        Returns:
            int: Number of tokens blacklisted
        """
        try:
            # Store user ID in blacklist with longer expiry
            # All token checks will also verify against this list
            key = f"user:blacklist:all:{user_id}"
            value = f"{reason}:{datetime.utcnow().isoformat()}"

            # Keep for 7 days (max refresh token lifetime)
            await self.redis_client.setex(
                key,
                timedelta(days=7).total_seconds(),
                value
            )

            logger.warning(f"All tokens blacklisted for user {user_id}: {reason}")
            return 1

        except Exception as e:
            logger.error(f"Failed to blacklist all user tokens: {e}")
            return 0

    async def is_user_blacklisted(self, user_id: int) -> bool:
        """
        Check if all tokens for a user are blacklisted.

        Args:
            user_id: The user ID

        Returns:
            bool: True if all user tokens are blacklisted
        """
        try:
            key = f"user:blacklist:all:{user_id}"
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to check user blacklist: {e}")
            return True  # Fail secure

    async def clear_user_blacklist(self, user_id: int) -> bool:
        """
        Remove user from blacklist (allow login again).

        Args:
            user_id: The user ID

        Returns:
            bool: True if successful
        """
        try:
            key = f"user:blacklist:all:{user_id}"
            await self.redis_client.delete(key)
            logger.info(f"User {user_id} removed from blacklist")
            return True
        except Exception as e:
            logger.error(f"Failed to clear user blacklist: {e}")
            return False

    async def get_blacklist_stats(self) -> dict:
        """
        Get statistics about blacklisted tokens.

        Returns:
            dict: Blacklist statistics
        """
        try:
            # Count blacklisted tokens
            token_keys = await self.redis_client.keys(f"{self.prefix}*")
            user_keys = await self.redis_client.keys("user:blacklist:all:*")

            return {
                "blacklisted_tokens": len(token_keys),
                "blacklisted_users": len(user_keys),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get blacklist stats: {e}")
            return {
                "blacklisted_tokens": 0,
                "blacklisted_users": 0,
                "error": str(e)
            }


# Global instance
token_blacklist = TokenBlacklist()


async def initialize_token_blacklist():
    """Initialize the token blacklist on application startup."""
    await token_blacklist.initialize()


async def shutdown_token_blacklist():
    """Shutdown the token blacklist on application shutdown."""
    await token_blacklist.close()
