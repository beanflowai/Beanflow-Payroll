"""Security utilities - JWT verification,  encryption"""

import logging
import time
from typing import Any, cast

import httpx
from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.core.config import get_config

logger = logging.getLogger(__name__)


class SecurityManager:
    """Security manager for JWT verification and encryption"""

    _fernet: Fernet | None = None
    _jwks_cache: dict[str, Any] | None = None
    _jwks_cache_time: float = 0
    JWKS_CACHE_TTL: int = 3600  # 1 hour

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
    def get_jwks(cls, supabase_url: str) -> dict[str, Any]:
        """Fetch and cache Supabase JWKS (JSON Web Key Set)

        Args:
            supabase_url: Supabase project URL

        Returns:
            JWKS dictionary with public keys
        """
        current_time = time.time()
        if cls._jwks_cache and (current_time - cls._jwks_cache_time) < cls.JWKS_CACHE_TTL:
            return cls._jwks_cache

        jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        try:
            response = httpx.get(jwks_url, timeout=10.0)
            response.raise_for_status()
            cls._jwks_cache = response.json()
            cls._jwks_cache_time = current_time
            logger.info(f"JWKS cache refreshed from {jwks_url}")
            return cls._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            # Return cached version if available, even if expired
            if cls._jwks_cache:
                logger.warning("Using expired JWKS cache")
                return cls._jwks_cache
            return {"keys": []}

    @classmethod
    def verify_supabase_jwt(cls, token: str) -> dict[str, Any] | None:
        """Verify a Supabase JWT token

        Supports both HS256 (symmetric, using JWT secret) and ES256/RS256
        (asymmetric, using JWKS public keys).

        Args:
            token: JWT access token from Supabase Auth

        Returns:
            Decoded token payload or None if invalid
        """
        config = get_config()

        try:
            # Get unverified header to determine algorithm
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg", "HS256")

            if alg == "HS256":
                # Use JWT secret for symmetric verification
                payload = jwt.decode(
                    token,
                    config.supabase_jwt_secret,
                    algorithms=["HS256"],
                    audience="authenticated",
                )
            elif alg in ("ES256", "RS256"):
                # Use JWKS public key for asymmetric verification
                kid = unverified_header.get("kid")
                jwks = cls.get_jwks(config.supabase_url)

                # Find matching key by kid
                key = None
                for k in jwks.get("keys", []):
                    if k.get("kid") == kid:
                        key = k
                        break

                if not key:
                    logger.warning(f"No matching JWKS key found for kid: {kid}")
                    return None

                payload = jwt.decode(
                    token,
                    key,
                    algorithms=[alg],
                    audience="authenticated",
                )
            else:
                logger.warning(f"Unsupported JWT algorithm: {alg}")
                return None

            return cast(dict[str, Any], payload)
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
    """Decrypt a SIN number.

    Handles both encrypted SINs and plain-text SINs (only in debug/dev environments).
    """
    # First, try to decrypt
    decrypted = SecurityManager.decrypt(encrypted_sin)
    if decrypted:
        return decrypted

    # If decryption fails, check if it's already a plain-text SIN (9 digits)
    # Only allow this fallback in debug/development environments for safety
    config = get_config()
    if config.debug:
        clean_sin = encrypted_sin.replace("-", "").replace(" ", "")
        if len(clean_sin) == 9 and clean_sin.isdigit():
            logger.warning("Using plain-text SIN - only allowed in debug mode")
            return clean_sin

    return None


def mask_sin(sin: str) -> str:
    """Mask a SIN number for display (***-***-XXX)"""
    if len(sin) >= 3:
        return f"***-***-{sin[-3:]}"
    return "***-***-***"
