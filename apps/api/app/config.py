"""
Application configuration with safety guards.
Rejects non-demo APP_ENV and non-test Razorpay keys at startup.
"""
from __future__ import annotations

import os


class ConfigError(RuntimeError):
    pass


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


class AppConfig:
    app_env: str
    log_level: str
    database_url: str
    gemini_api_key: str | None
    razorpay_key_id: str | None
    razorpay_key_secret: str | None
    razorpay_webhook_secret: str | None
    payment_provider: str
    allowed_origins: str

    def __init__(self) -> None:
        self.app_env = _get("APP_ENV", "demo")
        self.log_level = _get("LOG_LEVEL", "info")
        self.database_url = _get("DATABASE_URL", "sqlite+aiosqlite:///./paystate.db")
        self.gemini_api_key = _get("GEMINI_API_KEY") or None
        self.razorpay_key_id = _get("RAZORPAY_KEY_ID") or None
        self.razorpay_key_secret = _get("RAZORPAY_KEY_SECRET") or None
        self.razorpay_webhook_secret = _get("RAZORPAY_WEBHOOK_SECRET") or None
        self.payment_provider = _get("PAYMENT_PROVIDER", "fake")
        self.allowed_origins = _get("ALLOWED_ORIGINS", "http://localhost:3000")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    def validate(self) -> None:
        """
        Enforce safety boundaries at startup.
        Raises ConfigError if misconfigured.
        """
        if self.app_env != "demo":
            raise ConfigError(
                f"APP_ENV must be 'demo' for this prototype. Got: {self.app_env!r}. "
                "PayState Bridge does not support live payment processing."
            )

        if self.razorpay_key_id:
            if not self.razorpay_key_id.startswith("rzp_test_"):
                raise ConfigError(
                    "RAZORPAY_KEY_ID must start with 'rzp_test_'. "
                    "Live keys are not permitted in this prototype. "
                    f"Got prefix: {self.razorpay_key_id[:8]!r}"
                )

        if self.razorpay_key_id and not self.razorpay_key_secret:
            raise ConfigError(
                "RAZORPAY_KEY_SECRET must be set when RAZORPAY_KEY_ID is set."
            )

    @property
    def razorpay_configured(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def use_fake_provider(self) -> bool:
        return not self.razorpay_configured or self.payment_provider == "fake"


settings = AppConfig()
