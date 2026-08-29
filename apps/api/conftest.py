"""
Pytest configuration for PayState Bridge API tests.
Sets demo environment for all tests.
"""
import os
import pytest

os.environ.setdefault("APP_ENV", "demo")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./paystate_test.db")
