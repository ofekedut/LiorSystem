from datetime import datetime
import uuid
import logging

from server.database.database import get_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    pass


class TokenBlacklist:
    @classmethod
    async def add_to_blacklist(cls, jti: uuid.UUID, user_id: uuid.UUID, expires_at: datetime):
        conn = await  get_connection()
        try:
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO token_blacklist (jti, user_id, expires_at)
                    VALUES ($1, $2, $3)
                    """,
                    jti, user_id, expires_at
                )
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")

    @classmethod
    async def is_blacklisted(cls, jti: uuid.UUID) -> bool:
        conn = await get_connection()
        async with conn.transaction():
            try:
                async with conn.transaction():
                    result = await conn.fetchval(
                        "SELECT EXISTS(SELECT 1 FROM token_blacklist WHERE jti = $1)",
                        jti
                    )
                    return bool(result)
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                raise DatabaseError(f"Database operation failed: {str(e)}")

    @classmethod
    async def cleanup_expired(cls, batch_size: int = 1000) -> int:
        async with get_connection() as conn:
            try:
                async with conn.transaction():
                    result = await conn.execute(
                        """
                        WITH expired AS (
                            SELECT jti FROM token_blacklist 
                            WHERE expires_at < NOW()
                            LIMIT $1
                        )
                        DELETE FROM token_blacklist 
                        WHERE jti IN (SELECT jti FROM expired)
                        """,
                        batch_size
                    )
                    return int(result.split()[-1])
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                raise DatabaseError(f"Database operation failed: {str(e)}")


class LoginAttempts:
    @classmethod
    async def record_attempt(cls, email: str, max_attempts: int = 5, lockout_minutes: int = 15) -> bool:
        conn = await get_connection()
        async with conn.transaction():
            try:
                async with conn.transaction():
                    result = await conn.fetchrow("""
                            INSERT INTO login_attempts (email) 
                            VALUES ($1)
                            ON CONFLICT (email) DO UPDATE 
                            SET attempts = CASE 
                                WHEN login_attempts.locked_until IS NULL OR 
                                    login_attempts.locked_until < NOW()
                                THEN login_attempts.attempts + 1
                                ELSE login_attempts.attempts
                            END,
                            last_attempt = NOW(),
                            locked_until = CASE 
                                WHEN (login_attempts.attempts + 1 >= $2) AND
                                    (login_attempts.locked_until IS NULL OR 
                                    login_attempts.locked_until < NOW())
                                THEN NOW() + interval '1 minute' * $3
                                ELSE login_attempts.locked_until
                            END
                            RETURNING attempts, locked_until;
                            """, email, max_attempts, lockout_minutes)
                    return bool(result['locked_until'])
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                raise DatabaseError(f"Database operation failed: {str(e)}")

    @classmethod
    async def is_locked(cls, email: str) -> bool:
        conn = await  get_connection()
        async with conn.transaction():
            try:
                async with conn.transaction():
                    locked = await conn.fetchval("""
                            SELECT locked_until > NOW()
                            FROM login_attempts 
                            WHERE email = $1
                            """, email)
                    return bool(locked)
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                raise DatabaseError(f"Database operation failed: {str(e)}")

    @classmethod
    async def reset_attempts(self, email: str):
        conn = await get_connection()
        async with conn.transaction():
            try:
                async with conn.transaction():
                    await conn.execute("""
                            DELETE FROM login_attempts 
                            WHERE email = $1
                            """, email)
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                raise DatabaseError(f"Database operation failed: {str(e)}")

    @classmethod
    async def cleanup_stale(cls, older_than_days: int = 30, batch_size: int = 1000) -> int:
        conn = await get_connection()
        async with conn.transaction():
            try:
                async with conn.transaction():
                    result = await conn.execute("""
                            WITH stale AS (
                                SELECT email FROM login_attempts 
                                WHERE (last_attempt < NOW() - interval '1 day' * $1
                                    AND locked_until IS NULL)
                                OR (locked_until < NOW())
                                LIMIT $2
                            )
                            DELETE FROM login_attempts 
                            WHERE email IN (SELECT email FROM stale)
                            """, older_than_days, batch_size)
                    return int(result.split()[-1])
            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                raise DatabaseError(f"Database operation failed: {str(e)}")


async def get_current_user_id():
    """
    In a real application, this would fetch the current user ID from the request context
    or JWT token. For simplicity, we'll return a fixed user ID for testing.
    """
    # This is a placeholder - in production, you would extract this from the authentication system
    return uuid.UUID("00000000-0000-0000-0000-000000000001")
