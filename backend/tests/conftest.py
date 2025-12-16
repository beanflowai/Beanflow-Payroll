"""Pytest configuration and fixtures"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables"""
    os.environ.setdefault("APP_NAME", "BeanFlow Payroll Test")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_KEY", "test-key")
    os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret")
    os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
    yield
