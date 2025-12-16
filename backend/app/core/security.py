"""Security utilities - JWT verification,  encryption"""

import logging
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.core.config import get_config

logger = logging.getLogger(__name__)


class SecurityManager:
    """Security manager for JWT verification and encryption"""

    _fernet: Fernet | None = None

    @classmethod
    def get_fernet(cls) -> Fernet | None:
        """Get Fernet encryption instance (lazy initialization)

        Returns None if ENCRYPTION_KEY is not configured.
        This is expected in Phase 0 - encryption is only needed for SIN storage in Phase 1+.
        """
        if cls._fernet is None:
            config = get_config()
            if config.encryption_key:
                try:
                    cls._fernet = Fernet(config.encryption_key.encode())
                    logger.info("Fernet encryption initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Fernet: {e}")
        return cls._fernet

    @classmethod
    def verify_supabase_jwt(cls, token: str) -> dict[str, Any] | None:
        """Verify a Supabase JWT token

        Args:
            token: JWT access token from Supabase Auth

        Returns:
            Decoded token payload or None if invalid
        """
        config = get_config()

        try:
            # Supabase uses HS256 with the JWT secret
            payload = jwt.decode(
                token,
                config.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None

    @classmethod
    def encrypt(cls, data: str) -> str | None:
        """Encrypt sensitive data using Fernet

        Args:
            data: Plain text to encrypt

        Returns:
            Encrypted string (base64) or None if encryption not configured
        """
        fernet = cls.get_fernet()
        if fernet is None:
            logger.warning("Encryption key not configured")
            return None

        try:
            return fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None

    @classmethod
    def decrypt(cls, encrypted_data: str) -> str | None:
        """Decrypt data encrypted with Fernet

        Args:
            encrypted_data: Encrypted string (base64)

        Returns:
            Decrypted plain text or None if decryption fails
        """
        fernet = cls.get_fernet()
        if fernet is None:
            logger.warning("Encryption key not configured")
            return None

        try:
            return fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None


# Convenience functions
def verify_supabase_jwt(token: str) -> dict[str, Any] | None:
    """Verify a Supabase JWT token"""
    return SecurityManager.verify_supabase_jwt(token)


def encrypt_sin(sin: str) -> str | None:
    """Encrypt a SIN number"""
    return SecurityManager.encrypt(sin)


def decrypt_sin(encrypted_sin: str) -> str | None:
    """Decrypt a SIN number"""
    return SecurityManager.decrypt(encrypted_sin)


def mask_sin(sin: str) -> str:
    """Mask a SIN number for display (***-***-XXX)"""
    if len(sin) >= 3:
        return f"***-***-{sin[-3:]}"
    return "***-***-***"
